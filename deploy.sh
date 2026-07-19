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
command -v docker >/dev/null || { echo "✗ docker not found."; exit 1; }

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

# --- Terraform apply (creates Artifact Registry + Cloud Run service) ---------
echo
echo "▶ Applying Terraform configuration..."
terraform -chdir="${TF_DIR}" init -upgrade
terraform -chdir="${TF_DIR}" apply \
  -var="project_id=${PROJECT_ID}" \
  -var="region=${REGION}" \
  -var="app_name=${APP_NAME}" \
  -var="image_tag=${IMAGE_TAG}" \
  ${TF_ARGS}

# Configure Docker auth for Artifact Registry.
echo
echo "▶ Configuring Docker auth for Artifact Registry..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

# --- Build & push container image -------------------------------------------
echo
echo "▶ Building container image: ${IMAGE}"
docker build -t "${IMAGE}" "${SCRIPT_DIR}"

echo
echo "▶ Pushing image to Artifact Registry..."
docker push "${IMAGE}"

# --- Deploy: point Cloud Run at the freshly pushed image ---------------------
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
