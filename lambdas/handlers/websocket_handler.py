import json
import logging
import os

import boto3

from repositories import websocket_repository
from services import metrics_aggregation_service

logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    try:
        # Determine if this is a WebSocket event or a scheduled broadcast
        request_context = event.get("requestContext", {})
        route_key = request_context.get("routeKey")

        if route_key == "$connect":
            return _handle_connect(event)
        elif route_key == "$disconnect":
            return _handle_disconnect(event)
        elif route_key == "$default":
            return _handle_default(event)
        else:
            # Scheduled broadcast (e.g., from EventBridge or direct invoke)
            body = event if isinstance(event, dict) else json.loads(event)
            if body.get("action") == "broadcast_metrics":
                return _handle_broadcast()
            return {"statusCode": 200}

    except Exception:
        logger.exception("WebSocket handler error")
        return {"statusCode": 200}


def _handle_connect(event):
    connection_id = event["requestContext"]["connectionId"]
    # Extract user_id from query string or authorizer if available
    query_params = event.get("queryStringParameters") or {}
    user_id = query_params.get("user_id", "anonymous")

    websocket_repository.save_connection(connection_id, user_id)

    return {"statusCode": 200}


def _handle_disconnect(event):
    connection_id = event["requestContext"]["connectionId"]
    websocket_repository.remove_connection(connection_id)

    return {"statusCode": 200}


def _handle_default(event):
    body = json.loads(event.get("body") or "{}")

    if body.get("action") == "broadcast_metrics":
        return _handle_broadcast()

    return {"statusCode": 200}


def _handle_broadcast():
    endpoint = os.environ.get("WEBSOCKET_API_ENDPOINT")
    if not endpoint:
        logger.warning("WEBSOCKET_API_ENDPOINT not configured, skipping broadcast")
        return {"statusCode": 200}

    management_client = boto3.client(
        "apigatewaymanagementapi",
        endpoint_url=endpoint,
    )

    metrics = metrics_aggregation_service.get_realtime_metrics()
    payload = json.dumps(metrics, default=str).encode("utf-8")

    connection_ids = websocket_repository.get_all_connections()

    for connection_id in connection_ids:
        try:
            management_client.post_to_connection(
                ConnectionId=connection_id,
                Data=payload,
            )
        except management_client.exceptions.GoneException:
            logger.info("Removing stale connection", extra={"connection_id": connection_id})
            websocket_repository.remove_connection(connection_id)
        except Exception as e:
            logger.warning(
                "Failed to post to connection",
                extra={"connection_id": connection_id, "error": str(e)},
            )

    return {"statusCode": 200}
