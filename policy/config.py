"""Load version-controlled ModelShield policy configuration."""

from dataclasses import dataclass
from pathlib import Path

import yaml

from quality.evaluator import QualityMetrics


@dataclass(frozen=True)
class ModelPolicy:
    """Quality and drift thresholds from a policy file."""

    policy_version: str
    quality_thresholds: QualityMetrics
    psi_warning: float
    psi_critical: float


def load_model_policy(path: Path) -> ModelPolicy:
    """Load and validate model release thresholds from YAML."""
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise ValueError(f"unable to read model policy: {path}") from error
    if not isinstance(payload, dict) or not isinstance(payload.get("quality"), dict):
        raise ValueError("model policy must contain quality thresholds")
    quality = payload["quality"]
    drift = payload.get("drift")
    if not isinstance(drift, dict):
        raise ValueError("model policy must contain drift thresholds")
    try:
        policy = ModelPolicy(
            policy_version=str(payload["policy_version"]),
            quality_thresholds=QualityMetrics(
                accuracy=float(quality["minimum_accuracy"]),
                precision=float(quality["minimum_precision"]),
                recall=float(quality["minimum_recall"]),
                f1=float(quality["minimum_f1"]),
            ),
            psi_warning=float(drift["psi_warning"]),
            psi_critical=float(drift["psi_critical"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("model policy contains invalid thresholds") from error
    if not policy.policy_version.strip() or not 0 < policy.psi_warning <= policy.psi_critical:
        raise ValueError("model policy thresholds are invalid")
    return policy