# Document AI configuration

# Document AI processor
resource "google_document_ai_processor" "processor" {
  location     = "eu" # Hardcoded region where DOCUMENT_OCR_PROCESSOR is available
  type         = "OCR_PROCESSOR"
  display_name = "technical-document-processor"

  depends_on = [google_project_service.services]
}
