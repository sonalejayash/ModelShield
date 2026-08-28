"""HTTP API for deterministic release policy evaluation."""

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field

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


app = FastAPI(title="ModelShield", version="0.1.0")
policy_engine = PolicyEngine()


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