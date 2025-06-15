"""
Tests for document agent functionality.
"""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

from src.agent import document_agent

@pytest.fixture
def mock_document_data():
    """Fixture for mock document data."""
    return {
        "document_id": "doc-123",
        "filename": "test_document.pdf",
        "text_content": "This is a test document for a technical manual",
        "text_embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
        "visual_embeddings": [
            {
                "embedding": [0.5, 0.6, 0.7, 0.8, 0.9],
                "page": 1,
                "bbox": {"x1": 0.1, "y1": 0.2, "x2": 0.8, "y2": 0.9}
            }
        ],
        "metadata": {
            "title": "Technical Manual",
            "pages": 5
        }
    }

@pytest.fixture
def mock_search_results():
    """Fixture for mock search results."""
    return [
        {
            "document_id": "doc-123",
            "filename": "test_document.pdf",
            "similarity_score": 0.85,
            "relevance_score": 0.85,
            "combined_score": 0.85,
            "match_type": "text",
            "metadata": {"title": "Technical Manual"}
        },
        {
            "document_id": "doc-456",
            "filename": "another_doc.pdf",
            "similarity_score": 0.75,
            "relevance_score": 0.75,
            "combined_score": 0.75,
            "match_type": "text",
            "metadata": {"title": "Operating Procedures"}
        }
    ]

def test_find_similar_documents():
    """Test finding similar documents using the agent."""
    with patch('src.agent.document_agent.embedding.generate_text_embedding') as mock_generate_embedding, \
         patch('src.agent.document_agent.similarity.search_text_similarity') as mock_search:
        
        # Configure mocks
        mock_generate_embedding.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_search.return_value = [
            {
                "document_id": "doc-123",
                "filename": "test_document.pdf",
                "similarity_score": 0.85,
                "match_type": "text",
                "metadata": {"title": "Technical Manual"}
            }
        ]
        
        # Call function
        query = "find technical manual"
        results = document_agent.agent.find_similar_documents(query)
        
        # Verify results
        assert len(results) == 1
        assert results[0]["document_id"] == "doc-123"
        assert results[0]["similarity_score"] == 0.85
        
        # Verify embedding generation and search were called
        mock_generate_embedding.assert_called_once_with(query)
        mock_search.assert_called_once()


def test_process_query():
    """Test processing a natural language query through the agent."""
    # Create a mock response object from the ADK agent
    mock_response = MagicMock()
    type(mock_response).text = PropertyMock(return_value="I found these technical documents for you.")
    mock_response.documents = [
        {
            "document_id": "doc-123",
            "title": "Technical Manual",
            "relevance": 0.85
        }
    ]
    mock_response.thinking = "The user is looking for technical documents..."
    
    with patch.object(document_agent.agent.agent, 'chat', return_value=mock_response):
        # Call function
        result = document_agent.agent.process_query(
            query="Find me technical manuals about cooling systems",
            session_id="test-session"
        )
        
        # Verify result structure
        assert "response" in result
        assert "documents" in result
        assert "thinking" in result
        
        # Verify contents
        assert result["response"] == "I found these technical documents for you."
        assert len(result["documents"]) == 1
        assert result["documents"][0]["document_id"] == "doc-123"
        assert result["thinking"] == "The user is looking for technical documents..."


def test_extract_information(mock_document_data):
    """Test extracting information from a document."""
    with patch('src.agent.document_agent.firestore.Client') as mock_firestore, \
         patch.object(document_agent.agent, '_extract_with_llm') as mock_extract:
        
        # Configure mocks
        mock_doc_ref = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = mock_document_data
        mock_doc_ref.get.return_value = mock_doc
        mock_firestore.return_value.collection.return_value.document.return_value = mock_doc_ref
        
        # Mock extraction result
        mock_extract.return_value = {
            "title": "Technical Manual",
            "purpose": "Instruction for cooling system maintenance",
            "components": ["Pump", "Condenser", "Evaporator"]
        }
        
        # Extract information
        fields = ["title", "purpose", "components"]
        info = document_agent.agent.extract_information("doc-123", fields)
        
        # Verify results
        assert "title" in info
        assert info["title"] == "Technical Manual"
        assert "components" in info
        assert len(info["components"]) == 3
        
        # Verify Firestore was queried
        mock_firestore.return_value.collection.return_value.document.assert_called_once_with("doc-123")
        
        # Verify extraction was called
        mock_extract.assert_called_once_with(mock_document_data["text_content"], fields)
