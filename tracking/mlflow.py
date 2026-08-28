"""Thin, optional adapter for recording ModelShield releases in MLflow."""

from collections.abc import Mapping
from typing import Any

from policy.engine import PolicyResult


class MlflowTracker:
    """Record release evidence without making MLflow a policy dependency."""

    def __init__(self, client: Any) -> None:
        self.client = client

    @classmethod
    def from_installed_mlflow(cls) -> "MlflowTracker":
        """Create a tracker using the installed MLflow package."""
        import mlflow

        return cls(mlflow)

    def record_release(
        self,
        *,
        model_version: str,
        result: PolicyResult,
        metrics: Mapping[str, float],
        run_name: str = "modelshield-release",
    ) -> str:
        """Record release metadata and return the MLflow run ID."""
        if not model_version.strip() or not run_name.strip():
            raise ValueError("model_version and run_name must not be empty")
        with self.client.start_run(run_name=run_name) as run:
            self.client.log_params(
                {
                    "model_version": model_version,
                    "policy_version": result.policy_version,
                }
            )
            self.client.log_metrics(dict(metrics))
            self.client.set_tags(
                {
                    "modelshield.decision": result.decision.value,
                    "modelshield.reasons": "; ".join(result.reasons),
                }
            )
            return _run_id(run)


def _run_id(run: Any) -> str:
    run_id = getattr(getattr(run, "info", None), "run_id", None)
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("MLflow run did not provide a run ID")
    return run_id