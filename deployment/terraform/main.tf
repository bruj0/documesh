# Main OpenTofu configuration for technical document management system

provider "google" {
  project = var.project_id
  region  = var.region
}

# Get project data to access project number
data "google_project" "project" {}


