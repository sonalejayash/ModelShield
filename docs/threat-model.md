# Threat Model

## Assets

- Model artifacts and their hashes/signatures
- Release metadata and provenance
- Policy configuration
- Deployment credentials and Kubernetes permissions
- Audit records
- Runtime metrics and evidence

## Threats and controls

| Threat | Control |
|---|---|
| Tampered model artifact | Hash, inspect, sign, and verify before deployment |
| Untrusted dependency or image | Dependency scan and Trivy policy gate |
| False or incomplete provenance | Required metadata and provenance verification |
| Policy bypass | Central deterministic policy engine and explicit precedence |
| Over-privileged controller | Least-privilege ServiceAccount and RBAC |
| Compromised container | Non-root, dropped capabilities, resource limits, and read-only filesystem where practical |
| Network abuse | Kubernetes NetworkPolicy |
| Prompt injection in model metadata | AI is V2, read-only, schema-validated, and never authoritative |
| Misleading or missing AI evidence | Fail-safe handling and deterministic policy remains authoritative |
| Rollback loop | One automatic rollback attempt, then `ESCALATE` for manual review |

## Security assumptions

Security-test artifacts are safe simulations. ModelShield never executes arbitrary model payloads during inspection. Secrets are not committed to the repository. Thresholds are project policy values, not universal safety guarantees.
