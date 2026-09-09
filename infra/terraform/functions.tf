resource "google_storage_bucket_object" "function_zip" {
  name   = "${local.source_prefix}/resize-${filemd5(local.resize_archive)}.zip"
  bucket = google_storage_bucket.output_bucket.name
  source = local.resize_archive
}

resource "google_storage_bucket_object" "notification_function_zip" {
  name   = "${local.source_prefix}/notification-${filemd5(local.notification_archive)}.zip"
  bucket = google_storage_bucket.output_bucket.name
  source = local.notification_archive
}

resource "google_cloudfunctions2_function" "resize_image_function" {
  name        = "image-resizing-function"
  location    = local.region
  description = "Resizes images uploaded to the private input bucket."

  build_config {
    runtime         = "python311"
    entry_point     = "handler"
    service_account = google_service_account.function_builder_sa.id

    source {
      storage_source {
        bucket = google_storage_bucket.output_bucket.name
        object = google_storage_bucket_object.function_zip.name
      }
    }
  }

  service_config {
    max_instance_count             = 10
    available_memory               = "256M"
    timeout_seconds                = 60
    service_account_email          = google_service_account.function_sa.email
    ingress_settings               = "ALLOW_INTERNAL_ONLY"
    all_traffic_on_latest_revision = true

    environment_variables = {
      OUTPUT_BUCKET           = google_storage_bucket.output_bucket.name
      PROJECT_ID              = local.project_id
      SUCCESS_TOPIC_NAME      = google_pubsub_topic.resize_success_topic.name
      PUBLISH_TIMEOUT_SECONDS = "30"
    }
  }

  event_trigger {
    trigger_region        = local.region
    event_type            = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic          = google_pubsub_topic.resized_image_topic.id
    retry_policy          = "RETRY_POLICY_DO_NOT_RETRY"
    service_account_email = google_service_account.resize_trigger_sa.email
  }

  depends_on = [time_sleep.wait_for_iam_propagation]
}

resource "google_cloudfunctions2_function" "notification_function" {
  name        = "image-notification-function"
  location    = local.region
  description = "Writes a structured completion log for resized images."

  build_config {
    runtime         = "python311"
    entry_point     = "handler"
    service_account = google_service_account.function_builder_sa.id

    source {
      storage_source {
        bucket = google_storage_bucket.output_bucket.name
        object = google_storage_bucket_object.notification_function_zip.name
      }
    }
  }

  service_config {
    max_instance_count             = 5
    available_memory               = "256M"
    timeout_seconds                = 60
    service_account_email          = google_service_account.notification_runtime_sa.email
    ingress_settings               = "ALLOW_INTERNAL_ONLY"
    all_traffic_on_latest_revision = true
  }

  event_trigger {
    trigger_region        = local.region
    event_type            = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic          = google_pubsub_topic.resize_success_topic.id
    retry_policy          = "RETRY_POLICY_DO_NOT_RETRY"
    service_account_email = google_service_account.notification_trigger_sa.email
  }

  depends_on = [time_sleep.wait_for_iam_propagation]
}

resource "google_storage_notification" "gcs_notification" {
  bucket         = google_storage_bucket.input_bucket.name
  payload_format = "JSON_API_V1"
  topic          = google_pubsub_topic.resized_image_topic.id
  event_types    = ["OBJECT_FINALIZE"]

  depends_on = [google_pubsub_topic_iam_member.gcs_upload_publisher]
}
