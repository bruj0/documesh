"""
Similarity search module for finding similar technical documents.
"""
import os
from typing import Dict, List, Any, Optional, Union, Tuple
import json

from google.cloud import aiplatform
from google.cloud import firestore
from google.cloud import discoveryengine_v1 as discoveryengine

# Import local modules
from ..ingestion import embedding

# Configure environment
PROJECT_ID = os.environ.get("PROJECT_ID", "your-project-id")
LOCATION = os.environ.get("LOCATION", "us-central1")
INDEX_ENDPOINT_ID = os.environ.get("VECTOR_INDEX_ENDPOINT_ID", "your-index-endpoint")
TEXT_INDEX_ID = os.environ.get("TEXT_INDEX_ID", "your-text-index")
VISUAL_INDEX_ID = os.environ.get("VISUAL_INDEX_ID", "your-visual-index")
DATA_STORE_ID = os.environ.get("DATA_STORE_ID", "technical-documents-store")

# Initialize clients
db = firestore.Client()
aiplatform.init(project=PROJECT_ID, location=LOCATION)


def find_similar_documents(
    document_id: Optional[str] = None,
    text_query: Optional[str] = None,
    image_content: Optional[bytes] = None,
    top_k: int = 5,
    filter_criteria: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Find documents similar to the provided document ID or query.
    
    Args:
        document_id: Optional ID of reference document
        text_query: Optional text query
        image_content: Optional image content for visual search
        top_k: Number of results to return
        filter_criteria: Optional filtering criteria
        
    Returns:
        List of similar documents with similarity scores
    """
    if not document_id and not text_query and not image_content:
        raise ValueError("Either document_id, text_query, or image_content must be provided")
    
    # Get embeddings based on input type
    text_embedding = None
    visual_embeddings = []
    
    if document_id:
        # Get embeddings from existing document
        doc_ref = db.collection("documents").document(document_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise ValueError(f"Document with ID {document_id} not found")
            
        doc_data = doc.to_dict()
        text_embedding = doc_data.get("text_embedding", [])
        visual_embeddings = [ve.get("embedding", []) for ve in doc_data.get("visual_embeddings", [])]
        
    elif text_query:
        # Generate embedding from text query
        text_embedding = embedding.generate_text_embedding(text_query)
        
    elif image_content:
        # Generate embedding from image
        visual_embedding = embedding.generate_visual_embedding(image_content)
        visual_embeddings = [visual_embedding]
    
    # Perform similarity search
    text_results = []
    visual_results = []
    
    # Search with text embedding if available
    if text_embedding:
        text_results = search_text_similarity(text_embedding, top_k, filter_criteria)
        
    # Search with visual embeddings if available
    if visual_embeddings:
        visual_results = search_visual_similarity(visual_embeddings, top_k, filter_criteria)
    
    # Combine and rank results
    combined_results = rank_results(text_results, visual_results, text_weight=0.6, visual_weight=0.4)
    
    # Limit to top_k
    return combined_results[:top_k]


def search_text_similarity(
    text_embedding: List[float],
    top_k: int = 5,
    filter_criteria: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Perform text-based vector similarity search.
    
    Args:
        text_embedding: The text embedding vector
        top_k: Number of results to return
        filter_criteria: Optional filtering criteria
        
    Returns:
        List of matching documents with similarity scores
    """
    try:
        # Initialize Vector Search Index Endpoint
        index_endpoint = aiplatform.MatchingEngineIndexEndpoint(index_endpoint_name=INDEX_ENDPOINT_ID)
        
        # Prepare filter string if provided
        filter_str = ""
        if filter_criteria:
            filter_parts = []
            for key, value in filter_criteria.items():
                if isinstance(value, str):
                    filter_parts.append(f"{key}=\"{value}\"")
                else:
                    filter_parts.append(f"{key}={value}")
            
            if filter_parts:
                filter_str = " AND ".join(filter_parts)
        
        # Perform nearest neighbor search
        response = index_endpoint.match(
            deployed_index_id=TEXT_INDEX_ID,
            queries=[text_embedding],
            num_neighbors=top_k,
            filter=filter_str if filter_str else None
        )
        
        # Process results
        results = []
        if response and len(response) > 0:
            for match in response[0]:
                # Get document ID from the match
                document_id = match.id
                
                # Get full document data from Firestore
                doc_ref = db.collection("documents").document(document_id)
                doc = doc_ref.get()
                
                if doc.exists:
                    doc_data = doc.to_dict()
                    
                    # Add result with similarity score
                    results.append({
                        "document_id": document_id,
                        "filename": doc_data.get("filename", ""),
                        "similarity_score": float(match.distance),
                        "match_type": "text",
                        "metadata": doc_data.get("metadata", {})
                    })
        
        return results
    
    except Exception as e:
        print(f"Error in text similarity search: {str(e)}")
        return []


def search_visual_similarity(
    visual_embeddings: List[List[float]],
    top_k: int = 5,
    filter_criteria: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Perform visual-based vector similarity search.
    
    Args:
        visual_embeddings: List of visual embedding vectors
        top_k: Number of results to return
        filter_criteria: Optional filtering criteria
        
    Returns:
        List of matching documents with similarity scores
    """
    try:
        # Initialize Vector Search Index Endpoint
        index_endpoint = aiplatform.MatchingEngineIndexEndpoint(index_endpoint_name=INDEX_ENDPOINT_ID)
        
        # Prepare filter string if provided
        filter_str = ""
        if filter_criteria:
            filter_parts = []
            for key, value in filter_criteria.items():
                if isinstance(value, str):
                    filter_parts.append(f"{key}=\"{value}\"")
                else:
                    filter_parts.append(f"{key}={value}")
            
            if filter_parts:
                filter_str = " AND ".join(filter_parts)
                
        # For multiple visual embeddings, perform search for each and combine
        all_results = []
        
        for visual_embedding in visual_embeddings:
            # Perform nearest neighbor search
            response = index_endpoint.match(
                deployed_index_id=VISUAL_INDEX_ID,
                queries=[visual_embedding],
                num_neighbors=top_k,
                filter=filter_str if filter_str else None
            )
            
            # Process results
            if response and len(response) > 0:
                for match in response[0]:
                    # Get document ID and diagram ID from the match
                    ids = match.id.split(":")
                    if len(ids) == 2:
                        document_id, diagram_index = ids
                        
                        # Get full document data from Firestore
                        doc_ref = db.collection("documents").document(document_id)
                        doc = doc_ref.get()
                        
                        if doc.exists:
                            doc_data = doc.to_dict()
                            
                            # Add result with similarity score
                            all_results.append({
                                "document_id": document_id,
                                "diagram_index": int(diagram_index),
                                "filename": doc_data.get("filename", ""),
                                "similarity_score": float(match.distance),
                                "match_type": "visual",
                                "metadata": doc_data.get("metadata", {})
                            })
        
        # Sort by similarity score
        all_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        # Take top_k results
        return all_results[:top_k]
    
    except Exception as e:
        print(f"Error in visual similarity search: {str(e)}")
        return []


def rank_results(
    text_results: List[Dict[str, Any]],
    visual_results: List[Dict[str, Any]],
    text_weight: float = 0.6,
    visual_weight: float = 0.4
) -> List[Dict[str, Any]]:
    """
    Combine and rank results from text and visual similarity searches.
    
    Args:
        text_results: Results from text similarity search
        visual_results: Results from visual similarity search
        text_weight: Weight to give text results (0-1)
        visual_weight: Weight to give visual results (0-1)
        
    Returns:
        Combined and ranked list of results
    """
    # Normalize weights
    total_weight = text_weight + visual_weight
    text_weight = text_weight / total_weight
    visual_weight = visual_weight / total_weight
    
    # Create a dictionary to combine results by document_id
    combined_results = {}
    
    # Process text results
    for result in text_results:
        document_id = result["document_id"]
        
        if document_id not in combined_results:
            combined_results[document_id] = {
                "document_id": document_id,
                "filename": result.get("filename", ""),
                "metadata": result.get("metadata", {}),
                "text_score": 0.0,
                "visual_score": 0.0,
                "combined_score": 0.0,
                "match_types": []
            }
        
        combined_results[document_id]["text_score"] = result["similarity_score"]
        if "match_type" in result and "text" not in combined_results[document_id]["match_types"]:
            combined_results[document_id]["match_types"].append("text")
    
    # Process visual results
    for result in visual_results:
        document_id = result["document_id"]
        
        if document_id not in combined_results:
            combined_results[document_id] = {
                "document_id": document_id,
                "filename": result.get("filename", ""),
                "metadata": result.get("metadata", {}),
                "text_score": 0.0,
                "visual_score": 0.0,
                "combined_score": 0.0,
                "match_types": []
            }
        
        # Update visual score with the highest similarity
        current_score = combined_results[document_id]["visual_score"]
        new_score = result["similarity_score"]
        combined_results[document_id]["visual_score"] = max(current_score, new_score)
        
        if "match_type" in result and "visual" not in combined_results[document_id]["match_types"]:
            combined_results[document_id]["match_types"].append("visual")
            
        # Add diagram info if not already present
        if "diagrams" not in combined_results[document_id]:
            combined_results[document_id]["diagrams"] = []
            
        if "diagram_index" in result:
            diagram_info = {
                "index": result["diagram_index"],
                "similarity_score": result["similarity_score"]
            }
            combined_results[document_id]["diagrams"].append(diagram_info)
    
    # Calculate combined scores
    for document_id, data in combined_results.items():
        text_score = data["text_score"]
        visual_score = data["visual_score"]
        
        # Calculate weighted average
        if "text" in data["match_types"] and "visual" in data["match_types"]:
            # Both text and visual matches
            data["combined_score"] = (text_weight * text_score) + (visual_weight * visual_score)
        elif "text" in data["match_types"]:
            # Only text match
            data["combined_score"] = text_score
        elif "visual" in data["match_types"]:
            # Only visual match
            data["combined_score"] = visual_score
    
    # Convert to list and sort by combined score
    result_list = list(combined_results.values())
    result_list.sort(key=lambda x: x["combined_score"], reverse=True)
    
    return result_list
