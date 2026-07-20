#!/usr/bin/env bash
#
# audit_gcp_project.sh — Comprehensive GCP project resource audit
#
# Audits all resources in a GCP project, classifies them by detected
# application/purpose, and generates a markdown report with deletion
# safety assessments.
#
# Usage:
#   ./audit_gcp_project.sh PROJECT_ID [OUTPUT_FILE]
#
# Examples:
#   ./audit_gcp_project.sh my-project
#   ./audit_gcp_project.sh my-project ./audits/my-project-2026-01-01.md
#
# Requirements:
#   - gcloud CLI (authenticated)
#   - jq (for JSON processing)
#
set -o pipefail

# ─── Arguments ────────────────────────────────────────────────────────────────

PROJECT_ID="${1:?Usage: $0 PROJECT_ID [OUTPUT_FILE]}"
OUTPUT_FILE="${2:-gcp_audit_${PROJECT_ID}_$(date +%Y%m%d_%H%M%S).md}"
AUDIT_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
AUDITOR=$(gcloud config get-value account 2>/dev/null || echo "unknown")

# Disable all interactive prompts — critical for non-interactive script
export CLOUDSDK_CORE_DISABLE_PROMPTS=1
export CLOUDSDK_API_DISABLED_PROMPTS=never

# Temp files for raw data
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

# ─── Helpers ─────────────────────────────────────────────────────────────────

# Run a gcloud command, return JSON, swallow errors (for APIs not enabled)
# Uses --quiet to suppress prompts
gj() {
  gcloud "$@" --project="$PROJECT_ID" --format=json --quiet 2>/dev/null || echo '[]'
}

# Same as gj but for commands that may output status lines before JSON
gj_clean() {
  gcloud "$@" --project="$PROJECT_ID" --format=json --quiet 2>/dev/null \
    | jq '.' 2>/dev/null || echo '[]'
}

# Count items in a JSON array (always returns a single integer)
jcount() {
  local count
  count=$(echo "$1" | jq 'length' 2>/dev/null)
  if [ -z "$count" ] || ! [[ "$count" =~ ^[0-9]+$ ]]; then
    echo 0
  else
    echo "$count"
  fi
}

# Extract short name from a full resource path
# e.g. "projects/x/locations/y/repositories/sudoku-repo" → "sudoku-repo"
short_name() {
  basename "$1" 2>/dev/null || echo "$1"
}

# ─── Resource Collection ──────────────────────────────────────────────────────

echo "Auditing project: $PROJECT_ID" >&2

# Project metadata
PROJECT_INFO=$(gcloud projects describe "$PROJECT_ID" --format=json 2>/dev/null || echo '{}')
PROJECT_NUMBER=$(echo "$PROJECT_INFO" | jq -r '.projectNumber // "unknown"')
PROJECT_NAME=$(echo "$PROJECT_INFO" | jq -r '.name // "unknown"')
PROJECT_LIFECYCLE=$(echo "$PROJECT_INFO" | jq -r '.lifecycleState // "unknown"')
PROJECT_CREATED=$(echo "$PROJECT_INFO" | jq -r '.createTime // "unknown"')

echo "  Project number: $PROJECT_NUMBER" >&2

# Enabled APIs
ENABLED_APIS=$(gcloud services list --enabled --project="$PROJECT_ID" --quiet 2>/dev/null | sort)
API_COUNT=$(echo "$ENABLED_APIS" | grep -c '.' 2>/dev/null || echo 0)
if [ -z "$API_COUNT" ]; then API_COUNT=0; fi
echo "  Enabled APIs: $API_COUNT" >&2

# Cloud Run services
CLOUDRUN=$(gj run services list)
echo "  Cloud Run services: $(jcount "$CLOUDRUN")" >&2

# Artifact Registry repos — name field is a full path, handle separately
AR_REPOS=$(gj artifacts repositories list)
AR_COUNT=$(jcount "$AR_REPOS")
echo "  Artifact Registry repos: $AR_COUNT" >&2

# Compute resources
COMPUTE_BACKENDS=$(gj compute backend-services list)
COMPUTE_URLMAPS=$(gj compute url-maps list)
COMPUTE_HTTPS_PROXIES=$(gj compute target-https-proxies list)
COMPUTE_HTTP_PROXIES=$(gj compute target-http-proxies list)
COMPUTE_FWD_RULES=$(gj compute forwarding-rules list)
COMPUTE_ADDRESSES=$(gj compute addresses list)
COMPUTE_SSL_CERTS=$(gj compute ssl-certificates list)
COMPUTE_NEGS=$(gj compute network-endpoint-groups list)
COMPUTE_INSTANCES=$(gj compute instances list)
COMPUTE_DISKS=$(gj compute disks list)
COMPUTE_IMAGES=$(gj compute images list --no-standard-images 2>/dev/null || echo '[]')
COMPUTE_SNAPSHOTS=$(gj compute snapshots list)
COMPUTE_FIREWALLS=$(gj compute firewall-rules list)
COMPUTE_NETWORKS=$(gj compute networks list)
COMPUTE_ROUTERS=$(gj compute routers list)
echo "  Compute resources collected" >&2

# IAM
SERVICE_ACCOUNTS=$(gj iam service-accounts list)
IAM_POLICY=$(gcloud projects get-iam-policy "$PROJECT_ID" --format=json --quiet 2>/dev/null || echo '{}')
echo "  Service accounts: $(jcount "$SERVICE_ACCOUNTS")" >&2

