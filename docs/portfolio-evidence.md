# Portfolio Evidence

This document captures the current verification evidence for ModelShield. The README remains the primary project guide; this file is a concise evidence appendix for interview review.

## Final Local Demo

Command:

```bash
python scripts/demo.py --model-version portfolio-v1 --output-dir artifacts/portfolio-demo
```

Captured output:

```text
ModelShield demo
1. Running deterministic release gate
Training model...
Artifact SHA-256: 2b08cb2945a60fbfa4aae563717863400170e284e9e1610cc02dce58b5dbbfe4
Quality: PASS
Drift: PASS
Policy: PROMOTE
Audit: artifacts\portfolio-demo\audit.jsonl
Release: PROMOTED
2. Regenerating advisory investigation from audit
{
  "advisory_only": true,
  "decision": "PROMOTE",
  "findings": [
    {
      "evidence_fields": [
        "policy_version",
        "evidence_references"
      ],
      "message": "All supplied release evidence supports the policy outcome."
    }
  ],
  "policy_version": "policy-v1",
  "summary": "Release evidence supports promotion."
}
3. Summarizing historical release evidence
{
  "advisory_only": true,
  "decision_counts": {
    "PROMOTE": 1
  },
  "insights": [],
  "latest_decision": "PROMOTE",
  "latest_release_id": "release-portfolio-v1",
  "recurring_reasons": {},
  "total_releases": 1
}
Demo complete
```

## Verification Checklist

- Python regression tests: `71 passed`
- Repository verifier: passing
- Docker image build: verified in CI and local validation during development
- Trivy high/critical container scan: enforced in CI
- Conftest Kubernetes policy checks: enforced in CI and validated locally
- Terraform validation: enforced in CI and validated with the official Terraform container
- SBOM generation: CycloneDX artifact generated in CI
- OpenSSF Scorecard: dedicated workflow configured

## Interview Talking Points

- Deterministic policy remains the release authority.
- AI/intelligence is read-only, schema-validated, and advisory.
- Audit records contain the evidence needed to reproduce decisions.
- Security failures take precedence over drift and lower-priority conditions.
- The demo proves training, verification, policy, audit, investigation, and history analysis in one command.