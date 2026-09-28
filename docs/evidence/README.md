# Evidence index

Publish a run here only after it has genuinely completed. Each sanitized result
should record:

- tested Git commit and package hashes;
- UTC date, region, unique run ID, and object key;
- input generation, input/output dimensions, and checksums;
- the independent output-object and notification-log assertions;
- observed limitations, failures, or cleanup state.

Keep raw working data in `.local/evidence/<run-id>/`; it is intentionally
ignored. `screenshots/` and `results/` begin empty so they cannot imply a
deployment that has not happened. Do not add credentials, state, signed URLs,
billing data, unsanitized IAM exports, or upstream screenshots as personal
execution evidence.

## Published runs

- [2026-09-30 live verification](results/2026-09-30-live-verification.md) —
  three valid image cases, invalid-input case, matching notification assertions,
  and a subsequent no-change Terraform plan.
