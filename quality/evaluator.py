"""Deterministic binary-classification quality and PSI evaluation."""

from dataclasses import dataclass
from math import log
from collections.abc import Iterable, Sequence


@dataclass(frozen=True)
class QualityMetrics:
    """Computed metrics for binary predictions."""

    accuracy: float
    precision: float
    recall: float
    f1: float


def calculate_quality(actual: Sequence[int], predicted: Sequence[int]) -> QualityMetrics:
    """Calculate quality metrics for binary labels represented by 0 and 1."""
    if len(actual) == 0 or len(actual) != len(predicted):
        raise ValueError("actual and predicted must be non-empty and equally sized")
    if any(label not in (0, 1) for label in (*actual, *predicted)):
        raise ValueError("labels must be binary values 0 or 1")

    true_positives = sum(expected == 1 and result == 1 for expected, result in zip(actual, predicted))
    true_negatives = sum(expected == 0 and result == 0 for expected, result in zip(actual, predicted))
    false_positives = sum(expected == 0 and result == 1 for expected, result in zip(actual, predicted))
    false_negatives = sum(expected == 1 and result == 0 for expected, result in zip(actual, predicted))
    precision = true_positives / (true_positives + false_positives) if true_positives + false_positives else 0.0
    recall = true_positives / (true_positives + false_negatives) if true_positives + false_negatives else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return QualityMetrics(
        accuracy=(true_positives + true_negatives) / len(actual),
        precision=precision,
        recall=recall,
        f1=f1,
    )


def quality_passes(metrics: QualityMetrics, thresholds: QualityMetrics) -> bool:
    """Return whether every measured metric meets its configured minimum."""
    return all(
        measured >= minimum
        for measured, minimum in zip(
            (metrics.accuracy, metrics.precision, metrics.recall, metrics.f1),
            (thresholds.accuracy, thresholds.precision, thresholds.recall, thresholds.f1),
        )
    )


def calculate_psi(expected: Iterable[float], actual: Iterable[float], *, bins: int = 10) -> float:
    """Calculate population stability index using equal-width expected-data bins."""
    expected_values = list(expected)
    actual_values = list(actual)
    if not expected_values or not actual_values:
        raise ValueError("expected and actual distributions must be non-empty")
    if bins < 2:
        raise ValueError("bins must be at least 2")
    lower = min(expected_values)
    upper = max(expected_values)
    if lower == upper:
        return 0.0 if all(value == lower for value in actual_values) else float("inf")

    width = (upper - lower) / bins

    def distribution(values: list[float]) -> list[float]:
        counts = [0] * bins
        for value in values:
            index = min(int((value - lower) / width), bins - 1)
            index = max(index, 0)
            counts[index] += 1
        return [max(count / len(values), 1e-12) for count in counts]

    expected_distribution = distribution(expected_values)
    actual_distribution = distribution(actual_values)
    return sum(
        (actual_rate - expected_rate) * log(actual_rate / expected_rate)
        for expected_rate, actual_rate in zip(expected_distribution, actual_distribution)
    )