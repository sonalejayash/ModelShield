import pytest

from quality.evaluator import QualityMetrics, calculate_psi, calculate_quality, quality_passes


def test_calculates_binary_quality_metrics() -> None:
    metrics = calculate_quality([1, 1, 0, 0], [1, 0, 0, 0])

    assert metrics == QualityMetrics(accuracy=0.75, precision=1.0, recall=0.5, f1=2 / 3)


def test_quality_requires_every_threshold() -> None:
    measured = QualityMetrics(accuracy=0.95, precision=0.90, recall=0.80, f1=0.85)

    assert not quality_passes(measured, QualityMetrics(0.90, 0.85, 0.85, 0.90))


def test_psi_is_zero_for_identical_distributions() -> None:
    values = [0.1, 0.2, 0.3, 0.4]

    assert calculate_psi(values, values, bins=4) == pytest.approx(0.0)


def test_psi_detects_distribution_change() -> None:
    psi = calculate_psi([0.1] * 100, [0.9] * 100)

    assert psi > 0.20


def test_empty_quality_input_is_rejected() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        calculate_quality([], [])