# Storage
STORAGE_BUCKETS=$(gcloud storage buckets list --project="$PROJECT_ID" --format=json --quiet 2>/dev/null || echo '[]')
echo "  Storage buckets: $(jcount "$STORAGE_BUCKETS")" >&2

# IAP
IAP_BRANDS=$(gcloud iap oauth-brands list --project="$PROJECT_ID" --format=json --quiet 2>/dev/null || echo '[]')
echo "  IAP brands: $(jcount "$IAP_BRANDS")" >&2

# Cloud Build
CB_TRIGGERS=$(gj builds triggers list)
echo "  Cloud Build triggers: $(jcount "$CB_TRIGGERS")" >&2

# Cloud Functions (API may not be enabled)
CF_FUNCTIONS=$(gj functions list)
echo "  Cloud Functions: $(jcount "$CF_FUNCTIONS")" >&2

# GKE
GKE_CLUSTERS=$(gj container clusters list)
echo "  GKE clusters: $(jcount "$GKE_CLUSTERS")" >&2

# Firestore
FIRESTORE=$(gcloud firestore databases list --project="$PROJECT_ID" --format=json --quiet 2>/dev/null || echo '[]')

# BigQuery
BQ_DATASETS=$(bq --project_id="$PROJECT_ID" --format=json ls --quiet 2>/dev/null || echo '[]')
BQ_COUNT=$(echo "$BQ_DATASETS" | jq 'length' 2>/dev/null || echo 0)
if [ -z "$BQ_COUNT" ]; then BQ_COUNT=0; fi
echo "  BigQuery datasets: $BQ_COUNT" >&2

# Pub/Sub
PUBSUB_TOPICS=$(gj pubsub topics list)
echo "  Pub/Sub topics: $(jcount "$PUBSUB_TOPICS")" >&2

# Cloud SQL
SQL_INSTANCES=$(gj sql instances list)
echo "  Cloud SQL instances: $(jcount "$SQL_INSTANCES")" >&2

# Secret Manager
SECRETS=$(gj secrets list)
echo "  Secrets: $(jcount "$SECRETS")" >&2

# Cloud DNS
DNS_ZONES=$(gj dns managed-zones list)
echo "  DNS zones: $(jcount "$DNS_ZONES")" >&2

# ─── Classification Logic ────────────────────────────────────────────────────

# Detect app groups from resource name prefixes
detect_app_groups() {
  local all_names=""

  # Cloud Run — name field may be under metadata or top-level depending on API version
  all_names+=$(echo "$CLOUDRUN" | jq -r '.[].name // .[].metadata.name // empty' 2>/dev/null | while read -r p; do basename "$p"; done)
  all_names+=$'\n'
  # Artifact Registry — name is full path, extract last segment
  all_names+=$(echo "$AR_REPOS" | jq -r '.[].name // empty' 2>/dev/null | while read -r p; do basename "$p"; done)
  all_names+=$'\n'
  # Compute instances
  all_names+=$(echo "$COMPUTE_INSTANCES" | jq -r '.[].name // empty' 2>/dev/null)
  all_names+=$'\n'
  # Cloud SQL
  all_names+=$(echo "$SQL_INSTANCES" | jq -r '.[].name // empty' 2>/dev/null)
  all_names+=$'\n'
  # Secrets — name is a full path, extract last segment
  all_names+=$(echo "$SECRETS" | jq -r '.[].name // empty' 2>/dev/null | while read -r p; do basename "$p"; done)
  all_names+=$'\n'
  # Service accounts — extract the part before @ from email
  all_names+=$(echo "$SERVICE_ACCOUNTS" | jq -r '.[].email // empty' 2>/dev/null | sed 's/@.*//')
  all_names+=$'\n'
  # Compute addresses
  all_names+=$(echo "$COMPUTE_ADDRESSES" | jq -r '.[].name // empty' 2>/dev/null)
  all_names+=$'\n'
  # Storage buckets — bucket name
  all_names+=$(echo "$STORAGE_BUCKETS" | jq -r '.[].name // empty' 2>/dev/null)
  all_names+=$'\n'
  # Cloud Functions
  all_names+=$(echo "$CF_FUNCTIONS" | jq -r '.[].name // empty' 2>/dev/null)
  all_names+=$'\n'
  # GKE clusters
  all_names+=$(echo "$GKE_CLUSTERS" | jq -r '.[].name // empty' 2>/dev/null)

  # Extract prefixes (first word before -, _ or digit)
  # Only accept clean single-word prefixes (no @, /, dots, no digits)
  echo "$all_names" | tr '[:upper:]' '[:lower:]' | \
    sed -E 's/^([a-z]+)[-_0-9].*/\1/' | \
    grep -vE '^(service|default|compute|cloudbuild|container|gcp|goog|blueprint|artifact|run|iap|secret|sql|pubsub|storage|logging|monitoring|ppardyak|google|projects)$' | \
    grep -vE '[@/.]' | \
    grep -vE '^[0-9]' | \
    sort -u | grep -v '^$'
}

APP_GROUPS=$(detect_app_groups)

