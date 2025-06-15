# Vertex AI configuration

# Vertex AI Search datastore
resource "google_discovery_engine_data_store" "document_store" {
  location      = "global"  # Discovery Engine typically uses 'global' location
  data_store_id = "technical-documents-store"
  display_name  = "Technical Documents Store"
  industry_vertical = "GENERIC"
  content_config = "NO_CONTENT"
  solution_types = ["SOLUTION_TYPE_SEARCH"]
  
  depends_on = [google_project_service.services]
}

# Vertex AI Vector Search Index for text
resource "google_vertex_ai_index" "text_index" {
  display_name = "text-vector-index"
  description  = "Text embedding vector index"
  region       = var.region
  
  metadata {
    contents_delta_uri = "gs://${google_storage_bucket.document_storage.name}/vector_indices"
    config {
      dimensions = 768
      approximate_neighbors_count = 150
      distance_measure_type = "COSINE_DISTANCE"
      feature_norm_type = "UNIT_L2_NORM"
      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count = 1000
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
      dimensions = 512
      approximate_neighbors_count = 150
      distance_measure_type = "COSINE_DISTANCE"
      feature_norm_type = "UNIT_L2_NORM"
      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count = 1000
          leaf_nodes_to_search_percent = 10
        }
      }
    }
  }
  
  depends_on = [google_project_service.services]
}
