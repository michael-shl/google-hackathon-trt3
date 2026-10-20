# Dataset + graph reservation. Off by default: scripts/load.sh owns these (see README.md).
# Tables and the property graph are NOT managed here: load.sh replaces tables on every run, and
# the graph DDL lives in sql/ (P2), because it must be re-run whenever the tables change.

resource "google_bigquery_dataset" "a4i" {
  count = var.manage_bigquery_foundation ? 1 : 0

  dataset_id                 = var.dataset_id
  location                   = var.bq_location
  description                = "Challenge 3 corridor data (loaded by scripts/load.sh)."
  delete_contents_on_destroy = false
  depends_on                 = [google_project_service.enabled]
}

resource "google_bigquery_reservation" "graph" {
  count = var.manage_bigquery_foundation ? 1 : 0

  name              = var.reservation_name
  location          = var.bq_location
  edition           = "ENTERPRISE"
  slot_capacity     = 0
  ignore_idle_slots = true

  autoscale {
    max_slots = var.reservation_max_slots
  }

  depends_on = [google_project_service.enabled]
}

resource "google_bigquery_reservation_assignment" "graph" {
  count = var.manage_bigquery_foundation ? 1 : 0

  assignee    = "projects/${var.project_id}"
  job_type    = "QUERY"
  reservation = google_bigquery_reservation.graph[0].id
}
