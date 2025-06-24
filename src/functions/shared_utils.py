"""
Shared utilities for PDF processing and search functions.
Contains common initialization and helper functions.
"""
import os
from google.cloud import aiplatform
from google.cloud import firestore
from langchain_google_vertexai import VertexAIEmbeddings

# Global variables for model initialization
embeddings_model = None
db_client = None
project_id = os.environ.get('GCP_PROJECT', 'your-project-id')
location = os.environ.get('LOCATION', 'us-central1')
vector_search_endpoint_id = os.environ.get('VECTOR_SEARCH_ENDPOINT_ID')
vector_search_index_id = os.environ.get('VECTOR_SEARCH_INDEX_ID')

def initialize_clients():
    """Initialize Google Cloud clients and models."""
    global embeddings_model, db_client
    
    if embeddings_model is None:
        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=location)
        
        # Initialize embeddings model
        embeddings_model = VertexAIEmbeddings(
            model_name="textembedding-gecko@003"
        )
    
    if db_client is None:
        db_client = firestore.Client()

def get_embeddings_model():
    """Get the initialized embeddings model."""
    return embeddings_model

def get_db_client():
    """Get the initialized Firestore client."""
    return db_client

def get_vector_search_config():
    """Get vector search configuration."""
    return {
        'endpoint_id': vector_search_endpoint_id,
        'index_id': vector_search_index_id,
        'project_id': project_id,
        'location': location
    }
