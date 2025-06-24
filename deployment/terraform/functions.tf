# Cloud Functions configuration

# This is a placeholder - in production you would use a proper CI/CD pipeline
# to build and deploy the function
resource "google_cloudfunctions_function" "document_processor" {
  name        = "document-processor"
  description = "Function to process and analyze documents"
  runtime     = "python312"

  available_memory_mb          = 1024
  source_archive_bucket        = google_storage_bucket.function_bucket.name
  source_archive_object        = "function-source.zip"
  entry_point                  = "document_processor"
  service_account_email        = google_service_account.cloud_functions_sa.email

  event_trigger {
    event_type = "google.storage.object.finalize"
    resource   = google_storage_bucket.document_storage.name
  }

  environment_variables = {
    GCP_PROJECT                   = var.project_id
    LOCATION                      = var.region
    DOCUMENT_PROCESSOR_ID         = google_document_ai_processor.processor.id
    TEXT_EMBEDDING_MODEL          = "textembedding-gecko@003"
    MULTIMODAL_MODEL              = "multimodalembedding@latest"
    VECTOR_SEARCH_ENDPOINT_ID     = google_vertex_ai_index_endpoint.text_endpoint.id
    VECTOR_SEARCH_INDEX_ID        = google_vertex_ai_index_endpoint_deployed_index.text_deployed_index.deployed_index_id
    TEXT_INDEX_ID                 = google_vertex_ai_index.text_index.id
    VISUAL_INDEX_ID               = google_vertex_ai_index.visual_index.id
    VISUAL_VECTOR_SEARCH_ENDPOINT_ID = google_vertex_ai_index_endpoint.visual_endpoint.id
    VISUAL_VECTOR_SEARCH_INDEX_ID    = google_vertex_ai_index_endpoint_deployed_index.visual_deployed_index.deployed_index_id
  }

  depends_on = [google_project_service.services]
}

# Cloud Function for PDF document processing
resource "google_cloudfunctions_function" "pdf_ingestion" {
  name        = "pdf-ingestion"
  description = "Function to process PDF documents and create embeddings"
  runtime     = "python312"

  available_memory_mb          = 2048
  timeout                      = 540
  source_archive_bucket        = google_storage_bucket.function_bucket.name
  source_archive_object        = "pdf-search-source.zip"
  entry_point                  = "process_pdf"
  service_account_email        = google_service_account.cloud_functions_sa.email

  event_trigger {
    event_type = "google.storage.object.finalize"
    resource   = google_storage_bucket.document_storage.name
  }

  environment_variables = {
    GCP_PROJECT                   = var.project_id
    LOCATION                      = var.region
    TEXT_EMBEDDING_MODEL          = "textembedding-gecko@003"
    MULTIMODAL_MODEL              = "multimodalembedding@latest"
    VECTOR_SEARCH_ENDPOINT_ID     = google_vertex_ai_index_endpoint.text_endpoint.id
    VECTOR_SEARCH_INDEX_ID        = google_vertex_ai_index_endpoint_deployed_index.text_deployed_index.deployed_index_id
    VISUAL_VECTOR_SEARCH_ENDPOINT_ID = google_vertex_ai_index_endpoint.visual_endpoint.id
    VISUAL_VECTOR_SEARCH_INDEX_ID    = google_vertex_ai_index_endpoint_deployed_index.visual_deployed_index.deployed_index_id
  }

  depends_on = [
    google_project_service.services,
    google_vertex_ai_index_endpoint_deployed_index.text_deployed_index,
    google_vertex_ai_index_endpoint_deployed_index.visual_deployed_index
  ]
}

# Cloud Function for similarity search
resource "google_cloudfunctions_function" "similarity_search" {
  name        = "similarity-search"
  description = "Function to perform similarity search on document embeddings"
  runtime     = "python312"

  available_memory_mb          = 1024
  timeout                      = 60
  source_archive_bucket        = google_storage_bucket.function_bucket.name
  source_archive_object        = "search-source.zip"
  entry_point                  = "search_similar_documents"
  service_account_email        = google_service_account.cloud_functions_sa.email
  
  https_trigger_security_level = "SECURE_OPTIONAL"

  environment_variables = {
    GCP_PROJECT                   = var.project_id
    LOCATION                      = var.region
    TEXT_EMBEDDING_MODEL          = "textembedding-gecko@003"
    VECTOR_SEARCH_ENDPOINT_ID     = google_vertex_ai_index_endpoint.text_endpoint.id
    VECTOR_SEARCH_INDEX_ID        = google_vertex_ai_index_endpoint_deployed_index.text_deployed_index.deployed_index_id
    VISUAL_VECTOR_SEARCH_ENDPOINT_ID = google_vertex_ai_index_endpoint.visual_endpoint.id
    VISUAL_VECTOR_SEARCH_INDEX_ID    = google_vertex_ai_index_endpoint_deployed_index.visual_deployed_index.deployed_index_id
  }

  depends_on = [
    google_project_service.services,
    google_vertex_ai_index_endpoint_deployed_index.text_deployed_index,
    google_vertex_ai_index_endpoint_deployed_index.visual_deployed_index
  ]
}

# Cloud Function for document-based similarity search
resource "google_cloudfunctions_function" "document_similarity_search" {
  name        = "document-similarity-search"
  description = "Function to find similar documents to a given document"
  runtime     = "python312"

  available_memory_mb          = 1024
  timeout                      = 60
  source_archive_bucket        = google_storage_bucket.function_bucket.name
  source_archive_object        = "search-source.zip"
  entry_point                  = "search_by_document"
  service_account_email        = google_service_account.cloud_functions_sa.email
  
  https_trigger_security_level = "SECURE_OPTIONAL"

  environment_variables = {
    GCP_PROJECT                   = var.project_id
    LOCATION                      = var.region
    TEXT_EMBEDDING_MODEL          = "textembedding-gecko@003"
    VECTOR_SEARCH_ENDPOINT_ID     = google_vertex_ai_index_endpoint.text_endpoint.id
    VECTOR_SEARCH_INDEX_ID        = google_vertex_ai_index_endpoint_deployed_index.text_deployed_index.deployed_index_id
    VISUAL_VECTOR_SEARCH_ENDPOINT_ID = google_vertex_ai_index_endpoint.visual_endpoint.id
    VISUAL_VECTOR_SEARCH_INDEX_ID    = google_vertex_ai_index_endpoint_deployed_index.visual_deployed_index.deployed_index_id
  }

  depends_on = [
    google_project_service.services,
    google_vertex_ai_index_endpoint_deployed_index.text_deployed_index,
    google_vertex_ai_index_endpoint_deployed_index.visual_deployed_index
  ]
}
