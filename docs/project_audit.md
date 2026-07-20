# GCP Project Audit — Pre-Cleanup Inventory

Audited: 2026-07-20

## Project 1: `ppardyak-cad`

**State: Mostly empty — no Sudoku resources deployed here yet.**

### Resources present

| Category | Resource | Status |
|----------|----------|--------|
| **Service accounts** | `295092059542-compute@developer.gserviceaccount.com` | Default GCE SA (auto-created) |
| **Storage buckets** | `295092059542-us-central1-blueprint-config` | Blueprint config (likely auto-created) |
| **Storage buckets** | `ppardyak-cad_blueprints` | Blueprint storage |
| **IAM** | `user:ppardyak@google.com` → `roles/owner` | Your owner access |
| **IAM** | Various service agent bindings | Auto-managed by GCP |

### Sudoku resources
None — Cloud Run API is not even enabled.

### Unnecessary for Sudoku
- 2 storage buckets (blueprint config) — auto-created by Infrastructure Manager, not used by Sudoku
- Many enabled APIs that Sudoku doesn't need (GKE, BigQuery, Container Registry, etc.)

---

## Project 2: `ppardyak-new-project`

**State: Has Sudoku deployed + leftover resources from other apps (xwiki, test instances).**

### Sudoku-related resources ✅ (keep)

| Resource | Detail |
|----------|--------|
| Cloud Run service | `sudoku` — `https://sudoku-mldxflouqa-uc.a.run.app` (Ready) |
| Artifact Registry repo | `sudoku-repo` (Docker) |
| IAP brand | `Sudoku` (projects/1053231822532/brands/1053231822532) |
| IAM | `user:ppardyak@google.com` → `roles/owner` |

### Non-Sudoku resources (candidates for cleanup)

| Category | Resource | Detail | Safe to delete? |
|----------|----------|--------|-----------------|
| **Service accounts** | `goog-sc-java-application-415@...` | Java app SA | ⚠️ Check first |
| **Service accounts** | `xwiki-jgroup-gce@...` | XWiki SA | ⚠️ Check first |
| **Compute instances** | `test-01` (us-central1-a) | TERMINATED | ✅ Yes |
| **Compute instances** | `test-02` (us-central1-a) | TERMINATED | ✅ Yes |
| **Compute addresses** | `xwiki-db-address-gce` (internal 172.16.48.0) | XWiki DB | ⚠️ Check first |
| **Compute addresses** | `xwiki-lb-http-ip` (external 34.144.238.171) | XWiki LB | ⚠️ Check first |
| **Cloud SQL** | `xwiki-us-central1-db-gce` (MySQL 8.0) | XWiki DB | ⚠️ Check first |
| **Secret Manager** | `xwiki-db-password` | XWiki DB password | ⚠️ Check first |
| **Storage buckets** | `1053231822532-us-central1-blueprint-config` | Blueprint config | Likely auto-created |
| **Storage buckets** | `ppardyak-new-project_cloudbuild` | Cloud Build logs | Likely auto-created |

### IAP leftover (from failed IAP setup)

| Resource | Detail |
|----------|--------|
| IAP brand + client | Created during failed IAP attempt. Can be deleted if not needed, or left (harmless). |

---

## Summary

| | ppardyak-cad | ppardyak-new-project |
|---|---|---|
| Sudoku deployed? | ❌ No | ✅ Yes |
| Other apps' resources? | Minimal (2 buckets) | Yes — xwiki, test instances |
| Cloud Run enabled? | ❌ No | ✅ Yes |
| Needs cleanup before Sudoku deploy? | Just deploy | Clean up xwiki/test resources |

### Recommended actions

1. **ppardyak-cad**: Ready for a fresh Sudoku deploy — no cleanup needed
2. **ppardyak-new-project**: Delete the terminated test instances; decide on xwiki resources (they're from a different app)
