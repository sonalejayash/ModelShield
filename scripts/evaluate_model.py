"""Evaluate a persisted ModelShield model against its reproducible test split."""

import argparse
from pathlib import Path

import joblib
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split

from model.training import RANDOM_STATE, TEST_SIZE, load_metadata
from quality.evaluator import QualityMetrics, calculate_quality, quality_passes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metadata", type=Path)
    arguments = parser.parse_args()
    metadata = load_metadata(arguments.metadata)
    model = joblib.load(metadata.artifact_path)
    features, labels = load_breast_cancer(return_X_y=True)
    _, test_features, _, test_labels = train_test_split(
        features, labels, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=labels
    )
    predictions = model.predict(test_features)
    measured = calculate_quality(list(test_labels), list(predictions))
    print(f"model version: {metadata.model_version}")
    print(f"recorded metrics: {metadata.metrics}")
    print(f"quality thresholds pass: {quality_passes(metadata.metrics, QualityMetrics(0.90, 0.85, 0.85, 0.90))}")
    print(f"accuracy recheck: {measured.accuracy:.4f}")


if __name__ == "__main__":
    main()