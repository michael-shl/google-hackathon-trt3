#!/usr/bin/env bash
#
# Deploy the Grant Desk (Streamlit) to Cloud Run as a private service (owner: P5).
#
#   bash scripts/deploy_desk.sh
#   gcloud run services proxy grant-desk --region us-central1 --port 8501   ->  http://localhost:8501
#
# It calls the private grant-advisor service with an ID token for the grant-desk service account
# (roles/run.invoker, created by terraform). One instance with session affinity and a long request
# timeout, because Streamlit keeps each browser session in memory over a websocket.

set -euo pipefail

PROJECT="${PROJECT_ID:-qwiklabs-gcp-04-7254cc802c4d}"
REGION="${REGION:-us-central1}"
SA="grant-desk@${PROJECT}.iam.gserviceaccount.com"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

AGENT_URL="$(gcloud run services describe grant-advisor --project "${PROJECT}" --region "${REGION}" \
             --format='value(status.url)')"
[[ -n "${AGENT_URL}" ]] || { echo "grant-advisor not found: run scripts/deploy_agent.sh first" >&2; exit 1; }

echo "Deploying grant-desk -> ${AGENT_URL}"
gcloud run deploy grant-desk --source "${ROOT}/frontend/grant_desk" \
  --project "${PROJECT}" --region "${REGION}" --service-account "${SA}" \
  --set-env-vars "AGENT_URL=${AGENT_URL}" \
  --no-allow-unauthenticated --min-instances 1 --max-instances 1 \
  --session-affinity --timeout 3600 --memory 1Gi --quiet

echo
echo "Open it with:"
echo "  gcloud run services proxy grant-desk --project ${PROJECT} --region ${REGION} --port 8501"
echo "  then http://localhost:8501"
