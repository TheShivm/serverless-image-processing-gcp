# Troubleshooting

| Symptom | Check | Correct response |
| --- | --- | --- |
| Terraform cannot find a ZIP | Run `python scripts/package.py` before plan. | Do not hand-edit or commit generated archives. |
| Function build fails to read source | Confirm the builder identity and output-bucket source-object viewer binding. | Inspect the actual build error and least-privilege binding; do not broaden all runtime permissions. |
| Event trigger exists but function is not invoked | Inspect the trigger's configured service account and target Cloud Run IAM policy. | Grant `roles/run.invoker` to that explicit trigger identity on the matching service; never grant public invocation. |
| Upload notification cannot publish | Inspect the Cloud Storage service agent binding on the upload topic. | Grant that agent publisher only on the required topic. |
| Output exists but notification is absent | Search the resize function log for publish failure and the notification function log for the same object/run ID. | Treat it as partial completion, not an end-to-end success. |
| Notification log is missing | Query `jsonPayload.event="IMAGE_RESIZE_NOTIFICATION"` for the notification Cloud Run service. | Confirm deployed source uses JSON stdout and validate the Pub/Sub message. |
| Unexpected object version processed | Compare the upload generation to resize logs. | The handler downloads with the event generation where supplied; missing retained versions should be surfaced as errors. |
| A second plan has changes | Run `terraform plan -detailed-exitcode` and inspect state/resource differences. | Do not taint resources blindly; resolve the specific state or configuration mismatch. |
| Local state is missing | Look for the private backup of `infra/terraform/terraform.tfstate`. | Never initialize empty state and apply against a known live deployment without importing/reconciling it. |

The inherited migration history once used a public invoker workaround. It is
historical evidence, not a current fix. This project must remain authenticated.
