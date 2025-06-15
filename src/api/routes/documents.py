"""
API routes for document operations.
"""
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, Query, HTTPException, Depends
from fastapi.responses import JSONResponse
from google.cloud import storage
from pydantic import BaseModel

# Import local modules
from ...ingestion import processor

router = APIRouter()

# Models
class DocumentMetadata(BaseModel):
    """Document metadata model."""
    title: Optional[str] = None
    description: Optional[str] = None
    document_type: Optional[str] = None
    tags: Optional[List[str]] = None


class DocumentResponse(BaseModel):
    """Document response model."""
    document_id: str
    filename: str
    upload_time: datetime
    metadata: Optional[Dict[str, Any]] = None
    status: str


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    document_type: Optional[str] = Form(None),
    tags: Optional[str] = Form(None)
):
    """
    Upload a document to the system.
    
    Args:
        file: The document file
        title: Optional document title
        description: Optional document description
        document_type: Optional document type
        tags: Optional comma-separated tags
    """
    try:
        # Get file content
        file_content = await file.read()
        
        # Upload to Cloud Storage
        bucket_name = os.environ.get("DOCUMENT_BUCKET", "technical-documents")
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        blob_name = f"uploads/{timestamp}_{file.filename}"
        
        # Upload to GCS
        blob = bucket.blob(blob_name)
        blob.upload_from_string(file_content)
        
        # Prepare metadata
        metadata = {
            "title": title or file.filename,
            "description": description,
            "document_type": document_type,
            "tags": tags.split(",") if tags else []
        }
        
        # Process document in a separate background task
        # In a real-world application, we would trigger a Cloud Function or Pub/Sub
        # For this demo, we'll process directly
        document_id = processor.process_document(bucket_name, blob_name)
        
        return {
            "document_id": document_id,
            "filename": file.filename,
            "upload_time": datetime.now(),
            "metadata": metadata,
            "status": "processing"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")


@router.get("/{document_id}", response_model=Dict[str, Any])
async def get_document(document_id: str):
    """
    Get document details by ID.
    
    Args:
        document_id: The document ID
    """
    try:
        # In a real app, fetch from Firestore
        from google.cloud import firestore
        db = firestore.Client()
        
        # Get document from Firestore
        doc_ref = db.collection("documents").document(document_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
        
        # Return document data
        return doc.to_dict()
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error retrieving document: {str(e)}")


@router.get("/", response_model=List[Dict[str, Any]])
async def list_documents(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    document_type: Optional[str] = Query(None),
    tags: Optional[str] = Query(None)
):
    """
    List documents with optional filtering.
    
    Args:
        limit: Maximum number of documents to return
        offset: Number of documents to skip
        document_type: Filter by document type
        tags: Comma-separated tags to filter by
    """
    try:
        # In a real app, fetch from Firestore with filters
        from google.cloud import firestore
        db = firestore.Client()
        
        # Start with base query
        query = db.collection("documents")
        
        # Apply filters
        if document_type:
            query = query.where("document_type", "==", document_type)
            
        if tags:
            tag_list = tags.split(",")
            # In a real app, you'd use array-contains-any for multiple tags
            if len(tag_list) == 1:
                query = query.where("tags", "array_contains", tag_list[0])
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        # Execute query
        docs = query.stream()
        
        # Convert to list
        result = []
        for doc in docs:
            doc_data = doc.to_dict()
            # Remove large fields
            if "text_embedding" in doc_data:
                del doc_data["text_embedding"]
            if "visual_embeddings" in doc_data:
                del doc_data["visual_embeddings"]
                
            result.append(doc_data)
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document by ID.
    
    Args:
        document_id: The document ID
    """
    try:
        # In a real app, delete from Firestore, GCS, and Vector Search
        from google.cloud import firestore
        db = firestore.Client()
        
        # Get document from Firestore
        doc_ref = db.collection("documents").document(document_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
        
        # Get document data
        doc_data = doc.to_dict()
        
        # Delete from GCS
        if "source_bucket" in doc_data and "filename" in doc_data:
            storage_client = storage.Client()
            bucket = storage_client.bucket(doc_data["source_bucket"])
            blob = bucket.blob(doc_data["filename"])
            blob.delete()
        
        # Delete from Firestore
        doc_ref.delete()
        
        # In a real app, we'd also delete from Vector Search
        
        return {"status": "success", "message": f"Document {document_id} deleted"}
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")
