# GCP Project Audit: `ppardyak-cad`

| Field | Value |
|-------|-------|
| Project ID | `ppardyak-cad` |
| Project Name | ppardyak -- CaD |
| Project Number | 295092059542 |
| Lifecycle State | ACTIVE |
| Created | 2021-06-18T21:40:13.865Z |
| Audit Date | 2026-07-20T16:53:09Z |
| Audited By | ppardyak@google.com |

## Summary

| Resource Type | Count |
|---------------|-------|
| Enabled APIs | 42 |
| Cloud Run services | 0 |
| Artifact Registry repos | 0 |
| Compute instances | 0 |
| Compute backend services | 0 |
| Compute URL maps | 0 |
| Compute forwarding rules | 0 |
| Compute addresses | 0 |
| Compute SSL certificates | 0 |
| Compute NEGs | 0 |
| Compute disks | 0 |
| Compute images | 0 |
| Compute snapshots | 0 |
| Compute firewall rules | 4 |
| Compute networks | 1 |
| Service accounts | 1 |
| Storage buckets | 2 |
| IAP brands | 0 |
| Cloud Build triggers | 0 |
| Cloud Functions | 0 |
| GKE clusters | 0 |
| BigQuery datasets | 0 |
| Pub/Sub topics | 0 |
| Cloud SQL instances | 0 |
| Secret Manager secrets | 0 |
| DNS zones | 0 |

## Cloud Run Services

_No Cloud Run services found._

## Artifact Registry Repositories

_No Artifact Registry repositories found._

## Compute Instances

_No compute instances found._

## Cloud SQL Instances

_No Cloud SQL instances found._

## Secret Manager Secrets

_No secrets found._

## Storage Buckets

| Name | Location | Size | Classification | Assessment |
|------|----------|------|----------------|------------|
| `295092059542-us-central1-blueprint-config` | US-CENTRAL1 | 0 | auto-created | ✅ Safe to delete (empty bucket) |
| `ppardyak-cad_blueprints` | US | 7.0K | other | ⚠️ Investigate — bucket has data (size:7108) |

## Service Accounts

| Email | Display Name | Classification | Assessment |
|-------|-------------|----------------|------------|
| `295092059542-compute@developer.gserviceaccount.com` | Compute Engine default service account | auto-created | ✅ Auto-created default SA (will be recreated if needed) |

## Compute Addresses

_No compute addresses found._

## Load Balancer Components

_No load balancer components found._

## Network Endpoint Groups (NEGs)

_No NEGs found._

## Compute Disks

_No compute disks found._

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

_No IAP brands found (IAP API may not be enabled)._

## VPC Networks

| Name | Auto-create Subnetworks | Classification |
|------|------------------------|----------------|
| `default` | true | other |

## Firewall Rules

| Name | Direction | Priority | Classification |
|------|-----------|----------|----------------|
| `default-allow-icmp` | INGRESS | 65534 | other |
| `default-allow-internal` | INGRESS | 65534 | other |
| `default-allow-rdp` | INGRESS | 65534 | other |
| `default-allow-ssh` | INGRESS | 65534 | other |

## Enabled APIs

<details>
<summary>Click to expand (42 APIs enabled)</summary>

```
artifactregistry.googleapis.com          Artifact Registry API
autoscaling.googleapis.com               Cloud Autoscaling API
bcidcloudenforcer-pa.googleapis.com      BCID Cloud Enforcer Private API
bigquery.googleapis.com                  BigQuery API
bigquerystorage.googleapis.com           BigQuery Storage API
cloudapis.googleapis.com                 Google Cloud APIs
cloudbuild.googleapis.com                Cloud Build API
cloudtrace.googleapis.com                Cloud Trace API
compute.googleapis.com                   Compute Engine API
computescanning.googleapis.com           Compute Scanning API
config.googleapis.com                    Infrastructure Manager API
containeranalysis.googleapis.com         Container Analysis API
container.googleapis.com                 Kubernetes Engine API
containerregistry.googleapis.com         Container Registry API
containerscanning.googleapis.com         Container Scanning API
containerthreatdetection.googleapis.com  Container Threat Detection API
datastore.googleapis.com                 Cloud Datastore API
dns.googleapis.com                       Cloud DNS API
gkebackup.googleapis.com                 Backup for GKE API
gkeconnect.googleapis.com                GKE Connect API
gkehub.googleapis.com                    GKE Hub API
iamcredentials.googleapis.com            IAM Service Account Credentials API
iam.googleapis.com                       Identity and Access Management (IAM) API
krmapihosting.googleapis.com             KRM API Hosting API
logging.googleapis.com                   Cloud Logging API
monitoring.googleapis.com                Cloud Monitoring API
multiclustermetering.googleapis.com      Multi cluster metering API
NAME                                     TITLE
networkconnectivity.googleapis.com       Network Connectivity API
notebooksecurityscanner.googleapis.com   Notebook Security Scanner API
osconfig.googleapis.com                  OS Config API
oslogin.googleapis.com                   Cloud OS Login API
pubsub.googleapis.com                    Cloud Pub/Sub API
servicemanagement.googleapis.com         Service Management API
serviceusage.googleapis.com              Service Usage API
sourcerepo.googleapis.com                Cloud Source Repositories API
sql-component.googleapis.com             Cloud SQL
storage-api.googleapis.com               Google Cloud Storage JSON API
storage-component.googleapis.com         Cloud Storage
storage.googleapis.com                   Cloud Storage API
telemetry.googleapis.com                 Telemetry API
websecurityscanner.googleapis.com        Web Security Scanner API
```

</details>

## IAM Policy Bindings

<details>
<summary>Click to expand IAM bindings</summary>

| Role | Members |
|------|---------|
| `roles/cloudbuild.builds.builder` | serviceAccount:295092059542@cloudbuild.gserviceaccount.com |
| `roles/cloudbuild.serviceAgent` | serviceAccount:service-295092059542@gcp-sa-cloudbuild.iam.gserviceaccount.com |
| `roles/cloudconfig.serviceAgent` | serviceAccount:service-295092059542@gcp-sa-config.iam.gserviceaccount.com |
| `roles/compute.serviceAgent` | serviceAccount:service-295092059542@compute-system.iam.gserviceaccount.com |
| `roles/container.clusterViewer` | serviceAccount:295092059542@cloudbuild.gserviceaccount.com |
| `roles/container.developer` | serviceAccount:295092059542@cloudbuild.gserviceaccount.com |
| `roles/container.serviceAgent` | serviceAccount:service-295092059542@container-engine-robot.iam.gserviceaccount.com |
| `roles/containerregistry.ServiceAgent` | serviceAccount:service-295092059542@containerregistry.iam.gserviceaccount.com |
| `roles/editor` | serviceAccount:295092059542-compute@developer.gserviceaccount.com, serviceAccount:295092059542@cloudservices.gserviceaccount.com |
| `roles/krmapihosting.serviceAgent` | serviceAccount:service-295092059542@gcp-sa-krmapihosting.iam.gserviceaccount.com |
| `roles/owner` | serviceAccount:service-295092059542@gcp-sa-yakima.iam.gserviceaccount.com, user:ppardyak@google.com |
| `roles/pubsub.serviceAgent` | serviceAccount:service-295092059542@gcp-sa-pubsub.iam.gserviceaccount.com |

</details>

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

_No application groups detected (all resources appear to be auto-created or unclassified)._

---

_Generated by `audit_gcp_project.sh` on 2026-07-20T16:53:09Z by 
