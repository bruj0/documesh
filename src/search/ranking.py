"""
Document ranking module for technical document management system.
"""
from typing import Dict, List, Any, Optional, Tuple
import math


def calculate_relevance_score(
    text_score: float,
    visual_score: float,
    text_weight: float = 0.6,
    visual_weight: float = 0.4,
    metadata: Optional[Dict[str, Any]] = None
) -> float:
    """
    Calculate relevance score based on text and visual similarity scores.
    
    Args:
        text_score: Text similarity score
        visual_score: Visual similarity score
        text_weight: Weight for text score
        visual_weight: Weight for visual score
        metadata: Optional document metadata to consider
        
    Returns:
        Combined relevance score
    """
    # Normalize weights
    total_weight = text_weight + visual_weight
    text_weight = text_weight / total_weight
    visual_weight = visual_weight / total_weight
    
    # Calculate weighted score
    weighted_score = (text_weight * text_score) + (visual_weight * visual_score)
    
    # Apply metadata-based adjustments if available
    if metadata:
        # Example: boost recent documents
        if "created_date" in metadata:
            import datetime
            created_date = metadata["created_date"]
            today = datetime.datetime.now()
            
            # Boost recent documents by up to 10%
            if isinstance(created_date, datetime.datetime):
                days_old = (today - created_date).days
                if days_old < 30:  # Less than a month old
                    recency_boost = 1.0 - (days_old / 30.0) * 0.1  # Up to 10% boost
                    weighted_score *= recency_boost
        
        # Example: boost by view count (popular documents)
        if "view_count" in metadata:
            view_count = metadata["view_count"]
            if view_count > 0:
                popularity_boost = min(1.0 + (math.log10(view_count) * 0.05), 1.1)  # Up to 10% boost
                weighted_score *= popularity_boost
    
    return weighted_score


def rank_document_list(
    documents: List[Dict[str, Any]],
    query_context: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Rank a list of documents based on relevance scores and query context.
    
    Args:
        documents: List of document dictionaries with similarity scores
        query_context: Optional context about the query for personalization
        
    Returns:
        Ranked list of documents
    """
    # Deep copy to avoid modifying the original list
    import copy
    ranked_docs = copy.deepcopy(documents)
    
    # Calculate final relevance score for each document
    for doc in ranked_docs:
        # Get scores
        text_score = doc.get("text_score", 0.0)
        visual_score = doc.get("visual_score", 0.0)
        metadata = doc.get("metadata", {})
        
        # Default weights
        text_weight = 0.6
        visual_weight = 0.4
        
        # Adjust weights based on query context
        if query_context:
            # If query requests visual emphasis
            if query_context.get("visual_emphasis", False):
                text_weight = 0.4
                visual_weight = 0.6
            
            # If query requests text emphasis
            if query_context.get("text_emphasis", False):
                text_weight = 0.7
                visual_weight = 0.3
        
        # Calculate final relevance score
        doc["relevance_score"] = calculate_relevance_score(
            text_score, visual_score, text_weight, visual_weight, metadata
        )
    
    # Sort by relevance score (descending)
    ranked_docs.sort(key=lambda x: x.get("relevance_score", 0.0), reverse=True)
    
    return ranked_docs


def diversify_results(
    ranked_docs: List[Dict[str, Any]], 
    diversity_threshold: float = 0.3
) -> List[Dict[str, Any]]:
    """
    Re-rank results to ensure diversity in the top results.
    
    Args:
        ranked_docs: List of ranked documents
        diversity_threshold: Threshold for considering documents too similar
        
    Returns:
        Re-ranked list with improved diversity
    """
    if not ranked_docs:
        return []
        
    # Implementation of Maximum Marginal Relevance (MMR) algorithm
    # to balance relevance and diversity
    
    # Start with the most relevant document
    diversified_results = [ranked_docs[0]]
    candidates = ranked_docs[1:]
    
    while candidates and len(diversified_results) < len(ranked_docs):
        # Calculate diversity scores for each remaining candidate
        max_mmr_score = -float('inf')
        best_candidate_idx = -1
        
        for i, candidate in enumerate(candidates):
            # Relevance component
            relevance_score = candidate.get("relevance_score", 0.0)
            
            # Diversity component: maximum similarity to documents already selected
            max_similarity = 0.0
            for selected_doc in diversified_results:
                # Calculate similarity between candidate and selected document
                # This is a simplified approach - in production, use proper similarity calculation
                if candidate["document_id"] == selected_doc["document_id"]:
                    similarity = 1.0
                else:
                    # Get shared match types
                    candidate_types = set(candidate.get("match_types", []))
                    selected_types = set(selected_doc.get("match_types", []))
                    type_overlap = len(candidate_types.intersection(selected_types))
                    
                    # Simple similarity heuristic
                    similarity = type_overlap / max(len(candidate_types), len(selected_types), 1)
                
                max_similarity = max(max_similarity, similarity)
            
            # MMR formula: λ*relevance - (1-λ)*max_similarity
            # Higher λ values favor relevance, lower values favor diversity
            lambda_val = 0.7  # Balance between relevance and diversity
            mmr_score = lambda_val * relevance_score - (1 - lambda_val) * max_similarity
            
            if mmr_score > max_mmr_score:
                max_mmr_score = mmr_score
                best_candidate_idx = i
        
        # Add the candidate with highest MMR score
        if best_candidate_idx >= 0:
            diversified_results.append(candidates[best_candidate_idx])
            candidates.pop(best_candidate_idx)
        else:
            break
    
    return diversified_results
