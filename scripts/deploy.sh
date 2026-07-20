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
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TF_DIR="${PROJECT_ROOT}/terraform"

IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${APP_NAME}-repo/${APP_NAME}:${IMAGE_TAG}"

# Per-project state file so parallel deploys to different projects don't clobber
# each other's Terraform state.
TF_STATE_FILE="terraform.tfstate.${PROJECT_ID}"

# Whether to run audits (set SKIP_AUDITS=true to skip)
SKIP_AUDITS="${SKIP_AUDITS:-false}"

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

# NOTE: We intentionally do NOT call `gcloud config set project` here because it
# mutates the global gcloud config and would break parallel deploys to different
# projects. All gcloud commands below use explicit --project and --region flags.

# --- Pre-deploy audit --------------------------------------------------------
if [ "${SKIP_AUDITS}" != "true" ]; then
  echo
  echo "============================================"
  echo "  PRE-DEPLOY AUDIT"
  echo "============================================"
  "${SCRIPT_DIR}/run_audit.sh" "${PROJECT_ID}" "setup-pre" "false" || {
    echo "  ⚠ Pre-deploy audit found unexpected resources."
    echo "    Run cleanup.sh first or set SKIP_AUDITS=true to skip."
    exit 1
  }
fi

# --- Service account setup ---------------------------------------------------
# Cloud Build and Cloud Run both need a service account. The default Compute
# Engine SA ({project_number}-compute@developer.gserviceaccount.com) is normally
# used, but it may not exist if it was deleted (e.g. during a project cleanup).
# This function ensures a usable SA exists, creating one if necessary.
#
# If the default SA is missing or inaccessible, we create a dedicated SA named
# "{app_name}-sa" and grant it the roles needed for Cloud Build + Cloud Run.

SA_EMAIL="${APP_NAME}-sa@${PROJECT_ID}.iam.gserviceaccount.com}"
TF_SA_VAR=""
CB_SA_FLAG=""

echo
echo "▶ Checking service account availability..."

# Fetch the project number (needed for default SA email and logs bucket name).
PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)' 2>/dev/null || echo "")
if [ -z "$PROJECT_NUMBER" ]; then
  echo "✗ Could not determine project number for ${PROJECT_ID}"
  exit 1
fi

DEFAULT_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
LOGS_BUCKET="${PROJECT_NUMBER}-cloudbuild-logs"

# Check if the default Compute Engine SA exists and is accessible.
if gcloud iam service-accounts describe "${DEFAULT_SA}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  echo "  ✓ Default Compute Engine SA exists: ${DEFAULT_SA}"
  # Ensure the user can actAs the default SA (needed by Cloud Run).
  gcloud iam service-accounts add-iam-policy-binding "${DEFAULT_SA}" \
    --member="user:$(gcloud auth list --filter=status:ACTIVE --format='value(account)')" \
    --role="roles/iam.serviceAccountUser" \
    --project="${PROJECT_ID}" --quiet >/dev/null 2>&1 || true
  RUN_SA_EMAIL="${DEFAULT_SA}"
else
  echo "  ⚠ Default Compute Engine SA not found (may have been deleted)."
  echo "  → Creating dedicated service account: ${SA_EMAIL}"

  # Create the SA if it doesn't exist yet.
  if ! gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
    gcloud iam service-accounts create "${APP_NAME}-sa" \
      --display-name="Service account for ${APP_NAME} (Cloud Build + Cloud Run)" \
      --project="${PROJECT_ID}" --quiet
  fi

  # Grant roles needed for Cloud Build (build images, push to AR, write logs).
  for role in roles/cloudbuild.builds.builder roles/artifactregistry.writer roles/storage.objectAdmin; do
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
      --member="serviceAccount:${SA_EMAIL}" \
      --role="${role}" --quiet >/dev/null 2>&1 || true
  done

  # Grant the user permission to actAs this SA (needed by both Cloud Build and Cloud Run).
  gcloud iam service-accounts add-iam-policy-binding "${SA_EMAIL}" \
    --member="user:$(gcloud auth list --filter=status:ACTIVE --format='value(account)')" \
    --role="roles/iam.serviceAccountUser" \
    --project="${PROJECT_ID}" --quiet >/dev/null 2>&1 || true

  # Create a Cloud Build logs bucket (required when using a custom SA).
  if ! gcloud storage buckets describe "gs://${LOGS_BUCKET}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
    echo "  → Creating Cloud Build logs bucket: gs://${LOGS_BUCKET}"
    gcloud storage buckets create "gs://${LOGS_BUCKET}" \
      --project="${PROJECT_ID}" --location="${REGION}" --quiet >/dev/null 2>&1 || true
  fi
  # Grant the SA access to the logs bucket.
  gcloud storage buckets add-iam-policy-binding "gs://${LOGS_BUCKET}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/storage.objectAdmin" \
    --project="${PROJECT_ID}" --quiet >/dev/null 2>&1 || true

  # When using a custom SA, Cloud Build requires --service-account and --gcs-log-dir.
  CB_SA_FLAG="--service-account=projects/${PROJECT_ID}/serviceAccounts/${SA_EMAIL} --gcs-log-dir=gs://${LOGS_BUCKET}"

  # Tell Terraform to use this SA for the Cloud Run service.
  TF_SA_VAR="-var=service_account_email=${SA_EMAIL}"

  RUN_SA_EMAIL="${SA_EMAIL}"
  echo "  ✓ Dedicated SA ready: ${SA_EMAIL}"
