import pytest

from policy.engine import Decision, PolicyEngine, ReleaseEvidence


def evidence(**overrides: object) -> ReleaseEvidence:
    values: dict[str, object] = {
        "quality_passed": True,
        "drift_psi": 0.05,
        "critical_vulnerabilities": 0,
        "artifact_integrity_valid": True,
        "artifact_signature_valid": True,
        "provenance_valid": True,
        "dependency_scan_passed": True,
        "container_scan_passed": True,
    }
    values.update(overrides)
    return ReleaseEvidence(**values)


def test_promotes_when_all_required_gates_pass() -> None:
    result = PolicyEngine().evaluate(evidence())

    assert result.decision is Decision.PROMOTE
    assert result.policy_version == "policy-v1"


def test_security_failure_blocks_even_when_quality_and_drift_pass() -> None:
    result = PolicyEngine().evaluate(evidence(critical_vulnerabilities=1))

    assert result.decision is Decision.BLOCK
    assert "critical vulnerabilities detected" in result.reasons


def test_security_failure_blocks_instead_of_retrain() -> None:
    result = PolicyEngine().evaluate(evidence(drift_psi=0.30, artifact_signature_valid=False))

    assert result.decision is Decision.BLOCK


def test_quality_failure_blocks() -> None:
    result = PolicyEngine().evaluate(evidence(quality_passed=False))

    assert result.decision is Decision.BLOCK
    assert result.reasons == ("model quality gate failed",)


def test_severe_drift_requests_retraining() -> None:
    result = PolicyEngine().evaluate(evidence(drift_psi=0.20))

    assert result.decision is Decision.RETRAIN


def test_negative_drift_is_rejected() -> None:
    with pytest.raises(ValueError, match="drift_psi"):
        PolicyEngine().evaluate(evidence(drift_psi=-0.01))