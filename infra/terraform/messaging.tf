resource "google_pubsub_topic" "resized_image_topic" {
  name                       = var.pubsub_topic_name
  message_retention_duration = "604800s"

  labels = {
    application = "image-resizer"
    managed_by  = "terraform"
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_pubsub_topic" "resize_success_topic" {
  name                       = var.notification_success_topic_name
  message_retention_duration = "604800s"

  labels = {
    application = "image-resizer"
    managed_by  = "terraform"
  }

  depends_on = [google_project_service.required_apis]
}
