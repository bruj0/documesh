# OpenTofu variables for technical document management system

variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "The Google Cloud region for most resources"
  type        = string
  default     = "eu-west1" # Matching the GitHub connection region
}

variable "project_number" {
  description = "The Google Cloud Project Number (numeric ID)"
  type        = string
}

variable "firestore_location" {
  description = "Location for Firestore database"
  type        = string
  default     = "eur3" # Multi-region in North America
}

variable "storage_retention_days" {
  description = "Number of days to retain files in storage buckets"
  type        = number
  default     = 365
}

variable "document_ai_processors" {
  description = "Document AI processors to create"
  type        = map(string)
  default = {
    "ocr"  = "DOCUMENT_OCR_PROCESSOR"
    "form" = "FORM_PARSER_PROCESSOR"
  }
}

variable "env" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "documentai_location" {
  description = "Location for Document AI processors (limited availability)"
  type        = string
  default     = "eu" # Using EU region for Document AI
}

# Vector Search configuration variables
variable "vector_search_dimensions" {
  description = "Dimensions for the vector embeddings"
  type        = number
  default     = 768 # Default for textembedding-gecko@003
}

variable "vector_search_neighbors_count" {
  description = "Approximate number of neighbors for vector search"
  type        = number
  default     = 150
}

variable "vector_search_min_replicas" {
  description = "Minimum number of replicas for vector search endpoints"
  type        = number
  default     = 1
}

variable "vector_search_max_replicas" {
  description = "Maximum number of replicas for vector search endpoints"
  type        = number
  default     = 2
}

variable "github_repo" {
  description = "GitHub repository for the application"
  type        = string
  default     = "bruj0/documesh"
}
