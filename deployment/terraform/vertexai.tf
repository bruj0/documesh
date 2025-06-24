# Vertex AI configuration

# Vertex AI Vector Search Index for text
resource "google_vertex_ai_index" "text_index" {
  display_name = "text-vector-index"
  description  = "Text embedding vector index"
  region       = var.region

  metadata {
    contents_delta_uri = "gs://${google_storage_bucket.document_storage.name}/vector_indices"
    config {
      dimensions                  = var.vector_search_dimensions
      approximate_neighbors_count = var.vector_search_neighbors_count
      distance_measure_type       = "COSINE_DISTANCE"
      feature_norm_type           = "UNIT_L2_NORM"
      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count    = 1000
          leaf_nodes_to_search_percent = 10
        }
      }
    }
  }

  depends_on = [google_project_service.services]
}

# Vertex AI Vector Search Index for visual embeddings
resource "google_vertex_ai_index" "visual_index" {
  display_name = "visual-vector-index"
  description  = "Visual embedding vector index"
  region       = var.region

  metadata {
    contents_delta_uri = "gs://${google_storage_bucket.document_storage.name}/visual_indices"
    config {
      dimensions                  = 512
      approximate_neighbors_count = 150
      distance_measure_type       = "COSINE_DISTANCE"
      feature_norm_type           = "UNIT_L2_NORM"
      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count    = 1000
          leaf_nodes_to_search_percent = 10
        }
      }
    }
  }

  depends_on = [google_project_service.services]
}

# Vertex AI Index Endpoint for text search
resource "google_vertex_ai_index_endpoint" "text_endpoint" {
  display_name = "text-search-endpoint"
  description  = "Endpoint for text vector search"
  region       = var.region

  depends_on = [google_project_service.services]
}

# Vertex AI Index Endpoint for visual search
resource "google_vertex_ai_index_endpoint" "visual_endpoint" {
  display_name = "visual-search-endpoint"
  description  = "Endpoint for visual vector search"
  region       = var.region

  depends_on = [google_project_service.services]
}

# Deploy text index to endpoint
resource "google_vertex_ai_index_endpoint_deployed_index" "text_deployed_index" {
  index_endpoint = google_vertex_ai_index_endpoint.text_endpoint.id
  index          = google_vertex_ai_index.text_index.id
  deployed_index_id = "textdeployedindex"
  display_name   = "Text Deployed Index"

  automatic_resources {
    min_replica_count = var.vector_search_min_replicas
    max_replica_count = var.vector_search_max_replicas
  }

  depends_on = [
    google_vertex_ai_index.text_index,
    google_vertex_ai_index_endpoint.text_endpoint
  ]
}

# Deploy visual index to endpoint  
resource "google_vertex_ai_index_endpoint_deployed_index" "visual_deployed_index" {
  index_endpoint = google_vertex_ai_index_endpoint.visual_endpoint.id
  index          = google_vertex_ai_index.visual_index.id
  deployed_index_id = "visualdeployedindex"
  display_name   = "Visual Deployed Index"

  automatic_resources {
    min_replica_count = var.vector_search_min_replicas
    max_replica_count = var.vector_search_max_replicas
  }

  depends_on = [
    google_vertex_ai_index.visual_index,
    google_vertex_ai_index_endpoint.visual_endpoint
  ]
}
