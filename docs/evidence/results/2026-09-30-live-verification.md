# Live verification — 2026-09-30

| Field | Value |
| --- | --- |
| Tested infrastructure commit | `8294738584ef9526c06e23e24101b766e44059ad` |
| Function package manifest commit | `70f3a24d93a13c24a194dcb19a9eb404a70a6e10` |
| Project / region | `shivam-serverless` / `asia-south1` |
| Run ID | `20260930T075515Z-be78c4fb` |
| Started / finished (UTC) | `2026-09-30T07:55:15Z` / `2026-09-30T07:59:03Z` |
| Result | **PASS** |

The package source was unchanged between the package-manifest commit and the
tested infrastructure commit; the later infrastructure commit serializes the
first two Gen2 function builds to avoid the platform's shared-source-bucket
bootstrap race.

## Assertions

| Case | Object key suffix | Expected / observed dimensions | Output object | Matching notification | Result |
| --- | --- | --- | --- | --- | --- |
| JPEG | `sample-landscape.jpg` | 1600 × 1000 → 800 × 500 | yes | yes | PASS |
| Odd PNG | `odd-dimensions.png` | 641 × 481 → 320 × 240 | yes | yes | PASS |
| Tiny PNG | `tiny.png` | 1 × 1 → 1 × 1 | yes | yes | PASS |
| Invalid binary | `invalid-input.bin` | not an image | no | no `SUCCESS` in 90 seconds | PASS |

The successful cases were correlated to their unique run-id object paths and
input/output object generations. The verifier also recorded package hashes and
local image checksums in the private raw evidence directory. The resize and
notification functions were both `ACTIVE`, their Eventarc triggers used the
explicit trigger service accounts, and each Cloud Run service exposed only its
matching trigger identity as `roles/run.invoker`.

Finally, `terraform plan -detailed-exitcode` returned exit code `0` with
“No changes.” This confirms Terraform alignment at that time; it does not make
an exactly-once, ordering, or zero-cost claim.
