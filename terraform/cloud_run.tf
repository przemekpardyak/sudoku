/**
 * Cloud Run service that serves the Flask app.
 *
 * Image path: {region}-docker.pkg.dev/{project_id}/{app_name}-repo/{app_name}:{image_tag}
 * Cloud Run serves HTTPS automatically and maps $PORT to 8080 (matches Dockerfile).
 */

locals {
  image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.app_name}-repo/${var.app_name}:${var.image_tag}"
}

resource "google_cloud_run_v2_service" "app" {
  name     = var.app_name
  location = var.region

  template {
    containers {
      image = local.image
      resources {
        limits = {
          "memory" = var.memory
          "cpu"    = var.cpu
        }
      }
      env {
        name  = "PORT"
        value = "8080"
      }
    }

    scaling {
      min_instance_count = var.min_instance_count
      max_instance_count = var.max_instance_count
    }

    dynamic "service_account" {
      for_each = var.service_account_email != null ? [1] : []
      content {
        email = var.service_account_email
      }
    }
  }

  # Traffic routes 100% to the latest revision.
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    google_project_service.enabled_apis,
    google_artifact_registry_repository.app_repo,
  ]
}

/**
 * IAM binding: allow unauthenticated invocation so the web app is public.
 * Toggle with var.allow_unauthenticated.
 */
resource "google_cloud_run_v2_service_iam_binding" "public_invoker" {
  count    = var.allow_unauthenticated ? 1 : 0
  location = google_cloud_run_v2_service.app.location
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  members = [
    "allUsers",
  ]
}
