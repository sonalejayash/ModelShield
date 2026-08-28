import json
from pathlib import Path

import pytest

from security.scans import ScanResult, load_scan_result


def write_report(path: Path, vulnerabilities: list[dict[str, str]]) -> None:
    path.write_text(json.dumps({"Results": [{"Vulnerabilities": vulnerabilities}]}), encoding="utf-8")


def test_clean_dependency_scan_passes(tmp_path: Path) -> None:
    report = tmp_path / "dependencies.json"
    write_report(report, [{"Severity": "HIGH"}, {"Severity": "LOW"}])

    assert load_scan_result(report, scan_type="dependency") == ScanResult("dependency", True, 0, 1, 0, 1)


def test_critical_container_vulnerability_fails(tmp_path: Path) -> None:
    report = tmp_path / "container.json"
    write_report(report, [{"Severity": "CRITICAL"}, {"Severity": "MEDIUM"}])

    result = load_scan_result(report, scan_type="container")
    assert result.scan_type == "container"
    assert not result.passed
    assert result.critical == 1


def test_malformed_report_fails_closed(tmp_path: Path) -> None:
    report = tmp_path / "invalid.json"
    report.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="Results"):
        load_scan_result(report, scan_type="dependency")


def test_unknown_scan_type_is_rejected(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    write_report(report, [])

    with pytest.raises(ValueError, match="scan_type"):
        load_scan_result(report, scan_type="other")