output "project_id" {
  value       = local.project_id
  description = "Project that owns this deployment."
}

output "region" {
  value       = local.region
  description = "Region used by both functions and triggers."
}

output "input_bucket_name" {
  value       = google_storage_bucket.input_bucket.name
  description = "Private bucket for original image uploads."
}

output "output_bucket_name" {
  value       = google_storage_bucket.output_bucket.name
  description = "Private bucket for resized images and source artifacts."
}

output "upload_topic_id" {
  value       = google_pubsub_topic.resized_image_topic.id
  description = "Pub/Sub topic receiving input-bucket notifications."
}

output "success_topic_id" {
  value       = google_pubsub_topic.resize_success_topic.id
  description = "Pub/Sub topic receiving completion messages."
}

output "resize_function_name" {
  value       = google_cloudfunctions2_function.resize_image_function.name
  description = "Resize Cloud Function Gen2 name."
}

output "notification_function_name" {
  value       = google_cloudfunctions2_function.notification_function.name
  description = "Notification Cloud Function Gen2 name."
}

output "resize_runtime_service_account" {
  value       = google_service_account.function_sa.email
  description = "Runtime identity for the resize function."
}

output "notification_runtime_service_account" {
  value       = google_service_account.notification_runtime_sa.email
  description = "Runtime identity for the notification function."
}

output "resize_trigger_service_account" {
  value       = google_service_account.resize_trigger_sa.email
  description = "Authenticated trigger identity for the resize function."
}

output "notification_trigger_service_account" {
  value       = google_service_account.notification_trigger_sa.email
  description = "Authenticated trigger identity for the notification function."
}
