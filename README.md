
# PDF Ingestion and Similarity Search System

This system provides a complete solution for ingesting PDF documents, extracting text and images, creating embeddings using Google's Vertex AI, and performing similarity searches using Google's Vector Search service.

## Architecture

The system consists of two main components:

1. **PDF Ingestion Function** (`process_document`): A background Cloud Function triggered by Cloud Storage uploads
2. **Similarity Search Function** (`search_similar_documents`): An HTTP Cloud Function for querying similar content

## Features

- **PDF Processing**: Extracts text and images from PDF documents using PyMuPDF
- **Smart Text Chunking**: Splits text into manageable chunks with overlap for better embedding quality
- **Image Extraction**: Extracts and processes images from PDFs
- **Vertex AI Embeddings**: Uses Google's `textembedding-gecko@003` model for high-quality embeddings
- **Vector Search**: Stores embeddings in Google's Vector Search for fast similarity queries
- **Metadata Storage**: Stores document metadata and content in Firestore
- **Similarity Search**: Performs semantic similarity search across all ingested documents

## Setup Instructions

### 1. Prerequisites

- Google Cloud Project with billing enabled
- Cloud Functions API enabled
- Vertex AI API enabled
- Firestore API enabled
- Cloud Storage bucket for PDF uploads

### 2. Environment Setup

Set the following environment variables:

```bash
export GCP_PROJECT="your-project-id"
export LOCATION="us-central1"
export VECTOR_SEARCH_ENDPOINT_ID="your-endpoint-id"
export VECTOR_SEARCH_INDEX_ID="your-index-id"
```

### 3. Create Vector Search Index

Run the vector search setup script:

```bash
chmod +x vector_search_setup.sh
./vector_search_setup.sh
```

### 4. Deploy Cloud Functions

Update the configuration in `deploy.sh` and run:

```bash
chmod +x deploy.sh
./deploy.sh
```

## Usage

### PDF Ingestion

1. Upload a PDF file to your configured Cloud Storage bucket
2. The function will automatically:
   - Extract text and images
   - Create embeddings
   - Store in Firestore and Vector Search

### Similarity Search

Send a POST request to the search function:

```bash
curl -X POST "https://your-region-your-project.cloudfunctions.net/pdf-search-function" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "financial statements",
    "top_k": 5
  }'
```

## File Structure

```
app2/
├── src/functions/
│   ├── main.py                 # Main function code
│   └── requirements.txt        # Python dependencies
├── deploy.sh                   # Deployment script
├── vector_search_setup.sh      # Vector Search setup
├── vector_search_metadata.json # Vector Search configuration
├── test_search.py             # Test script
└── README.md                  # This file
```

## Dependencies

The system uses the following key dependencies:

- `google-cloud-storage`: Cloud Storage integration
- `google-cloud-firestore`: Document metadata storage
- `google-cloud-aiplatform`: Vertex AI and Vector Search
- `langchain-google-vertexai`: Vertex AI embeddings
- `PyMuPDF`: PDF processing
- `Pillow`: Image processing
* OpenTofu for infrastructure as code
* The Agent Development Kit provided by Google

## System Architecture

### Core Components
1. **Document Storage & Processing Pipeline**
2. **Search & Similarity Analysis System**
3. **API Layer & Agent Interface**
4. **Infrastructure as Code (OpenTofu)**

### Google Cloud Services Used

#### 1. Document Ingestion & Storage
- **Cloud Storage**: For raw document storage
- **Document AI**: To process and extract text/structure from documents
- **Vertex AI Vision**: For processing and analyzing visual diagrams

#### 2. Document Understanding & Search
- **Vertex AI Search**: Enterprise search capabilities for text content
- **Vertex AI Vector Search**: For similarity matching of visual diagrams and content
- **Vertex AI Embeddings**: To generate embeddings for both text and visual content

#### 3. Application Infrastructure
- **Cloud Run**: For hosting the API and web interface
- **Cloud Functions**: For event-driven document processing
- **Firestore**: For metadata storage and document relationships
- **Pub/Sub**: For asynchronous event processing
- **Cloud Logging & Monitoring**: For system observability

## Implementation Flow

### Document Ingestion Pipeline
```
User uploads document → Cloud Storage → Cloud Function trigger → Document AI processing → 
Extract text & visual elements → Generate embeddings → Store in Vector Search & Vertex AI Search
```

### Similarity Analysis Workflow
When a new document is added:
1. Extract text content with Document AI
2. Identify and separate diagrams using Vertex AI Vision
3. Generate embeddings for text and visual content
4. Perform vector similarity search against existing content
5. Rank and return similar documents
6. Store results in database and present to user

## Directory Structure

```
/app2
  /src
    /ingestion          # Document processing pipeline
      processor.py      # Document AI integration
      vision.py         # Vertex AI Vision integration
      embedding.py      # Vector embedding generation
    /search             # Search and similarity functions
      similarity.py     # Vector search implementation
      ranking.py        # Result ranking algorithms  
    /api                # API layer using FastAPI
      main.py           # API entry point
      routes/           # API endpoints
    /agent              # ADK integration
      document_agent.py # ADK agent implementation
  /deployment
    /terraform          # Infrastructure as Code
      main.tf           # Main Terraform configuration
      variables.tf      # Terraform variables
      outputs.tf        # Terraform outputs
  /tests                # Unit and integration tests
```

## Setup Instructions

### Prerequisites
1. Google Cloud Platform account
2. Enabled APIs:
   - Document AI API
   - Vision AI API
   - Vertex AI API
   - Cloud Storage API
   - Firestore API
   - Cloud Functions API
   - Cloud Run API

### Installation Steps
1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd app2
   ```

2. Set up Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Deploy infrastructure with Terraform:
   ```bash
   cd deployment/terraform
   tofu init
   tofu apply
   ```

4. Deploy the Cloud Functions:
   ```bash
   gcloud functions deploy document-processor \
     --runtime python312 \
     --trigger-bucket=YOUR_BUCKET_NAME \
     --entry-point=process_document
   ```

5. Deploy the API service:
   ```bash
   gcloud run deploy document-api \
     --source . \
     --region us-central1
   ```

## Usage

### Uploading Documents
1. Upload documents through the web interface
2. Or upload directly to the configured Cloud Storage bucket

### Searching for Similar Documents
1. Use the web interface to search for documents
2. Or query the API directly:
   ```bash
   curl -X POST https://YOUR_SERVICE_URL/api/search \
     -H "Content-Type: application/json" \
     -d '{"query": "hydraulic system maintenance"}'
   ```

3. Use the ADK agent for conversational search:
   ```python
   from agent.document_agent import document_agent
   
   response = document_agent.chat("Find me documents about cooling systems")
   ```

## Development

### Running Locally
1. Start the API server:
   ```bash
   cd src/api
   uvicorn main:app --reload
   ```

2. Use the local emulators for Firestore and Pub/Sub:
   ```bash
   gcloud emulators firestore start --project=local-dev
   gcloud emulators pubsub start --project=local-dev
   ```

### Running Tests
```bash
python -m pytest tests/
```

## ADK Agent Integration

The system includes an Agent Development Kit (ADK) integration that enables natural language conversation with your document repository. The agent can:
- Search for documents based on natural language queries
- Extract specific information from documents
- Provide summaries and insights from technical content
- Help navigate complex technical documentation
