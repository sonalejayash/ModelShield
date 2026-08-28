"""Small deterministic model service used by the local demonstration."""

from dataclasses import dataclass
from math import exp, isfinite
from collections.abc import Sequence


@dataclass(frozen=True)
class Prediction:
    """Prediction returned by the serving model."""

    label: int
    probability: float


class ModelService:
    """Score feature vectors with a bounded logistic baseline."""

    def __init__(self, *, threshold: float = 0.5) -> None:
        if not 0 < threshold < 1:
            raise ValueError("threshold must be between zero and one")
        self.threshold = threshold

    def predict(self, features: Sequence[float]) -> Prediction:
        """Return a binary prediction from a non-empty finite feature vector."""
        if not features or any(not isfinite(value) for value in features):
            raise ValueError("features must be non-empty and finite")
        logit = sum(features) / len(features)
        probability = 1 / (1 + exp(-max(min(logit, 60), -60)))
        return Prediction(int(probability >= self.threshold), probability)