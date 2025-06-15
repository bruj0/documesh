# API Services configuration

# Enable required APIs
resource "google_project_service" "services" {
  for_each = toset([
    "documentai.googleapis.com",
    "vision.googleapis.com",
    "aiplatform.googleapis.com",
    "discoveryengine.googleapis.com",
    "storage.googleapis.com",
    "firestore.googleapis.com",
    "cloudfunctions.googleapis.com",
    "run.googleapis.com",
    "pubsub.googleapis.com",
    "discoveryengine.googleapis.com",
    "retail.googleapis.com",           # Required for some Discovery Engine operations
    "artifactregistry.googleapis.com", # Required for Artifact Registry
    "cloudbuild.googleapis.com"        # Required for Cloud Build API
  ])

  service            = each.key
  disable_on_destroy = false
}
