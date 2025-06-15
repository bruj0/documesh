"""
API routes for agent operations.
"""
import os
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import local modules
from ...agent import document_agent

router = APIRouter()

# Models
class AgentQueryRequest(BaseModel):
    """Agent query request model."""
    query: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class AgentQueryResponse(BaseModel):
    """Agent query response model."""
    response: str
    documents: Optional[List[Dict[str, Any]]] = None
    session_id: str
    thinking: Optional[str] = None


@router.post("/query", response_model=AgentQueryResponse)
async def query_agent(request: AgentQueryRequest):
    """
    Query the document agent using natural language.
    
    Args:
        request: The agent query request
    """
    try:
        # Initialize or retrieve agent session
        session_id = request.session_id or f"session-{os.urandom(8).hex()}"
        
        # Process query through ADK agent
        result = document_agent.agent.process_query(
            query=request.query,
            session_id=session_id,
            context=request.context or {}
        )
        
        # Format response
        return {
            "response": result.get("response", "I couldn't process your request."),
            "documents": result.get("documents", []),
            "session_id": session_id,
            "thinking": result.get("thinking")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing agent query: {str(e)}")


@router.post("/extract-info", response_model=Dict[str, Any])
async def extract_document_info(
    document_id: str = Body(...),
    fields: Optional[List[str]] = Body(None)
):
    """
    Extract specific information from a document using the agent.
    
    Args:
        document_id: The document ID
        fields: Optional list of fields to extract
    """
    try:
        # Use agent to extract information
        extracted_info = document_agent.extract_information(
            document_id=document_id,
            fields=fields
        )
        
        return {
            "document_id": document_id,
            "extracted_info": extracted_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting document information: {str(e)}")


@router.post("/summarize", response_model=Dict[str, Any])
async def summarize_document(
    document_id: str = Body(...),
    max_length: Optional[int] = Body(500)
):
    """
    Generate a summary of a document using the agent.
    
    Args:
        document_id: The document ID
        max_length: Maximum length of the summary
    """
    try:
        # Use agent to summarize document
        summary = document_agent.summarize_document(
            document_id=document_id,
            max_length=max_length
        )
        
        return {
            "document_id": document_id,
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error summarizing document: {str(e)}")


@router.post("/compare", response_model=Dict[str, Any])
async def compare_documents(
    document_ids: List[str] = Body(...),
    aspects: Optional[List[str]] = Body(None)
):
    """
    Compare multiple documents using the agent.
    
    Args:
        document_ids: List of document IDs to compare
        aspects: Optional list of aspects to focus on
    """
    try:
        if len(document_ids) < 2:
            raise HTTPException(status_code=400, detail="At least 2 documents required for comparison")
        
        # Use agent to compare documents
        comparison = document_agent.compare_documents(
            document_ids=document_ids,
            aspects=aspects
        )
        
        return {
            "document_ids": document_ids,
            "comparison": comparison
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error comparing documents: {str(e)}")
