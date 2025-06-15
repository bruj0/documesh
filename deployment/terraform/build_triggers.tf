# Cloud Build Triggers configuration

# Cloud Build Trigger for the document-api application (main branch)
resource "google_cloudbuild_trigger" "document_api_trigger" {
  provider    = google
  location    = "eu-west1"
  name        = "documesh-api-trigger"
  description = "Trigger for building DocuMesh API Docker image"
  
  github {
    owner = "bruj0"
    name  = "documesh"
    push {
      branch = "^main$"
    }
  }
  
  included_files = ["src/**"]
  filename = "cloudbuild.yaml"  # Path to Cloud Build config file
  
  substitutions = {
    _REGION         = var.region
    _PROJECT_ID     = var.project_id
    _SERVICE_ACCOUNT = google_service_account.cloudbuild_sa.email
  }
  
  # Optional: Use a specific service account for this trigger
  service_account = google_service_account.cloudbuild_sa.id
}

# Additional trigger for PR validation
resource "google_cloudbuild_trigger" "document_api_pr_trigger" {
  provider    = google
  location    = "eu-west1"
  name        = "documesh-api-pr-validation"
  description = "PR validation for DocuMesh API"
  
  github {
    owner = "bruj0"
    name  = "documesh"
    pull_request {
      branch = "^main$"
      comment_control = "COMMENTS_ENABLED"
    }
  }
  
  included_files = ["src/**"]
  filename       = "cloudbuild.yaml"
  
  substitutions = {
    _REGION         = var.region
    _PROJECT_ID     = var.project_id
    _SERVICE_ACCOUNT = google_service_account.cloudbuild_sa.email
  }
  
  service_account = google_service_account.cloudbuild_sa.id
}
