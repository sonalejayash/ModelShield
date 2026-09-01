import json
from pathlib import Path

from tests.unit.test_release_controller import create_request
from controller.release import ReleaseController


def test_audit_record_contains_complete_release_evidence(tmp_path: Path) -> None:
    audit = tmp_path / "audit.jsonl"

    ReleaseController().evaluate_and_audit(create_request(tmp_path), audit)

    record = json.loads(audit.read_text(encoding="utf-8"))
    for field in (
        "release_id",
        "model",
        "version",
        "artifact_sha256",
        "quality",
        "drift",
        "security",
        "integrity",
        "provenance",
        "policy_version",
        "decision",
        "reasons",
        "evidence_references",
    ):
        assert field in record