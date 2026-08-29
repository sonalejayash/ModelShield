import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from controller.release import ReleaseController, ReleaseRequest
from policy.engine import Decision
from security.artifacts import ArtifactMetadata, calculate_sha256
from quality.evaluator import QualityMetrics


def create_request(tmp_path: Path, *, critical: bool = False) -> ReleaseRequest:
    artifact = tmp_path / "model.bin"
    artifact.write_bytes(b"model artifact")
    private_key = Ed25519PrivateKey.generate()
    digest = calculate_sha256(artifact)
    metadata = ArtifactMetadata(
        expected_sha256=digest,
        signature=private_key.sign(digest.encode("ascii")),
        public_key=private_key.public_key().public_bytes_raw(),
        source_repository="https://github.com/sonalejayash/ModelShield",
        source_revision="abc123",
        builder_identity="github-actions/model-build",
    )
    vulnerability = {"Severity": "CRITICAL"} if critical else {"Severity": "HIGH"}
    dependency = tmp_path / "dependency.json"
    container = tmp_path / "container.json"
    report = {"Results": [{"Vulnerabilities": [vulnerability]}]}
    dependency.write_text(json.dumps(report), encoding="utf-8")
    container.write_text(json.dumps({"Results": []}), encoding="utf-8")
    return ReleaseRequest(
        model_version="v1",
        artifact_path=artifact,
        artifact_metadata=metadata,
        quality_passed=True,
        drift_psi=0.05,
        dependency_report=dependency,
        container_report=container,
        release_id="release-test-1",
        quality_metrics=QualityMetrics(0.99, 0.99, 0.99, 0.99),
    )


def test_promotes_and_appends_audit_record(tmp_path: Path) -> None:
    audit = tmp_path / "audit.jsonl"

    result = ReleaseController().evaluate_and_audit(create_request(tmp_path), audit)

    assert result.decision is Decision.PROMOTE
    record = json.loads(audit.read_text(encoding="utf-8"))
    assert record["decision"] == "PROMOTE"
    assert record["model_version"] == "v1"
    assert record["release_id"] == "release-test-1"
    assert record["evidence"]["artifact_sha256"]
    assert record["evidence"]["quality_metrics"]["f1"] == 0.99
    assert record["evidence"]["release_id"] == "release-test-1"
    assert record["evidence"]["model_name"] == "modelshield-classifier"
    assert record["investigation"]["advisory_only"] is True
    assert record["investigation"]["decision"] == "PROMOTE"


def test_collects_canonical_artifact_and_scan_evidence(tmp_path: Path) -> None:
    request = create_request(tmp_path)

    evidence = ReleaseController().collect_evidence(request)

    assert evidence.model_version == "v1"
    assert len(evidence.artifact_sha256) == 64
    assert evidence.dependency_scan_critical == 0
    assert str(request.dependency_report) in evidence.evidence_references


def test_critical_scan_blocks_release(tmp_path: Path) -> None:
    result = ReleaseController().evaluate(create_request(tmp_path, critical=True))

    assert result.decision is Decision.BLOCK