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


def test_grafana_dashboard_binds_prometheus_datasource_and_real_metrics() -> None:
    dashboard = json.loads(Path("deploy/grafana/modelshield-dashboard.json").read_text())
    expressions = "\n".join(
        target["expr"]
        for panel in dashboard["panels"]
        for target in panel.get("targets", [])
    )

    assert dashboard["templating"]["list"][0]["type"] == "datasource"
    assert all(panel["datasource"]["uid"] == "${DS_PROMETHEUS}" for panel in dashboard["panels"])
    assert "modelshield_prediction_requests_total" in expressions
    assert "modelshield_prediction_latency_seconds_bucket" in expressions
    assert "modelshield_prediction_errors_total" in expressions
    assert "modelshield_model_version_info" in expressions
    assert "modelshield_predictions_total" in expressions
    assert "modelshield_drift_psi" in expressions
    assert "modelshield_release_decisions_total" in expressions
    assert "modelshield_rollback_events_total" in expressions


def test_grafana_prometheus_datasource_is_provisionable() -> None:
    datasource = Path("deploy/grafana/datasource-prometheus.yml").read_text(encoding="utf-8")

    assert "type: prometheus" in datasource
    assert "url: http://prometheus:9090" in datasource