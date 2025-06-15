#!/bin/bash
# Helper script for local development

# Ensure virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Export environment variables
export PROJECT_ID="local-development"
export LOCATION="us-central1"
export DOCUMENT_PROCESSOR_ID="local-processor"
export DOCUMENT_BUCKET="local-documents"
export TEXT_EMBEDDING_MODEL="textembedding-gecko@latest"
export MULTIMODAL_MODEL="multimodalembedding@latest"
export TEXT_INDEX_ID="local-text-index"
export VISUAL_INDEX_ID="local-visual-index"
export DATA_STORE_ID="local-datastore"
export GOOGLE_APPLICATION_CREDENTIALS="./credentials/service-account.json"

# Start the API server
echo "Starting API server..."
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8080
