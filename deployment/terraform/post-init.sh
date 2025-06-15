#!/bin/bash
# filepath: /home/bruj0/projects/google-ai-hackathon/app2/deployment/terraform/post-init.sh

# Exit on error
set -e

# Check if TF_VAR_project_id is set
if [ -z "${TF_VAR_project_id}" ]; then
    echo "Error: TF_VAR_project_id environment variable is not set."
    echo "Please set it with: export TF_VAR_project_id=your-project-id"
    exit 1
fi

echo "Importing terraform-deployer service account into OpenTofu state..."

# Import the terraform-deployer service account
tofu import google_service_account.terraform_deployer projects/${TF_VAR_project_id}/serviceAccounts/terraform-deployer@${TF_VAR_project_id}.iam.gserviceaccount.com

echo "Importing IAM role bindings for the service account..."

# Import each IAM role binding
tofu import 'google_project_iam_member.terraform_deployer_roles["roles/serviceusage.serviceUsageAdmin"]' \
  ${TF_VAR_project_id} roles/serviceusage.serviceUsageAdmin serviceAccount:terraform-deployer@${TF_VAR_project_id}.iam.gserviceaccount.com

tofu import 'google_project_iam_member.terraform_deployer_roles["roles/storage.admin"]' \
  ${TF_VAR_project_id} roles/storage.admin serviceAccount:terraform-deployer@${TF_VAR_project_id}.iam.gserviceaccount.com

tofu import 'google_project_iam_member.terraform_deployer_roles["roles/documentai.admin"]' \
  ${TF_VAR_project_id} roles/documentai.admin serviceAccount:terraform-deployer@${TF_VAR_project_id}.iam.gserviceaccount.com

tofu import 'google_project_iam_member.terraform_deployer_roles["roles/aiplatform.admin"]' \
  ${TF_VAR_project_id} roles/aiplatform.admin serviceAccount:terraform-deployer@${TF_VAR_project_id}.iam.gserviceaccount.com

tofu import 'google_project_iam_member.terraform_deployer_roles["roles/discoveryengine.admin"]' \
  ${TF_VAR_project_id} roles/discoveryengine.admin serviceAccount:terraform-deployer@${TF_VAR_project_id}.iam.gserviceaccount.com

tofu import 'google_project_iam_member.terraform_deployer_roles["roles/datastore.owner"]' \
  ${TF_VAR_project_id} roles/datastore.owner serviceAccount:terraform-deployer@${TF_VAR_project_id}.iam.gserviceaccount.com

tofu import 'google_project_iam_member.terraform_deployer_roles["roles/pubsub.admin"]' \
  ${TF_VAR_project_id} roles/pubsub.admin serviceAccount:terraform-deployer@${TF_VAR_project_id}.iam.gserviceaccount.com

tofu import 'google_project_iam_member.terraform_deployer_roles["roles/cloudfunctions.admin"]' \
  ${TF_VAR_project_id} roles/cloudfunctions.admin serviceAccount:terraform-deployer@${TF_VAR_project_id}.iam.gserviceaccount.com

tofu import 'google_project_iam_member.terraform_deployer_roles["roles/run.admin"]' \
  ${TF_VAR_project_id} roles/run.admin serviceAccount:terraform-deployer@${TF_VAR_project_id}.iam.gserviceaccount.com

tofu import 'google_project_iam_member.terraform_deployer_roles["roles/iam.serviceAccountUser"]' \
  ${TF_VAR_project_id} roles/iam.serviceAccountUser serviceAccount:terraform-deployer@${TF_VAR_project_id}.iam.gserviceaccount.com

tofu import 'google_project_iam_member.terraform_deployer_roles["roles/resourcemanager.projectIamAdmin"]' \
  ${TF_VAR_project_id} roles/resourcemanager.projectIamAdmin serviceAccount:terraform-deployer@${TF_VAR_project_id}.iam.gserviceaccount.com

tofu import 'google_project_iam_member.terraform_deployer_roles["roles/artifactregistry.admin"]' \
  ${TF_VAR_project_id} roles/artifactregistry.admin serviceAccount:terraform-deployer@${TF_VAR_project_id}.iam.gserviceaccount.com

echo "Import complete! The service account and IAM bindings are now in the OpenTofu state."
echo "You can now run 'tofu plan' to verify the state."
