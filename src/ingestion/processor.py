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
from google.api_core.client_options import ClientOptions

# Import local modules
from . import embedding
from . import vision as vision_processing

# Environment variables and configuration
PROJECT_ID = "hacker2025-team-5-dev"
LOCATION = "eu"

PROCESSOR_ID = "5b798e9bbfa51375"
BUCKET_NAME = "example_bucket_airbus"  # Replace with your GCS bucket name

# Initialize clients
document_client = documentai.DocumentProcessorServiceClient()
vision_client = vision.ImageAnnotatorClient()
storage_client = storage.Client()
db = firestore.Client()


def get_total_pages(file_path: str, mime_type: str) -> int:
    """
    Determines the total number of pages in a document based on its MIME type.
    Args:
        file_path: The path to the document file.
        mime_type: The MIME type of the document (e.g., "application/pdf").
    """
    if mime_type == "application/pdf":
        from PyPDF2 import PdfReader
        try:
            with open(file_path, "rb") as f:
                reader = PdfReader(f)
                return len(reader.pages)
        except Exception as e:
            print(f"Error reading PDF for page count: {e}")
            return 0  # Or raise an error
        print(
            "WARNING: Page count determination is not implemented. "
            "Assuming 1 page for this sample. You MUST implement this for multi-page processing."
        )
        return 1 # Replace with actual page count logic
    else:
        # For non-PDFs, Document AI's synchronous processing might handle them differently.
        # Often, non-PDFs are treated as a single "page" or image.
        # If batching is needed for other types, adjust logic accordingly.
        print(f"Page count for mime_type {mime_type} defaults to 1.")
        return 1

def get_total_pages_from_gcs(bucket_name: str, file_name: str) -> int:
    """
    Determines the total number of pages in a document stored in Google Cloud Storage.
    
    Args:
        bucket_name: The name of the GCS bucket
        file_name: The name of the file in the bucket
    Returns:
        int: The total number of pages in the document
    """
    # Get the file from GCS
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    
    if not blob.exists():
        raise FileNotFoundError(f"File {file_name} does not exist in bucket {bucket_name}.")
    
    file_content = blob.download_as_bytes()
    
    # Determine MIME type
    mime_type = _get_mime_type(file_name)
    
    return get_total_pages(file_content, mime_type)

def process_document(bucket_name: str, file_name: str) -> str:
    """
    Process a document uploaded to Cloud Storage.
    
    Args:
        bucket_name: The name of the GCS bucket
        file_name: The name of the file in the bucket
    
    Returns:
        document_id: The ID of the processed document
    """
    opts = ClientOptions(api_endpoint=f"{LOCATION}-documentai.googleapis.com")
    client = documentai.DocumentProcessorServiceClient(client_options=opts)
    mime_type = _get_mime_type(file_name)

    name = client.processor_path(PROJECT_ID, LOCATION, PROCESSOR_ID)

    # Download and read the image content from GCS
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    if not blob.exists():
        raise FileNotFoundError(f"File {file_name} does not exist in bucket {bucket_name}.")
    image_content = blob.download_as_bytes()

    raw_document = documentai.RawDocument(content=image_content, mime_type=mime_type)

    # Determine total pages (implement this function based on your document type)
    total_pages = get_total_pages_from_gcs(bucket_name, file_name)
    if total_pages == 0:
        print("Could not determine page count or document is empty.")
        return
    
    batch_size = 15  # Max pages per sync request with IndividualPageSelector for PDFs
    text_content = []

    print(f"Processing document with {total_pages} page(s) in batches of {batch_size}...")

    for i in range(0, total_pages, batch_size):
        start_page = i + 1
        end_page = min(i + batch_size, total_pages)
        pages_to_process = list(range(start_page, end_page + 1))

        print(f"Processing pages: {pages_to_process}...")

        process_options = documentai.ProcessOptions(
            individual_page_selector=documentai.ProcessOptions.IndividualPageSelector(
                pages=pages_to_process
            )
        )

        request = documentai.ProcessRequest(
            name=name,
            raw_document=raw_document,
            process_options=process_options,
        )

        result = client.process_document(request=request)
        document = result.document
        text_content.append(document.text)
    
    # Extract text content
    text_content = "\n".join(text_content)
    
    # Process for diagrams if it's a PDF, image, etc.
    diagrams = []
    if mime_type in ["application/pdf", "image/jpeg", "image/png", "image/tiff"]:
        diagrams = extract_diagrams_with_vision(image_content, mime_type)
    
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
