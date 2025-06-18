"""
Vision processing module for extracting and analyzing diagrams in documents.
"""
import io
from typing import Dict, List, Any, Tuple
import base64

from google.cloud import vision_v1 as vision
from google.cloud import documentai_v1 as documentai
import numpy as np
from PIL import Image

# Initialize Vision client
vision_client = vision.ImageAnnotatorClient()


def extract_diagrams_from_pdf(pdf_content: bytes) -> List[Dict[str, Any]]:
    """
    Extract diagrams from a PDF document.
    
    Args:
        pdf_content: The raw PDF content
    
    Returns:
        List of dictionaries containing diagrams with their metadata
    """
    # For PDF processing, we'd typically:
    # 1. Convert PDF pages to images
    # 2. Process each image with Vision AI
    # 3. Identify diagrams in each page
    
    # This is a simplified implementation that would need to be expanded
    # with PDF library like PyPDF2 or pdf2image in production
    
    # Placeholder for extracted diagrams
    diagrams = []
    
    # TODO: In production, convert PDF to images and process each page
    # For now, we'll simulate finding diagrams on pages 1 and 2
    
    # This would be replaced with actual image extraction from PDF
    # mock_diagram1 = {
    #     "image_content": pdf_content[:1000],  # First 1000 bytes as mock image
    #     "page": 1,
    #     "bbox": {
    #         "x1": 0.1,
    #         "y1": 0.2,
    #         "x2": 0.8,
    #         "y2": 0.7
    #     }
    # }
    
    # mock_diagram2 = {
    #     "image_content": pdf_content[1000:2000],  # Next 1000 bytes as mock image
    #     "page": 2,
    #     "bbox": {
    #         "x1": 0.2,
    #         "y1": 0.3,
    #         "x2": 0.9,
    #         "y2": 0.8
    #     }
    # }
    
    # diagrams.append(mock_diagram1)
    # diagrams.append(mock_diagram2)

    # # Now we will replace the mock diagrams with actual processing
    for diagram in diagrams:
        # Convert the mock image content to a Vision Image object
        image = vision.Image(content=diagram["image_content"])
        
        # Perform object detection
        response = vision_client.object_localization(image=image)
        
        if response.error.message:
            raise Exception(f"Error in object localization: {response.error.message}")
        
        # Process detected objects to identify diagrams
        objects = response.localized_object_annotations
        
        # Identify diagrams in the detected objects
        identified_diagrams = identify_diagrams(objects, None)
    
    return diagrams


def identify_diagrams(
    objects: List[vision.LocalizedObjectAnnotation],
    text_annotation: vision.TextAnnotation
) -> List[Dict[str, Any]]:
    """
    Identify diagrams in an image based on object detection and text analysis.
    
    Args:
        objects: Objects detected in the image
        text_annotation: Text detected in the image
    
    Returns:
        List of dictionaries containing diagram information including:
        - bbox: Bounding box coordinates
        - confidence: Detection confidence score
        - object_type: Type of object detected
        - caption: Associated caption text if found
        - nearby_text: Text elements found near the diagram
    """
    diagrams = []
    
    # Extract text blocks and their locations
    text_blocks = []
    if text_annotation and text_annotation.pages:
        for page in text_annotation.pages:
            for block in page.blocks:
                if not block.bounding_box:
                    continue
                    
                # Get text content
                text = ""
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        for symbol in word.symbols:
                            text += symbol.text
                
                # Get bounding box
                vertices = block.bounding_box.normalized_vertices
                text_bbox = {
                    "x1": vertices[0].x,
                    "y1": vertices[0].y,
                    "x2": vertices[2].x,
                    "y2": vertices[2].y
                }
                
                text_blocks.append({
                    "text": text.strip(),
                    "bbox": text_bbox
                })
    
    # Identify potential diagram objects
    diagram_objects = [obj for obj in objects if _is_likely_diagram(obj)]
    
    for obj in diagram_objects:
        # Extract bounding box
        bbox = {
            "x1": obj.bounding_poly.normalized_vertices[0].x,
            "y1": obj.bounding_poly.normalized_vertices[0].y,
            "x2": obj.bounding_poly.normalized_vertices[2].x,
            "y2": obj.bounding_poly.normalized_vertices[2].y,
        }
        
        # Find nearby text blocks
        nearby_text = []
        caption = None
        
        for text_block in text_blocks:
            # Check if text is near the diagram
            if _is_text_near_diagram(bbox, text_block["bbox"]):
                text = text_block["text"].lower()
                
                # Check if this might be a caption
                if _is_caption_text(text):
                    caption = text_block["text"]
                else:
                    nearby_text.append(text_block["text"])
        
        diagram = {
            "bbox": bbox,
            "confidence": obj.score,
            "object_type": obj.name,
            "caption": caption,
            "nearby_text": nearby_text
        }
        
        diagrams.append(diagram)
    
    return diagrams


