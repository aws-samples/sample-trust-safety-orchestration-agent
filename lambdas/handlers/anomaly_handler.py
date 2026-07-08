import json
import logging
import time

from services import anomaly_detection_service

logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        user_ids = body.get("user_ids", [])

        if not user_ids:
            return _response(400, {"error": "user_ids is required and must be non-empty"})
        if len(user_ids) > 100:
            return _response(400, {"error": "Maximum 100 user_ids per request"})

        start = time.time()
        results = []
        for user_id in user_ids:
            metrics = body.get("behavioral_metrics", {}).get(user_id, {})
            result = anomaly_detection_service.calculate_anomaly_score(user_id, metrics)
            results.append(result)

        processing_time_ms = int((time.time() - start) * 1000)

        return _response(200, {
            "results": results,
            "processing_time_ms": processing_time_ms,
        })
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON body"})
    except Exception as e:
        logger.exception("Anomaly handler error")
        return _response(500, {"error": "Internal server error"})


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body, default=str),
    }
