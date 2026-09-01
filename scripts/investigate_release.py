"""Generate an advisory investigation report from a saved release audit."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from intelligence.investigator import ReleaseInvestigator
from policy.engine import Decision, PolicyResult, ReleaseEvidence
from quality.evaluator import QualityMetrics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit", type=Path)
    arguments = parser.parse_args()
    record = _load_latest_record(arguments.audit)
    evidence = _release_evidence(record["evidence"])
    result = PolicyResult(
        decision=Decision(record["decision"]),
        reasons=tuple(record.get("reasons", ())),
        policy_version=record["policy_version"],
    )
    report = ReleaseInvestigator().investigate(evidence, result)
    print(json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True))
    return 0


def _load_latest_record(path: Path) -> dict[str, Any]:
    try:
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not lines:
            raise ValueError("audit log is empty")
        payload = json.loads(lines[-1])
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"unable to read audit log: {path}") from error
    if not isinstance(payload, dict) or "evidence" not in payload:
        raise SystemExit("audit record must contain evidence")
    return payload


def _release_evidence(payload: dict[str, Any]) -> ReleaseEvidence:
    metrics = payload.get("quality_metrics")
    quality_metrics = QualityMetrics(**metrics) if isinstance(metrics, dict) else None
    return ReleaseEvidence(
        quality_passed=payload["quality_passed"],
        drift_psi=payload["drift_psi"],
        critical_vulnerabilities=payload["critical_vulnerabilities"],
        artifact_integrity_valid=payload["artifact_integrity_valid"],
        artifact_signature_valid=payload["artifact_signature_valid"],
        provenance_valid=payload["provenance_valid"],
        dependency_scan_passed=payload["dependency_scan_passed"],
        container_scan_passed=payload["container_scan_passed"],
        release_id=payload.get("release_id", ""),
        model_name=payload.get("model_name", ""),
        model_version=payload.get("model_version", ""),
        artifact_path=payload.get("artifact_path", ""),
        artifact_sha256=payload.get("artifact_sha256", ""),
        quality_metrics=quality_metrics,
        drift_status=payload.get("drift_status", ""),
        high_vulnerabilities=payload.get("high_vulnerabilities", 0),
        dependency_scan_critical=payload.get("dependency_scan_critical", 0),
        container_scan_critical=payload.get("container_scan_critical", 0),
        evidence_references=tuple(payload.get("evidence_references", ())),
        metadata_consistent=payload.get("metadata_consistent", True),
    )


if __name__ == "__main__":
    sys.exit(main())