import json
import logging
import os
import time
from datetime import datetime, timezone

import boto3

from repositories import (
    case_repository,
    blocklist_repository,
    audit_repository,
    appeal_repository,
)

logger = logging.getLogger(__name__)

PLATFORM_USER_API_URL = os.environ.get("PLATFORM_USER_API_URL", "")
NOTIFICATION_QUEUE_URL = os.environ.get("NOTIFICATION_QUEUE_URL", "")

VALID_ACTIONS = {
    "warning",
    "content_removal",
    "rate_limit",
    "temporary_suspension",
    "permanent_ban",
}


def _call_platform_enforcement(user_id: str, action: str, params: dict | None = None) -> dict:
    import urllib.request
    url = f"{PLATFORM_USER_API_URL}/{user_id}/enforce"
    payload = json.dumps({"action": action, **(params or {})}).encode()
    try:
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "X-Api-Key": os.environ.get("PLATFORM_API_KEY", ""),
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        logger.error("Platform enforcement API failed", extra={"user_id": user_id, "error": str(e)})
        raise


def _queue_notification(user_id: str, notification_type: str, data: dict) -> None:
    if not NOTIFICATION_QUEUE_URL:
        logger.warning("Notification queue URL not configured")
        return
    sqs = boto3.client("sqs")
    sqs.send_message(
        QueueUrl=NOTIFICATION_QUEUE_URL,
        MessageBody=json.dumps({
            "user_id": user_id,
            "notification_type": notification_type,
            "data": data,
            "queued_at": datetime.now(timezone.utc).isoformat(),
        }),
    )


def execute_action(
    case_id: str,
    user_id: str,
    action: str,
    violation_type: str,
    confidence_score: float,
    is_autonomous: bool = True,
    reviewer_id: str | None = None,
    duration_hours: int | None = None,
) -> dict:
    if action not in VALID_ACTIONS:
        raise ValueError(f"Invalid enforcement action: {action}")

    start_time = time.time()
    decision_source = "autonomous" if is_autonomous else "human"

    audit_id = audit_repository.write_log(
        event_type="enforcement",
        action=action,
        case_id=case_id,
        user_id=user_id,
        violation_type=violation_type,
        confidence_score=confidence_score,
        decision_source=decision_source,
        reasoning=f"{decision_source} enforcement: {violation_type} ({confidence_score:.2%} confidence)",
    )

    params = {}
    if duration_hours and action == "temporary_suspension":
        params["duration_hours"] = duration_hours

    _call_platform_enforcement(user_id, action, params)

    if action == "permanent_ban":
        _handle_permanent_ban(user_id, violation_type)

    appeal_id = appeal_repository.create_enforcement_appeal_record(
        case_id=case_id,
        user_id=user_id,
        enforcement_action=action,
    )

    _queue_notification(user_id, "enforcement", {
        "case_id": case_id,
        "violation_type": violation_type,
        "action": action,
        "duration_hours": duration_hours,
        "appeal_id": appeal_id,
    })

    elapsed_ms = int((time.time() - start_time) * 1000)

    case_repository.update_case(
        case_id,
        status="resolved",
        enforcement_action=action,
        decision_source=decision_source,
        resolved_at=datetime.now(timezone.utc).isoformat(),
    )
    case_repository.append_audit_trail_id(case_id, audit_id)

    logger.info("Enforcement action executed", extra={
        "case_id": case_id,
        "action": action,
        "elapsed_ms": elapsed_ms,
    })

    return {
        "case_id": case_id,
        "audit_trail_id": audit_id,
        "action_status": "completed",
        "action": action,
        "user_notified": True,
        "appeal_id": appeal_id,
        "response_time_ms": elapsed_ms,
    }


def _handle_permanent_ban(user_id: str, violation_type: str) -> None:
    import hashlib
    fp_hash = hashlib.sha256(f"fp:{user_id}".encode()).hexdigest()
    sig_hash = hashlib.sha256(f"sig:{user_id}".encode()).hexdigest()
    blocklist_repository.add_bad_actor(
        fingerprint_hash=fp_hash,
        signature_hash=sig_hash,
        source_platform="platform",
        ban_reason=violation_type,
    )


def execute_bulk_action(
    case_id: str,
    user_ids: list[str],
    action: str,
    violation_type: str,
    attack_pattern: str | None = None,
) -> dict:
    if len(user_ids) > 500:
        raise ValueError("Bulk action limited to 500 users")

    audit_id = audit_repository.write_log(
        event_type="bulk_enforcement",
        action=action,
        case_id=case_id,
        reasoning=f"Bulk {action}: {len(user_ids)} users, pattern: {attack_pattern}",
    )

    succeeded = []
    failed = []
    batch_size = 100

    for i in range(0, len(user_ids), batch_size):
        batch = user_ids[i:i + batch_size]
        for uid in batch:
            try:
                _call_platform_enforcement(uid, action)
                succeeded.append(uid)
                if action == "permanent_ban":
                    _handle_permanent_ban(uid, violation_type)
            except Exception as e:
                logger.error("Bulk action failed for user", extra={"user_id": uid, "error": str(e)})
                failed.append(uid)

    case_repository.update_case(
        case_id,
        status="resolved",
        enforcement_action=f"bulk_{action}",
        decision_source="autonomous",
    )

    logger.info("Bulk enforcement complete", extra={
        "case_id": case_id,
        "succeeded": len(succeeded),
        "failed": len(failed),
    })

    return {
        "case_id": case_id,
        "audit_trail_id": audit_id,
        "total_users": len(user_ids),
        "succeeded": len(succeeded),
        "failed": len(failed),
        "failed_user_ids": failed,
    }
