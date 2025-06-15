# Cloud Storage configuration

# Cloud Storage buckets for document storage
resource "google_storage_bucket" "document_storage" {
  name     = "${var.project_id}-technical-documents"
  location = var.region
  uniform_bucket_level_access = true
  
  # Auto-delete files after 30 days if configured
  lifecycle_rule {
    condition {
      age = var.storage_retention_days
    }
    action {
      type = "Delete"
    }
  }
}

# Processing bucket for Document AI
resource "google_storage_bucket" "processing_bucket" {
  name     = "${var.project_id}-document-processing"
  location = var.region
  uniform_bucket_level_access = true
}

# Storage bucket for Cloud Functions
resource "google_storage_bucket" "function_bucket" {
  name     = "${var.project_id}-functions"
  location = var.region
  uniform_bucket_level_access = true
}
