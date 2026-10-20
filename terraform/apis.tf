locals {
  services = [
    "aiplatform.googleapis.com",       # Gemini via Vertex AI
    "artifactregistry.googleapis.com", # images built by adk deploy
    "bigquery.googleapis.com",
    "bigqueryreservation.googleapis.com", # graph queries need an Enterprise reservation
    "bigquerystorage.googleapis.com",
    "cloudbuild.googleapis.com", # source deploys
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "logging.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com", # Toolbox tools.yaml
    "storage.googleapis.com",       # load.sh snapshot
  ]
}

resource "google_project_service" "enabled" {
  for_each = toset(local.services)

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

data "google_project" "this" {
  project_id = var.project_id
}
