import json
import logging
from datetime import datetime, timezone
from typing import Optional

from .base import get_table, get_s3_client, get_bucket_name

logger = logging.getLogger(__name__)


def _table():
    return get_table("EVIDENCE_METADATA_TABLE")


def _bucket():
    return get_bucket_name("EVIDENCE_BUCKET")


def store_evidence(case_id: str, evidence_type: str, evidence_data: dict) -> str:
    s3_key = f"cases/{case_id}/{evidence_type}.json"
    get_s3_client().put_object(
        Bucket=_bucket(),
        Key=s3_key,
        Body=json.dumps(evidence_data, default=str),
        ContentType="application/json",
        ServerSideEncryption="AES256",
    )
    now = datetime.now(timezone.utc).isoformat()
    _table().put_item(
        Item={
            "case_id": case_id,
            "evidence_type": evidence_type,
            "s3_key": s3_key,
            "source_availability": "available",
            "gathered_at": now,
            "confidence_contribution": 0,
        }
    )
    logger.info("Evidence stored", extra={"case_id": case_id, "type": evidence_type})
    return s3_key


def store_evidence_package(case_id: str, package: dict) -> str:
    return store_evidence(case_id, "evidence_package", package)


def mark_source_unavailable(case_id: str, evidence_type: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    _table().put_item(
        Item={
            "case_id": case_id,
            "evidence_type": evidence_type,
            "s3_key": "",
            "source_availability": "unavailable",
            "gathered_at": now,
            "confidence_contribution": 0,
        }
    )


def get_evidence(case_id: str, evidence_type: str) -> Optional[dict]:
    resp = get_s3_client().get_object(
        Bucket=_bucket(),
        Key=f"cases/{case_id}/{evidence_type}.json",
    )
    return json.loads(resp["Body"].read())


def get_evidence_package(case_id: str) -> Optional[dict]:
    try:
        return get_evidence(case_id, "evidence_package")
    except get_s3_client().exceptions.NoSuchKey:
        return None


def get_evidence_metadata(case_id: str) -> list[dict]:
    from boto3.dynamodb.conditions import Key
    resp = _table().query(
        KeyConditionExpression=Key("case_id").eq(case_id)
    )
    return resp.get("Items", [])


def generate_presigned_url(case_id: str, evidence_type: str, expiry: int = 3600) -> str:
    s3_key = f"cases/{case_id}/{evidence_type}.json"
    return get_s3_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": _bucket(), "Key": s3_key},
        ExpiresIn=expiry,
    )
