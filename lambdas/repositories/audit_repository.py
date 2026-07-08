import csv
import io
import json
import logging
from datetime import datetime, timezone
from typing import Optional

import ulid
from boto3.dynamodb.conditions import Key

from .base import get_table, get_s3_client, get_bucket_name

logger = logging.getLogger(__name__)


def _table():
    return get_table("AUDIT_LOGS_TABLE")


def _archive_bucket():
    return get_bucket_name("AUDIT_ARCHIVE_BUCKET")


def write_log(
    event_type: str,
    action: str,
    case_id: str | None = None,
    user_id: str | None = None,
    admin_id: str | None = None,
    violation_type: str | None = None,
    confidence_score: float | None = None,
    decision_source: str | None = None,
    reasoning: str | None = None,
    previous_value: dict | None = None,
    new_value: dict | None = None,
    jurisdiction_code: str | None = None,
    response_time_ms: int | None = None,
) -> str:
    now = datetime.now(timezone.utc).isoformat()
    audit_id = f"AUDIT-{ulid.new().str}"
    item = {
        "audit_id": audit_id,
        "timestamp": now,
        "event_type": event_type,
        "action": action,
    }
    optional_fields = {
        "case_id": case_id,
        "user_id": user_id,
        "admin_id": admin_id,
        "violation_type": violation_type,
        "confidence_score": confidence_score,
        "decision_source": decision_source,
        "reasoning": reasoning,
        "previous_value": previous_value,
        "new_value": new_value,
        "jurisdiction_code": jurisdiction_code,
        "response_time_ms": response_time_ms,
    }
    for k, v in optional_fields.items():
        if v is not None:
            item[k] = v

    _table().put_item(Item=item)
    logger.info("Audit log written", extra={"audit_id": audit_id, "event_type": event_type})
    return audit_id


def query_by_case(case_id: str, limit: int = 100) -> list[dict]:
    resp = _table().query(
        IndexName="case_id-timestamp-index",
        KeyConditionExpression=Key("case_id").eq(case_id),
        ScanIndexForward=False,
        Limit=limit,
    )
    return resp.get("Items", [])


def query_by_event_type(
    event_type: str,
    start_time: str | None = None,
    end_time: str | None = None,
    limit: int = 100,
) -> list[dict]:
    key_expr = Key("event_type").eq(event_type)
    if start_time and end_time:
        key_expr &= Key("timestamp").between(start_time, end_time)
    elif start_time:
        key_expr &= Key("timestamp").gte(start_time)
    resp = _table().query(
        IndexName="event_type-timestamp-index",
        KeyConditionExpression=key_expr,
        ScanIndexForward=False,
        Limit=limit,
    )
    return resp.get("Items", [])


def query_by_jurisdiction(
    jurisdiction_code: str,
    start_time: str | None = None,
    end_time: str | None = None,
    limit: int = 100,
) -> list[dict]:
    key_expr = Key("jurisdiction_code").eq(jurisdiction_code)
    if start_time and end_time:
        key_expr &= Key("timestamp").between(start_time, end_time)
    resp = _table().query(
        IndexName="jurisdiction-timestamp-index",
        KeyConditionExpression=key_expr,
        ScanIndexForward=False,
        Limit=limit,
    )
    return resp.get("Items", [])


def export_to_s3(
    logs: list[dict],
    export_format: str = "json",
    prefix: str = "exports",
) -> str:
    export_id = ulid.new().str
    bucket = _archive_bucket()

    if export_format == "json":
        key = f"{prefix}/{export_id}/audit_export.json"
        body = json.dumps(logs, default=str)
        content_type = "application/json"
    else:
        key = f"{prefix}/{export_id}/audit_export.csv"
        if not logs:
            body = ""
        else:
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=logs[0].keys())
            writer.writeheader()
            for row in logs:
                writer.writerow({k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in row.items()})
            body = output.getvalue()
        content_type = "text/csv"

    get_s3_client().put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentType=content_type,
        ServerSideEncryption="AES256",
    )

    url = get_s3_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=3600,
    )
    logger.info("Audit export created", extra={"export_id": export_id, "format": export_format})
    return url