# Classify a resource name
# Returns: "auto-created", "app:<name>", or "other"
classify_name() {
  local name="$1"
  local lowername
  lowername=$(echo "$name" | tr '[:upper:]' '[:lower:]')

  # Auto-created patterns
  if echo "$lowername" | grep -qE '^[0-9]+-(compute|cloudbuild|blueprint)'; then
    echo "auto-created"
    return
  fi
  if echo "$lowername" | grep -qE '(blueprint-config|_cloudbuild$)'; then
    echo "auto-created"
    return
  fi
  if echo "$lowername" | grep -qE '^[0-9]+-compute@developer'; then
    echo "auto-created"
    return
  fi
  if echo "$lowername" | grep -qE '^service-[0-9]+@gcp-sa-'; then
    echo "auto-created (GCP service agent)"
    return
  fi

  # Check against detected app groups
  local prefix
  prefix=$(echo "$lowername" | sed -E 's/^([a-z]+)[-_0-9].*/\1/')
  for group in $APP_GROUPS; do
    if [ "$prefix" = "$group" ]; then
      echo "app:$group"
      return
    fi
  done

  echo "other"
}

# Assessment for deletion safety
# Args: resource_type, resource_name, extra_info
assess_deletion() {
  local rtype="$1"
  local rname="$2"
  local extra="$3"
  local classification
  classification=$(classify_name "$rname")

  case "$rtype" in
    compute_instance)
      if echo "$extra" | grep -qi "TERMINATED"; then
        echo "✅ Safe to delete (instance is TERMINATED)"
      elif echo "$extra" | grep -qi "RUNNING"; then
        echo "⚠️ Investigate — instance is RUNNING"
      else
        echo "⚠️ Investigate — instance status: $extra"
      fi
      ;;
    storage_bucket)
      if echo "$extra" | grep -q "size:0"; then
        echo "✅ Safe to delete (empty bucket)"
      elif [ "$classification" = "auto-created" ]; then
        echo "✅ Likely safe to delete (auto-created, $extra)"
      else
        echo "⚠️ Investigate — bucket has data ($extra)"
      fi
      ;;
    service_account)
      if [ "$classification" = "auto-created" ] || [ "$classification" = "auto-created (GCP service agent)" ]; then
        echo "✅ Auto-created default SA (will be recreated if needed)"
      else
        echo "⚠️ Investigate — custom service account for '$classification'"
      fi
      ;;
    cloud_sql)
      echo "⚠️ Investigate — database may contain data ($classification)"
      ;;
    secret)
      echo "⚠️ Investigate — secret may be in use ($classification)"
      ;;
    compute_address)
      if [ "$classification" = "auto-created" ]; then
        echo "✅ Likely safe to delete (auto-created)"
      else
        echo "⚠️ Investigate — address for '$classification'"
      fi
      ;;
    *)
      if [ "$classification" = "auto-created" ] || [ "$classification" = "auto-created (GCP service agent)" ]; then
        echo "✅ Auto-created (safe to ignore)"
      elif echo "$classification" | grep -q "^app:"; then
        echo "📦 Belongs to application: ${classification#app:}"
      else
        echo "ℹ️ No specific assessment (review manually)"
      fi
      ;;
  esac
}

# ─── Markdown Generation ─────────────────────────────────────────────────────

echo "Generating report: $OUTPUT_FILE" >&2

