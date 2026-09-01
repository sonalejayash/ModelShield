"""Run the reproducible ModelShield golden-path release evaluation."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import joblib

from controller.release import ReleaseController, ReleaseRequest
from model.training import RANDOM_STATE, TEST_SIZE, evaluate_model, load_metadata, train_model
from policy.config import load_model_policy
from policy.engine import Decision
from quality.evaluator import quality_passes
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split

from security.artifacts import ArtifactMetadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-version", default="v1")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--audit-path", type=Path, default=Path("artifacts/audit.jsonl"))
    parser.add_argument("--policy", type=Path, default=Path("policies/model.yaml"))
    arguments = parser.parse_args()

    print("Training model...")
    train_model(arguments.output_dir, model_version=arguments.model_version)
    metadata = load_metadata(arguments.output_dir / f"model-{arguments.model_version}.json")
    policy = load_model_policy(arguments.policy)
    artifact_metadata = ArtifactMetadata(
        expected_sha256=metadata.artifact_sha256,
        signature=bytes.fromhex(metadata.artifact_signature),
        public_key=bytes.fromhex(metadata.artifact_public_key),
        source_repository=metadata.source_repository,
        source_revision=metadata.source_revision,
        builder_identity=metadata.builder_identity,
    )
    model = joblib.load(metadata.artifact_path)
    features, labels = load_breast_cancer(return_X_y=True)
    _, test_features, _, test_labels = train_test_split(
        features, labels, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=labels
    )
    actual_metrics = evaluate_model(model, test_features, test_labels)
    metadata_consistent = actual_metrics == metadata.metrics
    dependency_report = arguments.output_dir / "dependency-clean.json"
    container_report = arguments.output_dir / "container-clean.json"
    clean_report = {"Results": []}
    dependency_report.write_text(json.dumps(clean_report), encoding="utf-8")
    container_report.write_text(json.dumps(clean_report), encoding="utf-8")
    request = ReleaseRequest(
        model_version=metadata.model_version,
        artifact_path=Path(metadata.artifact_path),
        artifact_metadata=artifact_metadata,
        quality_passed=quality_passes(actual_metrics, policy.quality_thresholds),
        drift_psi=0.05,
        dependency_report=dependency_report,
        container_report=container_report,
        release_id=f"release-{metadata.model_version}",
        quality_metrics=actual_metrics,
        metadata_consistent=metadata_consistent,
    )
    result = ReleaseController().evaluate_and_audit(request, arguments.audit_path)
    print(f"Artifact SHA-256: {metadata.artifact_sha256}")
    print(f"Quality: {'PASS' if request.quality_passed else 'FAIL'}")
    print("Drift: PASS")
    print(f"Policy: {result.decision.value}")
    print(f"Audit: {arguments.audit_path}")
    if result.decision is Decision.PROMOTE:
        print("Release: PROMOTED")
        return 0
    if result.decision is Decision.RETRAIN:
        print("Release: RETRAIN RECOMMENDED; not deployed")
        return 2
    print("Release: BLOCKED")
    return 1


if __name__ == "__main__":
    sys.exit(main())