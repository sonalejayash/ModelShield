from intelligence.investigator import ReleaseInvestigator
from policy.engine import Decision, PolicyResult, ReleaseEvidence


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
        "artifact_sha256": "a" * 64,
        "evidence_references": ("dependency.json",),
    }
    values.update(overrides)
    return ReleaseEvidence(**values)


def test_investigator_cites_blocking_evidence() -> None:
    report = ReleaseInvestigator().investigate(
        evidence(critical_vulnerabilities=1),
        PolicyResult(Decision.BLOCK, ("critical vulnerabilities detected",), "policy-v1"),
    )

    assert report.decision is Decision.BLOCK
    assert report.advisory_only
    assert report.findings[0].evidence_fields == ["critical_vulnerabilities"]


def test_investigator_is_schema_validated_and_advisory() -> None:
    report = ReleaseInvestigator().investigate(
        evidence(),
        PolicyResult(Decision.PROMOTE, ("all gates passed",), "policy-v1"),
    )

    assert report.model_dump()["policy_version"] == "policy-v1"
    assert report.findings[0].evidence_fields == ["policy_version", "evidence_references"]