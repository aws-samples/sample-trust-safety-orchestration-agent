import logging
import os
from typing import Optional

import redis

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None


def _get_redis() -> redis.Redis:
    """Lazily connect to Redis ElastiCache, caching the connection."""
    global _redis_client
    if _redis_client is None:
        endpoint = os.environ["REDIS_ENDPOINT"]
        port = int(os.environ.get("REDIS_PORT", "6379"))
        _redis_client = redis.Redis(
            host=endpoint,
            port=port,
            decode_responses=True,
            socket_connect_timeout=5,
        )
        logger.info("Redis connection established", extra={"endpoint": endpoint, "port": port})
    return _redis_client


def _build_key(identifier: str, limit_type: str) -> str:
    """Build a namespaced Redis key for rate limiting."""
    return f"safetyagent:rate_limit:{limit_type}:{identifier}"


def apply_rate_limit(user_id: str, limit_type: str, max_per_hour: int = 10) -> dict:
    """Apply a rate limit for a user action, incrementing the counter with a 1-hour TTL.

    Returns a dict with the current count and whether the limit has been reached.
    """
    client = _get_redis()
    key = _build_key(user_id, limit_type)

    pipe = client.pipeline()
    pipe.incr(key)
    pipe.ttl(key)
    results = pipe.execute()

    current_count = results[0]
    ttl = results[1]

    # Set TTL only on first increment (ttl returns -1 when no expiry is set)
    if ttl == -1:
        client.expire(key, 3600)

    is_limited = current_count >= max_per_hour

    logger.info(
        "Rate limit applied",
        extra={
            "user_id": user_id,
            "limit_type": limit_type,
            "current_count": current_count,
            "max_per_hour": max_per_hour,
            "is_limited": is_limited,
        },
    )

    return {
        "user_id": user_id,
        "limit_type": limit_type,
        "current_count": current_count,
        "max_per_hour": max_per_hour,
        "is_limited": is_limited,
    }


def apply_ip_range_limit(ip_range: str, limit_type: str, max_per_hour: int = 10) -> dict:
    """Apply a rate limit keyed on an IP range (e.g. CIDR block).

    Returns a dict with the current count and whether the limit has been reached.
    """
    client = _get_redis()
    key = _build_key(f"ip:{ip_range}", limit_type)

    pipe = client.pipeline()
    pipe.incr(key)
    pipe.ttl(key)
    results = pipe.execute()

    current_count = results[0]
    ttl = results[1]

    if ttl == -1:
        client.expire(key, 3600)

    is_limited = current_count >= max_per_hour

    logger.info(
        "IP range rate limit applied",
        extra={
            "ip_range": ip_range,
            "limit_type": limit_type,
            "current_count": current_count,
            "max_per_hour": max_per_hour,
            "is_limited": is_limited,
        },
    )

    return {
        "ip_range": ip_range,
        "limit_type": limit_type,
        "current_count": current_count,
        "max_per_hour": max_per_hour,
        "is_limited": is_limited,
    }


def check_rate_limit(user_id: str, limit_type: str) -> dict:
    """Check the current rate limit status for a user without incrementing.

    Returns a dict with is_limited, current_count, and max_per_hour.
    """
    client = _get_redis()
    key = _build_key(user_id, limit_type)

    current_count = client.get(key)
    current_count = int(current_count) if current_count is not None else 0

    # Retrieve the max_per_hour from a companion metadata key, default to 10
    meta_key = f"{key}:meta:max_per_hour"
    stored_max = client.get(meta_key)
    max_per_hour = int(stored_max) if stored_max is not None else 10

    is_limited = current_count >= max_per_hour

    logger.info(
        "Rate limit checked",
        extra={
            "user_id": user_id,
            "limit_type": limit_type,
            "current_count": current_count,
            "is_limited": is_limited,
        },
    )

    return {
        "is_limited": is_limited,
        "current_count": current_count,
        "max_per_hour": max_per_hour,
    }


def remove_rate_limit(user_id: str, limit_type: str) -> bool:
    """Delete the rate limit key for a user, effectively removing the limit.

    Returns True if the key existed and was deleted, False otherwise.
    """
    client = _get_redis()
    key = _build_key(user_id, limit_type)

    deleted = client.delete(key)
    was_deleted = deleted > 0

    logger.info(
        "Rate limit removed",
        extra={
            "user_id": user_id,
            "limit_type": limit_type,
            "was_deleted": was_deleted,
        },
    )

    return was_deleted
