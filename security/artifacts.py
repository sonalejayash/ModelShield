"""Cryptographic artifact integrity and provenance checks."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


@dataclass(frozen=True)
class ArtifactMetadata:
    """Trusted metadata required to verify one model artifact."""

    expected_sha256: str
    signature: bytes
    public_key: bytes
    source_repository: str
    source_revision: str
    builder_identity: str


def sign_digest(digest: str, private_key: bytes) -> bytes:
    """Sign an artifact digest with an Ed25519 private key."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    try:
        return Ed25519PrivateKey.from_private_bytes(private_key).sign(digest.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as error:
        raise ValueError("invalid digest or Ed25519 private key") from error


def calculate_sha256(path: Path) -> str:
    """Return the SHA-256 digest of a file."""
    digest = sha256()
    try:
        with path.open("rb") as artifact:
            for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise ValueError(f"unable to read artifact: {path}") from error
    return digest.hexdigest()


def verify_artifact(path: Path, metadata: ArtifactMetadata) -> bool:
    """Verify the artifact digest and Ed25519 signature over that digest."""
    actual_digest = calculate_sha256(path)
    if not verify_integrity(actual_digest, metadata.expected_sha256):
        return False
    return verify_signature(actual_digest, metadata)


def verify_integrity(actual_digest: str, expected_digest: str) -> bool:
    """Compare an observed digest with the expected artifact digest."""
    return actual_digest.lower() == expected_digest.lower()


def verify_signature(actual_digest: str, metadata: ArtifactMetadata) -> bool:
    """Verify an Ed25519 signature over an observed artifact digest."""
    try:
        Ed25519PublicKey.from_public_bytes(metadata.public_key).verify(
            metadata.signature,
            actual_digest.encode("ascii"),
        )
    except (InvalidSignature, ValueError):
        return False
    return True


def verify_provenance(metadata: ArtifactMetadata) -> bool:
    """Return whether all required provenance values are present."""
    return all(
        value.strip()
        for value in (
            metadata.source_repository,
            metadata.source_revision,
            metadata.builder_identity,
        )
    )