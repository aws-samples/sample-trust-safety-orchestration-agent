import json
import logging
import uuid
from datetime import datetime, timezone

from repositories.base import get_s3_client, get_bucket_name

logger = logging.getLogger(__name__)

BUCKET_ENV_VAR = "TRUSTGUARD_BUCKET"


def record_decision_feedback(
    case_id: str,
    predicted_violation: str,
    predicted_confidence: float,
    actual_decision: str,
    reviewer_id: str | None = None,
) -> str:
    s3 = get_s3_client()
    bucket = get_bucket_name(BUCKET_ENV_VAR)

    now = datetime.now(timezone.utc)
    date_prefix = now.strftime("%Y-%m-%d")
    s3_key = f"feedback/{date_prefix}/{case_id}.json"

    feedback = {
        "case_id": case_id,
        "predicted_violation": predicted_violation,
        "predicted_confidence": predicted_confidence,
        "actual_decision": actual_decision,
        "reviewer_id": reviewer_id,
        "recorded_at": now.isoformat(),
    }

    s3.put_object(
        Bucket=bucket,
        Key=s3_key,
        Body=json.dumps(feedback),
        ContentType="application/json",
    )
    logger.info("Decision feedback recorded", extra={"case_id": case_id, "s3_key": s3_key})
    return s3_key


def export_training_data(since_date: str) -> str:
    s3 = get_s3_client()
    bucket = get_bucket_name(BUCKET_ENV_VAR)

    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket, Prefix="feedback/")

    records = []
    for page in pages:
        for obj in page.get("Contents", []):
            key = obj["Key"]
            date_part = _extract_date_from_key(key)
            if date_part and date_part >= since_date:
                resp = s3.get_object(Bucket=bucket, Key=key)
                body = resp["Body"].read().decode("utf-8")
                try:
                    record = json.loads(body)
                    records.append(record)
                except json.JSONDecodeError:
                    logger.warning("Skipping malformed feedback file", extra={"key": key})

    export_id = uuid.uuid4().hex[:12]
    export_key = f"training-data/{export_id}.jsonl"

    jsonl_body = "\n".join(json.dumps(r) for r in records)
    s3.put_object(
        Bucket=bucket,
        Key=export_key,
        Body=jsonl_body,
        ContentType="application/jsonlines",
    )

    s3_uri = f"s3://{bucket}/{export_key}"
    logger.info(
        "Training data exported",
        extra={"export_id": export_id, "record_count": len(records), "s3_uri": s3_uri},
    )
    return s3_uri


def _extract_date_from_key(key: str) -> str | None:
    parts = key.split("/")
    if len(parts) >= 2:
        return parts[1]
    return None
