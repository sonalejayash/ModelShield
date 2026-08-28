"""Reproducible scikit-learn training and evaluation workflow."""

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import joblib
from sklearn.datasets import load_breast_cancer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from quality.evaluator import QualityMetrics, calculate_quality, quality_passes
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from security.artifacts import calculate_sha256, sign_digest


DATASET_NAME = "sklearn.datasets.load_breast_cancer"
RANDOM_STATE = 42
TEST_SIZE = 0.2


@dataclass(frozen=True)
class TrainingResult:
    """Persisted metadata describing one trained model."""

    model_version: str
    dataset: str
    random_state: int
    test_size: float
    artifact_path: str
    artifact_sha256: str
    artifact_signature: str
    artifact_public_key: str
    source_repository: str
    source_revision: str
    builder_identity: str
    metrics: QualityMetrics


def train_model(output_dir: Path, *, model_version: str = "v1") -> TrainingResult:
    """Train, persist, and describe a deterministic logistic model."""
    if not model_version.strip():
        raise ValueError("model_version must not be empty")
    output_dir.mkdir(parents=True, exist_ok=True)
    features, labels = load_breast_cancer(return_X_y=True)
    train_features, test_features, train_labels, test_labels = train_test_split(
        features,
        labels,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=labels,
    )
    model = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(max_iter=500, random_state=RANDOM_STATE)),
        ]
    )
    model.fit(train_features, train_labels)
    metrics = evaluate_model(model, test_features, test_labels)
    metrics = QualityMetrics(
        accuracy=float(metrics.accuracy),
        precision=float(metrics.precision),
        recall=float(metrics.recall),
        f1=float(metrics.f1),
    )
    artifact_path = output_dir / f"model-{model_version}.joblib"
    joblib.dump(model, artifact_path)
    digest = calculate_sha256(artifact_path)
    signing_key = Ed25519PrivateKey.generate()
    result = TrainingResult(
        model_version=model_version,
        dataset=DATASET_NAME,
        random_state=RANDOM_STATE,
        test_size=TEST_SIZE,
        artifact_path=str(artifact_path),
        artifact_sha256=digest,
        artifact_signature=sign_digest(digest, signing_key.private_bytes_raw()).hex(),
        artifact_public_key=signing_key.public_key().public_bytes_raw().hex(),
        source_repository="https://github.com/sonalejayash/ModelShield",
        source_revision=os.environ.get("GITHUB_SHA", "local"),
        builder_identity="modelshield/scripts/train_model.py",
        metrics=metrics,
    )
    (output_dir / f"model-{model_version}.json").write_text(
        json.dumps(_metadata(result), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def evaluate_model(model: Any, features: Any, labels: Any) -> QualityMetrics:
    """Evaluate a fitted classifier with the shared quality metric implementation."""
    predictions = model.predict(features)
    return calculate_quality(list(labels), list(predictions))


def load_metadata(path: Path) -> TrainingResult:
    """Load persisted model metadata."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    return TrainingResult(
        model_version=payload["model_version"],
        dataset=payload["dataset"],
        random_state=payload["random_state"],
        test_size=payload["test_size"],
        artifact_path=payload["artifact_path"],
        artifact_sha256=payload["artifact_sha256"],
        artifact_signature=payload["artifact_signature"],
        artifact_public_key=payload["artifact_public_key"],
        source_repository=payload["source_repository"],
        source_revision=payload["source_revision"],
        builder_identity=payload["builder_identity"],
        metrics=QualityMetrics(**payload["metrics"]),
    )


def _metadata(result: TrainingResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["metrics"] = asdict(result.metrics)
    return payload