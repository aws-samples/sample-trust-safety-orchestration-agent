import time
from unittest.mock import patch, MagicMock

import pytest

from services import circuit_breaker_service as svc
from services.circuit_breaker_service import CircuitOpenError


def _make_fake_redis():
    """Return a fake Redis client backed by a plain dict."""
    store = {}

    class FakeRedis:
        def get(self, key):
            return store.get(key)

        def set(self, key, value):
            store[key] = value

        def delete(self, key):
            store.pop(key, None)

    return FakeRedis(), store


class TestClosedState:
    @patch("services.circuit_breaker_service._get_redis")
    def test_closed_state_allows_calls(self, mock_get_redis):
        """A fresh circuit breaker (closed) should allow calls through."""
        fake_redis, _ = _make_fake_redis()
        mock_get_redis.return_value = fake_redis

        result = svc.call_with_breaker("test-service", lambda: "success")
        assert result == "success"

    @patch("services.circuit_breaker_service._get_redis")
    def test_closed_state_returns_callable_result(self, mock_get_redis):
        """The return value of the wrapped callable should be passed through."""
        fake_redis, _ = _make_fake_redis()
        mock_get_redis.return_value = fake_redis

        result = svc.call_with_breaker("test-service", lambda x: x * 2, 21)
        assert result == 42


class TestOpenAfterFailures:
    @patch("services.circuit_breaker_service._get_redis")
    def test_open_after_threshold_failures(self, mock_get_redis):
        """After 5 consecutive failures the circuit should open and reject calls."""
        fake_redis, store = _make_fake_redis()
        mock_get_redis.return_value = fake_redis

        def failing_fn():
            raise RuntimeError("boom")

        # Accumulate FAILURE_THRESHOLD (5) failures
        for _ in range(svc.FAILURE_THRESHOLD):
            with pytest.raises(RuntimeError):
                svc.call_with_breaker("flaky-svc", failing_fn)

        # State should now be open
        assert store.get("circuit_breaker:flaky-svc:state") == "open"

        # Next call should raise CircuitOpenError without invoking the callable
        with pytest.raises(CircuitOpenError) as exc_info:
            svc.call_with_breaker("flaky-svc", failing_fn)
        assert exc_info.value.service_name == "flaky-svc"


class TestHalfOpenAfterCooldown:
    @patch("services.circuit_breaker_service._get_redis")
    def test_half_open_after_cooldown(self, mock_get_redis):
        """After the cooldown period, the breaker should transition to half-open."""
        fake_redis, store = _make_fake_redis()
        mock_get_redis.return_value = fake_redis

        # Manually set state to open with opened_at in the past
        store["circuit_breaker:recover-svc:state"] = "open"
        store["circuit_breaker:recover-svc:opened_at"] = str(
            time.time() - svc.COOLDOWN_SECONDS - 1
        )

        # A call should now be allowed (trial call in half-open state)
        result = svc.call_with_breaker("recover-svc", lambda: "recovered")
        assert result == "recovered"

        # After a successful trial, state should be closed again
        assert store.get("circuit_breaker:recover-svc:state") == "closed"

    @patch("services.circuit_breaker_service._get_redis")
    def test_half_open_via_get_status(self, mock_get_redis):
        """get_circuit_status should return 'half_open' after the cooldown elapses."""
        fake_redis, store = _make_fake_redis()
        mock_get_redis.return_value = fake_redis

        store["circuit_breaker:status-svc:state"] = "open"
        store["circuit_breaker:status-svc:opened_at"] = str(
            time.time() - svc.COOLDOWN_SECONDS - 1
        )

        assert svc.get_circuit_status("status-svc") == "half_open"


class TestSuccessResetsCounter:
    @patch("services.circuit_breaker_service._get_redis")
    def test_success_resets_counter(self, mock_get_redis):
        """A successful call should reset the failure count to 0."""
        fake_redis, store = _make_fake_redis()
        mock_get_redis.return_value = fake_redis

        def failing_fn():
            raise RuntimeError("boom")

        # Record some failures (but not enough to open the circuit)
        for _ in range(svc.FAILURE_THRESHOLD - 1):
            with pytest.raises(RuntimeError):
                svc.call_with_breaker("reset-svc", failing_fn)

        # Failures recorded
        assert int(store.get("circuit_breaker:reset-svc:failures")) == svc.FAILURE_THRESHOLD - 1

        # One successful call should reset
        svc.call_with_breaker("reset-svc", lambda: "ok")
        assert store.get("circuit_breaker:reset-svc:failures") == "0"
        assert store.get("circuit_breaker:reset-svc:state") == "closed"


class TestResetCircuit:
    @patch("services.circuit_breaker_service._get_redis")
    def test_manual_reset(self, mock_get_redis):
        """reset_circuit should restore the breaker to a clean closed state."""
        fake_redis, store = _make_fake_redis()
        mock_get_redis.return_value = fake_redis

        store["circuit_breaker:manual-svc:state"] = "open"
        store["circuit_breaker:manual-svc:failures"] = "10"
        store["circuit_breaker:manual-svc:opened_at"] = str(time.time())

        svc.reset_circuit("manual-svc")

        assert store.get("circuit_breaker:manual-svc:state") == "closed"
        assert store.get("circuit_breaker:manual-svc:failures") == "0"
        assert store.get("circuit_breaker:manual-svc:opened_at") is None
