# Terraform: team infrastructure for `qwiklabs-gcp-04-7254cc802c4d`

**Owner: P5 (Platform).** State lives in `gs://qwiklabs-gcp-04-7254cc802c4d-tfstate/trt3` (versioned, locked during
apply), so it can run from Cloud Shell or a laptop, but from one place at a time.

**Status (applied 2026-10-20):** 32 resources created. Toolbox: `https://toolbox-7sw2gxdyba-uc.a.run.app` (5 MCP tools).
Agent: `grant-advisor` deployed in **mock** mode via `scripts/deploy_agent.sh mock`.

## What Terraform creates

| Resource | Name | Why we need it |
|---|---|---|
| 13 APIs | Vertex AI, BigQuery (+ Reservation, Storage), Cloud Run, Cloud Build, Artifact Registry, Secret Manager, IAM, Logging, Storage | Gemini, graph queries, deployments |
| Service account | `toolbox-identity` | Runs MCP Toolbox: BigQuery `jobUser` + `dataViewer`, Secret Manager accessor on `tools` only |
| Service account | `grant-advisor` | Runs the ADK agent: Vertex AI `user`, BigQuery `jobUser` + `dataViewer` (`dataEditor` if `agent_can_write_bigquery`), invoker on Toolbox |
| IAM for Compute default SA | `run.builder`, `artifactregistry.writer`, … | `adk deploy cloud_run` builds from source with this account; new projects often lack these roles |
| Secret | `tools` | `../toolbox/tools.yaml`; every edit becomes a new version and redeploys Toolbox |
| Cloud Run service | `toolbox` | **Google-managed MCP server** (challenge requirement), `min_instance_count=1` (no cold start on stage) |
| Cloud Run IAM | `allUsers` invoker (toggle `toolbox_public`) | Hackathon trade-off: fixed read-only queries over public data |
| *(optional)* BigQuery dataset | `a4i_econ` (US) | Only if `manage_bigquery_foundation = true` |
| *(optional)* Reservation + assignment | `a4i-graph`, Enterprise, 0 baseline → 50 autoscale, project `QUERY` | Graph (GQL) queries require it. Only if `manage_bigquery_foundation = true` |

## What Terraform intentionally does NOT manage

| Thing | Managed by | Why not Terraform |
|---|---|---|
| Tables in `a4i_econ` | `scripts/load.sh` (P2) | Replaced on every load; Terraform would fight it |
| Dataset + reservation (default) | `scripts/load.sh` | load.sh already creates/reuses them idempotently |
| Property graph `LocalEconomy`, `business_tract`, `applicants` | `sql/*.sql` (P2) | DDL over data that changes; must re-run after loads |
| Agent Cloud Run service `grant-advisor` | [`scripts/deploy_agent.sh`](../scripts/deploy_agent.sh) (`adk deploy cloud_run`) | ADK builds the container from source on each deploy |
| The GCP project itself | Qwiklabs | Provided per team; we have Owner, no billing setup needed |

## Run it (as the Qwiklabs student account)

**Cloud Shell:** Terraform and credentials are already there.
**Laptop:** use a separate gcloud config so your work account is untouched (zsh: don't paste `#` comments):
```bash
export CLOUDSDK_CONFIG=~/.config/gcloud-hackathon
export GOOGLE_APPLICATION_CREDENTIALS=$CLOUDSDK_CONFIG/application_default_credentials.json
```
(after `gcloud auth login` + `gcloud auth application-default login` as the student once).

```bash
cd ~/google-hackathon-trt3/terraform
gcloud config set project qwiklabs-gcp-04-7254cc802c4d
terraform init
terraform plan
terraform apply
terraform output toolbox_url
```

Smoke-test Toolbox over MCP (Toolbox v1.x disables the old `/api/toolset` endpoint; it returns 410):
```bash
curl -s -X POST "$(terraform output -raw toolbox_url)/mcp" \
  -H 'content-type: application/json' -H 'accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | head -c 400; echo
```

Deploy the agent (from the repo root, with `agent/.venv` active):
```bash
bash scripts/deploy_agent.sh mock     # mock corridor (works before the data lane finishes)
bash scripts/deploy_agent.sh real     # BigQuery + graph + MCP Toolbox
gcloud run services proxy grant-advisor --region us-central1 --port 8080    # then http://localhost:8080
```
The agent service is private (`--no-allow-unauthenticated`); the proxy uses your gcloud login.

## Common changes

- **Edited `toolbox/tools.yaml`** → `terraform apply` (new secret version + new Toolbox revision).
- **Make Toolbox private** → `toolbox_public = false` in `terraform.tfvars`, then in the agent use
  `ToolboxToolset(server_url=..., credentials=CredentialStrategy.workload_identity(target_audience=TOOLBOX_URL))`.
- **Intake-agent stretch writes edges** → `agent_can_write_bigquery = true`.

## Let Terraform own the dataset + reservation (optional)

- **Before `load.sh` has ever run:** set `manage_bigquery_foundation = true` and apply; load.sh then reuses them.
- **After `load.sh` ran** (likely): import first, then apply.
  ```bash
  P=qwiklabs-gcp-04-7254cc802c4d
  terraform import -var manage_bigquery_foundation=true 'google_bigquery_dataset.a4i[0]' "projects/$P/datasets/a4i_econ"
  terraform import -var manage_bigquery_foundation=true 'google_bigquery_reservation.graph[0]' "projects/$P/locations/US/reservations/a4i-graph"
  bq ls --reservation_assignment --location=US --project_id=$P     # copy the assignment ID
  terraform import -var manage_bigquery_foundation=true 'google_bigquery_reservation_assignment.graph[0]' \
    "projects/$P/locations/US/reservations/a4i-graph/assignments/<ASSIGNMENT_ID>"
  ```
  Then set `manage_bigquery_foundation = true` in `terraform.tfvars`.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Error 403 ... SERVICE_DISABLED` on first apply | APIs take a minute to propagate. Run `terraform apply` again |
| `allUsers` binding rejected (org policy) | Set `toolbox_public = false` and use the authenticated client (above) |
| `adk deploy` build fails with permission errors | Confirm `grant_build_roles = true` was applied; wait 1–2 min for IAM propagation, retry |
| Toolbox revision fails to start | `gcloud run services logs read toolbox --region us-central1 --limit 50`; usually YAML syntax in `tools.yaml` |
| Graph query: *"requires a reservation with Enterprise…"* | Reservation assignment takes ~1 min; or run `bash scripts/load.sh central-market` |

**Cleanup:** the Qwiklabs project is deleted when the lab ends. `terraform destroy` is not needed.
