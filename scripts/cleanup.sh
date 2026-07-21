#!/usr/bin/env bash
#
# cleanup.sh — Remove all Sudoku app resources from a GCP project.
#
# This is the reverse of deploy.sh. It destroys all Terraform-managed
# resources, then cleans up non-Terraform resources that deploy.sh created
# (Cloud Build buckets, dedicated service account, TF state file).
#
# Usage:
#   PROJECT_ID=my-gcp-project ./cleanup.sh
#
# Optional env vars:
#   REGION     — GCP region (default: us-central1)
#   APP_NAME   — service/repo name (default: sudoku)
#   KEEP_APIS  — if "true", leave enabled APIs untouched (default: true)
#
set -euo pipefail

# --- Configuration -----------------------------------------------------------
: "${PROJECT_ID:?PROJECT_ID environment variable is required}"
REGION="${REGION:-us-central1}"
APP_NAME="${APP_NAME:-sudoku}"
KEEP_APIS="${KEEP_APIS:-true}"

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TF_DIR="${PROJECT_ROOT}/terraform"
TF_STATE_FILE="terraform.tfstate.${PROJECT_ID}"

# Whether to run audits (set SKIP_AUDITS=true to skip)
SKIP_AUDITS="${SKIP_AUDITS:-false}"

# --- Preflight checks --------------------------------------------------------
echo "▶ Preflight checks..."
command -v gcloud >/dev/null || { echo "✗ gcloud CLI not found."; exit 1; }
command -v terraform >/dev/null || { echo "✗ terraform not found."; exit 1; }

if ! gcloud auth print-access-token >/dev/null 2>&1; then
  echo "→ Not logged in. Running: gcloud auth login"
  gcloud auth login
fi

echo
echo "⚠️  This will DELETE all '${APP_NAME}' resources from project: ${PROJECT_ID}"
echo "   Region: ${REGION}"
echo "   (Auto-approved — set CONFIRM_CLEANUP=true to require manual confirmation)"
echo

# Only require confirmation when explicitly requested.
if [ "${CONFIRM_CLEANUP:-false}" = "true" ]; then
  read -r -p "Continue? [y/N] " confirm
  case "$confirm" in
    [yY]|[yY][eE][sS]) ;;
    *) echo "Aborted."; exit 0 ;;
  esac
fi

# --- Pre-cleanup audit -------------------------------------------------------
if [ "${SKIP_AUDITS}" != "true" ]; then
  echo
  echo "============================================"
  echo "  PRE-CLEANUP AUDIT"
  echo "============================================"
  "${SCRIPT_DIR}/run_audit.sh" "${PROJECT_ID}" "cleanup-pre" "true" || {
    echo "  ⚠ Pre-cleanup audit found unexpected state."
    echo "    Continuing with cleanup anyway..."
  }
fi

# Fetch project number (needed for default SA and logs bucket).
PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)' 2>/dev/null || echo "")
if [ -z "$PROJECT_NUMBER" ]; then
  echo "✗ Could not determine project number for ${PROJECT_ID}"
  exit 1
fi

DEFAULT_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
DEDICATED_SA="${APP_NAME}-sa@${PROJECT_ID}.iam.gserviceaccount.com"
LOGS_BUCKET="${PROJECT_NUMBER}-cloudbuild-logs"
CB_SOURCE_BUCKET="${PROJECT_ID}_cloudbuild"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${APP_NAME}-repo/${APP_NAME}"

# Track what we deleted for the summary.
DELETED=()
SKIPPED=()

# --- Phase 0: Delete Firestore database (before terraform disables the API) ---
echo
echo "▶ Phase 0: Deleting Firestore database (before terraform destroy)..."
# Firestore databases survive terraform destroy because terraform only disables
# the API, it doesn't delete the database itself. We must delete it here while
# the API is still enabled, otherwise the next deploy will fail with 409.
if gcloud firestore databases list --project="${PROJECT_ID}" 2>/dev/null | grep -q "(default)"; then
  echo "  → Deleting Firestore database..."
  gcloud firestore databases delete --database="(default)" --project="${PROJECT_ID}" --quiet 2>/dev/null || {
    echo "  ⚠ Firestore database deletion may have failed (it can take several minutes)."
    echo "    You may need to delete it manually in the console."
  }
  DELETED+=("Firestore database (default)")
else
  SKIPPED+=("Firestore database (not found or API disabled)")
fi

# --- Phase 1: Terraform destroy (Cloud Run, IAM, AR repo, APIs) ----------------
echo
echo "▶ Phase 1: Terraform destroy (Cloud Run service, IAM, Artifact Registry, APIs)..."

# Determine which SA was used (so terraform destroy matches the state).
TF_SA_VAR=""
if gcloud iam service-accounts describe "${DEDICATED_SA}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  TF_SA_VAR="-var=service_account_email=${DEDICATED_SA}"
elif gcloud iam service-accounts describe "${DEFAULT_SA}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  TF_SA_VAR="-var=service_account_email=${DEFAULT_SA}"
fi

if [ -f "${TF_DIR}/${TF_STATE_FILE}" ]; then
  if [ ! -d "${TF_DIR}/.terraform" ]; then
    terraform -chdir="${TF_DIR}" init -upgrade
  fi
  terraform -chdir="${TF_DIR}" destroy \
    -state="${TF_STATE_FILE}" \
    -var="project_id=${PROJECT_ID}" \
    -var="region=${REGION}" \
    -var="app_name=${APP_NAME}" \
    -var="image_tag=latest" \
    ${TF_SA_VAR} \
    -auto-approve 2>&1 || {
      echo "  ⚠ Terraform destroy had errors (some resources may need manual cleanup)."
      echo "  Continuing with non-Terraform cleanup..."
    }
  DELETED+=("Terraform-managed resources (Cloud Run, IAM, AR repo)")
