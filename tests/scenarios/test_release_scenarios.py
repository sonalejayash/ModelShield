import json
from dataclasses import replace
from pathlib import Path
import subprocess
import sys

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from controller.release import ReleaseController, ReleaseRequest
from policy.engine import Decision
from security.artifacts import ArtifactMetadata, calculate_sha256


def release_request(tmp_path: Path, *, drift_psi: float = 0.05, quality_passed: bool = True) -> ReleaseRequest:
    artifact = tmp_path / "model.bin"
    artifact.write_bytes(b"scenario model artifact")
    private_key = Ed25519PrivateKey.generate()
    digest = calculate_sha256(artifact)
    metadata = ArtifactMetadata(
        expected_sha256=digest,
        signature=private_key.sign(digest.encode("ascii")),
        public_key=private_key.public_key().public_bytes_raw(),
        source_repository="https://github.com/sonalejayash/ModelShield",
        source_revision="scenario-revision",
        builder_identity="github-actions/model-build",
    )
    report = {"Results": []}
    dependency = tmp_path / "dependency.json"
    container = tmp_path / "container.json"
    dependency.write_text(json.dumps(report), encoding="utf-8")
    container.write_text(json.dumps(report), encoding="utf-8")
    return ReleaseRequest(
        model_version="scenario-v1",
        artifact_path=artifact,
        artifact_metadata=metadata,
        quality_passed=quality_passed,
        drift_psi=drift_psi,
        dependency_report=dependency,
        container_report=container,
    )


def test_healthy_release_is_promoted(tmp_path: Path) -> None:
    result = ReleaseController().evaluate(release_request(tmp_path))

    assert result.decision is Decision.PROMOTE


def test_quality_failure_is_blocked(tmp_path: Path) -> None:
    result = ReleaseController().evaluate(release_request(tmp_path, quality_passed=False))

    assert result.decision is Decision.BLOCK


def test_severe_drift_requests_retraining(tmp_path: Path) -> None:
    result = ReleaseController().evaluate(release_request(tmp_path, drift_psi=0.25))

    assert result.decision is Decision.RETRAIN


def test_invalid_signature_is_blocked(tmp_path: Path) -> None:
    request = release_request(tmp_path)
    invalid_metadata = replace(request.artifact_metadata, signature=b"invalid")

    result = ReleaseController().evaluate(replace(request, artifact_metadata=invalid_metadata))

    assert result.decision is Decision.BLOCK
    assert "signature" in result.reasons[0]


def test_invalid_provenance_is_blocked(tmp_path: Path) -> None:
    request = release_request(tmp_path)
    invalid_metadata = replace(request.artifact_metadata, source_revision=" ")

    result = ReleaseController().evaluate(replace(request, artifact_metadata=invalid_metadata))

    assert result.decision is Decision.BLOCK
    assert "provenance" in result.reasons[0]


def test_artifact_hash_mismatch_is_blocked(tmp_path: Path) -> None:
    request = release_request(tmp_path)
    invalid_metadata = replace(request.artifact_metadata, expected_sha256="0" * 64)

    result = ReleaseController().evaluate(replace(request, artifact_metadata=invalid_metadata))

    assert result.decision is Decision.BLOCK
    assert "integrity" in result.reasons[0]


def test_security_failure_wins_over_severe_drift(tmp_path: Path) -> None:
    request = release_request(tmp_path, drift_psi=0.40)
    dependency = json.loads(request.dependency_report.read_text(encoding="utf-8"))
    dependency["Results"] = [{"Vulnerabilities": [{"Severity": "CRITICAL"}]}]
    request.dependency_report.write_text(json.dumps(dependency), encoding="utf-8")

    result = ReleaseController().evaluate(request)

    assert result.decision is Decision.BLOCK


def test_metadata_mismatch_is_blocked(tmp_path: Path) -> None:
    request = replace(release_request(tmp_path), metadata_consistent=False)

    result = ReleaseController().evaluate(request)

    assert result.decision is Decision.BLOCK
    assert "metadata" in result.reasons[0]


def test_golden_path_audit_contains_advisory_investigation(tmp_path: Path) -> None:
    audit = tmp_path / "audit.jsonl"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/release.py",
            "--model-version",
            "scenario-v1",
            "--output-dir",
            str(tmp_path),
            "--audit-path",
            str(audit),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    record = json.loads(audit.read_text(encoding="utf-8"))
    assert record["decision"] == "PROMOTE"
    assert record["investigation"]["decision"] == "PROMOTE"
    assert record["investigation"]["advisory_only"] is True
    assert record["investigation"]["findings"][0]["evidence_fields"]


def test_blocked_audit_investigation_cites_failure_field(tmp_path: Path) -> None:
    request = release_request(tmp_path)
    invalid_metadata = replace(request.artifact_metadata, signature=b"invalid")
    audit = tmp_path / "audit.jsonl"

    result = ReleaseController().evaluate_and_audit(replace(request, artifact_metadata=invalid_metadata), audit)

    record = json.loads(audit.read_text(encoding="utf-8"))
    assert result.decision is Decision.BLOCK
    assert record["investigation"]["advisory_only"] is True
    assert ["artifact_signature_valid"] in [
        finding["evidence_fields"] for finding in record["investigation"]["findings"]
    ]


def test_investigation_cli_reads_existing_audit(tmp_path: Path) -> None:
    audit = tmp_path / "audit.jsonl"
    release = subprocess.run(
        [
            sys.executable,
            "scripts/release.py",
            "--model-version",
            "scenario-v2",
            "--output-dir",
            str(tmp_path),
            "--audit-path",
            str(audit),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    investigation = subprocess.run(
        [sys.executable, "scripts/investigate_release.py", str(audit)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert release.returncode == 0, release.stderr
    assert investigation.returncode == 0, investigation.stderr
    report = json.loads(investigation.stdout)
    assert report["decision"] == "PROMOTE"
    assert report["advisory_only"] is True
    assert report["findings"][0]["evidence_fields"]


def test_history_cli_summarizes_existing_audit(tmp_path: Path) -> None:
    audit = tmp_path / "audit.jsonl"
    release = subprocess.run(
        [
            sys.executable,
            "scripts/release.py",
            "--model-version",
            "history-v1",
            "--output-dir",
            str(tmp_path),
            "--audit-path",
            str(audit),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    history = subprocess.run(
        [sys.executable, "scripts/analyze_history.py", str(audit)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert release.returncode == 0, release.stderr
    assert history.returncode == 0, history.stderr
    report = json.loads(history.stdout)
    assert report["total_releases"] == 1
    assert report["decision_counts"] == {"PROMOTE": 1}
    assert report["advisory_only"] is True