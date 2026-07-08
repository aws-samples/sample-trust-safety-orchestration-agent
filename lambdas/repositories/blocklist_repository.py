import logging
from datetime import datetime, timezone
from typing import Optional

from boto3.dynamodb.conditions import Key

from .base import get_table

logger = logging.getLogger(__name__)


def _table():
    return get_table("BLOCKLIST_TABLE")


def add_bad_actor(
    fingerprint_hash: str,
    signature_hash: str,
    source_platform: str,
    ban_reason: str,
    confidence_score: float = 1.0,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _table().batch_writer() as batch:
        batch.put_item(
            Item={
                "hash_type": "fingerprint_hash",
                "hash_value": fingerprint_hash,
                "source_platform": source_platform,
                "ban_reason": ban_reason,
                "added_at": now,
                "confidence_score": confidence_score,
            }
        )
        batch.put_item(
            Item={
                "hash_type": "signature_hash",
                "hash_value": signature_hash,
                "source_platform": source_platform,
                "ban_reason": ban_reason,
                "added_at": now,
                "confidence_score": confidence_score,
            }
        )
    logger.info("Bad actor added to blocklist", extra={"source": source_platform})


def check_fingerprint(fingerprint_hash: str) -> Optional[dict]:
    resp = _table().get_item(
        Key={"hash_type": "fingerprint_hash", "hash_value": fingerprint_hash}
    )
    return resp.get("Item")


def check_signature(signature_hash: str) -> Optional[dict]:
    resp = _table().get_item(
        Key={"hash_type": "signature_hash", "hash_value": signature_hash}
    )
    return resp.get("Item")


def check_match(fingerprint_hash: str, signature_hash: str) -> Optional[dict]:
    fp_match = check_fingerprint(fingerprint_hash)
    if fp_match:
        return fp_match
    return check_signature(signature_hash)


def get_recent_additions(hash_type: str, since: str, limit: int = 100) -> list[dict]:
    resp = _table().query(
        KeyConditionExpression=Key("hash_type").eq(hash_type) & Key("hash_value").gte(""),
        FilterExpression="added_at >= :since",
        ExpressionAttributeValues={":since": since},
        Limit=limit,
    )
    return resp.get("Items", [])
