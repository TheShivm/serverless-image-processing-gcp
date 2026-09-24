# Deployment runbook

## Prerequisites

- A billing-enabled Google Cloud project.
- `gcloud` logged into a principal authorized to create the declared resources.
- Application Default Credentials: `gcloud auth application-default login`.
- Terraform 1.6 or newer.
- Python 3.11 for local tests and package generation.

The active `gcloud` project and Terraform's `gcp_project_id` must intentionally
refer to the same project. The deployer needs permissions beyond the runtime
service accounts defined by Terraform.

## Configure

```bash
gcloud config set project YOUR_PROJECT_ID
gcloud auth application-default login

cp infra/terraform/terraform.tfvars.example infra/terraform/terraform.tfvars
```

Set a project ID and two globally unique bucket names in `terraform.tfvars`.
Keep `force_destroy_buckets = false` unless deleting every object on teardown
is explicitly desired. The variables file and Terraform state are ignored and
must never be committed.

## Test, package, plan, apply

```bash
python3.11 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt -r functions/resize/requirements.txt

python -m pytest
python scripts/package.py

terraform -chdir=infra/terraform init
terraform -chdir=infra/terraform fmt -check
terraform -chdir=infra/terraform validate
terraform -chdir=infra/terraform plan -out=.local/image-pipeline.tfplan
terraform -chdir=infra/terraform apply .local/image-pipeline.tfplan
```

Packaging must run before planning: Terraform hashes `.build/resize.zip` and
`.build/notification.zip` to select source object names. The first apply
enables APIs, materializes service identities, grants the scoped bindings, then
waits briefly for IAM propagation before function deployment.

## Verify and inspect

```bash
python scripts/verify.py --terraform-dir infra/terraform
terraform -chdir=infra/terraform plan -detailed-exitcode
```

Exit code `0` from the final command means Terraform sees no managed changes;
`2` means it found drift/differences; `1` is an error. Review function and
trigger IAM policies separately to ensure the explicit trigger identities—not
public principals—hold `roles/run.invoker`.

## Teardown

After preserving any evidence you need:

```bash
terraform -chdir=infra/terraform destroy
```

APIs remain enabled by design. If `force_destroy_buckets` is true, destroy can
remove original images, output images, and `_function-source/` archives. Check
the project afterward for managed build/artifact resources before deleting
anything shared or unfamiliar.
