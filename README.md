
# Technical Document Management System

## Description of intent
This application will store documents with highly structured technical data, ranging from maintenance procedures to visual diagrams. 
Any time a new document is added it will perform a visual similarity search for diagrams and a text search to offer a ranking of documents that are similar.

## Tech Stack
* Google Cloud managed services as much as possible to offload the processing.
* Python programming language
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
   terraform init
   terraform apply
   ```

4. Deploy the Cloud Functions:
   ```bash
   gcloud functions deploy document-processor \
     --runtime python39 \
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

## Contributing
Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.