# Artifact Registry configuration

# Create Artifact Registry repository for document-api container images
resource "google_artifact_registry_repository" "document_api_repo" {
  provider      = google
  location      = var.region
  repository_id = "document-api"
  description   = "Docker repository for Document Management API container images"
  format        = "DOCKER"

  depends_on = [google_project_service.services]
}

# IAM policy to allow Cloud Build to push to the repository
resource "google_artifact_registry_repository_iam_member" "cloudbuild_pusher" {
  provider   = google
  location   = google_artifact_registry_repository.document_api_repo.location
  repository = google_artifact_registry_repository.document_api_repo.repository_id
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.cloudbuild_sa.email}"
}

# IAM policy to allow Cloud Run to pull from the repository
resource "google_artifact_registry_repository_iam_member" "cloudrun_puller" {
  provider   = google
  location   = google_artifact_registry_repository.document_api_repo.location
  repository = google_artifact_registry_repository.document_api_repo.repository_id
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:service-${data.google_project.project.number}@serverless-robot-prod.iam.gserviceaccount.com"
}
