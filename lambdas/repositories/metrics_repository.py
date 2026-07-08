import logging
import time
from datetime import datetime, timezone
from decimal import Decimal

from boto3.dynamodb.conditions import Key

from .base import get_table

logger = logging.getLogger(__name__)

TTL_DAYS = 90


def _table():
    return get_table("METRICS_TABLE")


def record_metric(metric_name: str, value: float, dimensions: dict | None = None) -> None:
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%dT%H:%M:00Z")
    ttl = int(time.time()) + (TTL_DAYS * 86400)
    item = {
        "metric_name": metric_name,
        "timestamp": timestamp,
        "value": Decimal(str(value)),
        "ttl": ttl,
    }
    if dimensions:
        item["dimensions"] = dimensions
    _table().put_item(Item=item)


def get_metric_values(
    metric_name: str,
    start_time: str,
    end_time: str | None = None,
    limit: int = 1000,
) -> list[dict]:
    if end_time:
        key_expr = Key("metric_name").eq(metric_name) & Key("timestamp").between(start_time, end_time)
    else:
        key_expr = Key("metric_name").eq(metric_name) & Key("timestamp").gte(start_time)
    resp = _table().query(
        KeyConditionExpression=key_expr,
        ScanIndexForward=False,
        Limit=limit,
    )
    return resp.get("Items", [])


def get_latest_metric(metric_name: str) -> dict | None:
    resp = _table().query(
        KeyConditionExpression=Key("metric_name").eq(metric_name),
        ScanIndexForward=False,
        Limit=1,
    )
    items = resp.get("Items", [])
    return items[0] if items else None


def get_metric_aggregate(
    metric_name: str,
    start_time: str,
    end_time: str,
) -> dict:
    values_list = get_metric_values(metric_name, start_time, end_time)
    if not values_list:
        return {"count": 0, "sum": 0, "avg": 0, "min": 0, "max": 0}
    vals = sorted(float(v["value"]) for v in values_list)
    count = len(vals)
    return {
        "count": count,
        "sum": sum(vals),
        "avg": sum(vals) / count,
        "min": vals[0],
        "max": vals[-1],
        "p50": vals[int(count * 0.5)],
        "p90": vals[int(count * 0.9)] if count >= 10 else vals[-1],
        "p99": vals[int(count * 0.99)] if count >= 100 else vals[-1],
    }


def increment_counter(metric_name: str, amount: int = 1) -> None:
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%dT%H:%M:00Z")
    ttl = int(time.time()) + (TTL_DAYS * 86400)
    _table().update_item(
        Key={"metric_name": metric_name, "timestamp": timestamp},
        UpdateExpression="SET #v = if_not_exists(#v, :zero) + :inc, #t = :ttl",
        ExpressionAttributeNames={"#v": "value", "#t": "ttl"},
        ExpressionAttributeValues={
            ":inc": Decimal(str(amount)),
            ":zero": Decimal("0"),
            ":ttl": ttl,
        },
    )
