locals {
  tools_yaml = file("${path.module}/${var.toolbox_config_path}")
}

resource "google_secret_manager_secret" "tools" {
  secret_id = "tools"

  replication {
    auto {}
  }

  depends_on = [google_project_service.enabled]
}

resource "google_secret_manager_secret_version" "tools" {
  secret      = google_secret_manager_secret.tools.id
  secret_data = local.tools_yaml
}

resource "google_secret_manager_secret_iam_member" "toolbox" {
  secret_id = google_secret_manager_secret.tools.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.toolbox.email}"
}

resource "google_cloud_run_v2_service" "toolbox" {
  name                = "toolbox"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    service_account = google_service_account.toolbox.email

    scaling {
      min_instance_count = var.toolbox_min_instances
      max_instance_count = 3
    }

    volumes {
      name = "tools"
      secret {
        secret = google_secret_manager_secret.tools.secret_id
        items {
          version = google_secret_manager_secret_version.tools.version
          path    = "tools.yaml"
        }
      }
    }

    containers {
      image = var.toolbox_image
      args  = ["--config=/app/tools.yaml", "--address=0.0.0.0", "--port=8080"]

      ports {
        container_port = 8080
      }

      # tools.yaml uses ${PROJECT_ID}; Toolbox substitutes environment variables at startup.
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }

      volume_mounts {
        name       = "tools"
        mount_path = "/app"
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }
  }

  depends_on = [
    google_project_service.enabled,
    google_secret_manager_secret_iam_member.toolbox,
    google_project_iam_member.toolbox,
  ]
}

resource "google_cloud_run_v2_service_iam_member" "toolbox_public" {
  count = var.toolbox_public ? 1 : 0

  name     = google_cloud_run_v2_service.toolbox.name
  location = google_cloud_run_v2_service.toolbox.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "toolbox_agent" {
  name     = google_cloud_run_v2_service.toolbox.name
  location = google_cloud_run_v2_service.toolbox.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.agent.email}"
}
