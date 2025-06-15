#!/bin/bash
# Script to create a service account with the necessary roles to deploy the
# technical document management system OpenTofu infrastructure

# Exit on any error
set -e

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "gcloud command not found. Please install the Google Cloud SDK."
    exit 1
fi

# Check if the user is logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo "You're not logged in with gcloud. Please run 'gcloud auth login'."
    exit 1
fi

# Get current project ID or use provided one
if [ -z "$1" ]; then
    PROJECT_ID=$(gcloud config get-value project)
    echo "Using current project: $PROJECT_ID"
else
    PROJECT_ID=$1
    echo "Using provided project: $PROJECT_ID"
fi

# Verify project ID
if [ -z "$PROJECT_ID" ]; then
    echo "No project ID found. Please set a default project with 'gcloud config set project PROJECT_ID' or pass it as an argument."
    exit 1
fi

# Create the service account
echo "Creating OpenTofu deployment service account..."
SERVICE_ACCOUNT_NAME="terraform-deployer"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Check if the service account already exists
if gcloud iam service-accounts describe "$SERVICE_ACCOUNT_EMAIL" --project="$PROJECT_ID" &> /dev/null; then
    echo "Service account $SERVICE_ACCOUNT_EMAIL already exists."
else
    gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
        --display-name="OpenTofu Deployment Service Account" \
        --project="$PROJECT_ID"
    echo "Service account created: $SERVICE_ACCOUNT_EMAIL"
    sleep 10 # Wait for the service account to be fully created
    echo "Service account $SERVICE_ACCOUNT_EMAIL created successfully."
fi

# List of roles needed for deployment
ROLES=(
    "roles/serviceusage.serviceUsageAdmin"     # For enabling APIs
    "roles/storage.admin"                      # For Cloud Storage buckets
    "roles/documentai.admin"                   # For Document AI processors
    "roles/aiplatform.admin"                   # For Vertex AI components
    "roles/discoveryengine.admin"              # For Discovery Engine data stores
    "roles/datastore.owner"                    # For Firestore database
    "roles/pubsub.admin"                       # For Pub/Sub topics
    "roles/cloudfunctions.admin"               # For Cloud Functions
    "roles/run.admin"                          # For Cloud Run services
    "roles/iam.serviceAccountUser"             # For services using other service accounts
    "roles/resourcemanager.projectIamAdmin"    # For setting IAM policies
    "roles/artifactregistry.admin"             # For container image repositories
)

# Assign roles to the service account
echo "Assigning necessary roles to the service account..."
for ROLE in "${ROLES[@]}"; do
    echo "Assigning role: $ROLE"
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="$ROLE"
done

# Create a service account key
echo "Creating service account key..."
KEY_FILE="service-account.json"
if [ -f "$KEY_FILE" ]; then
    echo "Key file $KEY_FILE already exists. Skipping key creation."
else
    gcloud iam service-accounts keys create "$KEY_FILE" \
        --iam-account="$SERVICE_ACCOUNT_EMAIL" \
        --project="$PROJECT_ID"
    echo "Service account key created: $KEY_FILE"
fi

echo "========================================================================"
echo "Setup completed successfully!"
echo "Service account: $SERVICE_ACCOUNT_EMAIL"
echo "Key file: $KEY_FILE"
echo ""
echo "To use this service account with OpenTofu, set the following environment variable:"
echo "export GOOGLE_APPLICATION_CREDENTIALS=\"$(pwd)/$KEY_FILE\""
echo ""
echo "Or configure the Google provider in your OpenTofu code to use this key file."
echo "========================================================================"
