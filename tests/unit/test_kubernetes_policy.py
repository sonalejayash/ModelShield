from pathlib import Path

import yaml


def test_deployment_contains_required_security_controls() -> None:
    deployment = yaml.safe_load(Path("deploy/kubernetes/deployment.yaml").read_text(encoding="utf-8"))
    pod_spec = deployment["spec"]["template"]["spec"]
    container = pod_spec["containers"][0]

    assert pod_spec["securityContext"]["runAsNonRoot"] is True
    assert pod_spec["securityContext"]["runAsUser"] == 10001
    assert container["securityContext"]["allowPrivilegeEscalation"] is False
    assert container["securityContext"]["readOnlyRootFilesystem"] is True
    assert "requests" in container["resources"]
    assert "limits" in container["resources"]