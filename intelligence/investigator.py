"""Read-only, evidence-cited release investigation."""

from pydantic import BaseModel, ConfigDict, Field

from policy.engine import Decision, PolicyResult, ReleaseEvidence


class Finding(BaseModel):
    """One advisory finding with exact evidence references."""

    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1)
    evidence_fields: list[str] = Field(min_length=1)


class InvestigationReport(BaseModel):
    """Schema-validated advisory output; it contains no authority to deploy."""

    model_config = ConfigDict(extra="forbid")

    decision: Decision
    summary: str = Field(min_length=1)
    findings: list[Finding]
    policy_version: str = Field(min_length=1)
    advisory_only: bool = True


class ReleaseInvestigator:
    """Correlate canonical evidence without mutating or overriding policy."""

    def investigate(self, evidence: ReleaseEvidence, result: PolicyResult) -> InvestigationReport:
        """Produce deterministic findings and citations for an existing decision."""
        findings: list[Finding] = []
        if evidence.critical_vulnerabilities:
            findings.append(
                Finding(
                    message="Critical vulnerabilities prevent promotion.",
                    evidence_fields=["critical_vulnerabilities"],
                )
            )
        if not evidence.artifact_integrity_valid:
            findings.append(
                Finding(
                    message="The artifact digest does not match the recorded digest.",
                    evidence_fields=["artifact_sha256", "artifact_integrity_valid"],
                )
            )
        if not evidence.artifact_signature_valid:
            findings.append(
                Finding(
                    message="The artifact signature could not be verified.",
                    evidence_fields=["artifact_signature_valid"],
                )
            )
        if not evidence.provenance_valid:
            findings.append(
                Finding(
                    message="Required artifact provenance is invalid.",
                    evidence_fields=["provenance_valid"],
                )
            )
        if not evidence.metadata_consistent:
            findings.append(
                Finding(
                    message="Recorded metadata does not match the actual evaluation.",
                    evidence_fields=["metadata_consistent", "quality_metrics"],
                )
            )
        if evidence.drift_psi >= 0.20:
            findings.append(
                Finding(
                    message="Severe drift requires retraining before promotion.",
                    evidence_fields=["drift_psi", "drift_status"],
                )
            )
        if not findings:
            findings.append(
                Finding(
                    message="All supplied release evidence supports the policy outcome.",
                    evidence_fields=["policy_version", "evidence_references"],
                )
            )
        return InvestigationReport(
            decision=result.decision,
            summary=_summary(result.decision),
            findings=findings,
            policy_version=result.policy_version,
        )


def _summary(decision: Decision) -> str:
    if decision is Decision.PROMOTE:
        return "Release evidence supports promotion."
    if decision is Decision.RETRAIN:
        return "Release evidence recommends retraining before deployment."
    return "Release evidence contains a blocking condition."