"""Deterministic runtime health and rollback state machine."""

from collections.abc import Callable
from enum import StrEnum

from observability.metrics import rollback_events


class RuntimeState(StrEnum):
    """States in the runtime rollback lifecycle."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    OBSERVING = "OBSERVING"
    FAILURE_CONFIRMED = "FAILURE_CONFIRMED"
    ROLLBACK = "ROLLBACK"
    RECOVERED = "RECOVERED"
    ESCALATE = "ESCALATE"


class RollbackStateMachine:
    """Track runtime failures and perform at most one automatic rollback."""

    def __init__(
        self,
        *,
        consecutive_failures: int = 2,
        observation_window_seconds: int = 60,
        cooldown_seconds: int = 300,
        maximum_attempts: int = 1,
    ) -> None:
        if consecutive_failures < 1 or observation_window_seconds < 1:
            raise ValueError("failure threshold and observation window must be positive")
        if cooldown_seconds < 0 or maximum_attempts < 1:
            raise ValueError("cooldown must not be negative and attempts must be positive")
        self.consecutive_failures = consecutive_failures
        self.observation_window_seconds = observation_window_seconds
        self.cooldown_seconds = cooldown_seconds
        self.maximum_attempts = maximum_attempts
        self.state = RuntimeState.HEALTHY
        self.failure_count = 0
        self.rollback_attempts = 0
        self._observation_started: float | None = None
        self._last_rollback: float | None = None

    def observe(self, healthy: bool, timestamp: float) -> RuntimeState:
        """Record one health evaluation and return the resulting runtime state."""
        if timestamp < 0:
            raise ValueError("timestamp must not be negative")
        if self.state is RuntimeState.ESCALATE:
            return self.state
        if healthy:
            self.failure_count = 0
            self._observation_started = None
            self.state = RuntimeState.HEALTHY
            return self.state
        if self._observation_started is None:
            self._observation_started = timestamp
        if timestamp - self._observation_started > self.observation_window_seconds:
            self.failure_count = 0
            self._observation_started = timestamp
        self.failure_count += 1
        self.state = RuntimeState.DEGRADED if self.failure_count == 1 else RuntimeState.OBSERVING
        if self.failure_count >= self.consecutive_failures:
            self.state = RuntimeState.FAILURE_CONFIRMED
        return self.state

    def rollback(self, timestamp: float, action: Callable[[], bool]) -> RuntimeState:
        """Attempt one rollback action, returning `RECOVERED` or `ESCALATE`."""
        if self.state is not RuntimeState.FAILURE_CONFIRMED:
            raise ValueError("rollback requires FAILURE_CONFIRMED state")
        if self._last_rollback is not None and timestamp - self._last_rollback < self.cooldown_seconds:
            raise ValueError("rollback is in cooldown")
        if self.rollback_attempts >= self.maximum_attempts:
            self.state = RuntimeState.ESCALATE
            return self.state
        self.state = RuntimeState.ROLLBACK
        self.rollback_attempts += 1
        self._last_rollback = timestamp
        if action():
            self.state = RuntimeState.RECOVERED
            rollback_events.labels(event="recovered").inc()
        else:
            self.state = RuntimeState.ESCALATE
            rollback_events.labels(event="escalated").inc()
        return self.state