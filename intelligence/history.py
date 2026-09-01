"""Read-only historical intelligence over release audit records."""

import json
from collections import Counter
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HistoricalInsight(BaseModel):
    """Evidence-backed insight from release history."""

    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1)
    evidence_fields: list[str] = Field(min_length=1)


class ReleaseHistoryReport(BaseModel):
    """Summary of prior release decisions and release trends."""

    model_config = ConfigDict(extra="forbid")

    total_releases: int
    decision_counts: dict[str, int]
    recurring_reasons: dict[str, int]
    latest_release_id: str
    latest_decision: str
    insights: list[HistoricalInsight]
    advisory_only: bool = True


def load_audit_records(path: Path) -> list[dict[str, Any]]:
    """Load non-empty JSONL audit records."""
    try:
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except OSError as error:
        raise ValueError(f"unable to read audit log: {path}") from error
    records: list[dict[str, Any]] = []
    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError("audit log contains invalid JSON") from error
        if not isinstance(record, dict) or "decision" not in record or "evidence" not in record:
            raise ValueError("audit records must contain decision and evidence")
        records.append(record)
    if not records:
        raise ValueError("audit log is empty")
    return records


def analyze_release_history(records: list[dict[str, Any]]) -> ReleaseHistoryReport:
    """Analyze release history without changing any policy decision."""
    if not records:
        raise ValueError("at least one audit record is required")
    decision_counts = Counter(str(record["decision"]) for record in records)
    reason_counts: Counter[str] = Counter()
    for record in records:
        reason_counts.update(str(reason) for reason in record.get("reasons", ()))
    latest = records[-1]
    insights = _quality_insights(records) + _drift_insights(records)
    recurring_reasons = {reason: count for reason, count in reason_counts.items() if count > 1}
    if recurring_reasons:
        insights.append(
            HistoricalInsight(
                message="Some policy reasons recur across release history.",
                evidence_fields=["reasons"],
            )
        )
    return ReleaseHistoryReport(
        total_releases=len(records),
        decision_counts=dict(decision_counts),
        recurring_reasons=recurring_reasons,
        latest_release_id=str(latest.get("release_id", "")),
        latest_decision=str(latest["decision"]),
        insights=insights,
    )


def _quality_insights(records: list[dict[str, Any]]) -> list[HistoricalInsight]:
    first_f1 = _f1(records[0])
    latest_f1 = _f1(records[-1])
    if first_f1 is not None and latest_f1 is not None and latest_f1 < first_f1:
        return [
            HistoricalInsight(
                message="Latest release F1 is lower than the first recorded release.",
                evidence_fields=["evidence.quality_metrics.f1"],
            )
        ]
    return []


def _drift_insights(records: list[dict[str, Any]]) -> list[HistoricalInsight]:
    first_drift = _drift(records[0])
    latest_drift = _drift(records[-1])
    if first_drift is not None and latest_drift is not None and latest_drift > first_drift:
        return [
            HistoricalInsight(
                message="Latest release drift PSI is higher than the first recorded release.",
                evidence_fields=["evidence.drift_psi"],
            )
        ]
    return []


def _f1(record: dict[str, Any]) -> float | None:
    metrics = record.get("evidence", {}).get("quality_metrics")
    if isinstance(metrics, dict) and metrics.get("f1") is not None:
        return float(metrics["f1"])
    return None


def _drift(record: dict[str, Any]) -> float | None:
    value = record.get("evidence", {}).get("drift_psi")
    return float(value) if value is not None else None