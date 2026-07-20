# GCP Project Audit: `ppardyak-new-project`

| Field | Value |
|-------|-------|
| Project ID | `ppardyak-new-project` |
| Project Name | ppardyak -- New Project |
| Project Number | 1053231822532 |
| Lifecycle State | ACTIVE |
| Created | 2020-06-04T19:38:46.004Z |
| Audit Date | 2026-07-20T16:52:19Z |
| Audited By | ppardyak@google.com |

## Summary

| Resource Type | Count |
|---------------|-------|
| Enabled APIs | 63 |
| Cloud Run services | 1 |
| Artifact Registry repos | 1 |
| Compute instances | 2 |
| Compute backend services | 0 |
| Compute URL maps | 0 |
| Compute forwarding rules | 0 |
| Compute addresses | 2 |
| Compute SSL certificates | 0 |
| Compute NEGs | 0 |
| Compute disks | 2 |
| Compute images | 0 |
| Compute snapshots | 0 |
| Compute firewall rules | 6 |
| Compute networks | 2 |
| Service accounts | 3 |
| Storage buckets | 2 |
| IAP brands | 1 |
| Cloud Build triggers | 0 |
| Cloud Functions | 0 |
| GKE clusters | 0 |
| BigQuery datasets | 0 |
| Pub/Sub topics | 0 |
| Cloud SQL instances | 1 |
| Secret Manager secrets | 1 |
| DNS zones | 0 |

## Detected Application Groups

Resources were classified into the following application groups based on naming conventions:

- **`sudoku`** — resources with prefix `sudoku-` or `sudoku_`
- **`test`** — resources with prefix `test-` or `test_`
- **`xwiki`** — resources with prefix `xwiki-` or `xwiki_`

> [!NOTE]
> Classification is based on resource name prefixes. Resources without a recognizable prefix are labeled "other". Auto-created resources (default service accounts, blueprint buckets, etc.) are labeled separately.

## Cloud Run Services

| Name | Region | URL | Status | Classification | Assessment |
|------|--------|-----|--------|----------------|------------|
| `sudoku` | N/A | https://sudoku-mldxflouqa-uc.a.run.app | N/A | app:sudoku | 📦 Belongs to application: sudoku |

## Artifact Registry Repositories

| Name | Format | Location | Size | Classification | Assessment |
|------|--------|----------|------|----------------|------------|
| `sudoku-repo` | DOCKER | null | 51M | app:sudoku | 📦 Belongs to application: sudoku |

## Compute Instances

| Name | Zone | Status | Machine Type | Classification | Assessment |
|------|------|--------|---------------|----------------|------------|
| `test-01` | us-central1-a | TERMINATED | e2-micro | app:test | ✅ Safe to delete (instance is TERMINATED) |
| `test-02` | us-central1-a | TERMINATED | e2-medium | app:test | ✅ Safe to delete (instance is TERMINATED) |

## Cloud SQL Instances

| Name | Database Version | Region | State | Classification | Assessment |
|------|------------------|--------|-------|----------------|------------|
| `xwiki-us-central1-db-gce` | MYSQL_8_0 | us-central1 | RUNNABLE | app:xwiki | ⚠️ Investigate — database may contain data (app:xwiki) |

## Secret Manager Secrets

| Name | Replication | Classification | Assessment |
|------|-------------|----------------|------------|
| `xwiki-db-password` | N/A | app:xwiki | ⚠️ Investigate — secret may be in use (app:xwiki) |

## Storage Buckets

| Name | Location | Size | Classification | Assessment |
|------|----------|------|----------------|------------|
| `1053231822532-us-central1-blueprint-config` | US-CENTRAL1 | 226K | auto-created | ✅ Likely safe to delete (auto-created, size:230662) |
| `ppardyak-new-project_cloudbuild` | US | 35M | auto-created | ✅ Likely safe to delete (auto-created, size:36685002) |

## Service Accounts

| Email | Display Name | Classification | Assessment |
|-------|-------------|----------------|------------|
| `1053231822532-compute@developer.gserviceaccount.com` | Compute Engine default service account | auto-created | ✅ Auto-created default SA (will be recreated if needed) |
| `goog-sc-java-application-415@ppardyak-new-project.iam.gserviceaccount.com` | java-application service account | other | ⚠️ Investigate — custom service account for 'other' |
| `xwiki-jgroup-gce@ppardyak-new-project.iam.gserviceaccount.com` |  | app:xwiki | ⚠️ Investigate — custom service account for 'app:xwiki' |

