locals {
  project_id           = var.gcp_project_id
  region               = var.gcp_region
  input_bucket         = var.gcp_input_bucket
  output_bucket        = var.gcp_output_bucket
  source_prefix        = "_function-source"
  resize_archive       = "${path.module}/../../.build/resize.zip"
  notification_archive = "${path.module}/../../.build/notification.zip"

  required_apis = toset([
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudfunctions.googleapis.com",
    "eventarc.googleapis.com",
    "iam.googleapis.com",
    "logging.googleapis.com",
    "pubsub.googleapis.com",
    "run.googleapis.com",
    "storage.googleapis.com",
  ])
}
