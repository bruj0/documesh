"""
Cloud Function for similarity search functionality.
Performs semantic similarity search on stored PDF embeddings.
"""
import os
import sys
from typing import List, Dict, Any, Optional
from google.cloud import aiplatform

# Add parent directory to path to import shared utilities
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared_utils import initialize_clients, get_embeddings_model, get_db_client, get_vector_search_config

def similarity_search(query: str, top_k: int = 5, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Perform similarity search on stored embeddings."""
    try:
        embeddings_model = get_embeddings_model()
        db_client = get_db_client()
        config = get_vector_search_config()
        
        # Create embedding for the query
        query_embedding = embeddings_model.embed_query(query)
        
        if not config['endpoint_id'] or not config['index_id']:
            print("Vector Search not configured, returning empty results")
            return []
        
        # Get the Vector Search index endpoint
        index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
            index_endpoint_name=config['endpoint_id']
        )
        
        # Prepare restricts for filtering
        restricts = []
        if content_type:
            restricts.append(
                aiplatform.MatchingEngineIndexEndpoint.FindNeighborsRequest.Query.Restriction(
                    namespace="content_type",
                    allow_list=[content_type]
                )
            )
        
        # Create query
        query_obj = aiplatform.MatchingEngineIndexEndpoint.FindNeighborsRequest.Query(
            feature_vector=query_embedding,
            neighbor_count=top_k,
            restricts=restricts if restricts else None
        )
        
        # Perform search
        response = index_endpoint.find_neighbors(
            deployed_index_id=config['index_id'],
            queries=[query_obj]
        )
        
        # Process results
        results = []
        if response.nearest_neighbors:
            for neighbor in response.nearest_neighbors[0].neighbors:
                vector_id = neighbor.datapoint.datapoint_id
                similarity_score = neighbor.distance
                
                # Get metadata from Firestore
                vector_ref = db_client.collection('vector_metadata').document(vector_id)
                vector_doc = vector_ref.get()
                
                if vector_doc.exists:
                    metadata = vector_doc.to_dict()
                    results.append({
                        'vector_id': vector_id,
                        'similarity_score': similarity_score,
                        'document_id': metadata.get('document_id'),
                        'content': metadata.get('content'),
                        'type': metadata.get('type'),
                        'page': metadata.get('page'),
                        'metadata': metadata.get('metadata', {})
                    })
        
        print(f"Found {len(results)} similar items for query: '{query}'")
        return results
        
    except Exception as e:
        print(f"Error in similarity search: {e}")
        return []

def search_similar_documents(request):
    """
    HTTP Cloud Function for similarity search.
    
    Args:
        request: HTTP request object
    
    Returns:
        JSON response with similar documents
    """
    try:
        initialize_clients()
        
        # Parse request
        request_json = request.get_json(silent=True)
        if not request_json or 'query' not in request_json:
            return {'error': 'Query parameter required'}, 400
        
        query = request_json['query']
        top_k = request_json.get('top_k', 5)
        content_type = request_json.get('content_type', None)
        
        # Perform similarity search
        results = similarity_search(query, top_k, content_type)
        
        return {
            'query': query,
            'results': results,
            'count': len(results),
            'content_type_filter': content_type
        }
        
    except Exception as e:
        return {'error': str(e)}, 500

def search_by_document(request):
    """
    HTTP Cloud Function to search for similar documents to a specific document.
    
    Args:
        request: HTTP request object
    
    Returns:
        JSON response with similar documents
    """
    try:
        initialize_clients()
        
        # Parse request
        request_json = request.get_json(silent=True)
        if not request_json or 'document_id' not in request_json:
            return {'error': 'Document ID parameter required'}, 400
        
        document_id = request_json['document_id']
        top_k = request_json.get('top_k', 5)
        content_type = request_json.get('content_type', None)
        
        db_client = get_db_client()
        
        # Get document chunks to use as query
        chunks_ref = db_client.collection('document_chunks').where('document_id', '==', document_id)
        chunks = chunks_ref.limit(1).stream()
        
        # Use the first chunk as the query
        query_text = None
        for chunk in chunks:
            chunk_data = chunk.to_dict()
            query_text = chunk_data.get('content', '')
            break
        
        if not query_text:
            return {'error': 'Document not found or has no content'}, 404
        
        # Perform similarity search
        results = similarity_search(query_text, top_k, content_type)
        
        # Filter out the source document from results
        filtered_results = [r for r in results if r['document_id'] != document_id]
        
        return {
            'source_document_id': document_id,
            'query_text': query_text[:200] + '...' if len(query_text) > 200 else query_text,
            'results': filtered_results,
            'count': len(filtered_results),
            'content_type_filter': content_type
        }
        
    except Exception as e:
        return {'error': str(e)}, 500
