# Model Lifecycle

## States

```text
CREATED -> EVALUATING -> PROMOTE -> DEPLOYED -> MONITORING -> HEALTHY
                         |                         |
                         +-> BLOCK                 +-> DEGRADED -> OBSERVING
                         |                                      |
                         +-> RETRAIN                              v
                                                   FAILURE_CONFIRMED -> ROLLBACK
                                                                        |
                                                           +------------+------------+
                                                           v                         v
                                                       RECOVERED                  ESCALATE
```

## Legal transition rules

- `BLOCK` cannot transition to `DEPLOYED`.
- Invalid signatures, failed provenance, or critical vulnerabilities cannot transition to `PROMOTE`.
- `RETRAIN` returns to a new evaluation cycle; it does not deploy the candidate.
- Runtime rollback selects the last approved healthy version.
- A failed automatic rollback transitions to `ESCALATE` and cannot automatically promote another version.

## Initial rollback policy

- Observation window: 60 seconds
- Evaluation interval: 15 seconds
- Trigger: 2 consecutive failed evaluations
- Cooldown: 5 minutes
- Maximum automatic rollback attempts: 1

These are initial configurable project values, not universal production standards.