## Compute Addresses

| Name | Type | Address | Region | Classification | Assessment |
|------|------|---------|--------|----------------|------------|
| `xwiki-db-address-gce` | INTERNAL | 172.16.48.0 | global | app:xwiki | ⚠️ Investigate — address for 'app:xwiki' |
| `xwiki-lb-http-ip` | EXTERNAL | 34.144.238.171 | global | app:xwiki | ⚠️ Investigate — address for 'app:xwiki' |

## Load Balancer Components

_No load balancer components found._

## Network Endpoint Groups (NEGs)

_No NEGs found._

## Compute Disks

| Name | Size (GB) | Zone | Status | Classification | Assessment |
|------|-----------|------|--------|----------------|------------|
| `test-01` | 10 | us-central1-a | READY | app:test | ⚠️ Investigate — disk is READY |
| `test-02` | 10 | us-central1-a | READY | app:test | ⚠️ Investigate — disk is READY |

## GKE Clusters

_No GKE clusters found._

## Cloud Functions

_No Cloud Functions found (API may not be enabled)._

## Cloud Build Triggers

_No Cloud Build triggers found._

## BigQuery Datasets

_No BigQuery datasets found._

## Pub/Sub Topics

_No Pub/Sub topics found._

## Cloud DNS Zones

_No DNS zones found._

## Identity-Aware Proxy (IAP)

| Brand Name | Application Title | Assessment |
|------------|-------------------|------------|
| `projects/1053231822532/brands/1053231822532` | Sudoku | ℹ️ IAP OAuth brand (one per project) |

## VPC Networks

| Name | Auto-create Subnetworks | Classification |
|------|------------------------|----------------|
| `default` | true | other |
| `xwiki-gce` | true | app:xwiki |

## Firewall Rules

| Name | Direction | Priority | Classification |
|------|-----------|----------|----------------|
| `default-allow-icmp` | INGRESS | 65534 | other |
| `default-allow-internal` | INGRESS | 65534 | other |
| `default-allow-rdp` | INGRESS | 65534 | other |
| `default-allow-ssh` | INGRESS | 65534 | other |
| `xwiki-allow-internal` | INGRESS | 1000 | app:xwiki |
| `xwiki-us-central1-ssh` | INGRESS | 1000 | app:xwiki |

## Enabled APIs

<details>
<summary>Click to expand (63 APIs enabled)</summary>

```
anthosconfigmanagement.googleapis.com             Anthos Config Management API
anthospolicycontroller.googleapis.com             Anthos Policy Controller API
artifactregistry.googleapis.com                   Artifact Registry API
autoscaling.googleapis.com                        Cloud Autoscaling API
bcidcloudenforcer-pa.googleapis.com               BCID Cloud Enforcer Private API
bigquery.googleapis.com                           BigQuery API
bigquerymigration.googleapis.com                  BigQuery Migration API
bigquerystorage.googleapis.com                    BigQuery Storage API
certificatemanager.googleapis.com                 Certificate Manager API
cloudaicompanion.googleapis.com                   Gemini for Google Cloud API
cloudapis.googleapis.com                          Google Cloud APIs
cloudbuild.googleapis.com                         Cloud Build API
cloudresourcemanager.googleapis.com               Cloud Resource Manager API
cloudtrace.googleapis.com                         Cloud Trace API
compute.googleapis.com                            Compute Engine API
computescanning.googleapis.com                    Compute Scanning API
config.googleapis.com                             Infrastructure Manager API
containeranalysis.googleapis.com                  Container Analysis API
containerfilesystem.googleapis.com                Container File System API
container.googleapis.com                          Kubernetes Engine API
containerregistry.googleapis.com                  Container Registry API
containerscanning.googleapis.com                  Container Scanning API
containerthreatdetection.googleapis.com           Container Threat Detection API
datastore.googleapis.com                          Cloud Datastore API
deploymentmanager.googleapis.com                  Cloud Deployment Manager V2 API
dns.googleapis.com                                Cloud DNS API
edgecache.googleapis.com                          Global Edge Cache Service
file.googleapis.com                               Cloud Filestore API
geminicloudassist.googleapis.com                  Gemini Cloud Assist API
gkebackup.googleapis.com                          Backup for GKE API
gkeconnect.googleapis.com                         GKE Connect API
gkehub.googleapis.com                             GKE Hub API
iamcredentials.googleapis.com                     IAM Service Account Credentials API
iam.googleapis.com                                Identity and Access Management (IAM) API
iap.googleapis.com                                Cloud Identity-Aware Proxy API
krmapihosting.googleapis.com                      KRM API Hosting API
logging.googleapis.com                            Cloud Logging API
monitoring.googleapis.com                         Cloud Monitoring API
multiclustermetering.googleapis.com               Multi cluster metering API
NAME                                              TITLE
networkconnectivity.googleapis.com                Network Connectivity API
networksecurity.googleapis.com                    Network Security API
networkservices.googleapis.com                    Network Services API
notebooksecurityscanner.googleapis.com            Notebook Security Scanner API
orgpolicy.googleapis.com                          Organization Policy API
osconfig.googleapis.com                           OS Config API
oslogin.googleapis.com                            Cloud OS Login API
pubsub.googleapis.com                             Cloud Pub/Sub API
run.googleapis.com                                Cloud Run Admin API
secretmanager.googleapis.com                      Secret Manager API
servicecontrol.googleapis.com                     Service Control API
servicemanagement.googleapis.com                  Service Management API
servicenetworking.googleapis.com                  Service Networking API
serviceusage.googleapis.com                       Service Usage API
sqladmin.googleapis.com                           Cloud SQL Admin API
sql-component.googleapis.com                      Cloud SQL
staging-cloudaicompanion.sandbox.googleapis.com   Gemini for Google Cloud API (Staging)
staging-geminicloudassist.sandbox.googleapis.com  Gemini Cloud Assist API (staging)
storage-api.googleapis.com                        Google Cloud Storage JSON API
storage-component.googleapis.com                  Cloud Storage
storage.googleapis.com                            Cloud Storage API
telemetry.googleapis.com                          Telemetry API
websecurityscanner.googleapis.com                 Web Security Scanner API
```

