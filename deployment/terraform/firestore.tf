# Firestore configuration

# Firestore database (for metadata)
resource "google_firestore_database" "document_db" {
  project     = var.project_id
  name        = "documesh-database" # Changed from "(default)" to a specific name
  location_id = var.firestore_location
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.services]
}
