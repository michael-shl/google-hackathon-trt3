resource "google_service_account" "toolbox" {
  account_id   = "toolbox-identity"
  display_name = "MCP Toolbox (read-only BigQuery tools)"
  depends_on   = [google_project_service.enabled]
}

resource "google_service_account" "agent" {
  account_id   = "grant-advisor"
  display_name = "ADK grant_advisor agent on Cloud Run"
  depends_on   = [google_project_service.enabled]
}

resource "google_service_account" "desk" {
  account_id   = "grant-desk"
  display_name = "Grant Desk Streamlit front end on Cloud Run"
  depends_on   = [google_project_service.enabled]
}

locals {
  toolbox_roles = [
    "roles/bigquery.jobUser",
    "roles/bigquery.dataViewer",
    "roles/logging.logWriter",
  ]

  agent_roles = [
    "roles/aiplatform.user",
    "roles/bigquery.jobUser",
    "roles/logging.logWriter",
    var.agent_can_write_bigquery ? "roles/bigquery.dataEditor" : "roles/bigquery.dataViewer",
  ]

  compute_sa = "${data.google_project.this.number}-compute@developer.gserviceaccount.com"

  build_roles = [
    "roles/run.builder",
    "roles/artifactregistry.writer",
    "roles/logging.logWriter",
    "roles/storage.objectViewer",
  ]
}

resource "google_project_iam_member" "toolbox" {
  for_each = toset(local.toolbox_roles)

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.toolbox.email}"
}

resource "google_project_iam_member" "agent" {
  for_each = toset(local.agent_roles)

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.agent.email}"
}

resource "google_project_iam_member" "build" {
  for_each = var.grant_build_roles ? toset(local.build_roles) : toset([])

  project    = var.project_id
  role       = each.value
  member     = "serviceAccount:${local.compute_sa}"
  depends_on = [google_project_service.enabled]
}

# The Grant Desk calls the private grant-advisor service. Project-level invoker because the agent
# service is created by `adk deploy`, not Terraform.
resource "google_project_iam_member" "desk" {
  for_each = toset(["roles/run.invoker", "roles/logging.logWriter"])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.desk.email}"
}
