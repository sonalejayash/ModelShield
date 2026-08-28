import pytest

from model.service import ModelService, Prediction


def test_predicts_a_bounded_probability() -> None:
    prediction = ModelService().predict([0.0, 1.0])

    assert prediction == Prediction(label=1, probability=pytest.approx(0.622459))


def test_rejects_empty_or_non_finite_features() -> None:
    service = ModelService()

    with pytest.raises(ValueError, match="non-empty"):
        service.predict([])
    with pytest.raises(ValueError, match="finite"):
        service.predict([float("inf")])


def test_threshold_controls_label() -> None:
    assert ModelService(threshold=0.9).predict([0.0, 1.0]).label == 0