data "google_project" "current" {
  project_id = local.project_id
}

data "google_storage_project_service_account" "gcs" {
  project = local.project_id

  depends_on = [google_project_service.required_apis]
}

resource "google_project_service_identity" "gcf_sa" {
  provider = google-beta
  project  = local.project_id
  service  = "cloudfunctions.googleapis.com"

  depends_on = [google_project_service.required_apis]
}

resource "google_project_service_identity" "eventarc_sa" {
  provider = google-beta
  project  = local.project_id
  service  = "eventarc.googleapis.com"

  depends_on = [google_project_service.required_apis]
}

resource "google_project_service_identity" "cloudbuild_sa" {
  provider = google-beta
  project  = local.project_id
  service  = "cloudbuild.googleapis.com"

  depends_on = [google_project_service.required_apis]
}
