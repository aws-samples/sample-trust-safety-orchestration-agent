import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from repositories import evidence_repository, blocklist_repository
from services import content_analysis_service, image_analysis_service

logger = logging.getLogger(__name__)

PLATFORM_USER_API_URL = os.environ.get("PLATFORM_USER_API_URL", "")
PLATFORM_MESSAGING_API_URL = os.environ.get("PLATFORM_MESSAGING_API_URL", "")


def _call_platform_api(url: str, params: dict | None = None) -> dict:
    import urllib.request
    full_url = url
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        full_url = f"{url}?{qs}"
    try:
        req = urllib.request.Request(full_url, headers={"X-Api-Key": os.environ.get("PLATFORM_API_KEY", "")})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        logger.warning("Platform API call failed", extra={"url": url, "error": str(e)})
        return {}


def gather_profile_metadata(user_id: str) -> dict:
    data = _call_platform_api(f"{PLATFORM_USER_API_URL}/{user_id}")
    return {
        "user_id": user_id,
        "created_at": data.get("created_at", ""),
        "device_fingerprint": data.get("device_fingerprint", ""),
        "ip_address": data.get("ip_address", ""),
        "registration_method": data.get("registration_method", ""),
        "account_age_days": data.get("account_age_days", 0),
    }


def gather_message_history(user_id: str, days: int = 30) -> dict:
    data = _call_platform_api(
        f"{PLATFORM_MESSAGING_API_URL}/{user_id}/messages",
        {"days": str(days)},
    )
    messages = data.get("messages", [])
    return {
        "user_id": user_id,
        "message_count": len(messages),
        "messages": messages,
        "period_days": days,
    }


def gather_previous_reports(user_id: str) -> list[dict]:
    data = _call_platform_api(f"{PLATFORM_USER_API_URL}/{user_id}/reports")
    return data.get("reports", [])


def assemble_evidence_package(case_id: str, user_id: str) -> dict:
    start_time = time.time()
    package = {
        "case_id": case_id,
        "user_id": user_id,
        "unavailable_sources": [],
        "assembled_at": datetime.now(timezone.utc).isoformat(),
    }

    tasks = {
        "profile_metadata": lambda: gather_profile_metadata(user_id),
        "message_history": lambda: gather_message_history(user_id),
        "previous_reports": lambda: gather_previous_reports(user_id),
    }

    results = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fn): name for name, fn in tasks.items()}
        for future in as_completed(futures, timeout=55):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception as e:
                logger.error(f"Evidence source failed: {name}", extra={"error": str(e)})
                results[name] = None
                package["unavailable_sources"].append(name)

    package["profile_metadata"] = results.get("profile_metadata") or {}
    package["previous_reports"] = results.get("previous_reports") or []

    message_history = results.get("message_history") or {}
    messages = message_history.get("messages", [])

    if messages:
        try:
            package["message_analysis"] = content_analysis_service.analyze_messages(messages)
        except Exception as e:
            logger.error("Message analysis failed", extra={"error": str(e)})
            package["message_analysis"] = {}
            package["unavailable_sources"].append("message_analysis")
    else:
        package["message_analysis"] = {"message_count": 0}

    profile = package["profile_metadata"]
    photo_urls = profile.get("photo_urls", []) if profile else []
    if photo_urls:
        try:
            package["image_analysis"] = image_analysis_service.analyze_profile_images(photo_urls)
        except Exception as e:
            logger.error("Image analysis failed", extra={"error": str(e)})
            package["image_analysis"] = {}
            package["unavailable_sources"].append("image_analysis")
    else:
        package["image_analysis"] = {}

    fingerprint = profile.get("device_fingerprint", "") if profile else ""
    if fingerprint:
        match = blocklist_repository.check_fingerprint(fingerprint)
        package["bad_actor_matches"] = [match] if match else []
    else:
        package["bad_actor_matches"] = []

    crisis = package.get("message_analysis", {}).get("crisis_indicators")
    package["crisis_detected"] = crisis is not None
    package["sensitive_category"] = crisis.get("type") if crisis else None

    evidence_repository.store_evidence_package(case_id, package)

    for source_name in ("profile_metadata", "message_analysis", "image_analysis"):
        data = package.get(source_name)
        if data and source_name not in package["unavailable_sources"]:
            evidence_repository.store_evidence(case_id, source_name, data)
        elif source_name in package["unavailable_sources"]:
            evidence_repository.mark_source_unavailable(case_id, source_name)

    elapsed = time.time() - start_time
    logger.info("Evidence assembly complete", extra={
        "case_id": case_id,
        "elapsed_seconds": round(elapsed, 2),
        "unavailable": package["unavailable_sources"],
    })
    package["assembly_time_seconds"] = round(elapsed, 2)
    return package
