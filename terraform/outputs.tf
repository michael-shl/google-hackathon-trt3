output "toolbox_url" {
  description = "MCP Toolbox endpoint. Use as TOOLBOX_URL for the agent."
  value       = google_cloud_run_v2_service.toolbox.uri
}

output "toolbox_service_account" {
  value = google_service_account.toolbox.email
}

output "agent_service_account" {
  value = google_service_account.agent.email
}

output "adk_deploy_command" {
  description = "Run from the repo's agent/ directory after the agent package exists."
  value       = <<-EOT
    adk deploy cloud_run --project ${var.project_id} --region ${var.region} \
      --service_name grant-advisor --with_ui \
      --env GOOGLE_GENAI_USE_VERTEXAI=TRUE \
      --env GOOGLE_CLOUD_PROJECT=${var.project_id} \
      --env GOOGLE_CLOUD_LOCATION=${var.region} \
      --env BQ_DATASET=${var.dataset_id} \
      --env USE_MOCK_DATA=false \
      --env TOOLBOX_URL=${google_cloud_run_v2_service.toolbox.uri} \
      ./grant_advisor \
      -- --service-account=${google_service_account.agent.email} --min-instances=1
  EOT
}
