# ModelShield Terraform

This module manages the minimal Kubernetes resources needed for the local ModelShield demonstration. It does not create cloud infrastructure and requires no cloud credentials.

Validate the module without a cluster:

```bash
terraform init
terraform fmt -check
terraform validate
```

Apply it only when a Kubernetes context is available:

```bash
terraform apply -var='image=modelshield:local'
```

The module mirrors the hardened deployment contract: non-root execution, dropped capabilities, a read-only root filesystem, resource limits, health probes, and Prometheus annotations.