# Architecture

## Control flow

```text
Model release
    |
    +--> quality evaluation
    +--> drift evaluation
    +--> artifact inspection and hash
    +--> dependency and container scans
    +--> provenance and signature verification
              |
              v
       deterministic policy engine
          |        |        |
       PROMOTE   BLOCK   RETRAIN
          |
       Kubernetes
          |
       runtime monitoring
          |
       rollback or escalation
```

## Ownership boundaries

- Evaluators produce structured evidence.
- The policy engine owns release decisions.
- The deployment controller acts only on an approved decision.
- Runtime monitoring produces health evidence and may trigger the rollback state machine.
- Audit records capture inputs, policy version, gate results, final decision, and evidence references.
- The future AI investigator is read-only and cannot approve, deploy, modify RBAC, or bypass policy.

## V1 design constraints

The model is intentionally a small scikit-learn fraud classifier. ModelShield is the engineering product. Kubernetes and the model service must be runnable locally for the primary demonstration; optional hosted infrastructure is not required.
