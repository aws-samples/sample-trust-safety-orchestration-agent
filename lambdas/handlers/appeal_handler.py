import json
import logging

from repositories import appeal_repository
from services import escalation_service, notification_service

logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")

        enforcement_id = body.get("enforcement_id")
        appeal_reason = body.get("appeal_reason")
        supporting_info = body.get("supporting_info")

        if not enforcement_id:
            raise ValueError("enforcement_id is required")
        if not appeal_reason:
            raise ValueError("appeal_reason is required")

        user_id = event["requestContext"]["authorizer"]["claims"]["sub"]

        appeal = appeal_repository.create_appeal(
            enforcement_id=enforcement_id,
            user_id=user_id,
            appeal_reason=appeal_reason,
            supporting_info=supporting_info,
        )

        escalation_service.escalate_case(
            case_id=enforcement_id,
            user_id=user_id,
            reason="appeal",
        )

        notification_service.send_appeal_acknowledgment(
            user_id=user_id,
            appeal_id=appeal["appeal_id"],
        )

        return _response(201, {
            "appeal_id": appeal["appeal_id"],
            "status": appeal["status"],
        })

    except ValueError as e:
        return _response(400, {"error": str(e)})
    except KeyError as e:
        logger.exception("Missing required field in event")
        return _response(401, {"error": "Unauthorized: missing user identity"})
    except Exception as e:
        logger.exception("Handler error")
        return _response(500, {"error": "Internal server error"})


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body, default=str),
    }
