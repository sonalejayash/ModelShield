from pathlib import Path

from policy.config import load_model_policy


def test_loads_versioned_model_policy() -> None:
    policy = load_model_policy(Path("policies/model.yaml"))

    assert policy.policy_version == "policy-v1"
    assert policy.quality_thresholds.f1 == 0.90
    assert policy.psi_critical == 0.20