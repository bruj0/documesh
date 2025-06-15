"""
Module for generating vector embeddings for text and visual content.
"""
from typing import List, Dict, Any, Optional
import os

from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel
from vertexai.vision_models import ImageTextModel, Image

# Configure environment
PROJECT_ID = os.environ.get("PROJECT_ID", "your-project-id")
LOCATION = os.environ.get("LOCATION", "us-central1")
TEXT_EMBEDDING_MODEL = os.environ.get("TEXT_EMBEDDING_MODEL", "textembedding-gecko@latest")
MULTIMODAL_MODEL = os.environ.get("MULTIMODAL_MODEL", "multimodalembedding@latest")

# Initialize Vertex AI
aiplatform.init(project=PROJECT_ID, location=LOCATION)


def generate_text_embedding(text: str) -> List[float]:
    """
    Generate embedding vector for text content.
    
    Args:
        text: The text content to generate embeddings for
    
    Returns:
        List of float values representing the embedding vector
    """
    # Initialize text embedding model
    model = TextEmbeddingModel.from_pretrained(TEXT_EMBEDDING_MODEL)
    
    # For long texts, we need to split and combine
    # This is a simplified implementation - production would handle long text better
    if len(text) > 3000:
        # Truncate text if too long
        text = text[:3000]
    
    # Generate embedding
    embeddings = model.get_embeddings([text])
    
    if embeddings and embeddings[0].values:
        return embeddings[0].values
    
    # Return empty vector if failed
    return []


def generate_visual_embedding(image_content: bytes) -> List[float]:
    """
    Generate embedding vector for visual content.
    
    Args:
        image_content: The binary content of the image
    
    Returns:
        List of float values representing the embedding vector
    """
    # In production, use a proper multimodal embedding model
    # For this example, we use a placeholder approach
    
    try:
        # Create Image object from binary content
        image = Image(image_content)
        
        # Use multimodal model to generate embedding
        # Note: This is simplified and would need to be adapted to your specific model
        model = ImageTextModel.from_pretrained(MULTIMODAL_MODEL)
        embedding_response = model.get_embeddings(image=image)
        
        # Extract embedding values
        if embedding_response and hasattr(embedding_response, 'image_embedding'):
            return embedding_response.image_embedding
    except Exception as e:
        print(f"Error generating visual embedding: {str(e)}")
        # In production, handle this error more gracefully
    
    # Return placeholder embedding if failed
    # In production, you should handle this case better
    import random
    return [random.random() for _ in range(512)]  # 512-dimensional placeholder


def combine_embeddings(
    text_embedding: List[float], 
    visual_embeddings: List[List[float]],
    weights: Optional[Dict[str, float]] = None
) -> List[float]:
    """
    Combine text and visual embeddings into a single embedding vector.
    
    Args:
        text_embedding: The text embedding vector
        visual_embeddings: List of visual embedding vectors
        weights: Optional weights for text vs. visual components
    
    Returns:
        Combined embedding vector
    """
    if not weights:
        weights = {"text": 0.6, "visual": 0.4}
        
    import numpy as np
    
    # Convert to numpy arrays for easier manipulation
    text_np = np.array(text_embedding)
    
    # If no visual embeddings, return text embedding
    if not visual_embeddings:
        return text_embedding
        
    # Average visual embeddings if multiple
    if len(visual_embeddings) > 1:
        visual_np = np.mean([np.array(ve) for ve in visual_embeddings], axis=0)
    else:
        visual_np = np.array(visual_embeddings[0])
    
    # Ensure same dimensionality (in production, use proper dimension alignment)
    min_dim = min(len(text_np), len(visual_np))
    text_np = text_np[:min_dim]
    visual_np = visual_np[:min_dim]
    
    # Combine with weights
    combined = (weights["text"] * text_np + weights["visual"] * visual_np)
    
    # Normalize the combined vector
    norm = np.linalg.norm(combined)
    if norm > 0:
        combined = combined / norm
    
    return combined.tolist()
