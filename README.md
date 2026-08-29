# ModelShield

ModelShield is a policy-driven secure ML release control plane. It evaluates model quality, data drift, artifact integrity, provenance, and supply-chain security before promoting a model to Kubernetes, then monitors runtime behavior and supports controlled rollback.

## Product promise

> No ML model reaches deployment unless its quality, security, provenance, and deployment policies pass.

Deterministic policy enforcement is the production safety boundary. Any future AI Release Intelligence layer will investigate evidence and explain decisions, but it will never override hard policy results.

## Current status

Phase 0 and the Phase 1 V1 implementation are complete. The repository currently contains a deterministic release-control workflow, a secure local model service, Kubernetes packaging, runtime rollback logic, and CI security gates.

Verify locally on Windows, macOS, or Linux:

```bash
python -m pip install -e ".[dev]"
python scripts/verify_phase_0.py
python -m pytest -q
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

The training workflow uses the built-in scikit-learn breast-cancer dataset and a seeded, scaled logistic-regression pipeline. Generated artifacts and metadata are written to the ignored `artifacts/` directory.

## Run locally

Start the API:

```bash
uvicorn api.app:app --reload
```

Train and evaluate the reproducible model workflow:

```bash
python scripts/train_model.py --output-dir artifacts --model-version v1
python scripts/evaluate_model.py artifacts/model-v1.json
```

Training records the dataset, random seed, test split, quality metrics, model version, artifact path, artifact SHA-256, signature, and provenance in `artifacts/model-v1.json`. Local training records `source_revision` as `local`; GitHub Actions records the triggering commit SHA through `GITHUB_SHA`.

Run the complete release gate from a clean artifact directory:

```bash
python scripts/release.py --model-version v1
```

The command trains the model, signs and verifies the artifact, re-evaluates the persisted model, checks policy thresholds and security evidence, writes `artifacts/audit.jsonl`, and returns exit code `0` only for `PROMOTE`. `BLOCK` returns `1`; `RETRAIN` returns `2` and is never deployed automatically.

Available endpoints:

- `GET /health`: service health
- `POST /v1/predict`: local model prediction
- `POST /v1/releases/evaluate`: deterministic release decision
- `GET /metrics`: Prometheus metrics

Build and run the container:

```bash
docker build --tag modelshield:local .
docker run --publish 8000:8000 modelshield:local
```

Deploy the local image to Kubernetes:

```bash
kubectl apply -f deploy/kubernetes/
```

The Kubernetes deployment uses two replicas, health probes, resource limits, a non-root security context, a read-only root filesystem, dropped capabilities, and a restrictive NetworkPolicy.

## Roadmap

### Phase 1.5: Platform improvements

- MLflow model and release tracking
- Terraform infrastructure modules
- Grafana dashboards
- SBOM generation and publication
- OPA/Conftest policy checks
- OpenSSF Scorecard integration

### Phase 2: Release intelligence

- Read-only AI evidence investigator
- Historical release intelligence
- Structured explanations with cited evidence

The AI layer will remain advisory. It will never approve, deploy, override policy, or modify access controls.

## Repository map

- `docs/`: architecture, threat model, and lifecycle contracts
- `policies/`: version-controlled policy inputs
- `scripts/`: repository and phase verification utilities
- `deploy/kubernetes/`: secure Deployment, Service, and NetworkPolicy manifests
- `tests/`: unit, integration, scenario, and security test suites

## Development rule

Each phase must be implemented, tested, verified, and documented before the next phase begins. No production capability is claimed until it is backed by executable evidence.
