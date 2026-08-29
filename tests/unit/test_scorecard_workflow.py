from pathlib import Path

import yaml


def test_scorecard_workflow_publishes_sarif_with_required_permissions() -> None:
    workflow = yaml.safe_load(Path(".github/workflows/scorecard.yml").read_text(encoding="utf-8"))
    job = workflow["jobs"]["analysis"]
    permissions = job["permissions"]

    assert permissions["contents"] == "read"
    assert permissions["security-events"] == "write"
    assert permissions["id-token"] == "write"
    scorecard = next(step for step in job["steps"] if "scorecard-action" in step.get("uses", ""))
    assert scorecard["with"]["results_format"] == "sarif"
    assert scorecard["with"]["publish_results"] is True