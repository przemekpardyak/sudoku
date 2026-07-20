#!/usr/bin/env bash
#
# deploy.sh — Build, push, and deploy the Sudoku Flask app to Google Cloud Run.
#
# Usage:
#   PROJECT_ID=my-gcp-project ./deploy.sh
#
# Optional env vars (override defaults):
#   REGION     — GCP region (default: us-central1)
#   APP_NAME   — service/repo name (default: sudoku)
#   IMAGE_TAG  — image tag (default: latest)
#   TF_ARGS    — extra args passed to `terraform apply` (e.g. "-auto-approve")
#
set -euo pipefail

# --- Configuration -----------------------------------------------------------
: "${PROJECT_ID:?PROJECT_ID environment variable is required}"
REGION="${REGION:-us-central1}"
APP_NAME="${APP_NAME:-sudoku}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
TF_ARGS="${TF_ARGS:-}"

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_DIR="${SCRIPT_DIR}/terraform"

IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${APP_NAME}-repo/${APP_NAME}:${IMAGE_TAG}"

# --- Preflight checks --------------------------------------------------------
echo "▶ Preflight checks..."
command -v gcloud >/dev/null || { echo "✗ gcloud CLI not found. Install: https://cloud.google.com/sdk/docs/install"; exit 1; }
command -v terraform >/dev/null || { echo "✗ terraform not found. Install: https://developer.hashicorp.com/terraform/downloads"; exit 1; }

# Ensure authenticated.
if ! gcloud auth print-access-token >/dev/null 2>&1; then
  echo "→ Not logged in. Running: gcloud auth login"
  gcloud auth login
fi
if ! gcloud auth application-default print-access-token >/dev/null 2>&1; then
  echo "→ Application default credentials missing. Running: gcloud auth application-default login"
  gcloud auth application-default login
fi

gcloud config set project "${PROJECT_ID}"
gcloud config set compute/region "${REGION}"

# --- Phase 1: Bootstrap infrastructure (Artifact Registry repo + APIs) ---------
# We create the supporting infra first WITHOUT the Cloud Run service, because
# Cloud Run v2 validates that the referenced container image exists at create
# time. The image won't exist until Phase 2 builds and pushes it.
echo
echo "▶ Phase 1: Bootstrapping infrastructure (Artifact Registry + APIs)..."
terraform -chdir="${TF_DIR}" init -upgrade
terraform -chdir="${TF_DIR}" apply \
  -var="project_id=${PROJECT_ID}" \
  -var="region=${REGION}" \
  -var="app_name=${APP_NAME}" \
  -var="image_tag=${IMAGE_TAG}" \
  -target=google_project_service.enabled_apis \
  -target=google_artifact_registry_repository.app_repo \
  ${TF_ARGS}

# --- Phase 2: Build & push the container image via Cloud Build ----------------
# We use Google Cloud Build instead of the local Docker daemon so the script
# works without the user being in the docker group. Cloud Build builds the
# image remotely and pushes it directly to Artifact Registry in one step.
echo
echo "▶ Phase 2: Building & pushing image via Cloud Build: ${IMAGE}"
gcloud builds submit "${SCRIPT_DIR}" \
  --tag="${IMAGE}" \
  --project="${PROJECT_ID}" \
  --quiet

# --- Phase 3: Create Cloud Run service (image now exists) and deploy revision --
echo
echo "▶ Phase 3: Applying remaining Terraform (Cloud Run service + IAM)..."
terraform -chdir="${TF_DIR}" apply \
  -var="project_id=${PROJECT_ID}" \
  -var="region=${REGION}" \
  -var="app_name=${APP_NAME}" \
  -var="image_tag=${IMAGE_TAG}" \
  ${TF_ARGS}

# Deploy a fresh revision pointing at the just-pushed image.
echo
echo "▶ Deploying new revision to Cloud Run..."
gcloud run deploy "${APP_NAME}" \
  --image="${IMAGE}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --port=8080 \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --concurrency=80 \
  --min-instances=0 \
  --max-instances=10

# --- Done --------------------------------------------------------------------
SERVICE_URL=$(gcloud run services describe "${APP_NAME}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --format='value(status.url)')

echo
echo "✅ Deployed successfully."
echo "   Service URL: ${SERVICE_URL}"
echo "   Image:       ${IMAGE}"
