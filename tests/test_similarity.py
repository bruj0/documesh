"""
Tests for document similarity functionality.
"""
import os
import pytest
from unittest.mock import patch, MagicMock

from src.search import similarity

@pytest.fixture
def mock_embedding():
    """Fixture for mock embedding."""
    return [0.1, 0.2, 0.3, 0.4, 0.5]

@pytest.fixture
def mock_visual_embedding():
    """Fixture for mock visual embedding."""
    return [0.2, 0.3, 0.4, 0.5, 0.6]

@pytest.fixture
def mock_document_results():
    """Fixture for mock document search results."""
    return [
        {
            "document_id": "doc-123",
            "filename": "test_doc1.pdf",
            "similarity_score": 0.85,
            "match_type": "text",
            "metadata": {"title": "Test Document 1"}
        },
        {
            "document_id": "doc-456",
            "filename": "test_doc2.pdf",
            "similarity_score": 0.75,
            "match_type": "text",
            "metadata": {"title": "Test Document 2"}
        }
    ]

@pytest.fixture
def mock_visual_results():
    """Fixture for mock visual search results."""
    return [
        {
            "document_id": "doc-789",
            "diagram_index": 0,
            "filename": "test_doc3.pdf",
            "similarity_score": 0.9,
            "match_type": "visual",
            "metadata": {"title": "Test Document 3"}
        },
        {
            "document_id": "doc-123",
            "diagram_index": 1,
            "filename": "test_doc1.pdf",
            "similarity_score": 0.65,
            "match_type": "visual",
            "metadata": {"title": "Test Document 1"}
        }
    ]

def test_rank_results(mock_document_results, mock_visual_results):
    """Test the ranking of combined results."""
    # Patch the firestore client
    with patch('src.search.similarity.db'):
        results = similarity.rank_results(
            mock_document_results,
            mock_visual_results,
            text_weight=0.6,
            visual_weight=0.4
        )
        
        # Check if results are returned
        assert len(results) > 0
        
        # Check if doc-123 which appears in both lists is ranked highest
        assert results[0]["document_id"] == "doc-123"
        
        # Check if combined score is calculated
        assert "combined_score" in results[0]
        assert results[0]["combined_score"] > 0
        
        # Check if match types are combined
        assert "match_types" in results[0]
        assert "text" in results[0]["match_types"]
        assert "visual" in results[0]["match_types"]


def test_search_text_similarity(mock_embedding):
    """Test text similarity search."""
    # Mock the MatchingEngine response
    mock_matches = [
        MagicMock(id="doc-123", distance=0.85),
        MagicMock(id="doc-456", distance=0.75)
    ]
    mock_response = [[match for match in mock_matches]]
    
    # Patch necessary components
    with patch('src.search.similarity.aiplatform.MatchingEngineIndexEndpoint') as mock_index_endpoint, \
         patch('src.search.similarity.db') as mock_db:
        
        # Setup mock return values
        mock_index_endpoint.return_value.match.return_value = mock_response
        
        # Mock Firestore document retrieval
        mock_doc1 = MagicMock()
        mock_doc1.exists = True
        mock_doc1.to_dict.return_value = {
            "filename": "test_doc1.pdf",
            "metadata": {"title": "Test Document 1"}
        }
        
        mock_doc2 = MagicMock()
        mock_doc2.exists = True
        mock_doc2.to_dict.return_value = {
            "filename": "test_doc2.pdf",
            "metadata": {"title": "Test Document 2"}
        }
        
        # Mock the document references
        mock_db.collection.return_value.document.side_effect = lambda x: {
            "doc-123": mock_doc1,
            "doc-456": mock_doc2
        }[x]
        
        # Execute the function
        results = similarity.search_text_similarity(mock_embedding, top_k=2)
        
        # Verify results
        assert len(results) == 2
        assert results[0]["document_id"] == "doc-123"
        assert results[0]["similarity_score"] == 0.85
        assert results[0]["match_type"] == "text"
        assert results[1]["document_id"] == "doc-456"
        assert results[1]["similarity_score"] == 0.75
        
        # Verify the match function was called with correct parameters
        mock_index_endpoint.return_value.match.assert_called_once()
        call_args = mock_index_endpoint.return_value.match.call_args[1]
        assert call_args["queries"] == [mock_embedding]
        assert call_args["num_neighbors"] == 2
