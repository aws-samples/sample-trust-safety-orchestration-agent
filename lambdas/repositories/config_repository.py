import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

import ulid
from boto3.dynamodb.conditions import Key

from .base import get_table, get_s3_client, get_bucket_name

logger = logging.getLogger(__name__)


def _table():
    return get_table("CONFIG_TABLE")


def _backup_bucket():
    return get_bucket_name("CONFIG_BACKUPS_BUCKET")


def _serialize_value(value: Any) -> dict:
    return json.loads(json.dumps(value), parse_float=Decimal)


def get_config(key: str) -> Optional[dict]:
    resp = _table().query(
        KeyConditionExpression=Key("config_key").eq(key),
        ScanIndexForward=False,
        Limit=10,
    )
    items = resp.get("Items", [])
    for item in items:
        if item.get("is_active"):
            return item
    return None


def get_active_value(key: str, default: Any = None) -> Any:
    config = get_config(key)
    if config is None:
        return default
    return config.get("value", default)


def get_all_active_configs() -> dict[str, Any]:
    configs = {}
    resp = _table().scan()
    for item in resp.get("Items", []):
        if item.get("is_active"):
            configs[item["config_key"]] = item.get("value")
    while resp.get("LastEvaluatedKey"):
        resp = _table().scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
        for item in resp.get("Items", []):
            if item.get("is_active"):
                configs[item["config_key"]] = item.get("value")
    return configs


def update_config(key: str, value: Any, admin_id: str) -> str:
    now = datetime.now(timezone.utc).isoformat()
    version_id = f"v-{ulid.new().str}"

    current = get_config(key)
    if current:
        _table().update_item(
            Key={"config_key": key, "version_id": current["version_id"]},
            UpdateExpression="SET is_active = :false",
            ExpressionAttributeValues={":false": False},
        )

    serialized = _serialize_value(value)
    _table().put_item(
        Item={
            "config_key": key,
            "version_id": version_id,
            "value": serialized,
            "updated_by": admin_id,
            "updated_at": now,
            "is_active": True,
        }
    )

    get_s3_client().put_object(
        Bucket=_backup_bucket(),
        Key=f"configs/{key}/{version_id}.json",
        Body=json.dumps({"key": key, "version": version_id, "value": value, "admin": admin_id, "timestamp": now}, default=str),
        ContentType="application/json",
    )

    logger.info("Config updated", extra={"key": key, "version": version_id})
    return version_id


def get_config_history(key: str, limit: int = 20) -> list[dict]:
    resp = _table().query(
        KeyConditionExpression=Key("config_key").eq(key),
        ScanIndexForward=False,
        Limit=limit,
    )
    return resp.get("Items", [])


def rollback_config(key: str, target_version_id: str, admin_id: str) -> str:
    target = _table().get_item(
        Key={"config_key": key, "version_id": target_version_id}
    ).get("Item")
    if not target:
        raise ValueError(f"Version {target_version_id} not found for key {key}")

    return update_config(key, target["value"], admin_id)


def validate_threshold(value: Any) -> tuple[bool, str]:
    if not isinstance(value, (int, float, Decimal)):
        return False, "Threshold must be a number"
    if value < 0 or value > 1:
        return False, "Threshold must be between 0 and 1"
    return True, ""
