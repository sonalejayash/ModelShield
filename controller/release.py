"""Orchestrate release evidence, policy evaluation, and audit recording."""

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from policy.engine import PolicyEngine, PolicyResult, ReleaseEvidence
from security.artifacts import (
    ArtifactMetadata,
    calculate_sha256,
    verify_integrity,
    verify_provenance,
    verify_signature,
)
from security.scans import load_scan_result
from quality.evaluator import QualityMetrics


@dataclass(frozen=True)
class ReleaseRequest:
    """Inputs required to evaluate one model release candidate."""

    model_version: str
    artifact_path: Path
    artifact_metadata: ArtifactMetadata
    quality_passed: bool
    drift_psi: float
    dependency_report: Path
    container_report: Path
    release_id: str = ""
    model_name: str = "modelshield-classifier"
    quality_metrics: QualityMetrics | None = None
    metadata_consistent: bool = True


class ReleaseController:
    """Collect release evidence and delegate the final decision to policy."""

    def __init__(self, policy_engine: PolicyEngine | None = None) -> None:
        self.policy_engine = policy_engine or PolicyEngine()

    def collect_evidence(self, request: ReleaseRequest) -> ReleaseEvidence:
        """Collect the canonical evidence used to evaluate a candidate."""
        if not request.model_version.strip():
            raise ValueError("model_version must not be empty")
        dependency_scan = load_scan_result(request.dependency_report, scan_type="dependency")
        container_scan = load_scan_result(request.container_report, scan_type="container")
        actual_digest = calculate_sha256(request.artifact_path)
        evidence = ReleaseEvidence(
            quality_passed=request.quality_passed,
            drift_psi=request.drift_psi,
            critical_vulnerabilities=dependency_scan.critical + container_scan.critical,
            artifact_integrity_valid=verify_integrity(actual_digest, request.artifact_metadata.expected_sha256),
            artifact_signature_valid=verify_signature(actual_digest, request.artifact_metadata),
            provenance_valid=verify_provenance(request.artifact_metadata),
            dependency_scan_passed=dependency_scan.passed,
            container_scan_passed=container_scan.passed,
        )
        return ReleaseEvidence(
            quality_passed=evidence.quality_passed,
            drift_psi=evidence.drift_psi,
            critical_vulnerabilities=evidence.critical_vulnerabilities,
            artifact_integrity_valid=evidence.artifact_integrity_valid,
            artifact_signature_valid=evidence.artifact_signature_valid,
            provenance_valid=evidence.provenance_valid,
            dependency_scan_passed=evidence.dependency_scan_passed,
            container_scan_passed=evidence.container_scan_passed,
            model_version=request.model_version,
            artifact_path=str(request.artifact_path),
            artifact_sha256=actual_digest,
            quality_metrics=request.quality_metrics,
            drift_status="CRITICAL" if request.drift_psi >= self.policy_engine.psi_critical else "PASS",
            release_id=request.release_id or f"{request.model_version}-{self.policy_engine.policy_version}",
            model_name=request.model_name,
            dependency_scan_critical=dependency_scan.critical,
            container_scan_critical=container_scan.critical,
            high_vulnerabilities=dependency_scan.high + container_scan.high,
            evidence_references=(str(request.dependency_report), str(request.container_report)),
            metadata_consistent=request.metadata_consistent,
        )

    def evaluate(self, request: ReleaseRequest) -> PolicyResult:
        """Evaluate a candidate and return its deterministic policy result."""
        return self.policy_engine.evaluate(self.collect_evidence(request))

    def evaluate_and_audit(self, request: ReleaseRequest, audit_path: Path) -> PolicyResult:
        """Evaluate a release and append a structured audit record."""
        result = self.evaluate(request)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "release_id": request.release_id or f"{request.model_version}-{result.policy_version}",
            "model": request.model_name,
            "model_version": request.model_version,
            "policy_version": result.policy_version,
            "decision": result.decision.value,
            "reasons": list(result.reasons),
            "evidence": _evidence_record(self.collect_evidence(request)),
            "evidence_references": [str(request.dependency_report), str(request.container_report)],
        }
        with audit_path.open("a", encoding="utf-8") as audit_log:
            audit_log.write(json.dumps(record, sort_keys=True) + "\n")
        return result


def _evidence_record(evidence: ReleaseEvidence) -> dict[str, object]:
    record = asdict(evidence)
    if evidence.quality_metrics is not None:
        record["quality_metrics"] = asdict(evidence.quality_metrics)
    return record