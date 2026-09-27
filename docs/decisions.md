# Decisions and attribution

## Scope

The implementation intentionally preserves the original feature: upload an
image, halve dimensions, store the result under the same object key, publish a
completion message, and record a structured notification. It does not add a
frontend, email/chat integrations, AI processing, databases, dashboards,
Kubernetes, multiregion behavior, or automatic cloud deployment from CI.

## Reproducible packages

Generated ZIPs were removed from version control. `scripts/package.py` uses an
explicit allowlist, sorted file names, fixed ZIP timestamps, and hashes so a
source change changes the deployed artifact. `.build/` remains ignored.

## Identities and logging

Runtime, trigger, build, and platform-managed identities are distinct. The
resizer's bucket/topic permissions are scoped to its business role; the
notifier uses stdout rather than a direct Logging client. JSON lines make the
notification contract observable without adding a new service.

## Delivery semantics

No exactly-once, ordering, or automatic replay claim is made. The output upload
can succeed before the success message publish fails. The verifier requires a
matching output and notification to mark an end-to-end pass.

## State and deletion

Local Terraform state suits a single operator and cannot safely support
disposable CI applies. Buckets default to `force_destroy = false`; enabling it
is an explicit disposable-project decision. APIs remain enabled after destroy.

## Upstream material

The initial code and historical screenshots came from
[`hemanth-yamsani/serverless-image-processing-gcp`](https://github.com/hemanth-yamsani/serverless-image-processing-gcp)
at the commit documented in [the audit plan](audit-plan.md). The inherited tree
did not include a license. This repository retains attribution and does not
invent an MIT or other license grant. Historical migration notes are not a
deployment runbook for this implementation.
