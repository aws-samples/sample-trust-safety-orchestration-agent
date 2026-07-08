import json
import logging

from services import escalation_service

logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    logger.info("Escalation handler invoked", extra={"event": json.dumps(event)[:500]})

    case_id = event["case_id"]
    user_id = event["user_id"]
    evidence = event.get("evidence")
    confidence = event.get("confidence")
    reason = event.get("reason", "system_error")

    logger.info(
        "Escalating case",
        extra={"case_id": case_id, "user_id": user_id, "reason": reason},
    )

    result = escalation_service.escalate_case(
        case_id=case_id,
        user_id=user_id,
        evidence=evidence,
        confidence=confidence,
        reason=reason,
    )

    logger.info(
        "Case escalated",
        extra={
            "case_id": case_id,
            "queue_id": result.get("queue_id"),
            "priority": result.get("priority"),
        },
    )

    return result
