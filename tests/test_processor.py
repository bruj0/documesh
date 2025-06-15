"""
Tests for document processing functionality.
"""
import os
import pytest
from unittest.mock import patch, MagicMock, ANY

from src.ingestion import processor

@pytest.fixture
def mock_document_bytes():
    """Fixture for mock document bytes."""
    return b'Test document content'

@pytest.fixture
def mock_document_ai_response():
    """Fixture for mock Document AI response."""
    mock_response = MagicMock()
    mock_document = MagicMock()
    mock_document.text = "Extracted text from document"
    mock_document.pages = [MagicMock()]
    mock_response.document = mock_document
    return mock_response

@pytest.fixture
def mock_vision_response():
    """Fixture for mock Vision AI response."""
    mock_object_response = MagicMock()
    mock_object_annotation = MagicMock()
    mock_object_annotation.name = "diagram"
    mock_object_annotation.score = 0.9
    
    # Mock bounding poly with normalized vertices
    mock_vertex1 = MagicMock()
    mock_vertex1.x = 0.1
    mock_vertex1.y = 0.1
    
    mock_vertex2 = MagicMock()
    mock_vertex2.x = 0.9
    mock_vertex2.y = 0.1
    
    mock_vertex3 = MagicMock()
    mock_vertex3.x = 0.9
    mock_vertex3.y = 0.9
    
    mock_vertex4 = MagicMock()
    mock_vertex4.x = 0.1
    mock_vertex4.y = 0.9
    
    mock_bounding_poly = MagicMock()
    mock_bounding_poly.normalized_vertices = [mock_vertex1, mock_vertex2, mock_vertex3, mock_vertex4]
    mock_object_annotation.bounding_poly = mock_bounding_poly
    
    mock_object_response.localized_object_annotations = [mock_object_annotation]
    
    mock_text_response = MagicMock()
    mock_full_text = MagicMock()
    mock_text_response.full_text_annotation = mock_full_text
    
    return mock_object_response, mock_text_response

def test_process_document(mock_document_bytes, mock_document_ai_response, mock_vision_response):
    """Test document processing."""
    # Mock all the dependencies
    with patch('src.ingestion.processor.document_client') as mock_doc_client, \
         patch('src.ingestion.processor.vision_client') as mock_vision_client, \
         patch('src.ingestion.processor.storage_client') as mock_storage_client, \
         patch('src.ingestion.processor.db') as mock_db, \
         patch('src.ingestion.processor.embedding') as mock_embedding, \
         patch('src.ingestion.processor._store_embeddings_in_vector_search') as mock_store, \
         patch('src.ingestion.processor.vision_processing') as mock_vision_processing, \
         patch('os.urandom') as mock_urandom:
        
        # Configure mock return values
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_blob.download_as_bytes.return_value = mock_document_bytes
        mock_bucket.blob.return_value = mock_blob
        mock_storage_client.bucket.return_value = mock_bucket
        
        mock_doc_client.process_document.return_value = mock_document_ai_response
        
        mock_vision_processing.extract_diagrams_from_pdf.return_value = [
            {
                "image_content": b"diagram1",
                "page": 1,
                "bbox": {"x1": 0.1, "y1": 0.1, "x2": 0.9, "y2": 0.9}
            }
        ]
        
        # Mock embeddings
        mock_embedding.generate_text_embedding.return_value = [0.1, 0.2, 0.3]
        mock_embedding.generate_visual_embedding.return_value = [0.4, 0.5, 0.6]
        
        # Mock random bytes for document ID generation
        mock_urandom.return_value = b'\xaa\xbb\xcc\xdd'
        
        # Run the function
        document_id = processor.process_document("test-bucket", "test-doc.pdf")
        
        # Check that document_id is returned
        assert document_id is not None
        assert "doc-" in document_id
        assert "aabbccdd" in document_id
        
        # Verify Document AI was called properly
        mock_doc_client.process_document.assert_called_once()
        
        # Verify Firestore was updated
        mock_db.collection.return_value.document.return_value.set.assert_called_once()
        
        # Verify embeddings were generated
        mock_embedding.generate_text_embedding.assert_called_once()
        mock_embedding.generate_visual_embedding.assert_called_once()
        
        # Verify embeddings were stored in Vector Search
        mock_store.assert_called_once()


def test_extract_diagrams_with_vision(mock_document_bytes, mock_vision_response):
    """Test extraction of diagrams from document using Vision AI."""
    mock_object_response, mock_text_response = mock_vision_response
    
    # Mock vision processing
    with patch('src.ingestion.processor.vision_client') as mock_vision_client, \
         patch('src.ingestion.processor.vision_processing') as mock_vision_processing:
            
        # Configure mock return values
        mock_vision_client.object_localization.return_value = mock_object_response
        mock_vision_client.document_text_detection.return_value = mock_text_response
        
        mock_vision_processing.identify_diagrams.return_value = [
            {
                "image_content": b"diagram1",
                "bbox": {"x1": 0.1, "y1": 0.1, "x2": 0.9, "y2": 0.9},
                "confidence": 0.9,
                "object_type": "diagram"
            }
        ]
        
        # Extract diagrams
        diagrams = processor.extract_diagrams_with_vision(mock_document_bytes, "image/jpeg")
        
        # Verify results
        assert len(diagrams) == 1
        assert diagrams[0]["confidence"] == 0.9
        assert diagrams[0]["object_type"] == "diagram"
        
        # Verify Vision AI was called properly
        mock_vision_client.object_localization.assert_called_once()
        mock_vision_client.document_text_detection.assert_called_once()
        mock_vision_processing.identify_diagrams.assert_called_once_with(
            mock_object_response.localized_object_annotations,
            mock_text_response.full_text_annotation
        )
