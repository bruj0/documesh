"""
Document processor module for technical document management.

This module handles extraction of text and diagrams from uploaded documents
using Google Cloud Document AI and Vision APIs.
"""
import os
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from google.cloud import documentai_v1 as documentai
from google.cloud import vision_v1 as vision
from google.cloud import storage
from google.cloud import firestore

# Import local modules
from . import embedding
from . import vision as vision_processing

# Environment variables and configuration
PROJECT_ID = os.environ.get("PROJECT_ID", "your-project-id")
LOCATION = os.environ.get("LOCATION", "us-central1")
PROCESSOR_ID = os.environ.get("DOCUMENT_PROCESSOR_ID", "your-processor-id")
BUCKET_NAME = os.environ.get("DOCUMENT_BUCKET", f"{PROJECT_ID}-technical-documents")

# Initialize clients
document_client = documentai.DocumentProcessorServiceClient()
vision_client = vision.ImageAnnotatorClient()
storage_client = storage.Client()
db = firestore.Client()


def process_document(bucket_name: str, file_name: str) -> str:
    """
    Process a document uploaded to Cloud Storage.
    
    Args:
        bucket_name: The name of the GCS bucket
        file_name: The name of the file in the bucket
    
    Returns:
        document_id: The ID of the processed document
    """
    # Log start of processing
    print(f"Processing document: {file_name} from bucket: {bucket_name}")
    
    # Get document from Cloud Storage
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    file_content = blob.download_as_bytes()
    
    # Get MIME type
    mime_type = _get_mime_type(file_name)
    
    # Process with Document AI
    processor_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{PROCESSOR_ID}"
    raw_document = documentai.RawDocument(content=file_content, mime_type=mime_type)
    request = documentai.ProcessRequest(name=processor_name, raw_document=raw_document)
    
    result = document_client.process_document(request=request)
    document = result.document
    
    # Extract text content
    text_content = document.text
    
    # Process for diagrams if it's a PDF, image, etc.
    diagrams = []
    if mime_type in ["application/pdf", "image/jpeg", "image/png", "image/tiff"]:
        diagrams = extract_diagrams_with_vision(file_content, mime_type)
    
    # Generate embeddings for text and diagrams
    text_embedding = embedding.generate_text_embedding(text_content)
    
    visual_embeddings = []
    for diagram in diagrams:
        visual_embedding = embedding.generate_visual_embedding(diagram["image_content"])
        visual_embeddings.append({
            "embedding": visual_embedding,
            "page": diagram.get("page", 0),
            "bbox": diagram.get("bbox", {})
        })
    
    # Create document record
    document_id = f"doc-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}"
    
    document_data = {
        "document_id": document_id,
        "filename": file_name,
        "source_bucket": bucket_name,
        "mime_type": mime_type,
        "text_content": text_content,
        "text_embedding": text_embedding,
        "visual_embeddings": visual_embeddings,
        "diagram_count": len(diagrams),
        "processed_at": firestore.SERVER_TIMESTAMP,
        "metadata": {
            "source": file_name,
            "pages": document.pages,
        }
    }
    
    # Store document data in Firestore
    db.collection("documents").document(document_id).set(document_data)
    
    # Store document embeddings in Vector Search
    _store_embeddings_in_vector_search(document_id, text_embedding, visual_embeddings)
    
    return document_id


def extract_diagrams_with_vision(file_content: bytes, mime_type: str) -> List[Dict[str, Any]]:
    """
    Extract diagrams from document using Vision AI.
    
    Args:
        file_content: The raw content of the file
        mime_type: The MIME type of the document
    
    Returns:
        List of dictionaries containing diagram information
    """
    # If PDF, we need to convert to images first using DocumentAI
    if mime_type == "application/pdf":
        return vision_processing.extract_diagrams_from_pdf(file_content)
    
    # For images, use Vision API directly
    image = vision.Image(content=file_content)
    
    # Detect objects and document features
    objects_response = vision_client.object_localization(image=image)
    document_response = vision_client.document_text_detection(image=image)
    
    # Process response to identify diagrams
    diagrams = vision_processing.identify_diagrams(
        objects_response.localized_object_annotations,
        document_response.full_text_annotation
    )
    
    return diagrams


def _get_mime_type(filename: str) -> str:
    """Determine MIME type from filename."""
    ext = filename.split(".")[-1].lower()
    mime_map = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "tiff": "image/tiff",
        "tif": "image/tiff",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    return mime_map.get(ext, "application/octet-stream")


def _store_embeddings_in_vector_search(
    document_id: str,
    text_embedding: List[float],
    visual_embeddings: List[Dict[str, Any]]
) -> None:
    """
    Store document embeddings in Vertex AI Vector Search.
    
    Args:
        document_id: The document ID
        text_embedding: The text embedding vector
        visual_embeddings: A list of visual embedding vectors with metadata
    """
    # This function would use the MatchingEngine API to store embeddings
    # Implementation depends on how your Vector Search index is set up
    from google.cloud import aiplatform
    
    # Initialize Vertex AI
    aiplatform.init(project=PROJECT_ID, location=LOCATION)
    
    # In a real implementation, you'd use code like:
    # index = aiplatform.MatchingEngineIndex(index_name="your-index-name")
    # index.deploy()
    # index_endpoint = index.deploy_index(...)
    # For now, we'll just log the action
    print(f"Storing embeddings for document {document_id} in Vector Search")
    print(f"Text embedding dimension: {len(text_embedding)}")
    print(f"Number of visual embeddings: {len(visual_embeddings)}")
