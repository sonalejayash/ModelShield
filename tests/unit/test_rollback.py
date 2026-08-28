import pytest

from controller.rollback import RollbackStateMachine, RuntimeState


def test_two_failures_confirm_failure_and_successful_rollback() -> None:
    machine = RollbackStateMachine(cooldown_seconds=300)

    assert machine.observe(False, 0) is RuntimeState.DEGRADED
    assert machine.observe(False, 15) is RuntimeState.FAILURE_CONFIRMED
    assert machine.rollback(15, lambda: True) is RuntimeState.RECOVERED


def test_failed_rollback_escalates_and_cannot_loop() -> None:
    machine = RollbackStateMachine(cooldown_seconds=0)
    machine.observe(False, 0)
    machine.observe(False, 15)

    assert machine.rollback(15, lambda: False) is RuntimeState.ESCALATE
    assert machine.observe(False, 30) is RuntimeState.ESCALATE


def test_rollback_requires_confirmed_failure() -> None:
    with pytest.raises(ValueError, match="FAILURE_CONFIRMED"):
        RollbackStateMachine().rollback(0, lambda: True)


def test_rollback_cooldown_prevents_a_second_attempt() -> None:
    machine = RollbackStateMachine(cooldown_seconds=300, maximum_attempts=2)
    machine.observe(False, 0)
    machine.observe(False, 15)
    machine.rollback(15, lambda: True)
    machine.observe(False, 30)
    machine.observe(False, 45)

    with pytest.raises(ValueError, match="cooldown"):
        machine.rollback(45, lambda: True)


def test_healthy_evaluation_resets_failure_observation() -> None:
    machine = RollbackStateMachine()
    machine.observe(False, 0)

    assert machine.observe(True, 15) is RuntimeState.HEALTHY
    assert machine.failure_count == 0