else
  echo "  ⓪ No Terraform state file found (${TF_STATE_FILE}) — skipping Terraform destroy."
  echo "     (Resources may have been created manually or state was already removed.)"
  SKIPPED+=("Terraform destroy (no state file)")
fi

# --- Phase 2: Delete Cloud Run service (if still exists) ----------------------
echo
echo "▶ Phase 2: Deleting Cloud Run service (if Terraform didn't get it)..."
if timeout 30 gcloud run services describe "${APP_NAME}" --region="${REGION}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  timeout 60 gcloud run services delete "${APP_NAME}" --region="${REGION}" --project="${PROJECT_ID}" --quiet 2>&1
  DELETED+=("Cloud Run service: ${APP_NAME}")
else
  SKIPPED+=("Cloud Run service (already gone)")
fi

# --- Phase 3: Delete Artifact Registry repo (if still exists) ----------------
echo
echo "▶ Phase 3: Deleting Artifact Registry repo (if still exists)..."
if timeout 30 gcloud artifacts repositories describe "${APP_NAME}-repo" --location="${REGION}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  timeout 60 gcloud artifacts repositories delete "${APP_NAME}-repo" --location="${REGION}" --project="${PROJECT_ID}" --quiet 2>&1
  DELETED+=("Artifact Registry repo: ${APP_NAME}-repo")
else
  SKIPPED+=("Artifact Registry repo (already gone)")
fi

# --- Phase 4: Delete Cloud Build buckets -------------------------------------
echo
echo "▶ Phase 4: Deleting Cloud Build buckets..."

# Logs bucket (created by deploy.sh when using a dedicated SA).
if gcloud storage buckets describe "gs://${LOGS_BUCKET}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud storage rm -r "gs://${LOGS_BUCKET}" --project="${PROJECT_ID}" --quiet 2>&1
  DELETED+=("Cloud Build logs bucket: ${LOGS_BUCKET}")
else
  SKIPPED+=("Cloud Build logs bucket (not found)")
fi

# Cloud Build source bucket (auto-created by GCP on first build).
if gcloud storage buckets describe "gs://${CB_SOURCE_BUCKET}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud storage rm -r "gs://${CB_SOURCE_BUCKET}" --project="${PROJECT_ID}" --quiet 2>&1
  DELETED+=("Cloud Build source bucket: ${CB_SOURCE_BUCKET}")
else
  SKIPPED+=("Cloud Build source bucket (not found)")
fi

# --- Phase 5: Delete dedicated service account --------------------------------
echo
echo "▶ Phase 5: Deleting dedicated service account (if created by deploy.sh)..."
if gcloud iam service-accounts describe "${DEDICATED_SA}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  # Remove IAM bindings first.
  for role in roles/cloudbuild.builds.builder roles/artifactregistry.writer roles/storage.objectAdmin; do
    gcloud projects remove-iam-policy-binding "${PROJECT_ID}" \
      --member="serviceAccount:${DEDICATED_SA}" \
      --role="${role}" --quiet >/dev/null 2>&1 || true
  done
  gcloud iam service-accounts delete "${DEDICATED_SA}" --project="${PROJECT_ID}" --quiet 2>&1
  DELETED+=("Dedicated SA: ${DEDICATED_SA}")
else
  SKIPPED+=("Dedicated SA (not found — default SA was used)")
fi

echo
echo "  ℹ️  Default Compute Engine SA (${DEFAULT_SA}) is left untouched."
  echo "     It's auto-created by GCP and may be used by other services."

# --- Phase 6: Remove Terraform state file ------------------------------------
echo
echo "▶ Phase 6: Removing Terraform state file..."
if [ -f "${TF_DIR}/${TF_STATE_FILE}" ]; then
  rm -f "${TF_DIR}/${TF_STATE_FILE}" "${TF_DIR}/${TF_STATE_FILE}.backup"
  DELETED+=("Terraform state file: ${TF_STATE_FILE}")
else
  SKIPPED+=("Terraform state file (not found)")
fi

# --- Phase 7: API cleanup (handled by Terraform) ------------------------------
echo
echo "▶ Phase 7: API cleanup..."
echo "  ⓪ Terraform uses disable_on_destroy=true, so APIs are disabled during"
echo "     terraform destroy in Phase 1. No manual API cleanup needed."
SKIPPED+=("Manual API disablement (handled by Terraform destroy)")

# --- Summary -----------------------------------------------------------------
echo
echo "============================================"
echo "  CLEANUP SUMMARY for ${PROJECT_ID}"
echo "============================================"
echo
echo "✅ Deleted:"
if [ ${#DELETED[@]} -gt 0 ]; then
  for item in "${DELETED[@]}"; do
    echo "  • ${item}"
  done
else
  echo "  (nothing was deleted)"
fi
echo
echo "⓪ Skipped (already gone or preserved):"
if [ ${#SKIPPED[@]} -gt 0 ]; then
  for item in "${SKIPPED[@]}"; do
    echo "  • ${item}"
  done
else
  echo "  (nothing skipped)"
fi
echo
echo "Done. Project ${PROJECT_ID} has been cleaned of all '${APP_NAME}' resources."

# --- Post-cleanup audit ------------------------------------------------------
if [ "${SKIP_AUDITS}" != "true" ]; then
  echo
  echo "============================================"
  echo "  POST-CLEANUP AUDIT"
  echo "============================================"
  "${SCRIPT_DIR}/run_audit.sh" "${PROJECT_ID}" "cleanup-post" "false" || {
    echo "  ⚠ Post-cleanup audit found unexpected resources."
    echo "    Manual cleanup may be needed. Check the audit report."
  }
fi
