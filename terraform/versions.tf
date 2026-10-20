terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 6.0, < 8.0"
    }
  }

  # Shared state in the lab project (versioned bucket), so Terraform can run from any teammate's
  # Cloud Shell or laptop. Run it from ONE place at a time; the GCS backend locks during apply.
  backend "gcs" {
    bucket = "qwiklabs-gcp-04-7254cc802c4d-tfstate"
    prefix = "trt3"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
