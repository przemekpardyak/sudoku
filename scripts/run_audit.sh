#!/usr/bin/env bash
#
# run_audit.sh — Run an audit and validate expected state.
#
# Usage:
#   ./run_audit.sh PROJECT_ID SOURCE [EXPECT_DEPLOYED]
#
# Arguments:
#   PROJECT_ID      — GCP project to audit
#   SOURCE          — who triggered the audit (e.g. "setup-pre", "setup-post", "cleanup-pre", "cleanup-post")
#   EXPECT_DEPLOYED — "true" if the app should be deployed, "false" if it should be clean
#
# Output:
#   Creates a timestamped markdown file in audits/ and prints the path.
#   Exits 0 if the audit matches expectations, 1 otherwise.
#
set -euo pipefail

PROJECT_ID="${1:?Usage: $0 PROJECT_ID SOURCE [EXPECT_DEPLOYED]}"
SOURCE="${2:?Usage: $0 PROJECT_ID SOURCE [EXPECT_DEPLOYED]}"
EXPECT_DEPLOYED="${3:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
AUDIT_DIR="${PROJECT_ROOT}/audits"
mkdir -p "${AUDIT_DIR}"

TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")
AUDIT_FILE="${AUDIT_DIR}/audit_${PROJECT_ID}_${SOURCE}_${TIMESTAMP}.md"

echo "▶ Running audit: ${SOURCE} for ${PROJECT_ID}..."
"${SCRIPT_DIR}/audit_gcp_project.sh" "${PROJECT_ID}" "${AUDIT_FILE}" 2>&1

echo "  📄 Audit report: ${AUDIT_FILE}"

# --- Validate expected state -------------------------------------------------
if [ -n "${EXPECT_DEPLOYED}" ]; then
  echo
  echo "▶ Validating expected state (expect_deployed=${EXPECT_DEPLOYED})..."

  # Parse key counts from the audit file.
  # The audit script outputs a markdown table like:
  #   | Cloud Run services | 1 |
  #   | Artifact Registry repos | 1 |
  #   | Storage buckets | 1 |
  CLOUD_RUN=$(grep -oP '\| Cloud Run services \| \K\d+' "${AUDIT_FILE}" || echo "0")
  AR_REPOS=$(grep -oP '\| Artifact Registry repos \| \K\d+' "${AUDIT_FILE}" || echo "0")
  STORAGE_BUCKETS=$(grep -oP '\| Storage buckets \| \K\d+' "${AUDIT_FILE}" || echo "0")

  PASS=true
  if [ "${EXPECT_DEPLOYED}" = "true" ]; then
    # Expect: 1 Cloud Run, 1 AR repo, at least 1 bucket (Cloud Build source)
    [ "${CLOUD_RUN}" -ge 1 ] || { echo "  ✗ Expected Cloud Run >= 1, got ${CLOUD_RUN}"; PASS=false; }
    [ "${AR_REPOS}" -ge 1 ] || { echo "  ✗ Expected AR repos >= 1, got ${AR_REPOS}"; PASS=false; }
    [ "${STORAGE_BUCKETS}" -ge 1 ] || { echo "  ✗ Expected buckets >= 1, got ${STORAGE_BUCKETS}"; PASS=false; }
  else
    # Expect: 0 Cloud Run, 0 AR repos, 0 buckets
    [ "${CLOUD_RUN}" -eq 0 ] || { echo "  ✗ Expected Cloud Run = 0, got ${CLOUD_RUN}"; PASS=false; }
    [ "${AR_REPOS}" -eq 0 ] || { echo "  ✗ Expected AR repos = 0, got ${AR_REPOS}"; PASS=false; }
    [ "${STORAGE_BUCKETS}" -eq 0 ] || { echo "  ✗ Expected buckets = 0, got ${STORAGE_BUCKETS}"; PASS=false; }
  fi

  echo
  if [ "${PASS}" = "true" ]; then
    echo "  ✅ State validation PASSED"
  else
    echo "  ❌ State validation FAILED"
    exit 1
  fi
fi

exit 0
