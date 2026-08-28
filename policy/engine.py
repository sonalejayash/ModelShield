"""Deterministic release policy evaluation."""

from dataclasses import dataclass
from enum import StrEnum

from quality.evaluator import QualityMetrics


class Decision(StrEnum):
    """Possible pre-release policy outcomes."""

    PROMOTE = "PROMOTE"
    BLOCK = "BLOCK"
    RETRAIN = "RETRAIN"


@dataclass(frozen=True)
class ReleaseEvidence:
    """Evidence collected for one candidate model release."""

    quality_passed: bool
    drift_psi: float
    critical_vulnerabilities: int
    artifact_integrity_valid: bool
    artifact_signature_valid: bool
    provenance_valid: bool
    dependency_scan_passed: bool
    container_scan_passed: bool
    release_id: str = ""
    model_name: str = ""
    model_version: str = ""
    artifact_path: str = ""
    artifact_sha256: str = ""
    quality_metrics: QualityMetrics | None = None
    drift_status: str = ""
    high_vulnerabilities: int = 0
    dependency_scan_critical: int = 0
    container_scan_critical: int = 0
    evidence_references: tuple[str, ...] = ()
    metadata_consistent: bool = True


@dataclass(frozen=True)
class PolicyResult:
    """A policy decision and the evidence-based reasons for it."""

    decision: Decision
    reasons: tuple[str, ...]
    policy_version: str


class PolicyEngine:
    """Apply ModelShield's fixed release decision precedence."""

    def __init__(
        self,
        *,
        policy_version: str = "policy-v1",
        psi_critical: float = 0.20,
    ) -> None:
        if not policy_version.strip():
            raise ValueError("policy_version must not be empty")
        if psi_critical <= 0:
            raise ValueError("psi_critical must be greater than zero")
        self.policy_version = policy_version
        self.psi_critical = psi_critical

    def evaluate(self, evidence: ReleaseEvidence) -> PolicyResult:
        """Return the highest-priority decision supported by the evidence."""
        self._validate_evidence(evidence)

        security_failures: list[str] = []
        if evidence.critical_vulnerabilities > 0:
            security_failures.append("critical vulnerabilities detected")
        if not evidence.artifact_integrity_valid:
            security_failures.append("artifact integrity verification failed")
        if not evidence.artifact_signature_valid:
            security_failures.append("artifact signature verification failed")
        if not evidence.provenance_valid:
            security_failures.append("provenance verification failed")
        if not evidence.dependency_scan_passed:
            security_failures.append("dependency scan failed")
        if not evidence.container_scan_passed:
            security_failures.append("container scan failed")

        if security_failures:
            return PolicyResult(Decision.BLOCK, tuple(security_failures), self.policy_version)
        if not evidence.metadata_consistent:
            return PolicyResult(
                Decision.BLOCK,
                ("recorded metadata does not match actual evaluation",),
                self.policy_version,
            )
        if not evidence.quality_passed:
            return PolicyResult(
                Decision.BLOCK,
                ("model quality gate failed",),
                self.policy_version,
            )
        if evidence.drift_psi >= self.psi_critical:
            return PolicyResult(
                Decision.RETRAIN,
                (f"severe data drift detected (PSI={evidence.drift_psi:.4f})",),
                self.policy_version,
            )
        return PolicyResult(Decision.PROMOTE, ("all required release gates passed",), self.policy_version)

    @staticmethod
    def _validate_evidence(evidence: ReleaseEvidence) -> None:
        if evidence.drift_psi < 0:
            raise ValueError("drift_psi must not be negative")
        if evidence.critical_vulnerabilities < 0:
            raise ValueError("critical_vulnerabilities must not be negative")