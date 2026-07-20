/**
 * Identity-Aware Proxy (IAP) in front of Cloud Run (OPTIONAL).
 *
 * Architecture:
 *   Internet → Global HTTPS LB → URL Map → Backend Service (IAP enabled)
 *     → Serverless NEG → Cloud Run service
 *
 * IAP intercepts unauthenticated browser requests and triggers the Google
 * login flow, attaching a signed JWT to proxied requests. Cloud Run's IAM
 * policy trusts the IAP service agent, so the org policy restriction on
 * allUsers is satisfied.
 *
 * NOTE: IAP requires an external HTTP/HTTPS Application Load Balancer. If your
 * org policy (compute.restrictLoadBalancerCreationForTypes) blocks
 * EXTERNAL_HTTP_HTTPS or EXTERNAL_MANAGED_HTTP_HTTPS, set enable_iap = false
 * (the default) and use `gcloud run services proxy` for local browser access
 * instead.
 */

locals {
  iap_members = length(var.iap_allowed_users) > 0 ? var.iap_allowed_users : ["user:${data.google_client_openid_userinfo.me.email}"]
}

# --- IAP OAuth brand ---------------------------------------------------------
# A brand must exist before IAP can be used. Only one brand per project.
resource "google_iap_brand" "app" {
  count             = var.enable_iap ? 1 : 0
  support_email     = data.google_client_openid_userinfo.me.email
  application_title = "Sudoku"

  depends_on = [google_project_service.iap_apis]
}

# IAP OAuth client (uses the brand above).
resource "google_iap_client" "app" {
  count        = var.enable_iap ? 1 : 0
  display_name = "${var.app_name}-iap-client"
  brand        = google_iap_brand.app[0].name
}

# --- Serverless NEG pointing at the Cloud Run service ------------------------
resource "google_compute_region_network_endpoint_group" "cloudrun_neg" {
  count                 = var.enable_iap ? 1 : 0
  name                  = "${var.app_name}-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region

  cloud_run {
    service = google_cloud_run_v2_service.app.name
  }

  depends_on = [google_project_service.iap_apis]
}

# --- Backend service with IAP enabled ---------------------------------------
resource "google_compute_backend_service" "iap_backend" {
  count                 = var.enable_iap ? 1 : 0
  name                  = "${var.app_name}-backend"
  protocol              = "HTTPS"
  enable_cdn            = false
  load_balancing_scheme = var.iap_lb_scheme
  compression_mode      = "DISABLED"

  backend {
    group = google_compute_region_network_endpoint_group.cloudrun_neg[0].id
  }

  # The presence of the iap block enables IAP on this backend service.
  iap {
    oauth2_client_id     = google_iap_client.app[0].client_id
    oauth2_client_secret = google_iap_client.app[0].secret
  }

  depends_on = [google_project_service.iap_apis]
}

# --- URL map + HTTPS proxy + frontend rule ----------------------------------
resource "google_compute_url_map" "lb" {
  count           = var.enable_iap ? 1 : 0
  name            = "${var.app_name}-url-map"
  default_service = google_compute_backend_service.iap_backend[0].id
}

# Google-managed SSL certificate for the custom domain (if provided).
resource "google_compute_managed_ssl_certificate" "ssl" {
  count = var.enable_iap ? 1 : 0
  name  = "${var.app_name}-ssl-cert"

  managed {
    domains = [var.domain != null ? var.domain : "placeholder.example.com"]
  }
}

# Target HTTPS proxy.
resource "google_compute_target_https_proxy" "https" {
  count            = var.enable_iap ? 1 : 0
  name             = "${var.app_name}-https-proxy"
  url_map          = google_compute_url_map.lb[0].id
  ssl_certificates = [google_compute_managed_ssl_certificate.ssl[0].id]
}

# Global static IP for the frontend.
resource "google_compute_global_address" "frontend" {
  count        = var.enable_iap ? 1 : 0
  name         = "${var.app_name}-lb-ip"
  ip_version   = "IPV4"
  address_type = "EXTERNAL"
}

# Global forwarding rule (frontend).
resource "google_compute_forwarding_rule" "https" {
  count                 = var.enable_iap ? 1 : 0
  name                  = "${var.app_name}-fr"
  target                = google_compute_target_https_proxy.https[0].id
  port_range            = "443"
  ip_address            = google_compute_global_address.frontend[0].id
  load_balancing_scheme = var.iap_lb_scheme
}

# --- IAP IAM: who can pass through IAP ---------------------------------------
resource "google_iap_web_backend_service_iam_binding" "allowed_users" {
  count               = var.enable_iap ? 1 : 0
  project             = var.project_id
  web_backend_service = google_compute_backend_service.iap_backend[0].name
  role                = "roles/iap.httpsResourceAccessor"
  members             = local.iap_members
}

# --- Cloud Run IAM: trust the Compute Engine default SA ---------------------
# The serverless NEG's backend service authenticates to Cloud Run using the
# project's Compute Engine default service account. Granting it run.invoker
# lets the LB (fronted by IAP) reach the Cloud Run service without requiring
# allUsers access (which the org policy blocks).
resource "google_cloud_run_v2_service_iam_member" "iap_invoker" {
  count    = var.enable_iap ? 1 : 0
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${data.google_project.number.number}-compute@developer.gserviceaccount.com"

  depends_on = [google_project_service.iap_apis]
}
