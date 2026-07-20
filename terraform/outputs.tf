/**
 * Outputs the most useful values after `terraform apply`:
 * - The Cloud Run service URL (open this in a browser to play the game).
 * - The Artifact Registry path used when pushing the image.
 */

output "cloud_run_service_url" {
  description = "Direct HTTPS URL of the Cloud Run service (requires IAM/IAP auth token — not directly browser-accessible)."
  value       = google_cloud_run_v2_service.app.uri
}

output "load_balancer_ip" {
  description = "Global static IPv4 address of the IAP-fronted HTTPS load balancer. Null when IAP is disabled."
  value       = var.enable_iap ? google_compute_global_address.frontend[0].address : null
}

output "iap_protected_url" {
  description = "HTTPS URL protected by IAP. Null when IAP is disabled. If a custom domain is configured, use that; otherwise access via the LB IP."
  value       = var.enable_iap ? (var.domain != null ? "https://${var.domain}" : "https://${google_compute_global_address.frontend[0].address}.nip.io") : null
}

output "cloud_run_proxy_command" {
  description = "The gcloud command to start a local proxy that injects your auth token. Use this when IAP is disabled and the Cloud Run service requires authentication."
  value       = "gcloud run services proxy ${var.app_name} --region=${var.region} --project=${var.project_id} --port=8080"
}

output "artifact_registry_image" {
  description = "Full image path in Artifact Registry that Cloud Run pulls from."
  value       = local.image
}

output "cloud_run_service_name" {
  description = "Name of the Cloud Run service."
  value       = google_cloud_run_v2_service.app.name
}
