"""Reproducible scikit-learn training and evaluation workflow."""

import json
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
from security.artifacts import calculate_sha256


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
    artifact_path = output_dir / f"model-{model_version}.joblib"
    joblib.dump(model, artifact_path)
    result = TrainingResult(
        model_version=model_version,
        dataset=DATASET_NAME,
        random_state=RANDOM_STATE,
        test_size=TEST_SIZE,
        artifact_path=str(artifact_path),
        artifact_sha256=calculate_sha256(artifact_path),
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
        metrics=QualityMetrics(**payload["metrics"]),
    )


def _metadata(result: TrainingResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["metrics"] = asdict(result.metrics)
    return payload