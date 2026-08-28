# ModelShield

ModelShield is a policy-driven secure ML release control plane. It evaluates model quality, data drift, artifact integrity, provenance, and supply-chain security before promoting a model to Kubernetes, then monitors runtime behavior and supports controlled rollback.

## Product promise

> No ML model reaches deployment unless its quality, security, provenance, and deployment policies pass.

Deterministic policy enforcement is the production safety boundary. Any future AI Release Intelligence layer will investigate evidence and explain decisions, but it will never override hard policy results.

## Phase 0 status

This repository contains the verified project foundation. Application implementation begins in Phase 1 after the structure, policy vocabulary, lifecycle, and threat model are reviewed.

Verify the baseline on Windows, macOS, or Linux:

```text
python scripts/verify_phase_0.py
```

## Golden path

```text
Git commit -> evaluate -> scan -> inspect -> hash/sign -> verify provenance -> policy decision -> Kubernetes -> monitoring -> rollback
```

## V1 scope

- Deterministic policy engine
- Model quality and PSI drift evaluation
- Artifact hashing and signature verification
- Dependency and container scanning
- FastAPI model service
- Kubernetes deployment
- Prometheus metrics
- Deterministic rollback
- Unit, integration, scenario, and security tests

Deferred work is documented in the project specification: MLflow, Terraform, Grafana polish, OPA/Conftest, Scorecard, and the AI intelligence layer.

## Repository map

- `docs/`: architecture, threat model, and lifecycle contracts
- `policies/`: version-controlled policy inputs
- `scripts/`: repository and phase verification utilities
- `tests/`: unit, integration, scenario, and security test suites

## Development rule

Each phase must be implemented, tested, verified, and documented before the next phase begins. No production capability is claimed until it is backed by executable evidence.
