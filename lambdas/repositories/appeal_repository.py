import logging
from datetime import datetime, timezone
from typing import Optional

import ulid
from boto3.dynamodb.conditions import Key

from .base import get_table

logger = logging.getLogger(__name__)


def _table():
    return get_table("APPEALS_TABLE")


def create_appeal(
    enforcement_id: str,
    user_id: str,
    appeal_reason: str,
    supporting_info: str | None = None,
) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    item = {
        "appeal_id": f"APPEAL-{ulid.new().str}",
        "enforcement_id": enforcement_id,
        "user_id": user_id,
        "status": "received",
        "appeal_reason": appeal_reason,
        "submitted_at": now,
    }
    if supporting_info:
        item["supporting_info"] = supporting_info
    _table().put_item(Item=item)
    logger.info("Appeal created", extra={"appeal_id": item["appeal_id"]})
    return item


def get_appeal(appeal_id: str) -> Optional[dict]:
    resp = _table().get_item(Key={"appeal_id": appeal_id})
    return resp.get("Item")


def get_appeals_by_user(user_id: str, status: str | None = None) -> list[dict]:
    kwargs = {
        "IndexName": "user_id-status-index",
        "KeyConditionExpression": Key("user_id").eq(user_id),
    }
    if status:
        kwargs["KeyConditionExpression"] &= Key("status").eq(status)
    resp = _table().query(**kwargs)
    return resp.get("Items", [])


def update_appeal_status(
    appeal_id: str,
    status: str,
    reviewer_id: str | None = None,
    decision_notes: str | None = None,
) -> None:
    expr = "SET #s = :status"
    names = {"#s": "status"}
    values = {":status": status}

    if reviewer_id:
        expr += ", reviewer_id = :rid, reviewed_at = :now"
        values[":rid"] = reviewer_id
        values[":now"] = datetime.now(timezone.utc).isoformat()
    if decision_notes:
        expr += ", decision_notes = :notes"
        values[":notes"] = decision_notes

    _table().update_item(
        Key={"appeal_id": appeal_id},
        UpdateExpression=expr,
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
    )


def create_enforcement_appeal_record(
    case_id: str,
    user_id: str,
    enforcement_action: str,
) -> str:
    item = create_appeal(
        enforcement_id=case_id,
        user_id=user_id,
        appeal_reason=f"Automatic appeal record for {enforcement_action}",
    )
    return item["appeal_id"]
