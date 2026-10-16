# Line 1 — Endpoint diagnosis

Start with [Endpoint Doctor](tools/endpoint-doctor/README.md) for a single
command combining failure triage, redirects, retry hints and cache evidence.
It demonstrates offline on a retained real swarm report and offers explicit
live capture through the existing process watchdog. See
[step 31](STEP-31-REVIEW.md) for verification and the new wall mark.

[Payload Lens](tools/payload-lens/README.md) checks whether a saved observation
actually established its expected response media type, strict JSON validation
and minimum body size. See [step 32](STEP-32-REVIEW.md).

The first working piece is [Endpoint Sentry](tools/endpoint-sentry/README.md), a standard-library Python command that explains a public HTTPS endpoint's response and checks optional JSON expectations. The line's permanent purpose is in GOAL.md.

Step 24 adds [TLS Route](tools/tls-route/README.md), which checks each public DNS
answer through TCP and hostname-verified TLS to identify the failing stage.
It includes a whole-process deadline for DNS stalls. See
[the step review](STEP-24-REVIEW.md) for the live observation and wall checks.

Step 23 repairs explicit-port validation in Endpoint Sentry and its
[Deadline Sentry](tools/deadline-sentry/README.md) wrapper: an explicit zero port
is rejected instead of silently probing port 443. See
[the step review](STEP-23-REVIEW.md) for checks and the preserved wall.

Step 01's mark is Pepe watching three ochre trails: two reach their rings while one stops short. It represents finding a broken connection. The cave keeps its original 1254 × 1254 size, stone, cracks, light, and framing. Future workers have most of the rock left to paint on. See VISUAL_REVIEW.md for the output and visual checks.

Step 25 adds [Report Delta](tools/report-delta/README.md), an offline comparison
of two completed probe reports. It shows health transitions, changed routes
and failure stages while treating body-digest changes as informational.
Its README command works without network on retained real swarm observations.
See [the step review](STEP-25-REVIEW.md) for checks and wall preservation.

Step 29 adds [Redirect Lens](tools/redirect-lens/README.md), an independent offline
explanation of saved redirect routes, origin changes and unobserved destinations.
See [the step review](STEP-29-REVIEW.md) for live evidence and wall preservation.

Step 30 adds [Retry Lens](tools/retry-lens/README.md), an offline explanation of
captured Retry-After hints, with explicit evaluation times and unknown outcomes
for ambiguous values. Endpoint Sentry now retains this one response header,
including duplicate fields and explicit absence. See
[the step review](STEP-30-REVIEW.md) for checks and the preserved wall.
