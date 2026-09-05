resource "google_storage_bucket" "input_bucket" {
  name                        = local.input_bucket
  location                    = local.region
  storage_class               = "STANDARD"
  force_destroy               = var.force_destroy_buckets
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  labels = {
    application = "image-resizer"
    managed_by  = "terraform"
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_storage_bucket" "output_bucket" {
  name                        = local.output_bucket
  location                    = local.region
  storage_class               = "STANDARD"
  force_destroy               = var.force_destroy_buckets
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  labels = {
    application = "image-resizer"
    managed_by  = "terraform"
  }

  depends_on = [google_project_service.required_apis]
}
