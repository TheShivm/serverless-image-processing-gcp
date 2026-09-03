variable "gcp_project_id" {
  description = "Google Cloud project ID that owns the pipeline."
  type        = string

  validation {
    condition     = length(var.gcp_project_id) > 4
    error_message = "Provide a valid Google Cloud project ID."
  }
}

variable "gcp_region" {
  description = "Region for Cloud Functions Gen2 and Eventarc triggers."
  type        = string
  default     = "asia-south1"
}

variable "gcp_input_bucket" {
  description = "Globally unique private bucket for source images."
  type        = string
}

variable "gcp_output_bucket" {
  description = "Globally unique private bucket for resized images and function source artifacts."
  type        = string
}

variable "pubsub_topic_name" {
  description = "Topic receiving Cloud Storage OBJECT_FINALIZE notifications."
  type        = string
  default     = "image-upload-events"
}

variable "notification_success_topic_name" {
  description = "Topic receiving successful image-resize completion messages."
  type        = string
  default     = "image-resize-success"
}

variable "force_destroy_buckets" {
  description = "Whether Terraform destroy may delete bucket contents. Enable only for disposable projects."
  type        = bool
  default     = false
}
