"""
API routes for search operations.
"""
import os
from typing import Dict, List, Optional, Any
import base64

from fastapi import APIRouter, UploadFile, File, Form, Query, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import local modules
from ...search import similarity, ranking

router = APIRouter()

# Models
class TextSearchRequest(BaseModel):
    """Text search request model."""
    query: str
    filters: Optional[Dict[str, Any]] = None
    limit: Optional[int] = 10
    text_weight: Optional[float] = 0.6
    visual_weight: Optional[float] = 0.4


class DocumentSimilarityRequest(BaseModel):
    """Document similarity request model."""
    document_id: str
    limit: Optional[int] = 10
    filters: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    """Search response model."""
    results: List[Dict[str, Any]]
    total_count: int
    query_time_ms: float


@router.post("/text", response_model=SearchResponse)
async def search_by_text(request: TextSearchRequest):
    """
    Search documents by text query.
    
    Args:
        request: The search request
    """
    try:
        import time
        start_time = time.time()
        
        # Get embeddings for the query text
        from ...ingestion import embedding
        query_embedding = embedding.generate_text_embedding(request.query)
        
        # Perform search
        results = similarity.search_text_similarity(
            query_embedding, 
            top_k=request.limit or 10,
            filter_criteria=request.filters
        )
        
        # Rank results
        query_context = {
            "text_emphasis": True,  # Since this is a text query
            "query": request.query
        }
        ranked_results = ranking.rank_document_list(results, query_context)
        
        # Add diversity
        diverse_results = ranking.diversify_results(ranked_results)
        
        # Calculate query time
        query_time_ms = (time.time() - start_time) * 1000
        
        return {
            "results": diverse_results,
            "total_count": len(diverse_results),
            "query_time_ms": query_time_ms
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching by text: {str(e)}")


@router.post("/visual", response_model=SearchResponse)
async def search_by_image(
    file: UploadFile = File(...),
    limit: int = Form(10)
):
    """
    Search documents by image similarity.
    
    Args:
        file: The image file to search with
        limit: Maximum number of results to return
    """
    try:
        import time
        start_time = time.time()
        
        # Read image file
        image_content = await file.read()
        
        # Generate visual embedding
        from ...ingestion import embedding
        visual_embedding = embedding.generate_visual_embedding(image_content)
        
        # Perform search
        results = similarity.search_visual_similarity(
            [visual_embedding],
            top_k=limit
        )
        
        # Rank results
        query_context = {
            "visual_emphasis": True  # Since this is a visual query
        }
        ranked_results = ranking.rank_document_list(results, query_context)
        
        # Add diversity
        diverse_results = ranking.diversify_results(ranked_results)
        
        # Calculate query time
        query_time_ms = (time.time() - start_time) * 1000
        
        return {
            "results": diverse_results,
            "total_count": len(diverse_results),
            "query_time_ms": query_time_ms
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching by image: {str(e)}")


@router.post("/similar", response_model=SearchResponse)
async def find_similar_documents(request: DocumentSimilarityRequest):
    """
    Find documents similar to a reference document.
    
    Args:
        request: The similarity request
    """
    try:
        import time
        start_time = time.time()
        
        # Find similar documents
        results = similarity.find_similar_documents(
            document_id=request.document_id,
            top_k=request.limit or 10,
            filter_criteria=request.filters
        )
        
        # Calculate query time
        query_time_ms = (time.time() - start_time) * 1000
        
        return {
            "results": results,
            "total_count": len(results),
            "query_time_ms": query_time_ms
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding similar documents: {str(e)}")


@router.post("/hybrid", response_model=SearchResponse)
async def hybrid_search(
    query: str = Form(...),
    file: Optional[UploadFile] = File(None),
    limit: int = Form(10),
    text_weight: float = Form(0.6),
    visual_weight: float = Form(0.4)
):
    """
    Perform hybrid search with both text and image inputs.
    
    Args:
        query: The text query
        file: Optional image file
        limit: Maximum number of results to return
        text_weight: Weight for text results (0-1)
        visual_weight: Weight for visual results (0-1)
    """
    try:
        import time
        start_time = time.time()
        
        # Generate text embedding
        from ...ingestion import embedding
        text_embedding = embedding.generate_text_embedding(query)
        
        # Get text search results
        text_results = similarity.search_text_similarity(
            text_embedding,
            top_k=limit
        )
        
        visual_results = []
        
        # If image provided, get visual search results
        if file:
            image_content = await file.read()
            visual_embedding = embedding.generate_visual_embedding(image_content)
            
            visual_results = similarity.search_visual_similarity(
                [visual_embedding],
                top_k=limit
            )
        
        # Combine and rank results
        combined_results = similarity.rank_results(
            text_results,
            visual_results,
            text_weight=text_weight,
            visual_weight=visual_weight
        )
        
        # Add diversity
        diverse_results = ranking.diversify_results(combined_results)
        
        # Calculate query time
        query_time_ms = (time.time() - start_time) * 1000
        
        return {
            "results": diverse_results[:limit],
            "total_count": len(diverse_results),
            "query_time_ms": query_time_ms
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing hybrid search: {str(e)}")
