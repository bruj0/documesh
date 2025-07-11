"""
Cloud Function to process PDF documents uploaded to Google Cloud Storage.
Extracts text and images, creates embeddings using Vertex AI, and stores them 
in Vector Search for similarity search functionality.
"""
import os
import hashlib
import base64
import sys
from typing import List, Dict, Any
from google.cloud import storage
from google.cloud import aiplatform
from google.cloud import firestore
from langchain.text_splitter import RecursiveCharacterTextSplitter
import fitz  # PyMuPDF

# Add parent directory to path to import shared utilities
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared_utils import initialize_clients, get_embeddings_model, get_db_client, get_vector_search_config

def extract_text_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """Extract text from PDF pages and split into chunks."""
    text_chunks = []
    doc = fitz.open(pdf_path)
    
    # Initialize text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        
        if text.strip():
            # Split text into chunks
            chunks = text_splitter.split_text(text)
            for i, chunk in enumerate(chunks):
                text_chunks.append({
                    'content': chunk,
                    'type': 'text',
                    'page': page_num + 1,
                    'chunk_id': f"page_{page_num + 1}_chunk_{i + 1}",
                    'metadata': {
                        'page_number': page_num + 1,
                        'chunk_index': i + 1,
                        'content_type': 'text'
                    }
                })
    
    doc.close()
    return text_chunks

def extract_images_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """Extract images from PDF pages."""
    images = []
    doc = fitz.open(pdf_path)
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        image_list = page.get_images()
        
        for img_index, img in enumerate(image_list):
            try:
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                
                if pix.n - pix.alpha < 4:  # GRAY or RGB
                    img_data = pix.tobytes("png")
                    
                    # Convert image to base64 for storage
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    
                    # Create text description for embedding
                    img_description = f"Image from page {page_num + 1}, position {img_index + 1}"
                    
                    images.append({
                        'content': img_description,  # Text description for embedding
                        'image_data': img_base64,
                        'type': 'image',
                        'page': page_num + 1,
                        'image_id': f"page_{page_num + 1}_img_{img_index + 1}",
                        'format': 'png',
                        'metadata': {
                            'page_number': page_num + 1,
                            'image_index': img_index + 1,
                            'content_type': 'image',
                            'format': 'png'
                        }
                    })
                
                pix = None
            except Exception as e:
                print(f"Error extracting image {img_index} from page {page_num + 1}: {e}")
                continue
    
    doc.close()
    return images

