import hashlib
import json
import logging
import os
from datetime import datetime, timezone

from repositories import blocklist_repository, audit_repository

logger = logging.getLogger(__name__)

PARTNER_NETWORK_INTEL_API_URL = os.environ.get("PARTNER_NETWORK_INTEL_API_URL", "")


def generate_fingerprint_hash(fingerprint: dict) -> str:
    normalized = json.dumps(fingerprint, sort_keys=True)
    return hashlib.sha256(normalized.encode()).hexdigest()


def generate_behavioral_signature_hash(signature: dict) -> str:
    normalized = json.dumps(signature, sort_keys=True)
    return hashlib.sha256(normalized.encode()).hexdigest()


def check_blocklist_match(
    device_fingerprint: str | dict,
    behavioral_signature: str | dict | None = None,
) -> dict | None:
    if isinstance(device_fingerprint, dict):
        fp_hash = generate_fingerprint_hash(device_fingerprint)
    else:
        fp_hash = device_fingerprint

    fp_match = blocklist_repository.check_fingerprint(fp_hash)
    if fp_match:
        return {
            "match_type": "fingerprint",
            "confidence": float(fp_match.get("confidence_score", 1.0)),
            "source_platform": fp_match.get("source_platform"),
            "ban_reason": fp_match.get("ban_reason"),
        }

    if behavioral_signature:
        if isinstance(behavioral_signature, dict):
            sig_hash = generate_behavioral_signature_hash(behavioral_signature)
        else:
            sig_hash = behavioral_signature

        sig_match = blocklist_repository.check_signature(sig_hash)
        if sig_match:
            return {
                "match_type": "behavioral_signature",
                "confidence": float(sig_match.get("confidence_score", 1.0)),
                "source_platform": sig_match.get("source_platform"),
                "ban_reason": sig_match.get("ban_reason"),
            }

    return None


def ingest_external_intelligence(
    source_platform: str,
    bad_actors: list[dict],
) -> dict:
    processed = 0
    errors = 0

    for actor in bad_actors:
        try:
            blocklist_repository.add_bad_actor(
                fingerprint_hash=actor["fingerprint_hash"],
                signature_hash=actor.get("behavioral_signature_hash", ""),
                source_platform=source_platform,
                ban_reason=actor.get("ban_reason", "unknown"),
                confidence_score=float(actor.get("confidence_score", 1.0)),
            )
            processed += 1
        except Exception as e:
            logger.error("Failed to ingest bad actor", extra={"error": str(e)})
            errors += 1

    audit_repository.write_log(
        event_type="intelligence_ingest",
        action="ingest_external",
        reasoning=f"Ingested {processed} bad actors from {source_platform} ({errors} errors)",
    )

    logger.info("Intelligence ingested", extra={
        "source": source_platform,
        "processed": processed,
        "errors": errors,
    })

    return {
        "source_platform": source_platform,
        "processed_count": processed,
        "error_count": errors,
    }


def publish_bad_actor(
    user_id: str,
    fingerprint_hash: str,
    signature_hash: str,
    ban_reason: str,
) -> dict:
    if not PARTNER_NETWORK_INTEL_API_URL:
        logger.warning("Partner Network Intel API URL not configured, skipping publish")
        return {"published": False, "reason": "api_not_configured"}

    payload = {
        "source_platform": "platform",
        "bad_actors": [
            {
                "fingerprint_hash": fingerprint_hash,
                "behavioral_signature_hash": signature_hash,
                "ban_reason": ban_reason,
                "ban_timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ],
    }

    _validate_no_pii(payload)

    try:
        import urllib.request
        req = urllib.request.Request(
            f"{PARTNER_NETWORK_INTEL_API_URL}/intelligence/ingest",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())

        audit_repository.write_log(
            event_type="intelligence_publish",
            action="publish_to_partners",
            user_id=user_id,
            reasoning=f"Published bad actor data to Partner Network partners: {ban_reason}",
        )

        logger.info("Bad actor published", extra={"user_id": user_id})
        return {"published": True, "result": result}

    except Exception as e:
        logger.error("Failed to publish intelligence", extra={"error": str(e)})
        return {"published": False, "reason": str(e), "queued_for_retry": True}


def _validate_no_pii(payload: dict) -> None:
    payload_str = json.dumps(payload).lower()
    pii_indicators = ["@", "name", "email", "phone", "address", "ssn"]
    for indicator in pii_indicators:
        if indicator in payload_str:
            for actor in payload.get("bad_actors", []):
                keys = set(actor.keys())
                allowed = {"fingerprint_hash", "behavioral_signature_hash", "ban_reason", "ban_timestamp", "confidence_score"}
                extra = keys - allowed
                if extra:
                    raise ValueError(f"Potential PII detected in intelligence payload: {extra}")
