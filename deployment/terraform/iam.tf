# Service Account and IAM configuration

# Service account for Cloud Build
resource "google_service_account" "cloudbuild_sa" {
  account_id   = "cloudbuild-sa"
  display_name = "Cloud Build Service Account"
  description  = "Service account for Cloud Build to deploy and manage resources"
}

# Service account for Cloud Run API service
resource "google_service_account" "api_service_sa" {
  account_id   = "document-api-sa"
  display_name = "Document API Service Account"
  description  = "Service account for the Document Management API Cloud Run service"
}

# Service account for Cloud Functions
resource "google_service_account" "cloud_functions_sa" {
  account_id   = "cloud-functions-sa"
  display_name = "Cloud Functions Service Account"
  description  = "Service account for Cloud Functions to access Vector Search and other services"
}

# IAM policy bindings for the API service account
resource "google_project_iam_member" "api_service_roles" {
  for_each = toset([
    "roles/storage.objectViewer",  # Access to read documents from storage
    "roles/storage.objectCreator", # Ability to upload new documents
    "roles/documentai.admin",      # Use Document AI processors
    "roles/aiplatform.admin",      # Access to Vertex AI for vector search
    "roles/datastore.owner",       # rw Firestore data
    "roles/pubsub.admin",          # Publish messages to topics
    "roles/cloudfunctions.admin",
    "roles/run.admin",
    "roles/iam.serviceAccountUser",
    "roles/artifactregistry.admin"
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.api_service_sa.email}"
}

# IAM policy bindings for the Cloud Build service account
resource "google_project_iam_member" "cloudbuild_sa_roles" {
  for_each = toset([

    "roles/artifactregistry.admin",
    "roles/cloudbuild.builds.builder",
    "roles/secretmanager.secretAccessor", # For accessing GitHub tokens if needed
    "roles/cloudkms.cryptoKeyEncrypterDecrypter",
    "roles/storage.admin",
    "roles/run.admin",
    "roles/cloudfunctions.admin",
    "roles/iam.serviceAccountUser"
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.cloudbuild_sa.email}"
}

# IAM policy bindings for the Cloud Functions service account
resource "google_project_iam_member" "cloud_functions_roles" {
  for_each = toset([
    "roles/storage.objectViewer",     # Access to read documents from storage
    "roles/storage.objectCreator",    # Ability to create objects in storage
    "roles/aiplatform.user",          # Access to Vertex AI Vector Search
    "roles/datastore.user",           # Read/Write Firestore data
    "roles/logging.logWriter",        # Write logs
    "roles/monitoring.metricWriter",  # Write metrics
    "roles/cloudtrace.agent"          # Write traces
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.cloud_functions_sa.email}"
}

# IAM bindings for the API service account to access specific resources

# Allow API service to access the document storage bucket
resource "google_storage_bucket_iam_member" "api_service_document_storage_access" {
  bucket = google_storage_bucket.document_storage.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.api_service_sa.email}"
}

# Allow API service to access the processing bucket
resource "google_storage_bucket_iam_member" "api_service_processing_bucket_access" {
  bucket = google_storage_bucket.processing_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.api_service_sa.email}"
}

# Allow Cloud Functions to access the document storage bucket
resource "google_storage_bucket_iam_member" "cloud_functions_document_storage_access" {
  bucket = google_storage_bucket.document_storage.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.cloud_functions_sa.email}"
}

# Allow Cloud Functions to access the processing bucket
resource "google_storage_bucket_iam_member" "cloud_functions_processing_bucket_access" {
  bucket = google_storage_bucket.processing_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.cloud_functions_sa.email}"
}

