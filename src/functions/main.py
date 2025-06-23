"""
Cloud Function to process a document uploaded to Google Cloud Storage.
This function is triggered by a GCS event when a new file is uploaded.
"""
import os
from google.cloud import storage

def process_document(event, context):
    """
    Background Cloud Function to be triggered by Cloud Storage.
    Args:
         event (dict):  The dictionary with data specific to this type of event.
         context (google.cloud.functions.Context): Metadata of triggering event.
    """
    bucket_name = event['bucket']
    file_name = event['name']
    print(f"Processing file: gs://{bucket_name}/{file_name}")

    # Initialize GCS client
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    # Download file content
    temp_file_path = f"/tmp/{os.path.basename(file_name)}"
    blob.download_to_filename(temp_file_path)
    print(f"Downloaded file to {temp_file_path}")

    # TODO: Add your document processing logic here
    # For example, extract text, analyze, or store metadata
    # ...

    # Clean up temp file
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)
        print(f"Removed temp file {temp_file_path}")

    print(f"Finished processing {file_name}")
