import json
import os
from pathlib import Path

from model.training import DATASET_NAME, RANDOM_STATE, load_metadata, train_model
from quality.evaluator import QualityMetrics


def test_training_persists_artifact_and_metadata(tmp_path: Path) -> None:
    result = train_model(tmp_path, model_version="test-v1")

    artifact = Path(result.artifact_path)
    metadata_path = tmp_path / "model-test-v1.json"
    assert artifact.is_file()
    assert metadata_path.is_file()
    assert result.dataset == DATASET_NAME
    assert result.random_state == RANDOM_STATE
    assert len(result.artifact_sha256) == 64
    assert result.artifact_signature
    assert result.artifact_public_key
    assert isinstance(result.metrics, QualityMetrics)
    assert load_metadata(metadata_path) == result


def test_training_is_reproducible_for_same_version(tmp_path: Path) -> None:
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"

    first = train_model(first_dir, model_version="v1")
    second = train_model(second_dir, model_version="v1")

    assert first.metrics == second.metrics
    assert first.artifact_sha256 == second.artifact_sha256


def test_metadata_contains_release_fields(tmp_path: Path) -> None:
    result = train_model(tmp_path, model_version="v2")
    payload = json.loads((tmp_path / "model-v2.json").read_text(encoding="utf-8"))

    assert payload["model_version"] == result.model_version
    assert payload["artifact_sha256"] == result.artifact_sha256
    assert set(payload["metrics"]) == {"accuracy", "precision", "recall", "f1"}
    expected_revision = os.environ.get("GITHUB_SHA", "local")
    assert payload["source_revision"] == expected_revision