{
  echo "# GCP Project Audit: \`$PROJECT_ID\`"
  echo
  echo "| Field | Value |"
  echo "|-------|-------|"
  echo "| Project ID | \`$PROJECT_ID\` |"
  echo "| Project Name | $PROJECT_NAME |"
  echo "| Project Number | $PROJECT_NUMBER |"
  echo "| Lifecycle State | $PROJECT_LIFECYCLE |"
  echo "| Created | $PROJECT_CREATED |"
  echo "| Audit Date | $AUDIT_DATE |"
  echo "| Audited By | $AUDITOR |"
  echo

  # ─── Summary ───────────────────────────────────────────────────────────────
  echo "## Summary"
  echo
  echo "| Resource Type | Count |"
  echo "|---------------|-------|"
  echo "| Enabled APIs | $API_COUNT |"
  echo "| Cloud Run services | $(jcount "$CLOUDRUN") |"
  echo "| Artifact Registry repos | $AR_COUNT |"
  echo "| Compute instances | $(jcount "$COMPUTE_INSTANCES") |"
  echo "| Compute backend services | $(jcount "$COMPUTE_BACKENDS") |"
  echo "| Compute URL maps | $(jcount "$COMPUTE_URLMAPS") |"
  echo "| Compute forwarding rules | $(jcount "$COMPUTE_FWD_RULES") |"
  echo "| Compute addresses | $(jcount "$COMPUTE_ADDRESSES") |"
  echo "| Compute SSL certificates | $(jcount "$COMPUTE_SSL_CERTS") |"
  echo "| Compute NEGs | $(jcount "$COMPUTE_NEGS") |"
  echo "| Compute disks | $(jcount "$COMPUTE_DISKS") |"
  echo "| Compute images | $(jcount "$COMPUTE_IMAGES") |"
  echo "| Compute snapshots | $(jcount "$COMPUTE_SNAPSHOTS") |"
  echo "| Compute firewall rules | $(jcount "$COMPUTE_FIREWALLS") |"
  echo "| Compute networks | $(jcount "$COMPUTE_NETWORKS") |"
  echo "| Service accounts | $(jcount "$SERVICE_ACCOUNTS") |"
  echo "| Storage buckets | $(jcount "$STORAGE_BUCKETS") |"
  echo "| IAP brands | $(jcount "$IAP_BRANDS") |"
  echo "| Cloud Build triggers | $(jcount "$CB_TRIGGERS") |"
  echo "| Cloud Functions | $(jcount "$CF_FUNCTIONS") |"
  echo "| GKE clusters | $(jcount "$GKE_CLUSTERS") |"
  echo "| BigQuery datasets | $BQ_COUNT |"
  echo "| Pub/Sub topics | $(jcount "$PUBSUB_TOPICS") |"
  echo "| Cloud SQL instances | $(jcount "$SQL_INSTANCES") |"
  echo "| Secret Manager secrets | $(jcount "$SECRETS") |"
  echo "| DNS zones | $(jcount "$DNS_ZONES") |"
  echo

  # ─── Detected Application Groups ──────────────────────────────────────────
  if [ -n "$APP_GROUPS" ]; then
    echo "## Detected Application Groups"
    echo
    echo "Resources were classified into the following application groups based on naming conventions:"
    echo
    for group in $APP_GROUPS; do
      echo "- **\`${group}\`** — resources with prefix \`${group}-\` or \`${group}_\`"
    done
    echo
    echo "> [!NOTE]"
    echo "> Classification is based on resource name prefixes. Resources without a recognizable prefix are labeled \"other\". Auto-created resources (default service accounts, blueprint buckets, etc.) are labeled separately."
    echo
  fi

  # ─── Cloud Run ────────────────────────────────────────────────────────────
  echo "## Cloud Run Services"
  echo
  cr_count=$(jcount "$CLOUDRUN")
  if [ "$cr_count" -eq 0 ]; then
    echo "_No Cloud Run services found._"
    echo
  else
    echo "| Name | Region | URL | Status | Classification | Assessment |"
    echo "|------|--------|-----|--------|----------------|------------|"
    echo "$CLOUDRUN" | jq -r '.[] | "\(.name // .metadata.name // "N/A")\t\(.region // "N/A")\t\(.status.uri // .status.url // "N/A")\t\(.status.conditions[0].state // "N/A")"' 2>/dev/null | while IFS=$'\t' read -r name region url status; do
      sname=$(short_name "$name")
      cls=$(classify_name "$sname")
      echo "| \`$sname\` | $region | $url | $status | $cls | $(assess_deletion cloud_run "$sname" "$status") |"
    done
    echo
  fi

  # ─── Artifact Registry ─────────────────────────────────────────────────────
  echo "## Artifact Registry Repositories"
  echo
  if [ "$AR_COUNT" -eq 0 ]; then
    echo "_No Artifact Registry repositories found._"
    echo
  else
    echo "| Name | Format | Location | Size | Classification | Assessment |"
    echo "|------|--------|----------|------|----------------|------------|"
    echo "$AR_REPOS" | jq -r '.[] | "\(.name)\t\(.format)\t\(.location)\t\(.sizeBytes // "N/A")"' 2>/dev/null | while IFS=$'\t' read -r name format location size; do
      sname=$(short_name "$name")
      cls=$(classify_name "$sname")
      # Human-readable size
      if [ "$size" != "N/A" ] && [ -n "$size" ]; then
        hsize=$(numfmt --to=iec "$size" 2>/dev/null || echo "${size}B")
      else
        hsize="N/A"
      fi
      echo "| \`$sname\` | $format | $location | $hsize | $cls | $(assess_deletion artifact_registry "$sname" "") |"
    done
    echo
  fi

  # ─── Compute Instances ─────────────────────────────────────────────────────
  echo "## Compute Instances"
  echo
  ci_count=$(jcount "$COMPUTE_INSTANCES")
  if [ "$ci_count" -eq 0 ]; then
    echo "_No compute instances found._"
    echo
  else
    echo "| Name | Zone | Status | Machine Type | Classification | Assessment |"
    echo "|------|------|--------|---------------|----------------|------------|"
    echo "$COMPUTE_INSTANCES" | jq -r '.[] | "\(.name)\t\(.zone // "N/A")\t\(.status)\t\(.machineType // "N/A")"' 2>/dev/null | while IFS=$'\t' read -r name zone status mtype; do
      zone=$(short_name "$zone")
      mtype=$(short_name "$mtype")
      cls=$(classify_name "$name")
      echo "| \`$name\` | $zone | $status | $mtype | $cls | $(assess_deletion compute_instance "$name" "$status") |"
    done
    echo
  fi

  # ─── Cloud SQL ─────────────────────────────────────────────────────────────
  echo "## Cloud SQL Instances"
  echo
  sql_count=$(jcount "$SQL_INSTANCES")
  if [ "$sql_count" -eq 0 ]; then
    echo "_No Cloud SQL instances found._"
    echo
  else
    echo "| Name | Database Version | Region | State | Classification | Assessment |"
    echo "|------|------------------|--------|-------|----------------|------------|"
    echo "$SQL_INSTANCES" | jq -r '.[] | "\(.name)\t\(.databaseVersion)\t\(.region)\t\(.state)"' 2>/dev/null | while IFS=$'\t' read -r name ver region state; do
      cls=$(classify_name "$name")
      echo "| \`$name\` | $ver | $region | $state | $cls | $(assess_deletion cloud_sql "$name" "") |"
    done
    echo
  fi

  # ─── Secret Manager ───────────────────────────────────────────────────────
  echo "## Secret Manager Secrets"
  echo
  sec_count=$(jcount "$SECRETS")
  if [ "$sec_count" -eq 0 ]; then
    echo "_No secrets found._"
    echo
  else
    echo "| Name | Replication | Classification | Assessment |"
    echo "|------|-------------|----------------|------------|"
    echo "$SECRETS" | jq -r '.[] | "\(.name)\t\(.replication.automatic.enabled // .replication.userManaged.replicas[0].location // "N/A")"' 2>/dev/null | while IFS=$'\t' read -r name repl; do
      sname=$(short_name "$name")
      cls=$(classify_name "$sname")
      echo "| \`$sname\` | $repl | $cls | $(assess_deletion secret "$sname" "") |"
    done
    echo
  fi

  # ─── Storage Buckets ───────────────────────────────────────────────────────
  echo "## Storage Buckets"
  echo
  sb_count=$(jcount "$STORAGE_BUCKETS")
  if [ "$sb_count" -eq 0 ]; then
    echo "_No storage buckets found._"
    echo
  else
    echo "| Name | Location | Size | Classification | Assessment |"
    echo "|------|----------|------|----------------|------------|"
    echo "$STORAGE_BUCKETS" | jq -r '.[] | "\(.name)\t\(.location // "N/A")"' 2>/dev/null | while IFS=$'\t' read -r name location; do
      cls=$(classify_name "$name")
      # Try to get bucket size (non-blocking, best-effort)
      size=$(gcloud storage du -s "gs://$name/" --project="$PROJECT_ID" --quiet 2>/dev/null | awk '{print $1}' || echo "0")
      if [ -z "$size" ]; then size="0"; fi
      hsize=$(numfmt --to=iec "$size" 2>/dev/null || echo "${size}B")
      echo "| \`$name\` | $location | $hsize | $cls | $(assess_deletion storage_bucket "$name" "size:$size") |"
    done
    echo
  fi

  # ─── Service Accounts ──────────────────────────────────────────────────────
  echo "## Service Accounts"
  echo
  sa_count=$(jcount "$SERVICE_ACCOUNTS")
  if [ "$sa_count" -eq 0 ]; then
    echo "_No service accounts found._"
    echo
  else
    echo "| Email | Display Name | Classification | Assessment |"
    echo "|-------|-------------|----------------|------------|"
    echo "$SERVICE_ACCOUNTS" | jq -r '.[] | "\(.email)\t\(.displayName // "")"' 2>/dev/null | while IFS=$'\t' read -r email dname; do
      cls=$(classify_name "$email")
      echo "| \`$email\` | $dname | $cls | $(assess_deletion service_account "$email" "") |"
    done
    echo
  fi

  # ─── Compute Addresses ─────────────────────────────────────────────────────
  echo "## Compute Addresses"
  echo
  ca_count=$(jcount "$COMPUTE_ADDRESSES")
  if [ "$ca_count" -eq 0 ]; then
    echo "_No compute addresses found._"
    echo
  else
    echo "| Name | Type | Address | Region | Classification | Assessment |"
    echo "|------|------|---------|--------|----------------|------------|"
    echo "$COMPUTE_ADDRESSES" | jq -r '.[] | "\(.name)\t\(.addressType)\t\(.address)\t\(.region // "global")"' 2>/dev/null | while IFS=$'\t' read -r name atype addr region; do
      region=$(short_name "$region")
      cls=$(classify_name "$name")
      echo "| \`$name\` | $atype | $addr | $region | $cls | $(assess_deletion compute_address "$name" "") |"
    done
    echo
  fi

  # ─── Compute Networking (LB components) ───────────────────────────────────
  echo "## Load Balancer Components"
  echo
  lb_total=0
  lb_total=$((lb_total + $(jcount "$COMPUTE_BACKENDS") + $(jcount "$COMPUTE_URLMAPS") + $(jcount "$COMPUTE_HTTPS_PROXIES") + $(jcount "$COMPUTE_HTTP_PROXIES") + $(jcount "$COMPUTE_FWD_RULES") + $(jcount "$COMPUTE_SSL_CERTS")))
  if [ "$lb_total" -eq 0 ]; then
    echo "_No load balancer components found._"
    echo
  else
    if [ "$(jcount "$COMPUTE_BACKENDS")" -gt 0 ]; then
      echo "### Backend Services"
      echo
      echo "| Name | Protocol | LB Scheme | Classification |"
      echo "|------|----------|-----------|----------------|"
      echo "$COMPUTE_BACKENDS" | jq -r '.[] | "\(.name)\t\(.protocol // "N/A")\t\(.loadBalancingScheme // "N/A")"' 2>/dev/null | while IFS=$'\t' read -r name proto scheme; do
        echo "| \`$name\` | $proto | $scheme | $(classify_name "$name") |"
      done
      echo
    fi
    if [ "$(jcount "$COMPUTE_FWD_RULES")" -gt 0 ]; then
      echo "### Forwarding Rules"
      echo
      echo "| Name | LB Scheme | IP Address | Target | Classification |"
      echo "|------|-----------|------------|--------|----------------|"
      echo "$COMPUTE_FWD_RULES" | jq -r '.[] | "\(.name)\t\(.loadBalancingScheme // "N/A")\t\(.IPAddress // "N/A")\t\(.target // "N/A")"' 2>/dev/null | while IFS=$'\t' read -r name scheme ip target; do
        echo "| \`$name\` | $scheme | $ip | $(short_name "$target") | $(classify_name "$name") |"
      done
      echo
    fi
    if [ "$(jcount "$COMPUTE_SSL_CERTS")" -gt 0 ]; then
      echo "### SSL Certificates"
      echo
      echo "| Name | Type | Managed Status | Classification |"
      echo "|------|------|----------------|----------------|"
      echo "$COMPUTE_SSL_CERTS" | jq -r '.[] | "\(.name)\t\(.type // "MANAGED")\t\(.managed.status // "N/A")"' 2>/dev/null | while IFS=$'\t' read -r name ctype mstatus; do
        echo "| \`$name\` | $ctype | $mstatus | $(classify_name "$name") |"
      done
      echo
    fi
  fi

  # ─── Compute NEGs ──────────────────────────────────────────────────────────
  echo "## Network Endpoint Groups (NEGs)"
  echo
  neg_count=$(jcount "$COMPUTE_NEGS")
  if [ "$neg_count" -eq 0 ]; then
    echo "_No NEGs found._"
    echo
  else
    echo "| Name | Type | Zone/Region | Classification |"
    echo "|------|------|-------------|----------------|"
    echo "$COMPUTE_NEGS" | jq -r '.[] | "\(.name)\t\(.networkEndpointType // "N/A")\t\(.zone // .region // "N/A")"' 2>/dev/null | while IFS=$'\t' read -r name ntype zregion; do
      zregion=$(short_name "$zregion")
      echo "| \`$name\` | $ntype | $zregion | $(classify_name "$name") |"
    done
    echo
  fi

  # ─── Compute Disks ─────────────────────────────────────────────────────────
  echo "## Compute Disks"
  echo
  cd_count=$(jcount "$COMPUTE_DISKS")
  if [ "$cd_count" -eq 0 ]; then
    echo "_No compute disks found._"
    echo
  else
    echo "| Name | Size (GB) | Zone | Status | Classification | Assessment |"
    echo "|------|-----------|------|--------|----------------|------------|"
    echo "$COMPUTE_DISKS" | jq -r '.[] | "\(.name)\t\(.sizeGb // "?")\t\(.zone // "N/A")\t\(.status // "N/A")"' 2>/dev/null | while IFS=$'\t' read -r name size zone status; do
      zone=$(short_name "$zone")
      cls=$(classify_name "$name")
      if echo "$status" | grep -qi "READY"; then
        echo "| \`$name\` | $size | $zone | $status | $cls | ⚠️ Investigate — disk is READY |"
      else
        echo "| \`$name\` | $size | $zone | $status | $cls | ✅ May be safe (status: $status) |"
      fi
    done
    echo
  fi

  # ─── GKE Clusters ──────────────────────────────────────────────────────────
  echo "## GKE Clusters"
  echo
  gke_count=$(jcount "$GKE_CLUSTERS")
  if [ "$gke_count" -eq 0 ]; then
    echo "_No GKE clusters found._"
    echo
  else
    echo "| Name | Location | Status | Classification | Assessment |"
    echo "|------|----------|--------|----------------|------------|"
    echo "$GKE_CLUSTERS" | jq -r '.[] | "\(.name)\t\(.location)\t\(.status // "N/A")"' 2>/dev/null | while IFS=$'\t' read -r name location status; do
      cls=$(classify_name "$name")
      echo "| \`$name\` | $location | $status | $cls | ⚠️ Investigate — GKE cluster |"
    done
    echo
  fi

  # ─── Cloud Functions ───────────────────────────────────────────────────────
  echo "## Cloud Functions"
  echo
  cf_count=$(jcount "$CF_FUNCTIONS")
  if [ "$cf_count" -eq 0 ]; then
    echo "_No Cloud Functions found (API may not be enabled)._"
    echo
  else
    echo "| Name | Status | Classification | Assessment |"
    echo "|------|--------|----------------|------------|"
    echo "$CF_FUNCTIONS" | jq -r '.[] | "\(.name)\t\(.status // "N/A")"' 2>/dev/null | while IFS=$'\t' read -r name status; do
      cls=$(classify_name "$name")
      echo "| \`$name\` | $status | $cls | $(assess_deletion cloud_function "$name" "$status") |"
    done
    echo
  fi

  # ─── Cloud Build Triggers ─────────────────────────────────────────────────
  echo "## Cloud Build Triggers"
  echo
  cb_count=$(jcount "$CB_TRIGGERS")
  if [ "$cb_count" -eq 0 ]; then
    echo "_No Cloud Build triggers found._"
    echo
  else
    echo "| Name | Trigger Type | Classification |"
    echo "|------|--------------|----------------|"
    echo "$CB_TRIGGERS" | jq -r '.[] | "\(.name)\t\(.triggerTemplate.branchName // .github.name // .webhook.config // "N/A")"' 2>/dev/null | while IFS=$'\t' read -r name ttype; do
      echo "| \`$name\` | $ttype | $(classify_name "$name") |"
    done
    echo
  fi

  # ─── BigQuery Datasets ─────────────────────────────────────────────────────
  echo "## BigQuery Datasets"
  echo
  if [ "$BQ_COUNT" -eq 0 ]; then
    echo "_No BigQuery datasets found._"
    echo
  else
    echo "| Dataset ID | Classification | Assessment |"
    echo "|------------|----------------|------------|"
    echo "$BQ_DATASETS" | jq -r '.[].datasetReference.datasetId // empty' 2>/dev/null | while IFS= read -r dsid; do
      echo "| \`$dsid\` | $(classify_name "$dsid") | ⚠️ Investigate — may contain data |"
    done
    echo
  fi

  # ─── Pub/Sub Topics ────────────────────────────────────────────────────────
  echo "## Pub/Sub Topics"
  echo
  ps_count=$(jcount "$PUBSUB_TOPICS")
  if [ "$ps_count" -eq 0 ]; then
    echo "_No Pub/Sub topics found._"
    echo
  else
    echo "| Topic | Classification |"
    echo "|-------|----------------|"
    echo "$PUBSUB_TOPICS" | jq -r '.[].name // empty' 2>/dev/null | while IFS= read -r topic; do
      tname=$(short_name "$topic")
      echo "| \`$tname\` | $(classify_name "$tname") |"
    done
    echo
  fi

  # ─── DNS Zones ─────────────────────────────────────────────────────────────
  echo "## Cloud DNS Zones"
  echo
  dns_count=$(jcount "$DNS_ZONES")
  if [ "$dns_count" -eq 0 ]; then
    echo "_No DNS zones found._"
    echo
  else
    echo "| Name | DNS Name | Visibility | Classification |"
    echo "|------|----------|------------|----------------|"
    echo "$DNS_ZONES" | jq -r '.[] | "\(.name)\t\(.dnsName)\t\(.visibility)"' 2>/dev/null | while IFS=$'\t' read -r name dnsname vis; do
      echo "| \`$name\` | $dnsname | $vis | $(classify_name "$name") |"
    done
    echo
  fi

  # ─── IAP ──────────────────────────────────────────────────────────────────
  echo "## Identity-Aware Proxy (IAP)"
  echo
  iap_count=$(jcount "$IAP_BRANDS")
  if [ "$iap_count" -eq 0 ]; then
    echo "_No IAP brands found (IAP API may not be enabled)._"
    echo
  else
    echo "| Brand Name | Application Title | Assessment |"
    echo "|------------|-------------------|------------|"
    echo "$IAP_BRANDS" | jq -r '.[] | "\(.name)\t\(.applicationTitle)"' 2>/dev/null | while IFS=$'\t' read -r name title; do
      echo "| \`$name\` | $title | ℹ️ IAP OAuth brand (one per project) |"
    done
    echo
  fi

  # ─── Compute Networks ──────────────────────────────────────────────────────
  echo "## VPC Networks"
  echo
  net_count=$(jcount "$COMPUTE_NETWORKS")
  if [ "$net_count" -eq 0 ]; then
    echo "_No VPC networks found._"
    echo
  else
    echo "| Name | Auto-create Subnetworks | Classification |"
    echo "|------|------------------------|----------------|"
    echo "$COMPUTE_NETWORKS" | jq -r '.[] | "\(.name)\t\(.autoCreateSubnetworks)"' 2>/dev/null | while IFS=$'\t' read -r name auto; do
      echo "| \`$name\` | $auto | $(classify_name "$name") |"
    done
    echo
  fi

  # ─── Firewall Rules ───────────────────────────────────────────────────────
  echo "## Firewall Rules"
  echo
  fw_count=$(jcount "$COMPUTE_FIREWALLS")
  if [ "$fw_count" -eq 0 ]; then
    echo "_No firewall rules found._"
    echo
  else
    echo "| Name | Direction | Priority | Classification |"
    echo "|------|-----------|----------|----------------|"
    echo "$COMPUTE_FIREWALLS" | jq -r '.[] | "\(.name)\t\(.direction)\t\(.priority)"' 2>/dev/null | while IFS=$'\t' read -r name dir prio; do
      echo "| \`$name\` | $dir | $prio | $(classify_name "$name") |"
    done
    echo
  fi

  # ─── Enabled APIs ──────────────────────────────────────────────────────────
  echo "## Enabled APIs"
  echo
  echo "<details>"
  echo "<summary>Click to expand ($API_COUNT APIs enabled)</summary>"
  echo
  echo '```'
  echo "$ENABLED_APIS"
  echo '```'
  echo
  echo "</details>"
  echo

  # ─── IAM Policy ────────────────────────────────────────────────────────────
  echo "## IAM Policy Bindings"
  echo
  echo "<details>"
  echo "<summary>Click to expand IAM bindings</summary>"
  echo
  echo "| Role | Members |"
  echo "|------|---------|"
  echo "$IAM_POLICY" | jq -r '.bindings[] | "\(.role)\t\(.members | join(", "))"' 2>/dev/null | while IFS=$'\t' read -r role members; do
    # Truncate very long member lists
    if [ ${#members} -gt 200 ]; then
      members="${members:0:200}..."
    fi
    echo "| \`$role\` | $members |"
  done
  echo
  echo "</details>"
  echo

  # ─── Resource Grouping & Related Resources ────────────────────────────────
  if [ -n "$APP_GROUPS" ]; then
    echo "## Resource Grouping by Application"
    echo
    echo "Resources attributed to detected application groups:"
    echo
    for group in $APP_GROUPS; do
      echo "### Application: \`$group\`"
      echo
      echo "| Resource Type | Resource Name |"
      echo "|---------------|---------------|"

      # Cloud Run
      echo "$CLOUDRUN" | jq -r '.[].name // .[].metadata.name // empty' 2>/dev/null | while read -r p; do basename "$p"; done | grep -i "^${group}" | while IFS= read -r n; do
        echo "| Cloud Run | \`$n\` |"
      done
      # Artifact Registry (name is full path, extract short name)
      echo "$AR_REPOS" | jq -r '.[].name // empty' 2>/dev/null | while IFS= read -r p; do
        sname=$(short_name "$p")
        if echo "$sname" | grep -qi "^$group"; then
          echo "| Artifact Registry | \`$sname\` |"
        fi
      done
      # Compute instances
      echo "$COMPUTE_INSTANCES" | jq -r '.[].name // empty' 2>/dev/null | grep -i "^$group" | while IFS= read -r n; do
        echo "| Compute instance | \`$n\` |"
      done
      # Cloud SQL
      echo "$SQL_INSTANCES" | jq -r '.[].name // empty' 2>/dev/null | grep -i "^$group" | while IFS= read -r n; do
        echo "| Cloud SQL | \`$n\` |"
      done
      # Secrets — extract short name from path
      echo "$SECRETS" | jq -r '.[].name // empty' 2>/dev/null | while IFS= read -r p; do
        sname=$(short_name "$p")
        if echo "$sname" | grep -qi "^${group}"; then
          echo "| Secret Manager | \`$sname\` |"
        fi
      done
      # Service accounts
      echo "$SERVICE_ACCOUNTS" | jq -r '.[].email // empty' 2>/dev/null | grep -i "$group" | while IFS= read -r n; do
        echo "| Service account | \`$n\` |"
      done
      # Compute addresses
      echo "$COMPUTE_ADDRESSES" | jq -r '.[].name // empty' 2>/dev/null | grep -i "^$group" | while IFS= read -r n; do
        echo "| Compute address | \`$n\` |"
      done
      # Storage buckets
      echo "$STORAGE_BUCKETS" | jq -r '.[].name // empty' 2>/dev/null | grep -i "$group" | while IFS= read -r n; do
        echo "| Storage bucket | \`$n\` |"
      done
      # Cloud Functions
      echo "$CF_FUNCTIONS" | jq -r '.[].name // empty' 2>/dev/null | grep -i "^$group" | while IFS= read -r n; do
        echo "| Cloud Function | \`$n\` |"
      done
      # GKE
      echo "$GKE_CLUSTERS" | jq -r '.[].name // empty' 2>/dev/null | grep -i "^$group" | while IFS= read -r n; do
        echo "| GKE cluster | \`$n\` |"
      done
      echo
      echo "> [!TIP]"
      echo "> All resources with the \`${group}-\` or \`${group}_\` prefix appear related. Deleting one may affect others in this group."
      echo
    done
  fi

  # ─── Cleanup Recommendations ─────────────────────────────────────────────
  echo "## Cleanup Recommendations"
  echo
  echo "### ✅ Likely Safe to Delete"
  echo
  echo "- **Terminated compute instances** — not running, no cost"
  echo "- **Empty storage buckets** — no data to lose"
  echo "- **Auto-created resources** — default service accounts, blueprint buckets (will be recreated if needed)"
  echo

  echo "### ⚠️ Investigate Before Deleting"
  echo
  echo "- **Running compute instances** — may be serving traffic"
  echo "- **Cloud SQL instances** — may contain application data"
  echo "- **Secrets** — may be referenced by running applications"
  echo "- **Storage buckets with data** — may contain important files"
  echo "- **Custom service accounts** — may be used by running applications"
  echo "- **Load balancer components** — may be serving traffic"
  echo

  echo "### 📦 Related Resource Groups"
  echo
  if [ -n "$APP_GROUPS" ]; then
    echo "The following application groups were detected. Resources within each group are likely related:"
    echo
    for group in $APP_GROUPS; do
      echo "- **\`$group\`** — review all resources with this prefix before deleting any"
    done
    echo
    echo "> [!WARNING]"
    echo "> Deleting resources from one application group without removing all related resources may leave orphaned resources (e.g., a service account without its Cloud SQL instance, or a compute address without its forwarding rule)."
  else
    echo "_No application groups detected (all resources appear to be auto-created or unclassified)._"
  fi
  echo

  # ─── Footer ───────────────────────────────────────────────────────────────
  echo "---"
  echo
  echo "_Generated by \`audit_gcp_project.sh\` on $AUDIT_DATE by $AUDITOR_"

} > "$OUTPUT_FILE"

echo "✅ Audit complete: $OUTPUT_FILE" >&2
echo "   Project: $PROJECT_ID ($PROJECT_NUMBER)" >&2
echo "   Resources audited: $(jcount "$CLOUDRUN") Cloud Run, $(jcount "$COMPUTE_INSTANCES") compute instances, $(jcount "$SQL_INSTANCES") SQL instances, $(jcount "$STORAGE_BUCKETS") buckets, $(jcount "$SERVICE_ACCOUNTS") service accounts" >&2
