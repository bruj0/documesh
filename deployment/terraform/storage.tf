# Cloud Storage configuration

# Cloud Storage buckets for document storage
resource "google_storage_bucket" "document_storage" {
  name                        = "${var.project_id}-technical-documents"
  location                    = var.region
  uniform_bucket_level_access = true
  lifecycle {
    create_before_destroy = false
    prevent_destroy       = false
    ignore_changes        = []
  }

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
  name                        = "${var.project_id}-document-processing"
  location                    = var.region
  uniform_bucket_level_access = true
  lifecycle {
    create_before_destroy = false
    prevent_destroy       = false
    ignore_changes        = []
  }

}

# Storage bucket for Cloud Functions
resource "google_storage_bucket" "function_bucket" {
  name                        = "${var.project_id}-functions"
  location                    = var.region
  uniform_bucket_level_access = true
  lifecycle {
    create_before_destroy = false
    prevent_destroy       = false
    #ignore_changes        = []
  }
  versioning {
    enabled = true
  }
  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age                   = 60
      matches_prefix        = []
      matches_storage_class = []
      matches_suffix        = []
    }
  }
}
