import json
import logging

from repositories import audit_repository
from services import notification_service

logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    logger.info("Notification processor invoked", extra={"record_count": len(event.get("Records", []))})

    batch_item_failures = []

    for record in event.get("Records", []):
        try:
            _process_record(record)
        except Exception as e:
            logger.error(
                "Failed to process notification record",
                extra={"error": str(e), "message_id": record.get("messageId")},
            )
            batch_item_failures.append({
                "itemIdentifier": record["messageId"],
            })

    return {"batchItemFailures": batch_item_failures}


def _process_record(record):
    body = json.loads(record["body"])
    user_id = body["user_id"]
    notification_type = body["notification_type"]
    data = body.get("data", {})

    logger.info(
        "Processing notification",
        extra={"user_id": user_id, "notification_type": notification_type},
    )

    if notification_type == "enforcement":
        result = notification_service.send_enforcement_notification(
            user_id=user_id,
            enforcement_id=data.get("enforcement_id", data.get("case_id", "")),
            violation_type=data.get("violation_type", "unknown"),
            action=data.get("action", "unknown"),
        )

    elif notification_type == "appeal_acknowledgment":
        result = notification_service.send_appeal_acknowledgment(
            user_id=user_id,
            appeal_id=data.get("appeal_id", ""),
            expected_review_time=data.get("expected_review_time", "24-48 hours"),
        )

    elif notification_type == "wellbeing_resources":
        result = notification_service.send_wellbeing_resources(
            user_id=user_id,
            crisis_type=data.get("crisis_type", "unknown"),
        )

    else:
        logger.warning("Unknown notification type", extra={"notification_type": notification_type})
        result = None

    audit_repository.write_log(
        event_type="notification_processed",
        action=f"send_{notification_type}",
        user_id=user_id,
        reasoning=f"Notification type={notification_type} processed successfully",
    )

    logger.info(
        "Notification processed",
        extra={"user_id": user_id, "notification_type": notification_type, "result": str(result)[:200]},
    )
