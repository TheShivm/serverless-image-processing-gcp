# Verification

`scripts/verify.py` is an opt-in live test. It reads Terraform outputs and
uploads unique objects only; it does not modify IAM, fix resources, or edit
Terraform state.

## Pass criteria

For each successful fixture, all of the following must pass for the same run
ID and object key:

1. The source upload exists in the input bucket and its generation is recorded.
2. A same-key object appears in the output bucket before the bounded timeout.
3. The downloaded output decodes at the expected dimensions.
4. The notification function emits a matching
   `IMAGE_RESIZE_NOTIFICATION` / `SUCCESS` structured log entry.

The live suite runs these fixtures:

| Fixture | Source dimensions | Expected output |
| --- | ---: | ---: |
| JPEG | 1600 × 1000 | 800 × 500 |
| Odd-dimension PNG | 641 × 481 | 320 × 240 |
| Tiny PNG | 1 × 1 | 1 × 1 |
| Invalid binary | not an image | no output and no matching `SUCCESS` during the observation window |

The script writes `verification.json`, `summary.txt`, inputs, outputs, object
generations, hashes, and package manifest under `.local/evidence/<run-id>/`.
That directory is private and ignored. Curate only sanitized material into
`docs/evidence/` after review.

## Local gates

```bash
python -m pytest
python scripts/package.py
terraform -chdir=infra/terraform fmt -check
terraform -chdir=infra/terraform validate
```

Unit tests use mocks and do not prove cloud permissions. Functions Framework
tests exercise the entrypoint contract but do not prove Eventarc delivery.
Terraform validation proves configuration shape, not a successful deployment.
The live verifier is the only gate that asserts both output and downstream log.

## Evidence discipline

Record the commit, package hashes, UTC time, project/region, run ID, object
key, input generation, image dimensions, and result. Do not publish raw state,
tokens, signed URLs, full account/IAM exports, billing information, or someone
else's screenshots. The architecture diagrams in `docs/assets/` explain the
design, but are not proof of this deployment.
