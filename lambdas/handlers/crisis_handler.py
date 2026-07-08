import json
import logging

from services import crisis_response_service

logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")

        user_id = body.get("user_id")
        crisis_type = body.get("crisis_type")
        case_id = body.get("case_id")

        if not user_id:
            raise ValueError("user_id is required")
        if not crisis_type:
            raise ValueError("crisis_type is required")
        if not case_id:
            raise ValueError("case_id is required")

        result = crisis_response_service.handle_crisis_detection(
            case_id=case_id,
            user_id=user_id,
            crisis_type=crisis_type,
        )

        return _response(200, result)

    except ValueError as e:
        return _response(400, {"error": str(e)})
    except Exception as e:
        logger.exception("Handler error")
        return _response(500, {"error": "Internal server error"})


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body, default=str),
    }
