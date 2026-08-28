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

## Policy precedence

The policy engine evaluates all available evidence, then applies the highest-priority
result. AI recommendations, when added, are advisory and cannot override these rules.

| Priority | Condition | Decision |
|---:|---|---|
| 1 | Critical vulnerability, invalid signature, or failed provenance | `BLOCK` |
| 2 | Failed quality gate | `BLOCK` |
| 2 | Severe pre-release drift with security gates passing | `RETRAIN` |
| 3 | All required gates pass | `PROMOTE` |
| Runtime | Sustained runtime degradation | `ROLLBACK` |

When multiple conditions apply, the highest-priority condition wins. For example, a
quality pass combined with a security failure always produces `BLOCK`, even if an AI
recommendation suggests promotion.

## Initial rollback policy

- Observation window: 60 seconds
- Evaluation interval: 15 seconds
- Trigger: 2 consecutive failed evaluations
- Cooldown: 5 minutes
- Maximum automatic rollback attempts: 1

These are initial configurable project values, not universal production standards.
