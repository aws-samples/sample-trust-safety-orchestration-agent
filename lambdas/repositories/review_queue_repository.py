import logging
from datetime import datetime, timezone
from typing import Optional

import ulid
from boto3.dynamodb.conditions import Key, Attr

from .base import get_table

logger = logging.getLogger(__name__)


def _table():
    return get_table("REVIEW_QUEUE_TABLE")


def add_to_queue(
    case_id: str,
    priority: str,
    escalation_reason: str,
    estimated_review_minutes: int = 5,
    similar_case_ids: list[str] | None = None,
) -> str:
    queue_id = f"Q-{ulid.new().str}"
    now = datetime.now(timezone.utc).isoformat()
    item = {
        "queue_id": queue_id,
        "case_id": case_id,
        "priority": priority,
        "added_at": now,
        "escalation_reason": escalation_reason,
        "status": "pending",
        "estimated_review_minutes": estimated_review_minutes,
        "similar_case_ids": similar_case_ids or [],
    }
    _table().put_item(Item=item)
    logger.info("Case added to review queue", extra={"queue_id": queue_id, "priority": priority})
    return queue_id


def get_queue(
    priority_filter: str | None = None,
    status: str = "pending",
    limit: int = 20,
    last_key: dict | None = None,
) -> tuple[list[dict], dict | None]:
    if priority_filter:
        kwargs = {
            "IndexName": "priority-added_at-index",
            "KeyConditionExpression": Key("priority").eq(priority_filter),
            "FilterExpression": Attr("status").eq(status),
            "ScanIndexForward": True,
            "Limit": limit,
        }
    else:
        kwargs = {
            "IndexName": "status-priority-index",
            "KeyConditionExpression": Key("status").eq(status),
            "ScanIndexForward": True,
            "Limit": limit,
        }
    if last_key:
        kwargs["ExclusiveStartKey"] = last_key
    resp = _table().query(**kwargs)
    return resp.get("Items", []), resp.get("LastEvaluatedKey")


def get_queue_depth() -> dict[str, int]:
    depths = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for priority in depths:
        resp = _table().query(
            IndexName="priority-added_at-index",
            KeyConditionExpression=Key("priority").eq(priority),
            FilterExpression=Attr("status").eq("pending"),
            Select="COUNT",
        )
        depths[priority] = resp.get("Count", 0)
    return depths


def assign_case(queue_id: str, reviewer_id: str) -> None:
    _table().update_item(
        Key={"queue_id": queue_id},
        UpdateExpression="SET assigned_reviewer = :rid, assigned_at = :now, #s = :status",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":rid": reviewer_id,
            ":now": datetime.now(timezone.utc).isoformat(),
            ":status": "in_progress",
        },
    )


def complete_review(queue_id: str) -> None:
    _table().update_item(
        Key={"queue_id": queue_id},
        UpdateExpression="SET #s = :status, completed_at = :now",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":status": "completed",
            ":now": datetime.now(timezone.utc).isoformat(),
        },
    )


def get_stale_cases(older_than_iso: str) -> list[dict]:
    resp = _table().query(
        IndexName="status-priority-index",
        KeyConditionExpression=Key("status").eq("pending"),
        FilterExpression=Attr("added_at").lt(older_than_iso),
    )
    return resp.get("Items", [])
