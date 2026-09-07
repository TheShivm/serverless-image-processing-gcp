resource "google_service_account" "function_sa" {
  project      = local.project_id
  account_id   = "image-resizer-sa"
  display_name = "Image resize runtime"
  description  = "Reads input images, writes resized output, and publishes completion events."
}

resource "google_service_account" "notification_runtime_sa" {
  project      = local.project_id
  account_id   = "image-notifier-sa"
  display_name = "Image notification runtime"
  description  = "Consumes completion messages and writes structured stdout logs."
}

resource "google_service_account" "resize_trigger_sa" {
  project      = local.project_id
  account_id   = "resize-trigger-sa"
  display_name = "Resize trigger delivery identity"
  description  = "Authenticated Eventarc delivery identity for the resize function."
}

resource "google_service_account" "notification_trigger_sa" {
  project      = local.project_id
  account_id   = "notify-trigger-sa"
  display_name = "Notification trigger delivery identity"
  description  = "Authenticated Eventarc delivery identity for the notification function."
}

resource "google_service_account" "function_builder_sa" {
  project      = local.project_id
  account_id   = "function-builder-sa"
  display_name = "Cloud Functions build identity"
  description  = "Builds the two Cloud Functions Gen2 source packages."
}

resource "google_storage_bucket_iam_member" "resize_input_reader" {
  bucket = google_storage_bucket.input_bucket.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.function_sa.email}"
}

resource "google_storage_bucket_iam_member" "resize_output_writer" {
  bucket = google_storage_bucket.output_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.function_sa.email}"
}

resource "google_pubsub_topic_iam_member" "resize_success_publisher" {
  project = local.project_id
  topic   = google_pubsub_topic.resize_success_topic.name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.function_sa.email}"
}

resource "google_pubsub_topic_iam_member" "gcs_upload_publisher" {
  project = local.project_id
  topic   = google_pubsub_topic.resized_image_topic.name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${data.google_storage_project_service_account.gcs.email_address}"
}

resource "google_storage_bucket_iam_member" "function_builder_source_reader" {
  bucket = google_storage_bucket.output_bucket.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.function_builder_sa.email}"
}

resource "google_project_iam_member" "function_builder_project_roles" {
  for_each = toset([
    "roles/artifactregistry.writer",
    "roles/cloudbuild.builds.builder",
    "roles/logging.logWriter",
  ])

  project = local.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.function_builder_sa.email}"
}

resource "google_service_account_iam_member" "cloudfunctions_uses_builder" {
  service_account_id = google_service_account.function_builder_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_project_service_identity.gcf_sa.email}"
}

resource "google_cloud_run_service_iam_member" "resize_trigger_invoker" {
  project  = local.project_id
  location = local.region
  service  = google_cloudfunctions2_function.resize_image_function.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.resize_trigger_sa.email}"
}

resource "google_cloud_run_service_iam_member" "notification_trigger_invoker" {
  project  = local.project_id
  location = local.region
  service  = google_cloudfunctions2_function.notification_function.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.notification_trigger_sa.email}"
}
