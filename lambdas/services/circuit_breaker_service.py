import logging
import os
import time

import redis

logger = logging.getLogger(__name__)

_redis_client = None

FAILURE_THRESHOLD = 5
COOLDOWN_SECONDS = 60


class CircuitOpenError(Exception):
    """Raised when a circuit breaker is open and the call is rejected."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        super().__init__(f"Circuit breaker is open for service: {service_name}")


def _get_redis():
    global _redis_client
    if _redis_client is None:
        endpoint = os.environ.get("REDIS_ENDPOINT", "localhost")
        port = int(os.environ.get("REDIS_PORT", "6379"))
        _redis_client = redis.Redis(host=endpoint, port=port, decode_responses=True)
    return _redis_client


def _key(service_name: str, suffix: str) -> str:
    return f"circuit_breaker:{service_name}:{suffix}"


def call_with_breaker(service_name: str, callable_fn, *args, **kwargs):
    r = _get_redis()

    state = r.get(_key(service_name, "state")) or "closed"

    if state == "open":
        opened_at = r.get(_key(service_name, "opened_at"))
        if opened_at and (time.time() - float(opened_at)) >= COOLDOWN_SECONDS:
            logger.info("Circuit half-open, allowing trial call", extra={"service": service_name})
            r.set(_key(service_name, "state"), "half_open")
        else:
            raise CircuitOpenError(service_name)

    try:
        result = callable_fn(*args, **kwargs)
    except Exception:
        _record_failure(r, service_name)
        raise

    r.set(_key(service_name, "failures"), "0")
    r.set(_key(service_name, "state"), "closed")
    logger.debug("Call succeeded, circuit closed", extra={"service": service_name})

    return result


def _record_failure(r, service_name: str) -> None:
    failures = int(r.get(_key(service_name, "failures")) or "0") + 1
    r.set(_key(service_name, "failures"), str(failures))

    if failures >= FAILURE_THRESHOLD:
        r.set(_key(service_name, "state"), "open")
        r.set(_key(service_name, "opened_at"), str(time.time()))
        logger.warning(
            "Circuit breaker opened",
            extra={"service": service_name, "failure_count": failures},
        )
    else:
        logger.info(
            "Failure recorded",
            extra={"service": service_name, "failure_count": failures},
        )


def get_circuit_status(service_name: str) -> str:
    r = _get_redis()
    state = r.get(_key(service_name, "state")) or "closed"

    if state == "open":
        opened_at = r.get(_key(service_name, "opened_at"))
        if opened_at and (time.time() - float(opened_at)) >= COOLDOWN_SECONDS:
            return "half_open"

    return state


def reset_circuit(service_name: str) -> None:
    r = _get_redis()
    r.set(_key(service_name, "state"), "closed")
    r.set(_key(service_name, "failures"), "0")
    r.delete(_key(service_name, "opened_at"))
    logger.info("Circuit breaker manually reset", extra={"service": service_name})
