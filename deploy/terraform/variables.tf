variable "namespace" {
  description = "Kubernetes namespace for ModelShield."
  type        = string
  default     = "modelshield"
}

variable "image" {
  description = "ModelShield container image."
  type        = string
  default     = "modelshield:local"
}

variable "replicas" {
  description = "Number of model-service replicas."
  type        = number
  default     = 2

  validation {
    condition     = var.replicas >= 1 && floor(var.replicas) == var.replicas
    error_message = "replicas must be a positive whole number."
  }
}

variable "kubeconfig_path" {
  description = "Optional kubeconfig path used by the Kubernetes provider."
  type        = string
  default     = null
  nullable    = true
}

variable "kube_context" {
  description = "Optional Kubernetes context used by the provider."
  type        = string
  default     = null
  nullable    = true
}