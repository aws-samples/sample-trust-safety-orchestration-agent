import logging
from datetime import datetime, timezone
from typing import Optional

import ulid
from boto3.dynamodb.conditions import Key

from .base import get_table

logger = logging.getLogger(__name__)


def _table():
    return get_table("CASES_TABLE")


def create_case(
    user_id: str,
    trigger_source: str,
    violation_type: str | None = None,
) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    item = {
        "case_id": f"CASE-{ulid.new().str}",
        "user_id": user_id,
        "status": "detected",
        "trigger_source": trigger_source,
        "violation_type": violation_type or "unknown",
        "confidence_score": 0,
        "created_at": now,
        "updated_at": now,
        "audit_trail_ids": [],
    }
    _table().put_item(Item=item)
    logger.info("Case created", extra={"case_id": item["case_id"]})
    return item


def get_case(case_id: str) -> Optional[dict]:
    resp = _table().get_item(Key={"case_id": case_id})
    return resp.get("Item")


def update_case(case_id: str, **updates) -> None:
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    expr_parts = []
    names = {}
    values = {}
    for i, (k, v) in enumerate(updates.items()):
        alias = f"#k{i}"
        val_alias = f":v{i}"
        expr_parts.append(f"{alias} = {val_alias}")
        names[alias] = k
        values[val_alias] = v
    _table().update_item(
        Key={"case_id": case_id},
        UpdateExpression="SET " + ", ".join(expr_parts),
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
    )


def update_case_status(case_id: str, status: str) -> None:
    updates = {"status": status}
    if status == "resolved":
        updates["resolved_at"] = datetime.now(timezone.utc).isoformat()
    update_case(case_id, **updates)


def append_audit_trail_id(case_id: str, audit_id: str) -> None:
    _table().update_item(
        Key={"case_id": case_id},
        UpdateExpression="SET updated_at = :now ADD audit_trail_ids :aid",
        ExpressionAttributeValues={
            ":now": datetime.now(timezone.utc).isoformat(),
            ":aid": {audit_id},
        },
    )


def get_cases_by_user(user_id: str, status: str | None = None) -> list[dict]:
    kwargs = {
        "IndexName": "user_id-status-index",
        "KeyConditionExpression": Key("user_id").eq(user_id),
    }
    if status:
        kwargs["KeyConditionExpression"] &= Key("status").eq(status)
    resp = _table().query(**kwargs)
    return resp.get("Items", [])


def get_cases_by_status(status: str, limit: int = 50, last_key: dict | None = None) -> tuple[list[dict], dict | None]:
    kwargs = {
        "IndexName": "status-created_at-index",
        "KeyConditionExpression": Key("status").eq(status),
        "ScanIndexForward": False,
        "Limit": limit,
    }
    if last_key:
        kwargs["ExclusiveStartKey"] = last_key
    resp = _table().query(**kwargs)
    return resp.get("Items", []), resp.get("LastEvaluatedKey")


def get_active_cases(limit: int = 50, last_key: dict | None = None) -> tuple[list[dict], dict | None]:
    all_items = []
    for status in ("detected", "investigating", "decision_pending", "escalated"):
        items, _ = get_cases_by_status(status, limit=limit)
        all_items.extend(items)
    all_items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return all_items[:limit], None
