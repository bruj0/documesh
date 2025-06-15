# Service Account and IAM configuration

# Service account for OpenTofu deployment
# resource "google_service_account" "terraform_deployer" {
#   account_id   = "terraform-deployer"
#   display_name = "OpenTofu Deployment Service Account"
#   description  = "Service account for deploying OpenTofu infrastructure"
# }

# Service account for Cloud Build
resource "google_service_account" "cloudbuild_sa" {
  account_id   = "cloudbuild-sa"
  display_name = "Cloud Build Service Account"
  description  = "Service account for Cloud Build to deploy and manage resources"
}

# IAM policy bindings for the OpenTofu deployer service account
# resource "google_project_iam_member" "terraform_deployer_roles" {
#   for_each = toset([
#     "roles/serviceusage.serviceUsageAdmin",
#     "roles/storage.admin",
#     "roles/documentai.admin",
#     "roles/aiplatform.admin",
#     "roles/discoveryengine.admin",
#     "roles/datastore.owner",
#     "roles/pubsub.admin",
#     "roles/cloudfunctions.admin",
#     "roles/run.admin",
#     "roles/iam.serviceAccountUser",
#     "roles/resourcemanager.projectIamAdmin",
#     "roles/artifactregistry.admin"
#   ])
  
#   project = var.project_id
#   role    = each.key
#   member  = "serviceAccount:${google_service_account.terraform_deployer.email}"
# }

# IAM policy bindings for the Cloud Build service account
resource "google_project_iam_member" "cloudbuild_sa_roles" {
  for_each = toset([
    "roles/artifactregistry.admin",
    "roles/cloudbuild.builds.builder",
    "roles/cloudbuild.integrations.creator", # For GitHub integrations
    "roles/secretmanager.secretAccessor",    # For accessing GitHub tokens if needed
    "roles/cloudkms.cryptoKeyEncrypterDecrypter",
    "roles/storage.admin",
    "roles/run.admin",
    "roles/cloudfunctions.admin",
    "roles/iam.serviceAccountUser"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.cloudbuild_sa.email}"
}
