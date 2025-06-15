# Pub/Sub configuration

# Pub/Sub topic for document processing
resource "google_pubsub_topic" "document_processing_topic" {
  name = "document-processing-topic"

  depends_on = [google_project_service.services]
}
