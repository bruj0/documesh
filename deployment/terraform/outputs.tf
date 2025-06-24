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

# Vector Search outputs
output "text_vector_search_endpoint_id" {
  value       = google_vertex_ai_index_endpoint.text_endpoint.id
  description = "ID of the text vector search endpoint"
}

output "text_vector_search_index_id" {
  value       = google_vertex_ai_index_endpoint_deployed_index.text_deployed_index.deployed_index_id
  description = "ID of the deployed text vector search index"
}

output "visual_vector_search_endpoint_id" {
  value       = google_vertex_ai_index_endpoint.visual_endpoint.id
  description = "ID of the visual vector search endpoint"
}

output "visual_vector_search_index_id" {
  value       = google_vertex_ai_index_endpoint_deployed_index.visual_deployed_index.deployed_index_id
  description = "ID of the deployed visual vector search index"
}

# Cloud Functions outputs
output "similarity_search_function_url" {
  value       = google_cloudfunctions_function.similarity_search.https_trigger_url
  description = "URL for the similarity search Cloud Function"
}

output "document_similarity_search_function_url" {
  value       = google_cloudfunctions_function.document_similarity_search.https_trigger_url
  description = "URL for the document similarity search Cloud Function"
}

output "pdf_ingestion_function_name" {
  value       = google_cloudfunctions_function.pdf_ingestion.name
  description = "Name of the PDF ingestion Cloud Function"
}

# Service Account outputs
output "cloud_functions_service_account" {
  value       = google_service_account.cloud_functions_sa.email
  description = "Email address of the Cloud Functions service account"
}
