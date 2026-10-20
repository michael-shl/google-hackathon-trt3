terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 6.0, < 8.0"
    }
  }

  # State is local (terraform/terraform.tfstate in Cloud Shell's persistent $HOME).
  # Only ONE teammate (P5) runs apply. See README.md for an optional GCS backend.
}

provider "google" {
  project = var.project_id
  region  = var.region
}
