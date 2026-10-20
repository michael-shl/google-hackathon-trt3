#!/usr/bin/env bash
#
# Deploy the grant_advisor ADK agent to Cloud Run (owner: P5).
#
#   bash scripts/deploy_agent.sh mock    # mock corridor, local lookup tools (pipeline test / demo fallback)
#   bash scripts/deploy_agent.sh real    # BigQuery + LocalEconomy graph + MCP Toolbox (default)
#
# Needs: adk on PATH (activate agent/.venv), gcloud signed in to the lab project, and
# `terraform apply` done (service account grant-advisor + Cloud Run service toolbox).
# The service is private; open it with:
#   gcloud run services proxy grant-advisor --region us-central1 --port 8080   ->  http://localhost:8080

set -euo pipefail

MODE="${1:-real}"
PROJECT="${PROJECT_ID:-qwiklabs-gcp-04-7254cc802c4d}"
REGION="${REGION:-us-central1}"
SERVICE="grant-advisor"
SA="grant-advisor@${PROJECT}.iam.gserviceaccount.com"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

command -v adk >/dev/null || { echo "adk not found: source agent/.venv/bin/activate" >&2; exit 1; }

ENV_ARGS=(
  --env GOOGLE_GENAI_USE_VERTEXAI=TRUE
  --env GOOGLE_CLOUD_PROJECT="${PROJECT}"
  --env GOOGLE_CLOUD_LOCATION="${REGION}"
  --env BQ_DATASET=a4i_econ
  --env BQ_GRAPH=LocalEconomy
)
case "${MODE}" in
  mock)
    # Mock ids (B01...) do not exist in BigQuery, so Toolbox lookups stay off in mock mode.
    ENV_ARGS+=(--env USE_MOCK_DATA=true)
    ;;
  real)
    TOOLBOX_URL="$(gcloud run services describe toolbox --project "${PROJECT}" --region "${REGION}" \
                   --format='value(status.url)')"
    [[ -n "${TOOLBOX_URL}" ]] || { echo "Toolbox service not found: run terraform apply first" >&2; exit 1; }
    ENV_ARGS+=(--env USE_MOCK_DATA=false --env TOOLBOX_URL="${TOOLBOX_URL}")
    ;;
  *)
    echo "usage: bash scripts/deploy_agent.sh [mock|real]" >&2; exit 1 ;;
esac

echo "Deploying ${SERVICE} (${MODE}) to ${PROJECT}/${REGION} as ${SA}"
cd "${ROOT}/agent"
adk deploy cloud_run --project "${PROJECT}" --region "${REGION}" \
  --service_name "${SERVICE}" --with_ui "${ENV_ARGS[@]}" \
  ./grant_advisor \
  -- --service-account="${SA}" --min-instances=1 --no-allow-unauthenticated --quiet

echo
echo "Deployed. Open it with:"
echo "  gcloud run services proxy ${SERVICE} --project ${PROJECT} --region ${REGION} --port 8080"
echo "  then http://localhost:8080"
