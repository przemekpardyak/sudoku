/**
 * Artifact Registry repo to hold the container image for Cloud Run.
 */

resource "google_artifact_registry_repository" "app_repo" {
  location      = var.region
  repository_id = "${var.app_name}-repo"
  description   = "Container images for the ${var.app_name} Flask app."
  format        = "DOCKER"

  depends_on = [google_project_service.enabled_apis]
}
