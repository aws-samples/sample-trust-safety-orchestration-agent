import logging
import time
from datetime import datetime, timezone
from decimal import Decimal

from .base import get_table

logger = logging.getLogger(__name__)

TTL_DAYS = 90


def _table():
    return get_table("REVIEWER_STATE_TABLE")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def get_reviewer_state(reviewer_id: str, date: str | None = None) -> dict | None:
    date = date or _today()
    resp = _table().get_item(
        Key={"reviewer_id": reviewer_id, "date": date}
    )
    return resp.get("Item")


def _ensure_state(reviewer_id: str, date: str) -> None:
    ttl = int(time.time()) + (TTL_DAYS * 86400)
    _table().update_item(
        Key={"reviewer_id": reviewer_id, "date": date},
        UpdateExpression=(
            "SET cases_reviewed = if_not_exists(cases_reviewed, :zero), "
            "harmful_exposure_count = if_not_exists(harmful_exposure_count, :zero), "
            "time_on_sensitive_minutes = if_not_exists(time_on_sensitive_minutes, :zero), "
            "ttl = :ttl"
        ),
        ExpressionAttributeValues={
            ":zero": Decimal("0"),
            ":ttl": ttl,
        },
    )


def increment_cases_reviewed(reviewer_id: str) -> None:
    date = _today()
    _ensure_state(reviewer_id, date)
    _table().update_item(
        Key={"reviewer_id": reviewer_id, "date": date},
        UpdateExpression="SET cases_reviewed = cases_reviewed + :one",
        ExpressionAttributeValues={":one": Decimal("1")},
    )


def increment_harmful_exposure(reviewer_id: str, count: int = 1) -> None:
    date = _today()
    _ensure_state(reviewer_id, date)
    _table().update_item(
        Key={"reviewer_id": reviewer_id, "date": date},
        UpdateExpression="SET harmful_exposure_count = harmful_exposure_count + :inc",
        ExpressionAttributeValues={":inc": Decimal(str(count))},
    )


def add_sensitive_time(reviewer_id: str, minutes: float) -> None:
    date = _today()
    _ensure_state(reviewer_id, date)
    _table().update_item(
        Key={"reviewer_id": reviewer_id, "date": date},
        UpdateExpression="SET time_on_sensitive_minutes = time_on_sensitive_minutes + :mins",
        ExpressionAttributeValues={":mins": Decimal(str(minutes))},
    )


def set_content_preference(reviewer_id: str, preference: str) -> None:
    date = _today()
    _ensure_state(reviewer_id, date)
    _table().update_item(
        Key={"reviewer_id": reviewer_id, "date": date},
        UpdateExpression="SET content_visibility_preference = :pref",
        ExpressionAttributeValues={":pref": preference},
    )


def record_wellness_prompt(reviewer_id: str) -> None:
    _table().update_item(
        Key={"reviewer_id": reviewer_id, "date": _today()},
        UpdateExpression="SET last_wellness_prompt = :now",
        ExpressionAttributeValues={":now": datetime.now(timezone.utc).isoformat()},
    )


def get_exposure_metrics(reviewer_id: str, days: int = 7) -> dict:
    from boto3.dynamodb.conditions import Key
    from datetime import timedelta
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    resp = _table().query(
        KeyConditionExpression=(
            Key("reviewer_id").eq(reviewer_id) &
            Key("date").between(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        ),
    )
    items = resp.get("Items", [])
    totals = {"cases_reviewed": 0, "harmful_exposure_count": 0, "time_on_sensitive_minutes": 0}
    for item in items:
        for k in totals:
            totals[k] += int(item.get(k, 0))
    today = get_reviewer_state(reviewer_id) or {}
    return {
        "reviewer_id": reviewer_id,
        "today": {
            "cases_reviewed": int(today.get("cases_reviewed", 0)),
            "harmful_content_exposure": int(today.get("harmful_exposure_count", 0)),
            "time_on_sensitive_cases_minutes": int(today.get("time_on_sensitive_minutes", 0)),
        },
        "this_week": totals,
        "exposure_threshold_reached": int(today.get("harmful_exposure_count", 0)) >= 20,
    }
