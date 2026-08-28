from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from policy.engine import Decision, PolicyResult
from tracking.mlflow import MlflowTracker


@dataclass
class RunInfo:
    run_id: str = "run-123"


@dataclass
class FakeRun:
    info: RunInfo = field(default_factory=RunInfo)


class FakeMlflow:
    def __init__(self) -> None:
        self.params: dict[str, Any] = {}
        self.metrics: dict[str, float] = {}
        self.tags: dict[str, str] = {}

    @contextmanager
    def start_run(self, *, run_name: str) -> Any:
        yield FakeRun()

    def log_params(self, values: dict[str, Any]) -> None:
        self.params.update(values)

    def log_metrics(self, values: dict[str, float]) -> None:
        self.metrics.update(values)

    def set_tags(self, values: dict[str, str]) -> None:
        self.tags.update(values)


def test_records_release_decision_and_metrics() -> None:
    client = FakeMlflow()
    result = PolicyResult(Decision.PROMOTE, ("all gates passed",), "policy-v1")

    run_id = MlflowTracker(client).record_release(
        model_version="v1",
        result=result,
        metrics={"drift_psi": 0.05, "critical_vulnerabilities": 0},
    )

    assert run_id == "run-123"
    assert client.params["model_version"] == "v1"
    assert client.metrics["drift_psi"] == 0.05
    assert client.tags["modelshield.decision"] == "PROMOTE"


def test_rejects_empty_model_version() -> None:
    result = PolicyResult(Decision.BLOCK, ("security failure",), "policy-v1")

    try:
        MlflowTracker(FakeMlflow()).record_release(model_version=" ", result=result, metrics={})
    except ValueError as error:
        assert "model_version" in str(error)
    else:
        raise AssertionError("empty model version should be rejected")