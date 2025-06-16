# Output values

output "document_bucket_name" {
  value = google_storage_bucket.document_storage.name
}

output "api_url" {
  value = google_cloud_run_service.api_service.status[0].url
}

output "document_processor_id" {
  value = google_document_ai_processor.processor.id
}

output "cloudbuild_service_account" {
  value       = google_service_account.cloudbuild_sa.email
  description = "Email address of the service account used by Cloud Build"
}

output "artifact_registry_url" {
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/document-api/document-api"
  description = "URL of the Artifact Registry repository for the document API images"
}
