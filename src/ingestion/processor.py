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
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents import Document
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_chroma import Chroma


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

    request = documentai.ProcessRequest(
        name=name,
        raw_document=raw_document,
    )
    result = client.process_document(request=request)
    document = result.document
    # Create document record
    document_id = f"doc-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}"
    document_data = {
        "document_id": document_id,
        "filename": file_name,
        "source_bucket": bucket_name,
        "mime_type": mime_type,
        "text_content": document.text,
        # "text_embedding": text_embedding,
        # "visual_embeddings": visual_embeddings,
        # "diagram_count": len(diagrams), # TO-DO -> First we implement the workflow for text extraction
        "processed_at": firestore.SERVER_TIMESTAMP,
        "metadata": {
            "source": file_name,
            "pages": document.pages,
        }
    }

    import vertexai
    vertexai.init(project=PROJECT_ID, location="us-central1")
    embeddings = VertexAIEmbeddings(model_name="text-embedding-004")

    splitted_docs = split_docs(docs=[Document(page_content=document.text)])
    vector_store = Chroma(
        collection_name="foo",
        embedding_function=embeddings,
        # other params...
    )
    vector_store.add_documents(documents=splitted_docs, ids=[str(i) for i in range(1, len(splitted_docs)+1)])
    
    return vector_store, document_id


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


def split_docs(docs):
    # Markdown
    headers_to_split_on = [
        ("#", "Title 1"),
        ("##", "Sub-title 1"),
        ("###", "Sub-title 2"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on
    )
    # Split based on markdown and add original metadata
    md_docs = []
    for doc in docs:
        md_doc = markdown_splitter.split_text(doc.page_content)
        for i in range(len(md_doc)):
            md_doc[i].metadata = md_doc[i].metadata | doc.metadata
        md_docs.extend(md_doc)
    # RecursiveTextSplitter
    # Chunk size big enough
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=20,
        separators=["\n\n", "\n", r"(?<=\. )", " ", ""],
    )
    splitted_docs = splitter.split_documents(md_docs)
    return splitted_docs
