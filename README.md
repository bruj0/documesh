
# PDF Ingestion and Similarity Search System

This system provides a complete solution for ingesting PDF documents, extracting text and images, creating embeddings using Google's Vertex AI, and performing similarity searches using Google's Vector Search service.

## Architecture

The system consists of three main components:

1. **PDF Ingestion Function** (`pdf_ingestion/main.py`): A background Cloud Function triggered by Cloud Storage uploads
2. **Similarity Search Function** (`search/main.py`): HTTP Cloud Functions for querying similar content
3. **Shared Utilities** (`shared_utils.py`): Common initialization and helper functions

## Directory Structure

```
app2/
├── src/functions/
│   ├── shared_utils.py         # Shared utilities for both functions
│   ├── pdf_ingestion/          # PDF ingestion function
│   │   ├── main.py            # PDF processing logic
│   │   └── requirements.txt   # Dependencies for PDF function
│   └── search/                # Search functions
│       ├── main.py           # Search logic
│       └── requirements.txt  # Dependencies for search function
├── deploy.sh                  # Deployment script for all functions
├── vector_search_setup.sh     # Vector Search setup
├── vector_search_metadata.json # Vector Search configuration
├── test_search.py            # Test script
└── README.md                 # This file
```

## Features

- **PDF Processing**: Extracts text and images from PDF documents using PyMuPDF
- **Smart Text Chunking**: Splits text into manageable chunks with overlap for better embedding quality
- **Image Extraction**: Extracts and processes images from PDFs
- **Vertex AI Embeddings**: Uses Google's `textembedding-gecko@003` model for high-quality embeddings
- **Vector Search**: Stores embeddings in Google's Vector Search for fast similarity queries
- **Metadata Storage**: Stores document metadata and content in Firestore
- **Multiple Search Types**: 
  - Text-based similarity search
  - Document-to-document similarity search
  - Content type filtering (text/image)

## Deployed Functions

### 1. PDF Ingestion Function
- **Function Name**: `pdf-ingestion-function`
- **Trigger**: Cloud Storage uploads (PDF files only)
- **Purpose**: Processes uploaded PDFs and creates embeddings

### 2. Similarity Search Function
- **Function Name**: `pdf-search-function`
- **Trigger**: HTTP POST requests
- **Purpose**: Performs text-based similarity search

### 3. Document Search Function
- **Function Name**: `pdf-document-search-function`
- **Trigger**: HTTP POST requests  
- **Purpose**: Finds documents similar to a given document

## API Endpoints

### PDF Ingestion
1. Upload a PDF file to your configured Cloud Storage bucket
2. The function will automatically process it and create embeddings

### Text-based Search
```bash
curl -X POST "https://your-region-your-project.cloudfunctions.net/pdf-search-function" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "financial statements",
    "top_k": 5,
    "content_type": "text"
  }'
```

### Document-to-Document Search
```bash
curl -X POST "https://your-region-your-project.cloudfunctions.net/pdf-document-search-function" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "your-document-id",
    "top_k": 5
  }'
```

### Testing
Run the test script to verify functionality:

```bash
python test_search.py
```

## Dependencies

### PDF Processing Function
- `google-cloud-storage`: Cloud Storage integration
- `google-cloud-firestore`: Document metadata storage
- `google-cloud-aiplatform`: Vertex AI and Vector Search
- `langchain-google-vertexai`: Vertex AI embeddings
- `PyMuPDF`: PDF processing

### Search Function
- `google-cloud-firestore`: Document metadata storage
- `google-cloud-aiplatform`: Vector Search
- `langchain-google-vertexai`: Vertex AI embeddings


## Implementation Flow

### Document Ingestion Pipeline
```
User uploads document → Cloud Storage → Cloud Function trigger → Document AI processing → 
Extract text & visual elements → Generate embeddings → Store in Vector Search & Vertex AI Search
```
