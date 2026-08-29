output "namespace" {
  description = "Namespace containing ModelShield."
  value       = kubernetes_namespace.modelshield.metadata[0].name
}

output "service_name" {
  description = "Internal Kubernetes service name."
  value       = kubernetes_service.modelshield.metadata[0].name
}