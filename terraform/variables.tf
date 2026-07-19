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
  description = "If true, Cloud Run allows public unauthenticated invocations. Required for a public web app."
  type        = bool
  default     = true
}