def create_embeddings(content_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create embeddings for text content using Vertex AI."""
    embeddings_model = get_embeddings_model()
    texts = [item['content'] for item in content_items]
    
    try:
        # Generate embeddings using Vertex AI
        embeddings = embeddings_model.embed_documents(texts)
        
        for i, item in enumerate(content_items):
            item['embedding'] = embeddings[i]
            item['embedding_hash'] = hashlib.md5(str(embeddings[i]).encode()).hexdigest()
        
        return content_items
    except Exception as e:
        print(f"Error creating embeddings: {e}")
        raise

def store_in_firestore(document_id: str, text_chunks: List[Dict[str, Any]], 
                      images: List[Dict[str, Any]], metadata: Dict[str, Any]):
    """Store document metadata and content in Firestore."""
    db_client = get_db_client()
    
    # Store document metadata
    doc_ref = db_client.collection('documents').document(document_id)
    doc_ref.set({
        'filename': metadata['filename'],
        'bucket': metadata['bucket'],
        'file_path': metadata['file_path'],
        'created_at': firestore.SERVER_TIMESTAMP,
        'total_text_chunks': len(text_chunks),
        'total_images': len(images),
        'status': 'processed',
        'processing_metadata': metadata
    })
    
    # Store text chunks
    for chunk in text_chunks:
        chunk_ref = db_client.collection('document_chunks').document()
        chunk_ref.set({
            'document_id': document_id,
            'content': chunk['content'],
            'embedding_hash': chunk['embedding_hash'],
            'page': chunk['page'],
            'chunk_id': chunk['chunk_id'],
            'type': chunk['type'],
            'metadata': chunk['metadata'],
            'created_at': firestore.SERVER_TIMESTAMP
        })
    
    # Store images
    for image in images:
        img_ref = db_client.collection('document_chunks').document()
        img_ref.set({
            'document_id': document_id,
            'content': image['content'],
            'image_data': image['image_data'],
            'embedding_hash': image['embedding_hash'],
            'page': image['page'],
            'image_id': image['image_id'],
            'type': image['type'],
            'metadata': image['metadata'],
            'created_at': firestore.SERVER_TIMESTAMP
        })

def store_in_vector_search(content_items: List[Dict[str, Any]], document_id: str):
    """Store embeddings in Vertex AI Vector Search."""
    config = get_vector_search_config()
    db_client = get_db_client()
    
    if not config['endpoint_id'] or not config['index_id']:
        print("Vector Search endpoint or index not configured, skipping vector storage")
        return
    
    try:
        # Get the Vector Search index
        index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
            index_endpoint_name=config['endpoint_id']
        )
        
        # Prepare data for Vector Search
        datapoints = []
        for item in content_items:
            vector_id = f"{document_id}_{item.get('chunk_id', item.get('image_id', 'unknown'))}"
            
            # Create datapoint for Vector Search
            datapoint = aiplatform.MatchingEngineIndexEndpoint.Datapoint(
                datapoint_id=vector_id,
                feature_vector=item['embedding'],
                restricts=[
                    aiplatform.MatchingEngineIndexEndpoint.Datapoint.Restriction(
                        namespace="document_id",
                        allow_list=[document_id]
                    ),
                    aiplatform.MatchingEngineIndexEndpoint.Datapoint.Restriction(
                        namespace="content_type",
                        allow_list=[item['type']]
                    )
                ]
            )
            datapoints.append(datapoint)
        
        # Upsert vectors to the index
        if datapoints:
            response = index_endpoint.upsert_datapoints(
                deployed_index_id=config['index_id'],
                datapoints=datapoints
            )
            print(f"Successfully stored {len(datapoints)} vectors in Vector Search")
            
            # Also store metadata in Firestore for reference
            for i, item in enumerate(content_items):
                vector_id = f"{document_id}_{item.get('chunk_id', item.get('image_id', 'unknown'))}"
                vector_ref = db_client.collection('vector_metadata').document(vector_id)
                vector_ref.set({
                    'document_id': document_id,
                    'content': item['content'][:500],  # Truncate for storage
                    'type': item['type'],
                    'page': item['page'],
                    'metadata': item.get('metadata', {}),
                    'created_at': firestore.SERVER_TIMESTAMP
                })
        
    except Exception as e:
        print(f"Error storing in Vector Search: {e}")

def process_document(event, context):
    """
    Background Cloud Function to be triggered by Cloud Storage.
    Processes PDF files, extracts text and images, creates embeddings,
    and stores them for similarity search.
    
    Args:
         event (dict): The dictionary with data specific to this type of event.
         context (google.cloud.functions.Context): Metadata of triggering event.
    """
    bucket_name = event['bucket']
    file_name = event['name']
    temp_file_path = None
    
    # Only process PDF files
    if not file_name.lower().endswith('.pdf'):
        print(f"Skipping non-PDF file: {file_name}")
        return
    
    print(f"Processing PDF file: gs://{bucket_name}/{file_name}")
    
    try:
        # Initialize clients
        initialize_clients()
        
        # Initialize GCS client
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        
        # Download file content
        temp_file_path = f"/tmp/{os.path.basename(file_name)}"
        blob.download_to_filename(temp_file_path)
        print(f"Downloaded PDF to {temp_file_path}")
        
        # Generate document ID
        document_id = hashlib.md5(f"{bucket_name}/{file_name}".encode()).hexdigest()
        
        # Extract text and images
        print("Extracting text from PDF...")
        text_chunks = extract_text_from_pdf(temp_file_path)
        print(f"Extracted {len(text_chunks)} text chunks")
        
        print("Extracting images from PDF...")
        images = extract_images_from_pdf(temp_file_path)
        print(f"Extracted {len(images)} images")
        
        # Combine all content for embedding
        all_content = text_chunks + images
        
        if all_content:
            # Create embeddings
            print("Creating embeddings...")
            all_content = create_embeddings(all_content)
            
            # Store in Firestore
            print("Storing in Firestore...")
            metadata = {
                'filename': os.path.basename(file_name),
                'bucket': bucket_name,
                'file_path': file_name,
                'file_size': blob.size,
                'content_type': blob.content_type
            }
            store_in_firestore(document_id, text_chunks, images, metadata)
            
            # Store in Vector Search
            print("Storing in Vector Search...")
            store_in_vector_search(all_content, document_id)
            
            print(f"Successfully processed {file_name}")
        else:
            print(f"No content extracted from {file_name}")
        
    except Exception as e:
        print(f"Error processing {file_name}: {e}")
        raise
    
    finally:
        # Clean up temp file
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            print(f"Removed temp file {temp_file_path}")
