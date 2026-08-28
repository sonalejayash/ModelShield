"""Evaluate a persisted ModelShield model against its reproducible test split."""

import argparse
from pathlib import Path

import joblib
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split

from model.training import RANDOM_STATE, TEST_SIZE, load_metadata
from policy.config import load_model_policy
from quality.evaluator import calculate_quality, quality_passes
from security.artifacts import ArtifactMetadata, calculate_sha256, verify_artifact, verify_provenance


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metadata", type=Path)
    parser.add_argument("--policy", type=Path, default=Path("policies/model.yaml"))
    arguments = parser.parse_args()
    metadata = load_metadata(arguments.metadata)
    artifact_path = Path(metadata.artifact_path)
    artifact_metadata = ArtifactMetadata(
        expected_sha256=metadata.artifact_sha256,
        signature=bytes.fromhex(metadata.artifact_signature),
        public_key=bytes.fromhex(metadata.artifact_public_key),
        source_repository=metadata.source_repository,
        source_revision=metadata.source_revision,
        builder_identity=metadata.builder_identity,
    )
    if not verify_artifact(artifact_path, artifact_metadata) or not verify_provenance(artifact_metadata):
        raise SystemExit("artifact integrity, signature, or provenance verification failed")
    model = joblib.load(artifact_path)
    features, labels = load_breast_cancer(return_X_y=True)
    _, test_features, _, test_labels = train_test_split(
        features, labels, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=labels
    )
    predictions = model.predict(test_features)
    measured = calculate_quality(list(test_labels), list(predictions))
    print(f"model version: {metadata.model_version}")
    policy = load_model_policy(arguments.policy)
    if measured != metadata.metrics:
        raise SystemExit(f"metadata metrics do not match actual metrics: {metadata.metrics} != {measured}")
    print(f"recorded metrics: {metadata.metrics}")
    print(f"actual metrics: {measured}")
    print(f"quality thresholds pass: {quality_passes(measured, policy.quality_thresholds)}")
    print(f"sha256 verified: {calculate_sha256(artifact_path) == metadata.artifact_sha256}")


if __name__ == "__main__":
    main()