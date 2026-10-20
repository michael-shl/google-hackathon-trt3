# Deployment Instructions — Grant Advisor (TRT3, Challenge 3)

> **GCP Project:** `qwiklabs-gcp-04-7254cc802c4d`
> **Region:** `us-central1`
> **Corridor:** Central Market, San Francisco
> **Components:** Terraform infra → Data pipeline → ADK Agent → Streamlit front end

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [Phase 1 — Infrastructure (Terraform)](#3-phase-1--infrastructure-terraform)
4. [Phase 2 — Data Pipeline](#4-phase-2--data-pipeline)
5. [Phase 3 — Deploy the Agent](#5-phase-3--deploy-the-agent)
6. [Phase 4 — Deploy Grant Desk (Front End)](#6-phase-4--deploy-grant-desk-front-end)
7. [Verification Checklist](#7-verification-checklist)
8. [Running Locally](#8-running-locally)
9. [Rollback](#9-rollback)
10. [Troubleshooting](#10-troubleshooting)
11. [Reference](#11-reference)

---

## 1. Overview

The system consists of **four private Cloud Run services** and a BigQuery property graph:

```
┌────────────────┐     ID token     ┌─────────────────┐     tool calls     ┌──────────────┐
│  Grant Desk    │ ──────────────►  │  grant-advisor   │ ──────────────────►│  MCP Toolbox │
│  (Streamlit)   │                  │  (ADK 2.12)      │                    │  (managed)   │
│  port 8501     │                  │  port 8080       │                    │  port 443    │
└────────────────┘                  │                  │                    └──────────────┘
                                    │  Custom tools:   │
                                    │  get_cascade     │──── GQL MATCH ────►  BigQuery
                                    │  rank_applicants │                      a4i_econ.LocalEconomy
                                    │  equity_audit    │
                                    │  build_grant_memo│
                                    └─────────────────┘
```

**Deploy order matters:** Terraform → Data → Agent → Grant Desk. Each phase depends on the previous one.

---

## 2. Prerequisites

| Requirement | Details |
|---|---|
| **GCP Project** | `qwiklabs-gcp-04-7254cc802c4d` (Owner access via Qwiklabs) |
| **gcloud CLI** | [Install](https://cloud.google.com/sdk/docs/install) v450+ |
| **Terraform** | v1.5+ (pre-installed in Cloud Shell) |
| **Python** | 3.11+ |
| **ADK** | `google-adk[toolbox]>=2.12` (installed in `agent/.venv`) |
| **bq CLI** | Bundled with gcloud SDK |

### Authenticate

```bash
# Cloud Shell — already authenticated. Just set the project:
gcloud config set project qwiklabs-gcp-04-7254cc802c4d

# Laptop — use a separate gcloud config (keeps your work account untouched):
export CLOUDSDK_CONFIG=~/.config/gcloud-hackathon
export GOOGLE_APPLICATION_CREDENTIALS=$CLOUDSDK_CONFIG/application_default_credentials.json
gcloud auth login                          # Qwiklabs student account
gcloud auth application-default login      # for Vertex AI / ADK
gcloud config set project qwiklabs-gcp-04-7254cc802c4d
```

---

## 3. Phase 1 — Infrastructure (Terraform)

> **Owner:** P5 (Platform)
> **State:** `gs://qwiklabs-gcp-04-7254cc802c4d-tfstate/trt3` (versioned, locked during apply)

Terraform creates 32 resources: 13 GCP APIs, 3 service accounts (`toolbox-identity`, `grant-advisor`, `grant-desk`), IAM bindings, a Secret Manager secret for Toolbox config, and the MCP Toolbox Cloud Run service.

### 3.1 Apply

```bash
cd terraform
terraform init
terraform plan                # review changes
terraform apply               # confirm with 'yes'
```

### 3.2 Verify Toolbox

```bash
# Get the Toolbox URL
TOOLBOX_URL=$(terraform output -raw toolbox_url)
echo "Toolbox: ${TOOLBOX_URL}"

# Smoke-test via MCP protocol (Toolbox v1.x returns 410 on the old /api/toolset endpoint)
curl -s -X POST "${TOOLBOX_URL}/mcp" \
  -H 'content-type: application/json' \
  -H 'accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | head -c 400; echo
```

Expected: JSON response listing 5 tools (`find_business`, `list_applicants`, `get_neighborhood`, `get_loan_history`, `corridor_industry_mix`).

### 3.3 Key Variables (`terraform.tfvars`)

| Variable | Default | Notes |
|---|---|---|
| `manage_bigquery_foundation` | `false` | Set `true` only if applying **before** `load.sh`, or after `terraform import` |
| `toolbox_public` | `true` | Hackathon trade-off; read-only queries over public data |
| `agent_can_write_bigquery` | `false` | Only for the intake-agent stretch goal |
| `grant_build_roles` | `true` | Gives Compute default SA the roles `adk deploy` needs |

> [!IMPORTANT]
> If `terraform apply` fails with `Error 403 ... SERVICE_DISABLED`, APIs take ~1 minute to propagate. Simply run `terraform apply` again.

---

## 4. Phase 2 — Data Pipeline

> **Owner:** P2 (Data)

### 4.1 Load tables from Cloud Storage snapshot

```bash
# From the repo root, in Cloud Shell:
bash scripts/load.sh                    # defaults to 'central-market'
bash scripts/load.sh 24th-st            # or another corridor
bash scripts/load.sh --list             # list available corridors
```

This creates/reuses the BigQuery dataset `a4i_econ` (location: `US`), an Enterprise reservation `a4i-graph` (0 baseline → 50 autoscale slots), and loads 6 tables from Parquet:

| Table | Type |
|---|---|
| `businesses` | Real (Google Places) |
| `employer_blocks` | Real (LEHD) |
| `supplies` | **Modeled** (BEA direct requirements) |
| `draws_footfall_from` | **Modeled** (LEHD jobs allocated) |
| `borrowed_from` | Real (SBA loans, optional) |
| `tract_demographics` | Real (ACS) |

> [!NOTE]
> Safe to re-run at any time — every table load uses `--replace`.

### 4.2 Create the property graph and derived tables

Run the SQL scripts **in order** after every data load:

```bash
P=qwiklabs-gcp-04-7254cc802c4d

# 1. Property graph (LocalEconomy)
bq --project_id=$P query --use_legacy_sql=false < sql/01_property_graph.sql

# 2. Business need scores (from ACS tract demographics)
bq --project_id=$P query --use_legacy_sql=false < sql/02_business_need.sql

# 3. Simulated applicant pool (11 applications from real businesses)
bq --project_id=$P query --use_legacy_sql=false < sql/03_applicants.sql
```

### 4.3 Verify the graph has depth

```bash
bq --project_id=$P query --use_legacy_sql=false \
  "SELECT COUNT(DISTINCT a.supplier_id)
   FROM \`$P.a4i_econ.supplies\` a
   JOIN \`$P.a4i_econ.supplies\` b ON b.supplier_id = a.buyer_id
   WHERE b.buyer_id != a.supplier_id"
```

Expected: **≥ 86** businesses that reach someone two hops out. If this is 0, the graph loads fine but cascade queries return nothing.

---

## 5. Phase 3 — Deploy the Agent

> **Owner:** P5 (Platform) / P1 (Agent)
> **Service:** `grant-advisor` on Cloud Run
> **Service Account:** `grant-advisor@qwiklabs-gcp-04-7254cc802c4d.iam.gserviceaccount.com`
> **Access:** Private (`--no-allow-unauthenticated`), accessed via `gcloud run services proxy`

### 5.1 Set up the Python environment

```bash
cd agent
python3 -m venv .venv && source .venv/bin/activate
pip install -r grant_advisor/requirements.txt
```

### 5.2 Deploy to Cloud Run

```bash
# From the repo root, with agent/.venv activated:

# Option A — Mock mode (works before data lane finishes)
bash scripts/deploy_agent.sh mock

# Option B — Real mode (requires Phase 2 complete + Toolbox running)
bash scripts/deploy_agent.sh real
```

**What the script does:**
1. Verifies `adk` is on PATH
2. In `real` mode, discovers the Toolbox Cloud Run URL
3. Runs `adk deploy cloud_run` with environment variables:
   - `GOOGLE_GENAI_USE_VERTEXAI=TRUE`
   - `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`
   - `BQ_DATASET=a4i_econ`, `BQ_GRAPH=LocalEconomy`
   - `USE_MOCK_DATA=true|false`
   - `TOOLBOX_URL` (real mode only)
4. Deploys as `grant-advisor` with `--min-instances=1` (no cold starts)

### 5.3 Access the agent

```bash
gcloud run services proxy grant-advisor --region us-central1 --port 8080
# → http://localhost:8080  (ADK Dev UI)
```

> [!TIP]
> The proxy rewrites `Host` to `*.run.app`, so ADK's origin check must allow localhost. The deploy script sets `ALLOW_ORIGINS` to `regex:http://(localhost|127\.0\.0\.1):\d+` by default.

---

## 6. Phase 4 — Deploy Grant Desk (Front End)

> **Owner:** P5 (Platform)
> **Service:** `grant-desk` on Cloud Run
> **Service Account:** `grant-desk@qwiklabs-gcp-04-7254cc802c4d.iam.gserviceaccount.com`
> **Access:** Private, accessed via `gcloud run services proxy`

### 6.1 Deploy

```bash
# From the repo root (requires grant-advisor to be deployed first):
bash scripts/deploy_desk.sh
```

**What the script does:**
1. Discovers the `grant-advisor` Cloud Run URL
2. Runs `gcloud run deploy --source frontend/grant_desk/`
3. Sets `AGENT_URL` to the private agent URL
4. Configures: `--min-instances 1`, `--max-instances 1`, `--session-affinity`, `--timeout 3600`, `--memory 1Gi`

### 6.2 Access Grant Desk

```bash
gcloud run services proxy grant-desk --region us-central1 --port 8501
# → http://localhost:8501
```

---

## 7. Verification Checklist

Run through this after a full deployment:

| # | Check | Command / Action | Expected |
|---|---|---|---|
| 1 | Terraform state | `cd terraform && terraform plan` | `No changes. Infrastructure is up-to-date.` |
| 2 | Toolbox tools | `curl -s -X POST "$(terraform output -raw toolbox_url)/mcp" -H 'content-type: application/json' -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'` | 5 tools listed |
| 3 | BigQuery tables | `bq ls a4i_econ` | 6+ tables |
| 4 | Graph depth | See [§4.3](#43-verify-the-graph-has-depth) | ≥ 86 |
| 5 | Agent responds | Open `http://localhost:8080`, type: *"I have $50,000. Who should we fund?"* | Ranked applicant list with cascade analysis |
| 6 | Grant Desk loads | Open `http://localhost:8501` | 4-panel UI with data source badge (🟢 BigQuery or 🟠 MOCK) |
| 7 | Memo generation | In Grant Desk, click through to memo | 7-section Grant Memo with Graphviz cascade picture |
| 8 | Cloud Run revisions | `gcloud run revisions list --service=grant-advisor --region=us-central1` | Active revision with traffic = 100% |
| 9 | Logs clean | `gcloud run services logs read grant-advisor --region=us-central1 --limit=20` | No ERROR-level entries |

---

## 8. Running Locally

### Agent (mock data, no cloud services needed for tools)

```bash
cd agent
source .venv/bin/activate
cp grant_advisor/.env.example grant_advisor/.env    # USE_MOCK_DATA=true by default
gcloud auth application-default login               # Gemini via Vertex AI
adk web                                              # http://localhost:8000 → grant_advisor
```

### Agent (real data, local Toolbox)

```bash
# Edit grant_advisor/.env:
#   USE_MOCK_DATA=false
#   TOOLBOX_URL=http://127.0.0.1:5000   (or the Cloud Run URL)
adk web
```

### Grant Desk (against deployed agent)

```bash
gcloud run services proxy grant-advisor --region us-central1 --port 8080 &
cd frontend/grant_desk
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
AGENT_URL=http://localhost:8080 streamlit run app.py   # http://localhost:8501
```

### Grant Desk (against local `adk web`)

```bash
AGENT_URL=http://localhost:8000 streamlit run app.py
```

### Tests

```bash
# Agent tests (offline, mock corridor)
cd agent && pytest ../tests -q

# Grant Desk tests
pytest tests/test_grant_desk.py -q
```

---

## 9. Rollback

### Agent — redeploy a previous revision

```bash
# List revisions
gcloud run revisions list --service=grant-advisor --region=us-central1

# Route traffic to a specific revision
gcloud run services update-traffic grant-advisor \
  --to-revisions=<REVISION_NAME>=100 \
  --region=us-central1

# Or re-deploy mock mode as a fallback
bash scripts/deploy_agent.sh mock
```

### Grant Desk — redeploy

```bash
gcloud run revisions list --service=grant-desk --region=us-central1

gcloud run services update-traffic grant-desk \
  --to-revisions=<REVISION_NAME>=100 \
  --region=us-central1
```

### Toolbox — revert secret version

If a bad `tools.yaml` was applied:

```bash
# List secret versions
gcloud secrets versions list tools

# Disable the broken version
gcloud secrets versions disable <VERSION_NUMBER> --secret=tools

# Enable the previous good version
gcloud secrets versions enable <PREV_VERSION_NUMBER> --secret=tools

# Redeploy Toolbox to pick up the change
cd terraform && terraform apply
```

### Data — reload tables

```bash
# Safe to re-run, every load uses --replace
bash scripts/load.sh central-market

# Then re-run the SQL scripts
bq query --use_legacy_sql=false < sql/01_property_graph.sql
bq query --use_legacy_sql=false < sql/02_business_need.sql
bq query --use_legacy_sql=false < sql/03_applicants.sql
```

---

## 10. Troubleshooting

### Infrastructure

| Symptom | Cause | Fix |
|---|---|---|
| `Error 403 ... SERVICE_DISABLED` on `terraform apply` | APIs need ~1 min to propagate | Run `terraform apply` again |
| `allUsers` binding rejected | Org policy blocks public access | Set `toolbox_public = false` in `terraform.tfvars`, use authenticated Toolbox client |
| `adk deploy` build fails with permission errors | Missing IAM roles on Compute default SA | Confirm `grant_build_roles = true` was applied; wait 1–2 min for IAM propagation |
| Toolbox revision fails to start | Bad YAML syntax in `tools.yaml` | `gcloud run services logs read toolbox --region us-central1 --limit 50` |

### Data

| Symptom | Cause | Fix |
|---|---|---|
| *"requires a reservation with Enterprise…"* | Reservation assignment takes ~1 min | Wait, or re-run `bash scripts/load.sh central-market` |
| Graph depth = 0 | `supplies` table is empty or IDs don't chain | Re-run `load.sh`, then re-run all 3 SQL scripts in order |
| `load.sh` can't find corridor | Typo or unavailable snapshot | `bash scripts/load.sh --list` to see available corridors |

### Agent

| Symptom | Cause | Fix |
|---|---|---|
| `adk not found` | venv not activated | `source agent/.venv/bin/activate` |
| ADK Dev UI loads blank (403) | Origin not allowed | Check `ALLOW_ORIGINS` env var; deploy script sets localhost regex by default |
| Agent returns empty cascades in real mode | Graph not created or SQL scripts not run | Run `sql/01` → `sql/03` in order |
| Toolbox tools not available | `TOOLBOX_URL` not set or Toolbox service down | Check `terraform output toolbox_url`; verify service is running |

### Grant Desk

| Symptom | Cause | Fix |
|---|---|---|
| `grant-advisor not found` error from `deploy_desk.sh` | Agent not deployed yet | Run `scripts/deploy_agent.sh` first |
| Desk shows 🟠 MOCK instead of 🟢 BigQuery | Agent running in mock mode | Redeploy agent: `bash scripts/deploy_agent.sh real` |
| WebSocket disconnects | Session affinity not configured | Verify `--session-affinity` flag in deploy (set by `deploy_desk.sh`) |

### Viewing Logs

```bash
# Agent logs
gcloud run services logs read grant-advisor --region=us-central1 --limit=50

# Grant Desk logs
gcloud run services logs read grant-desk --region=us-central1 --limit=50

# Toolbox logs
gcloud run services logs read toolbox --region=us-central1 --limit=50

# Stream live logs
gcloud run services logs tail grant-advisor --region=us-central1
```

---

## 11. Reference

### Deploy Order (Quick Reference)

```bash
# 1. Infrastructure
cd terraform && terraform init && terraform apply

# 2. Data
bash scripts/load.sh central-market
bq query --use_legacy_sql=false < sql/01_property_graph.sql
bq query --use_legacy_sql=false < sql/02_business_need.sql
bq query --use_legacy_sql=false < sql/03_applicants.sql

# 3. Agent
cd agent && source .venv/bin/activate
bash scripts/deploy_agent.sh real

# 4. Front End
bash scripts/deploy_desk.sh

# 5. Access
gcloud run services proxy grant-advisor --region us-central1 --port 8080
gcloud run services proxy grant-desk --region us-central1 --port 8501
```

### Service Accounts

| Service Account | Cloud Run Service | Key Roles |
|---|---|---|
| `toolbox-identity` | `toolbox` | BigQuery `jobUser` + `dataViewer`, Secret Manager accessor |
| `grant-advisor` | `grant-advisor` | Vertex AI `user`, BigQuery `jobUser` + `dataViewer`, `run.invoker` on Toolbox |
| `grant-desk` | `grant-desk` | `run.invoker` (calls private agent), `logging.logWriter` |

### Environment Variables

| Variable | Service | Values |
|---|---|---|
| `GOOGLE_GENAI_USE_VERTEXAI` | agent | `TRUE` |
| `GOOGLE_CLOUD_PROJECT` | agent | `qwiklabs-gcp-04-7254cc802c4d` |
| `GOOGLE_CLOUD_LOCATION` | agent | `us-central1` |
| `USE_MOCK_DATA` | agent | `true` / `false` |
| `BQ_DATASET` | agent | `a4i_econ` |
| `BQ_GRAPH` | agent | `LocalEconomy` |
| `TOOLBOX_URL` | agent | Cloud Run URL of Toolbox service |
| `AGENT_URL` | grant-desk | Cloud Run URL of agent service |
| `GRANT_ADVISOR_MODEL` | agent | `gemini-2.5-flash` |

### Key File Paths

| File | Purpose |
|---|---|
| [`terraform/`](../terraform/) | Infrastructure as code (APIs, SAs, IAM, Toolbox) |
| [`terraform/terraform.tfvars`](../terraform/terraform.tfvars) | Project-specific config |
| [`toolbox/tools.yaml`](../toolbox/tools.yaml) | MCP Toolbox tool definitions |
| [`scripts/load.sh`](../scripts/load.sh) | Data pipeline (Cloud Storage → BigQuery) |
| [`sql/01_property_graph.sql`](../sql/01_property_graph.sql) | `LocalEconomy` property graph DDL |
| [`sql/02_business_need.sql`](../sql/02_business_need.sql) | Business need scores from ACS |
| [`sql/03_applicants.sql`](../sql/03_applicants.sql) | Simulated applicant pool |
| [`scripts/deploy_agent.sh`](../scripts/deploy_agent.sh) | Agent deployment (ADK → Cloud Run) |
| [`scripts/deploy_desk.sh`](../scripts/deploy_desk.sh) | Grant Desk deployment (Streamlit → Cloud Run) |
| [`agent/grant_advisor/.env.example`](../agent/grant_advisor/.env.example) | Agent env template |
| [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) | System architecture |
| [`docs/DATA_SOURCES.md`](DATA_SOURCES.md) | Data provenance (real vs. modeled) |

### External Links

| Resource | URL |
|---|---|
| ADK Documentation | https://google.github.io/adk-docs/ |
| MCP Toolbox for Databases | https://github.com/googleapis/mcp-toolbox |
| BigQuery Property Graphs | https://cloud.google.com/bigquery/docs/property-graph |
| Cloud Run Documentation | https://cloud.google.com/run/docs |
| Terraform GCP Provider | https://registry.terraform.io/providers/hashicorp/google/latest/docs |

---

> **Cleanup:** The Qwiklabs project is deleted when the lab ends. `terraform destroy` is not needed.

*Last updated: 2026-10-20*
