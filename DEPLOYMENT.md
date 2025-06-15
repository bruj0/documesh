# Deployment Guide

This guide explains how to deploy the Technical Document Management System to Google Cloud.

## Prerequisites

1. Google Cloud account with billing enabled
2. Google Cloud SDK installed and configured
3. Required APIs enabled (Document AI, Vision, Vertex AI, etc.)
4. OpenTofu installed locally

## Deployment Steps

### 1. Set Up Environment Variables

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
```

### 2. Authenticate with Google Cloud

```bash
gcloud auth login
gcloud config set project $PROJECT_ID
```

### 3. Deploy Infrastructure with OpenTofu

```bash
cd deployment/terraform

# Create a tofu.tfvars file with your settings
cp terraform.tfvars.example tofu.tfvars
# Edit tofu.tfvars with your values

# Initialize OpenTofu
tofu init

# Plan the deployment
tofu plan -var project_id=$PROJECT_ID -var region=$REGION

# Deploy
tofu apply -var project_id=$PROJECT_ID -var region=$REGION
```

### 4. Build and Deploy the API

You can use Cloud Build to automate the deployment:

```bash
gcloud builds submit --config cloudbuild.yaml
```

Or manually:

```bash
# Build the Docker image
docker build -t gcr.io/$PROJECT_ID/document-api:latest .

# Push to Container Registry
docker push gcr.io/$PROJECT_ID/document-api:latest

# Deploy to Cloud Run
gcloud run deploy document-management-api \
  --image gcr.io/$PROJECT_ID/document-api:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated
```

### 5. Deploy the Document Processor Function

```bash
# Create function source archive
cd src
zip -r ../function-source.zip .
cd ..
zip -g function-source.zip requirements.txt

# Deploy the function
gcloud functions deploy document-processor \
  --runtime python39 \
  --trigger-bucket=$PROJECT_ID-technical-documents \
  --source=function-source.zip \
  --entry-point=document_processor
```

## Monitoring and Logging

Access Cloud Monitoring and Logging for your project:

- Cloud Run logs: `https://console.cloud.google.com/run/detail/$REGION/document-management-api/logs`
- Cloud Functions logs: `https://console.cloud.google.com/functions/details/$REGION/document-processor/logs`
- Firestore data: `https://console.cloud.google.com/firestore/data`

## Clean Up

To delete all resources:

```bash
# Remove with OpenTofu
cd deployment/terraform
tofu destroy -var project_id=$PROJECT_ID -var region=$REGION

# Or manually delete resources
gcloud run services delete document-management-api --region=$REGION
gcloud functions delete document-processor --region=$REGION
# Delete other resources manually as needed
```
