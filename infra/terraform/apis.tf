resource "google_project_service" "required_apis" {
  for_each = local.required_apis

  project            = local.project_id
  service            = each.value
  disable_on_destroy = false
}