fi

# --- Phase 1: Bootstrap infrastructure (Artifact Registry repo + APIs) ---------
# We create the supporting infra first WITHOUT the Cloud Run service, because
# Cloud Run v2 validates that the referenced container image exists at create
# time. The image won't exist until Phase 2 builds and pushes it.
echo
echo "▶ Phase 1: Bootstrapping infrastructure (Artifact Registry + APIs)..."
# Only run init if .terraform/ is missing (avoids races in parallel deploys).
if [ ! -d "${TF_DIR}/.terraform" ]; then
  terraform -chdir="${TF_DIR}" init -upgrade
fi

# Retry loop: if deploying immediately after cleanup, APIs may still be
# deactivating. GCP requires deactivation to complete before re-enabling.
# compute.googleapis.com in particular can take up to 5+ minutes.
MAX_RETRIES=5
RETRY_DELAY=90
for attempt in $(seq 1 ${MAX_RETRIES}); do
  terraform -chdir="${TF_DIR}" apply \
    -state="${TF_STATE_FILE}" \
    -var="project_id=${PROJECT_ID}" \
    -var="region=${REGION}" \
    -var="app_name=${APP_NAME}" \
    -var="image_tag=${IMAGE_TAG}" \
    -target=google_project_service.enabled_apis \
    -target=google_artifact_registry_repository.app_repo \
    ${TF_ARGS}
  TF_EXIT=$?
  if [ ${TF_EXIT} -eq 0 ]; then
    break
  fi
  if [ ${attempt} -lt ${MAX_RETRIES} ]; then
    echo "  ⚠ Terraform apply failed (attempt ${attempt}/${MAX_RETRIES})."
    echo "    This often happens when APIs are still deactivating from a"
    echo "    previous cleanup. Waiting ${RETRY_DELAY}s before retry..."
    sleep ${RETRY_DELAY}
  else
    echo "  ✗ Terraform apply failed after ${MAX_RETRIES} attempts."
    exit 1
  fi
done

# Wait for APIs to propagate before Cloud Build tries to use them.
# GCP APIs can take 10-30s to become fully available after enablement.
echo "  Waiting 30s for API propagation..."
sleep 30

# --- Phase 2: Build & push the container image via Cloud Build ----------------
# We use Google Cloud Build instead of the local Docker daemon so the script
# works without the user being in the docker group. Cloud Build builds the
# image remotely and pushes it directly to Artifact Registry in one step.
echo
echo "▶ Phase 2: Building & pushing image via Cloud Build: ${IMAGE}"
# Retry loop: Cloud Build API may not be fully propagated yet.
MAX_RETRIES=3
RETRY_DELAY=30
for attempt in $(seq 1 ${MAX_RETRIES}); do
  # shellcheck disable=SC2086
  timeout 300 gcloud builds submit "${PROJECT_ROOT}" \
    --tag="${IMAGE}" \
    --project="${PROJECT_ID}" \
    ${CB_SA_FLAG} \
    --quiet
  CB_EXIT=$?
  if [ ${CB_EXIT} -eq 0 ]; then
    break
  fi
  if [ ${attempt} -lt ${MAX_RETRIES} ]; then
    echo "  ⚠ Cloud Build failed (attempt ${attempt}/${MAX_RETRIES})."
    echo "    Waiting ${RETRY_DELAY}s before retry..."
    sleep ${RETRY_DELAY}
  else
    echo "  ✗ Cloud Build failed after ${MAX_RETRIES} attempts."
    exit 1
  fi
done

# --- Phase 3: Create Cloud Run service (image now exists) and deploy revision --
echo
echo "▶ Phase 3: Applying remaining Terraform (Cloud Run service + IAM)..."
terraform -chdir="${TF_DIR}" apply \
  -state="${TF_STATE_FILE}" \
  -var="project_id=${PROJECT_ID}" \
  -var="region=${REGION}" \
  -var="app_name=${APP_NAME}" \
  -var="image_tag=${IMAGE_TAG}" \
  ${TF_SA_VAR} \
  ${TF_ARGS}

# Deploy a fresh revision pointing at the just-pushed image.
echo
echo "▶ Deploying new revision to Cloud Run..."
gcloud run deploy "${APP_NAME}" \
  --image="${IMAGE}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --port=8080 \
  --no-allow-unauthenticated \
  --service-account="${RUN_SA_EMAIL}" \
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
echo "   Access:      gcloud run services proxy ${APP_NAME} --region=${REGION} --project=${PROJECT_ID} --port=8080"

# --- Post-deploy audit -------------------------------------------------------
if [ "${SKIP_AUDITS}" != "true" ]; then
  echo
  echo "============================================"
  echo "  POST-DEPLOY AUDIT"
  echo "============================================"
  "${SCRIPT_DIR}/run_audit.sh" "${PROJECT_ID}" "setup-post" "true" || {
    echo "  ⚠ Post-deploy audit found unexpected state."
    echo "    Check the audit report for details."
  }
fi
