"""
Module for generating vector embeddings for text and visual content.
"""
from typing import List, Dict, Any, Optional
import os

from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel
from vertexai.vision_models import ImageTextModel, Image, MultiModalEmbeddingModel
from google.genai.types import EmbedContentConfig
from google.genai import Client

# Configure environment
PROJECT_ID = os.environ.get("PROJECT_ID","hacker2025-team-5-dev")
LOCATION = os.environ.get("LOCATION", "us-central1")
TEXT_EMBEDDING_MODEL = os.environ.get("TEXT_EMBEDDING_MODEL","gemini-embedding-001")
# MULTIMODAL_MODEL = os.environ.get("MULTIMODAL_MODEL","gemini-vision-001")

# import vertexai

# from vertexai.vision_models import Image, MultiModalEmbeddingModel

# # TODO(developer): Update & uncomment line below
# # PROJECT_ID = "your-project-id"
# vertexai.init(project=PROJECT_ID, location="us-central1")

# # TODO(developer): Try different dimenions: 128, 256, 512, 1408
# embedding_dimension = 128

# model = MultiModalEmbeddingModel.from_pretrained("imagetextmodel@001")
# image = Image.load_from_file(
#     "gs://cloud-samples-data/vertex-ai/llm/prompts/landmark1.png"
# )

# embeddings = model.get_embeddings(
#     image=image,
#     contextual_text="Colosseum",
#     dimension=embedding_dimension,
# )

# print(f"Image Embedding: {embeddings.image_embedding}")
# print(f"Text Embedding: {embeddings.text_embedding}")

def generate_text_embedding(text: str) -> List[float]:
    """
    Generate embedding vector for text content.
    
    Args:
        text: The text content to generate embeddings for
    
    Returns:
        List of float values representing the embedding vector
    """
    print(PROJECT_ID)
    print(LOCATION)
    client = Client(vertexai = True, project = PROJECT_ID, location = LOCATION)
    response = client.models.embed_content(
        model= TEXT_EMBEDDING_MODEL,
        contents = text,
        config=EmbedContentConfig(
         task_type="RETRIEVAL_DOCUMENT",  # Optional
         output_dimensionality=3072,  # Optional
        #  title="Driver's License",  # Optional
        ),
    )
    
    print(response)


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
        model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")
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
