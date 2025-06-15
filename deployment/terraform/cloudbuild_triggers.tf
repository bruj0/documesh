# Cloud Build Triggers configuration

# Cloud Build Trigger for the document-api application (main branch)
resource "google_cloudbuild_trigger" "document_api_trigger" {
  location    = var.region
  name        = "documesh-api-trigger"
  description = "Trigger for building DocuMesh API Docker image"

  source_to_build {
    uri       = "https://github.com/bruj0/documesh"
    ref       = "refs/heads/main"
    repo_type = "GITHUB"
  }

  included_files = ["src/**", "Dockerfile", "cloudbuild.yaml"]
  filename       = "cloudbuild.yaml" # Path to Cloud Build config file

  substitutions = {
    _REGION          = var.region
    _PROJECT_ID      = var.project_id
#    _SERVICE_ACCOUNT = google_service_account.cloudbuild_sa.id
  }

  # Optional: Use a specific service account for this trigger
  service_account = google_service_account.cloudbuild_sa.id

  # Ensure the Cloud Build API is enabled before creating triggers
  depends_on = [google_project_service.services["cloudbuild.googleapis.com"]]
}

# Additional trigger for PR validation
resource "google_cloudbuild_trigger" "document_api_pr_trigger" {
  location    = var.region
  name        = "documesh-api-pr-validation"
  description = "PR validation for DocuMesh API"

  github {
    owner = "bruj0"
    name  = "documesh"
    pull_request {
      branch = ".*"
      comment_control = "COMMENTS_ENABLED"
    }
  }

  included_files = ["src/**"]
  filename       = "cloudbuild.yaml"

  substitutions = {
    _REGION          = var.region
    _PROJECT_ID      = var.project_id
#    _SERVICE_ACCOUNT = google_service_account.cloudbuild_sa.id
  }

  service_account = google_service_account.cloudbuild_sa.id

  # Ensure the Cloud Build API is enabled before creating triggers
  depends_on = [google_project_service.services["cloudbuild.googleapis.com"]]
}
