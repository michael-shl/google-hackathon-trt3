# Grant Desk: the officer-facing front end (owner: P5)

A one-page Streamlit app over the `grant_advisor` agent. It sends plain-language requests to the
agent's API and draws its panels from the agent's **own tool responses**, so every table and
picture is backed by the multi-hop graph traversal, not re-computed in the UI.

| Panel | Built from |
|---|---|
| 1 · Funding queue (budget, allocation, ★ pick, runner-up, hub flag, sensitivity) | `rank_applicants` |
| 2 · Cascade it protects (Graphviz picture + path table) | `get_cascade` |
| 3 · Grant Memo (7 sections + picture + download) | `build_grant_memo` |
| 4 · Ask the advisor (free text) + "Agent tool calls" trace | any tool |

**Data source badge** (sidebar + under the title): 🟢 `BigQuery <project>.a4i_econ · real`,
🟢 `… (MCP Toolbox)` for Toolbox lookups, 🟠 `MOCK corridor` for the test corridor. It is read from the
`data_source` field that every tool response carries, so it shows what the agent actually used.

**Why not ship `adk web`?** Our user is an internal grant officer deciding a funding queue, not a
developer reading an event log. The Dev UI stays available as the debugging view and demo fallback.

## Run locally

```bash
export CLOUDSDK_CONFIG=~/.config/gcloud-hackathon            # laptop only: lab student login
gcloud run services proxy grant-advisor --region us-central1 --port 8080 &
cd frontend/grant_desk
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
AGENT_URL=http://localhost:8080 streamlit run app.py         # http://localhost:8501
```
`AGENT_URL` can also be `http://localhost:8000` for a local `adk web`.

## Deployed (private Cloud Run service `grant-desk`)

```bash
bash scripts/deploy_desk.sh
gcloud run services proxy grant-desk --region us-central1 --port 8501     # then http://localhost:8501
```
Runs as service account `grant-desk` (Terraform) with `roles/run.invoker`, and calls the private agent
with an ID token from the metadata server. 1–3 instances, 250 concurrent requests each, session
affinity and a 15-minute timeout. Each open tab holds a websocket; the old 1 × 80 limit caused
"Rate exceeded" (429) once stale websockets filled the slots.

**Access:** the agent is private. The desk currently has Cloud Run's *allow public access* enabled
(`invoker-iam-disabled=true`, set in the console) so the deck link opens without a login. Turn it off
with `gcloud run services update grant-desk --region us-central1 --invoker-iam-check`.

Tests: `pytest tests/test_grant_desk.py -q` (event parsing, cascade picture, queue rows).
