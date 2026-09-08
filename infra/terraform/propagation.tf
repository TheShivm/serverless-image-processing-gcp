resource "time_sleep" "wait_for_iam_propagation" {
  create_duration = "90s"

  depends_on = [
    google_project_service_identity.gcf_sa,
    google_project_service_identity.eventarc_sa,
    google_project_service_identity.cloudbuild_sa,
    google_storage_bucket_iam_member.resize_input_reader,
    google_storage_bucket_iam_member.resize_output_writer,
    google_storage_bucket_iam_member.function_builder_source_reader,
    google_pubsub_topic_iam_member.resize_success_publisher,
    google_pubsub_topic_iam_member.gcs_upload_publisher,
    google_project_iam_member.function_builder_project_roles,
    google_service_account_iam_member.cloudfunctions_uses_builder,
  ]
}
