from fastapi.testclient import TestClient

from api.app import app


client = TestClient(app)


def valid_evidence() -> dict[str, object]:
    return {
        "quality_passed": True,
        "drift_psi": 0.05,
        "critical_vulnerabilities": 0,
        "artifact_integrity_valid": True,
        "artifact_signature_valid": True,
        "provenance_valid": True,
        "dependency_scan_passed": True,
        "container_scan_passed": True,
    }


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_evaluate_endpoint_returns_policy_decision() -> None:
    response = client.post("/v1/releases/evaluate", json=valid_evidence())

    assert response.status_code == 200
    assert response.json()["decision"] == "PROMOTE"


def test_evaluate_endpoint_preserves_security_precedence() -> None:
    payload = valid_evidence()
    payload["critical_vulnerabilities"] = 1

    response = client.post("/v1/releases/evaluate", json=payload)

    assert response.status_code == 200
    assert response.json()["decision"] == "BLOCK"


def test_evaluate_endpoint_rejects_unknown_fields() -> None:
    payload = valid_evidence()
    payload["ai_recommendation"] = "PROMOTE"

    response = client.post("/v1/releases/evaluate", json=payload)

    assert response.status_code == 422