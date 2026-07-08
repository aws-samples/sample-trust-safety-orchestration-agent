import json
import logging

from services import enforcement_engine_service

logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    logger.info("Enforcement executor invoked", extra={"event": json.dumps(event)[:500]})

    case_id = event["case_id"]
    user_id = event["user_id"]
    action = event["action"]
    violation_type = event["violation_type"]
    confidence_score = event["confidence_score"]
    is_autonomous = event.get("is_autonomous", True)

    logger.info(
        "Executing enforcement action",
        extra={
            "case_id": case_id,
            "user_id": user_id,
            "action": action,
            "violation_type": violation_type,
            "confidence_score": confidence_score,
            "is_autonomous": is_autonomous,
        },
    )

    result = enforcement_engine_service.execute_action(
        case_id=case_id,
        user_id=user_id,
        action=action,
        violation_type=violation_type,
        confidence_score=confidence_score,
        is_autonomous=is_autonomous,
    )

    logger.info(
        "Enforcement action complete",
        extra={
            "case_id": case_id,
            "action_status": result.get("action_status"),
            "response_time_ms": result.get("response_time_ms"),
        },
    )

    return result
