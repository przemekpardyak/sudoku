/**
 * Provider configuration and project bootstrap.
 * Requires Application Default Credentials (`gcloud auth application-default login`).
 */

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Core APIs required for the app (always enabled).
resource "google_project_service" "enabled_apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "compute.googleapis.com",
    "iamcredentials.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = true
  disable_dependent_services = true
}

# IAP-related APIs (only enabled when IAP is requested).
# These are separated so that projects not using IAP don't get unnecessary APIs resources.
resource "google_project_service" "iap_apis" {
  for_each = var.enable_iap ? toset([
    "iap.googleapis.com",
    "certificatemanager.googleapis.com",
    "networkservices.googleapis.com",
    "networksecurity.googleapis.com",
    "servicecontrol.googleapis.com",
    "servicemanagement.googleapis.com",
  ]) : toset([])

  service            = each.value
  disable_on_destroy = true
  disable_dependent_services = true
}