def _is_likely_diagram(obj: vision.LocalizedObjectAnnotation) -> bool:
    """
    Determine if an object is likely to be a diagram or technical drawing.
    
    Args:
        obj: The detected object
    
    Returns:
        Boolean indicating if the object is likely a diagram
    """
    diagram_related_objects = [
        "diagram", "chart", "drawing", "graph", "figure",
        "blueprint", "schematic", "technical drawing", "flowchart",
        "architecture", "system", "workflow", "process", "map"
    ]
    
    # Check object name against expanded list
    if any(term in obj.name.lower() for term in diagram_related_objects):
        return True
    
    # Check confidence score and size
    bbox = obj.bounding_poly.normalized_vertices
    width = bbox[2].x - bbox[0].x
    height = bbox[2].y - bbox[0].y
    area = width * height
    
    # Diagrams typically have:
    # 1. High confidence score
    # 2. Significant size (not too small)
    # 3. Reasonable aspect ratio (not extremely narrow)
    if (obj.score > 0.6 and
        area > 0.05 and  # At least 5% of image area
        0.2 < (width / height) < 5  # Reasonable aspect ratio
    ):
        return True
        
    return False


def _is_text_near_diagram(diagram_bbox: Dict[str, float], text_bbox: Dict[str, float]) -> bool:
    """
    Determine if a text block is near a diagram.
    
    Args:
        diagram_bbox: Diagram bounding box coordinates
        text_bbox: Text block bounding box coordinates
    
    Returns:
        Boolean indicating if the text is near the diagram
    """
    # Define proximity threshold (as fraction of diagram size)
    PROXIMITY_THRESHOLD = 0.2
    
    # Calculate diagram dimensions
    diagram_width = diagram_bbox["x2"] - diagram_bbox["x1"]
    diagram_height = diagram_bbox["y2"] - diagram_bbox["y1"]
    
    # Calculate distances to text block
    dx = min(abs(diagram_bbox["x2"] - text_bbox["x1"]),
             abs(diagram_bbox["x1"] - text_bbox["x2"]))
    dy = min(abs(diagram_bbox["y2"] - text_bbox["y1"]),
             abs(diagram_bbox["y1"] - text_bbox["y2"]))
    
    # Text is near if it's within the threshold distance in either direction
    return (dx <= PROXIMITY_THRESHOLD * diagram_width or
            dy <= PROXIMITY_THRESHOLD * diagram_height)


def _is_caption_text(text: str) -> bool:
    """
    Determine if text appears to be a diagram caption.
    
    Args:
        text: The text to analyze
    
    Returns:
        Boolean indicating if the text appears to be a caption
    """
    caption_indicators = [
        "figure", "fig.", "fig", "diagram", "illustration",
        "chart", "graph", "drawing", "schematic"
    ]
    
    text_lower = text.lower()
    
    # Check for caption indicators at start of text
    for indicator in caption_indicators:
        if text_lower.startswith(indicator):
            return True
    
    # Check for common caption patterns (e.g., "Figure 1:", "Fig. 1.2")
    import re
    caption_patterns = [
        r"^(figure|fig\.?)\s*\d+[.:)]",
        r"^diagram\s*\d+[.:)]",
        r"^illustration\s*\d+[.:)]"
    ]
    
    for pattern in caption_patterns:
        if re.match(pattern, text_lower):
            return True
    
    return False


def extract_image_from_region(
    image_content: bytes, 
    bbox: Dict[str, float]
) -> bytes:
    """
    Extract a region from an image based on a bounding box.
    
    Args:
        image_content: The full image content
        bbox: Normalized coordinates (x1,y1,x2,y2) for the bounding box
    
    Returns:
        Binary content of the extracted region
    """
    # Convert image content to PIL Image
    image = Image.open(io.BytesIO(image_content))
    
    # Get actual pixel coordinates from normalized coordinates
    width, height = image.size
    x1 = int(bbox["x1"] * width)
    y1 = int(bbox["y1"] * height)
    x2 = int(bbox["x2"] * width)
    y2 = int(bbox["y2"] * height)
    
    # Crop image to the specified region
    region = image.crop((x1, y1, x2, y2))
    
    # Convert back to bytes
    output = io.BytesIO()
    region.save(output, format=image.format or 'PNG')
    
    return output.getvalue()
