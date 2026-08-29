"""Shared Prometheus metrics with low-cardinality labels."""

from prometheus_client import Counter, Gauge, Histogram


release_decisions = Counter(
    "modelshield_release_decisions_total",
    "Release decisions by outcome",
    ["decision"],
)
model_drift_psi = Gauge("modelshield_drift_psi", "Latest observed model drift PSI")
model_version = Gauge("modelshield_model_version_info", "Loaded model version", ["version"])
prediction_requests = Counter("modelshield_prediction_requests_total", "Prediction requests")
model_predictions = Counter("modelshield_predictions_total", "Model predictions by label", ["label"])
prediction_errors = Counter("modelshield_prediction_errors_total", "Prediction errors")
prediction_latency = Histogram("modelshield_prediction_latency_seconds", "Prediction latency")
rollback_events = Counter("modelshield_rollback_events_total", "Runtime rollback events", ["event"])