import json
from pathlib import Path


def test_grafana_dashboard_has_required_operational_panels() -> None:
    dashboard = json.loads(Path("deploy/grafana/modelshield-dashboard.json").read_text())
    titles = {panel["title"] for panel in dashboard["panels"]}

    assert titles == {
        "Request Rate",
        "Request Latency",
        "Request Errors",
        "Model Version",
        "Model Predictions",
        "Model Drift",
        "Release Decisions",
        "Rollback Events",
    }