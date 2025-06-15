# Cloud Run configuration

# Cloud Run service for API
resource "google_cloud_run_service" "api_service" {
  name     = "document-management-api"
  location = var.region

  template {
    metadata {
      annotations = {
        "run.googleapis.com/cpu-architecture" = "arm64"
      }
    }

    spec {

      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.document_api_repo.repository_id}/document-api:latest"

        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }

        env {
          name  = "DOCUMENT_BUCKET"
          value = google_storage_bucket.document_storage.name
        }

        env {
          name  = "DOCUMENT_PROCESSOR_ID"
          value = google_document_ai_processor.processor.id
        }

        env {
          name  = "TEXT_INDEX_ID"
          value = google_vertex_ai_index.text_index.id
        }

        env {
          name  = "VISUAL_INDEX_ID"
          value = google_vertex_ai_index.visual_index.id
        }

        env {
          name  = "DATA_STORE_ID"
          value = google_discovery_engine_data_store.document_store.data_store_id
        }

        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.services]
}

# Make API publicly accessible
resource "google_cloud_run_service_iam_member" "api_public" {
  service  = google_cloud_run_service.api_service.name
  location = google_cloud_run_service.api_service.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
