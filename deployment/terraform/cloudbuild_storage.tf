# Storage resources for Cloud Build and related artifacts

# Storage bucket for Cloud Build artifacts
resource "google_storage_bucket" "cloudbuild_artifacts" {
  provider                    = google
  name                        = "${var.project_id}-cloudbuild-artifacts"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy              = true  # Allow deleting non-empty buckets (use with caution)
  
  versioning {
    enabled = true  # Keep versions of build artifacts
  }
  lifecycle {
    create_before_destroy = false
    prevent_destroy = false
    ignore_changes = []
  }
  lifecycle_rule {
    condition {
      age = 30  # days
    }
    action {
      type = "Delete"
    }
  }
}

# Storage bucket for function source code
resource "google_storage_bucket" "function_source" {
  provider                    = google
  name                        = "${var.project_id}-functions"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy              = true
  
  versioning {
    enabled = true
  }
  
  lifecycle {
    create_before_destroy = false
    prevent_destroy = false
    ignore_changes = []
  }

  lifecycle_rule {
    condition {
      age = 60  # days
    }
    action {
      type = "Delete"
    }
  }
}

# IAM policy to allow Cloud Build to access the buckets
resource "google_storage_bucket_iam_member" "cloudbuild_artifacts_access" {
  provider = google
  bucket   = google_storage_bucket.cloudbuild_artifacts.name
  role     = "roles/storage.admin"
  member   = "serviceAccount:${google_service_account.cloudbuild_sa.email}"
}

resource "google_storage_bucket_iam_member" "function_source_access" {
  provider = google
  bucket   = google_storage_bucket.function_source.name
  role     = "roles/storage.admin"
  member   = "serviceAccount:${google_service_account.cloudbuild_sa.email}"
}
