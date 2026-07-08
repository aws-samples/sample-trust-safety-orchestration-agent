import logging
import time
from datetime import datetime, timezone

from .base import get_table

logger = logging.getLogger(__name__)

TTL_HOURS = 24


def _table():
    return get_table("WEBSOCKET_CONNECTIONS_TABLE")


def save_connection(connection_id: str, user_id: str) -> None:
    ttl = int(time.time()) + (TTL_HOURS * 3600)
    _table().put_item(
        Item={
            "connection_id": connection_id,
            "user_id": user_id,
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "last_ping": datetime.now(timezone.utc).isoformat(),
            "ttl": ttl,
        }
    )
    logger.info("WebSocket connection saved", extra={"connection_id": connection_id})


def remove_connection(connection_id: str) -> None:
    _table().delete_item(Key={"connection_id": connection_id})
    logger.info("WebSocket connection removed", extra={"connection_id": connection_id})


def get_all_connections() -> list[str]:
    connection_ids = []
    resp = _table().scan(ProjectionExpression="connection_id")
    connection_ids.extend(item["connection_id"] for item in resp.get("Items", []))
    while resp.get("LastEvaluatedKey"):
        resp = _table().scan(
            ProjectionExpression="connection_id",
            ExclusiveStartKey=resp["LastEvaluatedKey"],
        )
        connection_ids.extend(item["connection_id"] for item in resp.get("Items", []))
    return connection_ids


def update_last_ping(connection_id: str) -> None:
    ttl = int(time.time()) + (TTL_HOURS * 3600)
    _table().update_item(
        Key={"connection_id": connection_id},
        UpdateExpression="SET last_ping = :now, #t = :ttl",
        ExpressionAttributeNames={"#t": "ttl"},
        ExpressionAttributeValues={
            ":now": datetime.now(timezone.utc).isoformat(),
            ":ttl": ttl,
        },
    )
