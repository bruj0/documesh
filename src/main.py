"""
Cloud Function for document processing.
"""
import functions_framework
import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

# Import document processor
try:
    from ingestion.processor import process_document
except ImportError:
    # Fallback for different deployment environments
    from src.ingestion.processor import process_document


@functions_framework.cloud_event
def document_processor(cloud_event):
    """
    Cloud Function triggered by a Cloud Storage event.
    
    Args:
        cloud_event: The Cloud Event that triggered the function
    """
    # Extract bucket and file information
    data = cloud_event.data
    
    if not data:
        print("No data in event")
        return
        
    bucket_name = data.get("bucket")
    file_name = data.get("name")
    
    if not bucket_name or not file_name:
        print("Missing bucket or file information")
        return
        
    print(f"Processing new document: {file_name} from bucket: {bucket_name}")
    
    try:
        # Process document
        _, document_id = process_document(bucket_name, file_name)
        print(f"Document processed successfully. Document ID: {document_id}")
        
        return {"document_id": document_id, "status": "success"}
    except Exception as e:
        print(f"Error processing document: {str(e)}")
        return {"status": "error", "message": str(e)}
