"""Normalize dependency and container vulnerability scan reports."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ScanResult:
    """Security scan outcome with severity counts."""

    scan_type: str
    passed: bool
    critical: int
    high: int
    medium: int
    low: int


def load_scan_result(path: Path, *, scan_type: str) -> ScanResult:
    """Load a Trivy-compatible JSON report and fail closed on invalid input."""
    if scan_type not in {"dependency", "container"}:
        raise ValueError("scan_type must be dependency or container")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"unable to read valid scan report: {path}") from error
    vulnerabilities = _vulnerabilities(payload)
    counts = {severity: 0 for severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW")}
    for item in vulnerabilities:
        severity = item.get("Severity")
        if severity in counts:
            counts[severity] += 1
    return ScanResult(
        scan_type=scan_type,
        passed=counts["CRITICAL"] == 0,
        critical=counts["CRITICAL"],
        high=counts["HIGH"],
        medium=counts["MEDIUM"],
        low=counts["LOW"],
    )


def _vulnerabilities(payload: Any) -> list[dict[str, Any]]:
    """Extract vulnerability entries from each Trivy result block."""
    if not isinstance(payload, dict) or not isinstance(payload.get("Results"), list):
        raise ValueError("scan report must contain a Results list")
    vulnerabilities: list[dict[str, Any]] = []
    for result in payload["Results"]:
        if not isinstance(result, dict):
            raise ValueError("each scan result must be an object")
        entries = result.get("Vulnerabilities", [])
        if not isinstance(entries, list) or any(not isinstance(item, dict) for item in entries):
            raise ValueError("Vulnerabilities must be a list of objects")
        vulnerabilities.extend(entries)
    return vulnerabilities