</details>

## IAM Policy Bindings

<details>
<summary>Click to expand IAM bindings</summary>

| Role | Members |
|------|---------|
| `roles/artifactregistry.serviceAgent` | serviceAccount:service-1053231822532@gcp-sa-artifactregistry.iam.gserviceaccount.com |
| `roles/cloudaicompanion.serviceAgent` | serviceAccount:service-1053231822532@gcp-sa-cloudaicompanion.iam.gserviceaccount.com |
| `roles/cloudbuild.builds.builder` | serviceAccount:1053231822532@cloudbuild.gserviceaccount.com |
| `roles/cloudbuild.serviceAgent` | serviceAccount:service-1053231822532@gcp-sa-cloudbuild.iam.gserviceaccount.com |
| `roles/cloudconfig.serviceAgent` | serviceAccount:service-1053231822532@gcp-sa-config.iam.gserviceaccount.com |
| `roles/cloudsql.admin` | serviceAccount:goog-sc-java-application-415@ppardyak-new-project.iam.gserviceaccount.com |
| `roles/compute.admin` | serviceAccount:goog-sc-java-application-415@ppardyak-new-project.iam.gserviceaccount.com |
| `roles/compute.serviceAgent` | serviceAccount:service-1053231822532@compute-system.iam.gserviceaccount.com |
| `roles/config.agent` | serviceAccount:goog-sc-java-application-415@ppardyak-new-project.iam.gserviceaccount.com |
| `roles/container.serviceAgent` | serviceAccount:service-1053231822532@container-engine-robot.iam.gserviceaccount.com |
| `roles/containeranalysis.ServiceAgent` | serviceAccount:service-1053231822532@container-analysis.iam.gserviceaccount.com |
| `roles/containerregistry.ServiceAgent` | serviceAccount:service-1053231822532@containerregistry.iam.gserviceaccount.com |
| `roles/editor` | serviceAccount:1053231822532-compute@developer.gserviceaccount.com, serviceAccount:1053231822532@cloudservices.gserviceaccount.com |
| `roles/file.editor` | serviceAccount:goog-sc-java-application-415@ppardyak-new-project.iam.gserviceaccount.com |
| `roles/file.serviceAgent` | serviceAccount:service-1053231822532@cloud-filer.iam.gserviceaccount.com |
| `roles/iam.serviceAccountAdmin` | serviceAccount:goog-sc-java-application-415@ppardyak-new-project.iam.gserviceaccount.com |
| `roles/iam.serviceAccountUser` | serviceAccount:goog-sc-java-application-415@ppardyak-new-project.iam.gserviceaccount.com |
| `roles/logging.admin` | serviceAccount:goog-sc-java-application-415@ppardyak-new-project.iam.gserviceaccount.com |
| `roles/monitoring.admin` | serviceAccount:goog-sc-java-application-415@ppardyak-new-project.iam.gserviceaccount.com |
| `roles/osconfig.serviceAgent` | serviceAccount:service-1053231822532@gcp-sa-osconfig.iam.gserviceaccount.com |
| `roles/owner` | user:ppardyak@google.com |
| `roles/pubsub.serviceAgent` | serviceAccount:service-1053231822532@gcp-sa-pubsub.iam.gserviceaccount.com |
| `roles/resourcemanager.projectIamAdmin` | serviceAccount:goog-sc-java-application-415@ppardyak-new-project.iam.gserviceaccount.com |
| `roles/run.serviceAgent` | serviceAccount:service-1053231822532@serverless-robot-prod.iam.gserviceaccount.com |
| `roles/secretmanager.admin` | serviceAccount:goog-sc-java-application-415@ppardyak-new-project.iam.gserviceaccount.com |
| `roles/servicenetworking.networksAdmin` | serviceAccount:goog-sc-java-application-415@ppardyak-new-project.iam.gserviceaccount.com |
| `roles/servicenetworking.serviceAgent` | serviceAccount:service-1053231822532@service-networking.iam.gserviceaccount.com |
| `roles/serviceusage.serviceUsageAdmin` | serviceAccount:goog-sc-java-application-415@ppardyak-new-project.iam.gserviceaccount.com |
| `roles/storage.admin` | serviceAccount:goog-sc-java-application-415@ppardyak-new-project.iam.gserviceaccount.com |
| `roles/storage.hmacKeyAdmin` | serviceAccount:goog-sc-java-application-415@ppardyak-new-project.iam.gserviceaccount.com |
| `roles/storage.objectAdmin` | serviceAccount:xwiki-jgroup-gce@ppardyak-new-project.iam.gserviceaccount.com |

