/**
 * Input variables for the Sudoku Cloud Run deployment.
 */

variable "project_id" {
  description = "Google Cloud project ID where the app will be deployed."
  type        = string
}

variable "region" {
  description = "Google Cloud region for Cloud Run and Artifact Registry."
  type        = string
  default     = "us-central1"
}

variable "app_name" {
  description = "Logical name used to prefix resources."
  type        = string
  default     = "sudoku"
}

variable "image_tag" {
  description = "Container image tag to deploy. Defaults to \"latest\" for convenience."
  type        = string
  default     = "latest"
}

variable "service_account_email" {
  description = "Optional existing service account email for the Cloud Run revision to run as. If null, the default Compute Engine SA is used."
  type        = string
  default     = null
}

variable "concurrency" {
  description = "Maximum concurrent requests per Cloud Run container instance."
  type        = number
  default     = 80
}

variable "max_instance_count" {
  description = "Maximum number of Cloud Run container instances."
  type        = number
  default     = 10
}

variable "min_instance_count" {
  description = "Minimum number of Cloud Run container instances (keeps warm instances). 0 scales to zero."
  type        = number
  default     = 0
}

variable "memory" {
  description = "Memory limit per Cloud Run container instance."
  type        = string
  default     = "512Mi"
}

variable "cpu" {
  description = "CPU limit per Cloud Run container instance."
  type        = string
  default     = "1"
}

variable "allow_unauthenticated" {
  description = "If true and invoker_members is empty, grants the run.invoker role to the currently authenticated gcloud user. Set invoker_members=[\"allUsers\"] for fully public access (requires org policy to allow it)."
  type        = bool
  default     = true
}

variable "invoker_members" {
  description = "IAM members to grant roles/run.invoker on the Cloud Run service. Defaults to the currently authenticated gcloud user when empty. Use [\"allUsers\"] for public access (if your org policy allows it)."
  type        = list(string)
  default     = []
}

variable "domain" {
  description = "Optional custom domain for the Load Balancer frontend (e.g. sudoku.example.com). If null, the LB IP must be accessed directly via the generated https://IP.nip.io-style address."
  type        = string
  default     = null
}

variable "iap_allowed_users" {
  description = "IAM members allowed through Identity-Aware Proxy. Defaults to the currently authenticated gcloud user when empty."
  type        = list(string)
  default     = []
}

variable "enable_iap" {
  description = "If true, creates a global HTTPS Load Balancer with Identity-Aware Proxy in front of Cloud Run. Requires the org policy to allow EXTERNAL_HTTP_HTTPS or EXTERNAL_MANAGED_HTTP_HTTPS load balancers. Defaults to false — use `gcloud run services proxy` for local browser access."
  type        = bool
  default     = false
}

variable "iap_lb_scheme" {
  description = "Load balancing scheme for the IAP frontend. Use \"EXTERNAL\" for the classic external Application LB or \"EXTERNAL_MANAGED\" for the newer Application LB. Must be allowed by your org policy."
  type        = string
  default     = "EXTERNAL"
}

variable "firestore_location" {
  description = "Location for the Firestore database. Use a multi-region (e.g. nam5) for best availability or a regional location close to your Cloud Run region."
  type        = string
  default     = "nam5"
}

variable "firestore_enable_pitr" {
  description = "Enable point-in-time recovery for Firestore (continuous backups). Adds cost but allows restoring to any point in the last hour."
  type        = bool
  default     = false
}
