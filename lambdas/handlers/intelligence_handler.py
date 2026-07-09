import json
import logging

from services import intelligence_service

logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    try:
        path = event.get("path", "") or event.get("resource", "")

        if path.endswith("/ingest"):
            return _handle_ingest(event)
        elif path.endswith("/publish"):
            return _handle_publish(event)
        else:
            return _response(404, {"error": f"Unknown path: {path}"})

    except ValueError as e:
        return _response(400, {"error": str(e)})
    except Exception:
        logger.exception("Handler error")
        return _response(500, {"error": "Internal server error"})


def _handle_ingest(event):
    body = json.loads(event.get("body") or "{}")

    source_platform = body.get("source_platform")
    bad_actors = body.get("bad_actors")

    if not source_platform:
        raise ValueError("source_platform is required")
    if not bad_actors or not isinstance(bad_actors, list):
        raise ValueError("bad_actors array is required")

    result = intelligence_service.ingest_external_intelligence(
        source_platform=source_platform,
        bad_actors=bad_actors,
    )

    return _response(200, result)


def _handle_publish(event):
    body = json.loads(event.get("body") or "{}")

    user_id = body.get("user_id")
    fingerprint_hash = body.get("fingerprint_hash")
    signature_hash = body.get("signature_hash")
    ban_reason = body.get("ban_reason")

    if not all([user_id, fingerprint_hash, signature_hash, ban_reason]):
        raise ValueError("user_id, fingerprint_hash, signature_hash, and ban_reason are required")

    result = intelligence_service.publish_bad_actor(
        user_id=user_id,
        fingerprint_hash=fingerprint_hash,
        signature_hash=signature_hash,
        ban_reason=ban_reason,
    )

    return _response(200, result)


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body, default=str),
    }
