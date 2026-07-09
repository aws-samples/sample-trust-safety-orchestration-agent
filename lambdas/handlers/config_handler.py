import json
import logging

from repositories import config_repository
from services import audit_service

logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    try:
        path = event.get("resource", event.get("path", ""))
        method = event.get("httpMethod", "GET")

        if method == "GET" and "current" in path:
            return _get_current_config(event)
        elif method == "PUT" and "thresholds" in path:
            return _update_thresholds(event)
        elif method == "POST" and "rollback" in path:
            return _rollback_config(event)
        else:
            return _response(404, {"error": "Not found"})
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON body"})
    except ValueError as e:
        return _response(400, {"error": str(e)})
    except Exception:
        logger.exception("Config handler error")
        return _response(500, {"error": "Internal server error"})


def _get_admin_id(event):
    claims = event.get("requestContext", {}).get("authorizer", {}).get("claims", {})
    return claims.get("sub", "unknown")


def _get_current_config(event):
    configs = config_repository.get_all_active_configs()
    return _response(200, {"configs": configs})


def _update_thresholds(event):
    body = json.loads(event.get("body", "{}"))
    admin_id = _get_admin_id(event)

    violation_type = body.get("violation_type")
    if not violation_type:
        return _response(400, {"error": "violation_type is required"})

    for key in ("autonomous_threshold", "investigation_trigger_threshold"):
        if key in body:
            valid, msg = config_repository.validate_threshold(body[key])
            if not valid:
                return _response(400, {"error": f"{key}: {msg}"})

    config_key = f"threshold_{violation_type}"
    previous = config_repository.get_active_value(config_key)
    version_id = config_repository.update_config(config_key, body, admin_id)

    audit_service.log_config_change(
        admin_id=admin_id,
        config_key=config_key,
        previous_value=previous,
        new_value=body,
    )

    return _response(200, {
        "config_key": config_key,
        "version_id": version_id,
        "status": "updated",
    })


def _rollback_config(event):
    body = json.loads(event.get("body", "{}"))
    admin_id = _get_admin_id(event)

    config_key = body.get("config_key")
    version_id = body.get("version_id")
    if not config_key or not version_id:
        return _response(400, {"error": "config_key and version_id are required"})

    previous = config_repository.get_active_value(config_key)
    new_version = config_repository.rollback_config(config_key, version_id, admin_id)

    audit_service.log_config_change(
        admin_id=admin_id,
        config_key=config_key,
        previous_value=previous,
        new_value={"rolled_back_to": version_id},
    )

    return _response(200, {
        "config_key": config_key,
        "new_version_id": new_version,
        "rolled_back_to": version_id,
        "status": "rolled_back",
    })


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body, default=str),
    }
