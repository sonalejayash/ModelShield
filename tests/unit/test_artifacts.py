from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from security.artifacts import ArtifactMetadata, calculate_sha256, verify_artifact, verify_provenance


def metadata_for(path: Path, private_key: Ed25519PrivateKey) -> ArtifactMetadata:
    digest = calculate_sha256(path)
    return ArtifactMetadata(
        expected_sha256=digest,
        signature=private_key.sign(digest.encode("ascii")),
        public_key=private_key.public_key().public_bytes_raw(),
        source_repository="https://github.com/sonalejayash/ModelShield",
        source_revision="abc123",
        builder_identity="github-actions/model-build",
    )


def test_verifies_intact_signed_artifact(tmp_path: Path) -> None:
    artifact = tmp_path / "model.bin"
    artifact.write_bytes(b"model artifact")
    metadata = metadata_for(artifact, Ed25519PrivateKey.generate())

    assert verify_artifact(artifact, metadata)
    assert verify_provenance(metadata)


def test_rejects_tampered_artifact(tmp_path: Path) -> None:
    artifact = tmp_path / "model.bin"
    artifact.write_bytes(b"model artifact")
    metadata = metadata_for(artifact, Ed25519PrivateKey.generate())
    artifact.write_bytes(b"tampered artifact")

    assert not verify_artifact(artifact, metadata)


def test_rejects_missing_provenance(tmp_path: Path) -> None:
    artifact = tmp_path / "model.bin"
    artifact.write_bytes(b"model artifact")
    metadata = metadata_for(artifact, Ed25519PrivateKey.generate())
    incomplete = ArtifactMetadata(
        expected_sha256=metadata.expected_sha256,
        signature=metadata.signature,
        public_key=metadata.public_key,
        source_repository=" ",
        source_revision=metadata.source_revision,
        builder_identity=metadata.builder_identity,
    )

    assert not verify_provenance(incomplete)