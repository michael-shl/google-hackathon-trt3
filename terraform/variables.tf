variable "project_id" {
  description = "Shared Qwiklabs team project."
  type        = string
  default     = "qwiklabs-gcp-04-7254cc802c4d"
}

variable "region" {
  description = "Region for Cloud Run and Secret Manager replicas."
  type        = string
  default     = "us-central1"
}

variable "bq_location" {
  description = "BigQuery location. Must match scripts/load.sh (LOCATION=US)."
  type        = string
  default     = "US"
}

variable "dataset_id" {
  description = "Dataset loaded by scripts/load.sh."
  type        = string
  default     = "a4i_econ"
}

variable "manage_bigquery_foundation" {
  description = <<-EOT
    Create the a4i_econ dataset and the Enterprise reservation (a4i-graph) + project assignment.
    Default false because scripts/load.sh already creates them. Set true only if you apply BEFORE
    load.sh runs, or after importing the existing objects (see README.md).
  EOT
  type        = bool
  default     = false
}

variable "reservation_name" {
  description = "Reservation name used by scripts/load.sh."
  type        = string
  default     = "a4i-graph"
}

variable "reservation_max_slots" {
  description = "Autoscale ceiling for the graph reservation (load.sh uses 50)."
  type        = number
  default     = 50
}

variable "toolbox_image" {
  description = "MCP Toolbox container image."
  type        = string
  default     = "us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:latest"
}

variable "toolbox_config_path" {
  description = "Path to the Toolbox tools.yaml, relative to this directory."
  type        = string
  default     = "../toolbox/tools.yaml"
}

variable "toolbox_min_instances" {
  description = "Keep one Toolbox instance warm so the demo never pays a cold start."
  type        = number
  default     = 1
}

variable "toolbox_public" {
  description = <<-EOT
    Allow unauthenticated calls to the Toolbox service. Hackathon trade-off: tools are fixed,
    read-only queries over public data. If false, only the agent service account can invoke it.
  EOT
  type        = bool
  default     = true
}

variable "agent_can_write_bigquery" {
  description = "Grant the agent BigQuery dataEditor (only needed for the intake-agent stretch that writes edges)."
  type        = bool
  default     = false
}

variable "grant_build_roles" {
  description = "Grant the Compute Engine default service account the roles Cloud Run source deploys (adk deploy) need."
  type        = bool
  default     = true
}
