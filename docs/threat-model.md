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
| Prompt injection in model metadata | Release intelligence is read-only, schema-validated, and never authoritative |
| Misleading or missing AI evidence | Fail-safe handling and deterministic policy remains authoritative |
| Rollback loop | One automatic rollback attempt, then `ESCALATE` for manual review |

## AI release-intelligence threats and controls

| Threat | Control |
|---|---|
| Prompt injection | Evidence is treated as untrusted data and never as instructions |
| Malicious audit evidence | Structured evidence only and schema validation |
| Missing evidence | Explicit missing-evidence findings and deterministic fallback |
| Contradictory evidence | Decision consistency validation and contradiction findings |
| Malformed AI output | Schema validation and fail-closed parsing |
| Decision manipulation | Policy engine remains authoritative and decisions must match |
| Tool escalation | No shell access, no unrestricted `kubectl`, and no tool execution path |
| AI hallucination | Evidence-cited findings and deterministic fallback |
| Ollama unavailable | Optional transport fails closed without changing release safety |
| AI timeout/failure | Timeout-bound transport and deterministic non-AI investigation fallback |

AI release intelligence has no secret access, no deployment permission, and no authority to approve, block, retrain, roll back, or modify access controls.

## Security assumptions

Security-test artifacts are safe simulations. ModelShield never executes arbitrary model payloads during inspection. Secrets are not committed to the repository. Thresholds are project policy values, not universal safety guarantees.
