# Cloud Functions configuration

# This is a placeholder - in production you would use a proper CI/CD pipeline
# to build and deploy the function
resource "google_cloudfunctions_function" "document_processor" {
  name        = "document-processor"
  description = "Function to process and analyze documents"
  runtime     = "python312"

  available_memory_mb   = 1024
  source_archive_bucket = google_storage_bucket.function_bucket.name
  source_archive_object = "function-source.zip"
  entry_point           = "document_processor"

  event_trigger {
    event_type = "google.storage.object.finalize"
    resource   = google_storage_bucket.document_storage.name
  }

  environment_variables = {
    PROJECT_ID            = var.project_id
    LOCATION              = var.region
    DOCUMENT_PROCESSOR_ID = google_document_ai_processor.processor.id
    TEXT_EMBEDDING_MODEL  = "textembedding-gecko@latest"
    MULTIMODAL_MODEL      = "multimodalembedding@latest"
    TEXT_INDEX_ID         = google_vertex_ai_index.text_index.id
    VISUAL_INDEX_ID       = google_vertex_ai_index.visual_index.id
  }

  depends_on = [google_project_service.services]
}
