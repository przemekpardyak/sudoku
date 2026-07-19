/**
 * Outputs the most useful values after `terraform apply`:
 * - The Cloud Run service URL (open this in a browser to play the game).
 * - The Artifact Registry path used when pushing the image.
 */

output "cloud_run_service_url" {
  description = "Public HTTPS URL of the deployed Cloud Run service."
  value       = google_cloud_run_v2_service.app.uri
}

output "artifact_registry_image" {
  description = "Full image path in Artifact Registry that Cloud Run pulls from."
  value       = local.image
}

output "cloud_run_service_name" {
  description = "Name of the Cloud Run service."
  value       = google_cloud_run_v2_service.app.name
}
