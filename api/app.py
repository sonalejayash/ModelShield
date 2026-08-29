"""HTTP API for deterministic release policy evaluation."""

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, ConfigDict, Field
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from model.service import ModelService
from observability.metrics import (
    model_drift_psi,
    model_predictions,
    model_version,
    prediction_requests,
    prediction_errors,
    prediction_latency,
    release_decisions,
)
from policy.engine import PolicyEngine, ReleaseEvidence


class EvidenceRequest(BaseModel):
    """JSON representation of release evidence."""

    model_config = ConfigDict(extra="forbid")

    quality_passed: bool
    drift_psi: float = Field(ge=0)
    critical_vulnerabilities: int = Field(ge=0)
    artifact_integrity_valid: bool
    artifact_signature_valid: bool
    provenance_valid: bool
    dependency_scan_passed: bool
    container_scan_passed: bool


class EvaluationResponse(BaseModel):
    """JSON representation of a policy result."""

    decision: str
    reasons: list[str]
    policy_version: str


class PredictionRequest(BaseModel):
    """JSON feature vector for the local model service."""

    model_config = ConfigDict(extra="forbid")

    features: list[float] = Field(min_length=1)


class PredictionResponse(BaseModel):
    """JSON prediction returned by the local model service."""

    label: int
    probability: float


app = FastAPI(title="ModelShield", version="0.1.0")
policy_engine = PolicyEngine()
model_service = ModelService()
model_version.labels(version="v1").set(1)


@app.get("/health")
def health() -> dict[str, str]:
    """Report API availability."""
    return {"status": "ok"}


@app.post("/v1/releases/evaluate", response_model=EvaluationResponse)
def evaluate_release(request: EvidenceRequest) -> EvaluationResponse:
    """Evaluate structured release evidence using the deterministic policy engine."""
    result = policy_engine.evaluate(ReleaseEvidence(**request.model_dump()))
    release_decisions.labels(decision=result.decision.value).inc()
    model_drift_psi.set(request.drift_psi)
    return EvaluationResponse(
        decision=result.decision.value,
        reasons=list(result.reasons),
        policy_version=result.policy_version,
    )


@app.post("/v1/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest) -> PredictionResponse:
    """Score a feature vector and record serving metrics."""
    try:
        with prediction_latency.time():
            result = model_service.predict(request.features)
    except ValueError:
        prediction_errors.inc()
        raise
    prediction_requests.inc()
    model_predictions.labels(label=str(result.label)).inc()
    return PredictionResponse(label=result.label, probability=result.probability)


@app.get("/metrics", response_class=PlainTextResponse)
def metrics() -> PlainTextResponse:
    """Expose Prometheus metrics for the model service."""
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)