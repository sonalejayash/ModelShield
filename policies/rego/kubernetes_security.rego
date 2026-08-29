package main

deny contains msg if {
  input.kind == "Deployment"
  not input.spec.template.spec.securityContext.runAsNonRoot
  msg := "Deployment pods must require non-root execution"
}

deny contains msg if {
  input.kind == "Deployment"
  not input.spec.template.spec.securityContext.runAsUser
  msg := "Deployment pods must set an explicit non-root user"
}

deny contains msg if {
  input.kind == "Deployment"
  some i
  container := input.spec.template.spec.containers[i]
  not container.securityContext.allowPrivilegeEscalation == false
  msg := sprintf("Container %q must disable privilege escalation", [container.name])
}

deny contains msg if {
  input.kind == "Deployment"
  some i
  container := input.spec.template.spec.containers[i]
  not container.securityContext.readOnlyRootFilesystem
  msg := sprintf("Container %q must use a read-only root filesystem", [container.name])
}

deny contains msg if {
  input.kind == "Deployment"
  some i
  container := input.spec.template.spec.containers[i]
  container.securityContext.privileged == true
  msg := sprintf("Container %q must not be privileged", [container.name])
}

deny contains msg if {
  input.kind == "Deployment"
  some i
  container := input.spec.template.spec.containers[i]
  not container.resources.requests.cpu
  msg := sprintf("Container %q must define a CPU request", [container.name])
}

deny contains msg if {
  input.kind == "Deployment"
  some i
  container := input.spec.template.spec.containers[i]
  not container.resources.requests.memory
  msg := sprintf("Container %q must define a memory request", [container.name])
}

deny contains msg if {
  input.kind == "Deployment"
  some i
  container := input.spec.template.spec.containers[i]
  not container.resources.limits.cpu
  msg := sprintf("Container %q must define a CPU limit", [container.name])
}

deny contains msg if {
  input.kind == "Deployment"
  some i
  container := input.spec.template.spec.containers[i]
  not container.resources.limits.memory
  msg := sprintf("Container %q must define a memory limit", [container.name])
}