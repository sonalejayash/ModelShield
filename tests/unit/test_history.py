import json
from pathlib import Path

import pytest

from intelligence.history import analyze_release_history, load_audit_records


def record(release_id: str, decision: str, *, reason: str, f1: float, drift: float) -> dict[str, object]:
    return {
        "release_id": release_id,
        "decision": decision,
        "reasons": [reason],
        "evidence": {"quality_metrics": {"f1": f1}, "drift_psi": drift},
    }


def test_analyzes_decision_history_and_trends() -> None:
    records = [
        record("r1", "PROMOTE", reason="all required release gates passed", f1=0.98, drift=0.02),
        record("r2", "BLOCK", reason="artifact signature verification failed", f1=0.95, drift=0.10),
        record("r3", "BLOCK", reason="artifact signature verification failed", f1=0.90, drift=0.25),
    ]

    report = analyze_release_history(records)

    assert report.total_releases == 3
    assert report.decision_counts == {"PROMOTE": 1, "BLOCK": 2}
    assert report.recurring_reasons == {"artifact signature verification failed": 2}
    assert report.latest_release_id == "r3"
    assert any("F1" in insight.message for insight in report.insights)
    assert any("drift" in insight.message for insight in report.insights)
    assert report.advisory_only


def test_loads_jsonl_audit_records(tmp_path: Path) -> None:
    audit = tmp_path / "audit.jsonl"
    records = [record("r1", "PROMOTE", reason="all required release gates passed", f1=0.98, drift=0.02)]
    audit.write_text("\n".join(json.dumps(item) for item in records), encoding="utf-8")

    assert load_audit_records(audit) == records


def test_rejects_empty_audit_log(tmp_path: Path) -> None:
    audit = tmp_path / "audit.jsonl"
    audit.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="empty"):
        load_audit_records(audit)