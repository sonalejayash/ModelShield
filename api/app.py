"""HTTP API for deterministic release policy evaluation."""

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, ConfigDict, Field
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from model.service import ModelService
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
prediction_requests = Counter("modelshield_prediction_requests_total", "Prediction requests")
prediction_latency = Histogram("modelshield_prediction_latency_seconds", "Prediction latency")


@app.get("/health")
def health() -> dict[str, str]:
    """Report API availability."""
    return {"status": "ok"}


@app.post("/v1/releases/evaluate", response_model=EvaluationResponse)
def evaluate_release(request: EvidenceRequest) -> EvaluationResponse:
    """Evaluate structured release evidence using the deterministic policy engine."""
    result = policy_engine.evaluate(ReleaseEvidence(**request.model_dump()))
    return EvaluationResponse(
        decision=result.decision.value,
        reasons=list(result.reasons),
        policy_version=result.policy_version,
    )


@app.post("/v1/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest) -> PredictionResponse:
    """Score a feature vector and record serving metrics."""
    with prediction_latency.time():
        result = model_service.predict(request.features)
    prediction_requests.inc()
    return PredictionResponse(label=result.label, probability=result.probability)


@app.get("/metrics", response_class=PlainTextResponse)
def metrics() -> PlainTextResponse:
    """Expose Prometheus metrics for the model service."""
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)