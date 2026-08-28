import json
from pathlib import Path

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