/**
 * Cloud Run service that serves the Flask app.
 *
 * Image path: {region}-docker.pkg.dev/{project_id}/{app_name}-repo/{app_name}:{image_tag}
 * Cloud Run serves HTTPS automatically and maps $PORT to 8080 (matches Dockerfile).
 */

locals {
  image               = "${var.region}-docker.pkg.dev/${var.project_id}/${var.app_name}-repo/${var.app_name}:${var.image_tag}"
  run_service_account = var.service_account_email
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
      # NOTE: Do not set PORT here — Cloud Run v2 sets it automatically as a reserved variable.
      # The container must listen on $PORT (gunicorn in the Dockerfile binds to 0.0.0.0:8080
      # by default; Cloud Run matches PORT=8080 to the EXPOSE directive).
    }

    scaling {
      min_instance_count = var.min_instance_count
      max_instance_count = var.max_instance_count
    }

    # service_account_email, if provided, is attached to the revision.
    service_account = local.run_service_account
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
 * IAM binding: grant the run.invoker role to the configured members.
 *
 * Defaults to the currently authenticated gcloud user, since this project's
 * organization policy blocks the `allUsers` public member. To make the service
 * fully public (if allowed by your org policy), set:
 *   allow_unauthenticated = true  +  invoker_members = ["allUsers"]
 */
data "google_client_config" "current" {}

data "google_client_openid_userinfo" "me" {}

data "google_project" "number" {
  project_id = var.project_id
}

resource "google_cloud_run_v2_service_iam_binding" "invoker" {
  count    = var.allow_unauthenticated || length(var.invoker_members) > 0 ? 1 : 0
  location = google_cloud_run_v2_service.app.location
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  members  = length(var.invoker_members) > 0 ? var.invoker_members : ["user:${data.google_client_openid_userinfo.me.email}"]
}
