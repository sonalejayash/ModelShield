"""Optional model-backed explanation adapter with fail-safe validation."""

import json
from collections.abc import Callable
from dataclasses import asdict

from policy.engine import PolicyResult, ReleaseEvidence

from .investigator import InvestigationReport


class ModelBackedInvestigator:
    """Ask an injected model for explanation while policy remains authoritative."""

    def __init__(self, complete: Callable[[str], str]) -> None:
        self.complete = complete

    def investigate(self, evidence: ReleaseEvidence, result: PolicyResult) -> InvestigationReport:
        """Generate and validate an advisory explanation from structured evidence."""
        prompt = json.dumps(
            {
                "task": "Explain the existing release decision using only this evidence.",
                "evidence": asdict(evidence),
                "policy_decision": {
                    "decision": result.decision.value,
                    "policy_version": result.policy_version,
                    "reasons": list(result.reasons),
                },
                "output_schema": InvestigationReport.model_json_schema(),
            },
            sort_keys=True,
            default=str,
        )
        try:
            report = InvestigationReport.model_validate_json(self.complete(prompt))
        except Exception as error:
            raise ValueError("model explanation was not valid investigation JSON") from error
        if report.decision is not result.decision or report.policy_version != result.policy_version:
            raise ValueError("model explanation cannot change the deterministic policy result")
        if not report.advisory_only:
            raise ValueError("model explanation must be advisory_only")
        return report