</details>

## Resource Grouping by Application

Resources attributed to detected application groups:

### Application: `sudoku`

| Resource Type | Resource Name |
|---------------|---------------|
| Cloud Run | `sudoku` |
| Artifact Registry | `sudoku-repo` |

> [!TIP]
> All resources with the `sudoku-` or `sudoku_` prefix appear related. Deleting one may affect others in this group.

### Application: `test`

| Resource Type | Resource Name |
|---------------|---------------|
| Compute instance | `test-01` |
| Compute instance | `test-02` |

> [!TIP]
> All resources with the `test-` or `test_` prefix appear related. Deleting one may affect others in this group.

### Application: `xwiki`

| Resource Type | Resource Name |
|---------------|---------------|
| Cloud SQL | `xwiki-us-central1-db-gce` |
| Secret Manager | `xwiki-db-password` |
| Service account | `xwiki-jgroup-gce@ppardyak-new-project.iam.gserviceaccount.com` |
| Compute address | `xwiki-db-address-gce` |
| Compute address | `xwiki-lb-http-ip` |

> [!TIP]
> All resources with the `xwiki-` or `xwiki_` prefix appear related. Deleting one may affect others in this group.

## Cleanup Recommendations

### ✅ Likely Safe to Delete

- **Terminated compute instances** — not running, no cost
- **Empty storage buckets** — no data to lose
- **Auto-created resources** — default service accounts, blueprint buckets (will be recreated if needed)

### ⚠️ Investigate Before Deleting

- **Running compute instances** — may be serving traffic
- **Cloud SQL instances** — may contain application data
- **Secrets** — may be referenced by running applications
- **Storage buckets with data** — may contain important files
- **Custom service accounts** — may be used by running applications
- **Load balancer components** — may be serving traffic

### 📦 Related Resource Groups

The following application groups were detected. Resources within each group are likely related:

- **`sudoku`** — review all resources with this prefix before deleting any
- **`test`** — review all resources with this prefix before deleting any
- **`xwiki`** — review all resources with this prefix before deleting any

> [!WARNING]
> Deleting resources from one application group without removing all related resources may leave orphaned resources (e.g., a service account without its Cloud SQL instance, or a compute address without its forwarding rule).

---

_Generated by `audit_gcp_project.sh` on 2026-07-20T16:52:19Z by 
