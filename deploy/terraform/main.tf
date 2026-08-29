resource "kubernetes_namespace" "modelshield" {
  metadata {
    name = var.namespace
  }
}

resource "kubernetes_deployment" "modelshield" {
  metadata {
    name      = "modelshield"
    namespace = kubernetes_namespace.modelshield.metadata[0].name
    labels = {
      "app.kubernetes.io/name"      = "modelshield"
      "app.kubernetes.io/component" = "model-service"
    }
  }

  spec {
    replicas = var.replicas

    selector {
      match_labels = {
        "app.kubernetes.io/name" = "modelshield"
      }
    }

    template {
      metadata {
        labels = {
          "app.kubernetes.io/name"      = "modelshield"
          "app.kubernetes.io/component" = "model-service"
        }
        annotations = {
          "prometheus.io/scrape" = "true"
          "prometheus.io/path"   = "/metrics"
          "prometheus.io/port"   = "8000"
        }
      }

      spec {
        automount_service_account_token = false

        security_context {
          run_as_non_root = true
          run_as_user     = 10001
        }

        container {
          name              = "modelshield"
          image             = var.image
          image_pull_policy = "IfNotPresent"

          port {
            name           = "http"
            container_port = 8000
          }

          security_context {
            allow_privilege_escalation = false
            read_only_root_filesystem  = true
            capabilities {
              drop = ["ALL"]
            }
          }

          resources {
            requests = {
              cpu    = "100m"
              memory = "128Mi"
            }
            limits = {
              cpu    = "500m"
              memory = "256Mi"
            }
          }

          readiness_probe {
            http_get {
              path = "/health"
              port = "http"
            }
            period_seconds    = 15
            timeout_seconds   = 3
            failure_threshold = 2
          }

          liveness_probe {
            http_get {
              path = "/health"
              port = "http"
            }
            period_seconds    = 15
            timeout_seconds   = 3
            failure_threshold = 2
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "modelshield" {
  metadata {
    name      = "modelshield"
    namespace = kubernetes_namespace.modelshield.metadata[0].name
  }

  spec {
    selector = {
      "app.kubernetes.io/name" = "modelshield"
    }
    port {
      name        = "http"
      port        = 8000
      target_port = "http"
    }
    type = "ClusterIP"
  }
}