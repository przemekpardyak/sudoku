/**
 * Firestore database for game state persistence.
 *
 * Cloud Run containers are stateless, so we need server-side storage
 * to persist game state across restarts. Firestore (Native mode) is
 * used because it's serverless, scales to zero, and has a generous
 * free tier.
 *
 * The app uses the FIRESTORE_PROJECT env var to connect. In production
 * on Cloud Run, the service account attached to the Cloud Run service
 * is automatically used for authentication.
 */

resource "google_firestore_database" "games_db" {
  name        = "(default)"
  type        = "FIRESTORE_NATIVE"
  location_id = var.firestore_location

  # Point in time recovery enables continuous backups.
  point_in_time_recovery_enablement = var.firestore_enable_pitr ? "POINT_IN_TIME_RECOVERY_ENABLED" : "POINT_IN_TIME_RECOVERY_DISABLED"

  # Prevent accidental deletion via Terraform destroy — cleanup.sh handles it.
  delete_protection_state = "DELETE_PROTECTION_DISABLED"

  depends_on = [google_project_service.enabled_apis, google_project_service.firestore_api]
}

# Enable the Firestore API (required before creating a database).
# We add it to the enabled_apis list in providers.tf, but also ensure
# the Firestore-specific API is enabled here for clarity.
resource "google_project_service" "firestore_api" {
  service                    = "firestore.googleapis.com"
  disable_on_destroy         = true
  disable_dependent_services = true

  project = var.project_id
}
