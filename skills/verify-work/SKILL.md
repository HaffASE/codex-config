---
name: verify-work
description: "Run a bounded evidence-based verification and repair cycle for authorized work. Read-only by default; fixes require implementation authority."
---

# Verify work

Determine the requested claim, scope, current source snapshot and acceptance criteria.
Inspect the repository's actual verification scripts and their side effects. Check
existing receipts for freshness; do not accept a prior exit 0 for a changed tree.
A bare verification request authorizes checks within host permissions, not code edits,
dependency installation, snapshot rewrites, deployments or waived gates.

Choose the smallest sufficient checks: targeted behavior, types/lint, build, contracts,
real browser states or integration as applicable. Tests with zero discovered cases
are not behavior proof. Mocks, typechecks and static traces cannot establish production
connectivity, actual browser layout or complete business-flow correctness.
Record exact commands, exit codes, discovery/execution/skips and meaningful output.

For a failure, distinguish introduced regression, pre-existing failure and environment
limitation. With explicit repair authority, fix the supported in-scope cause and rerun
the affected gate; otherwise report the cause and proposed repair. Do not make a
failing gate pass by deleting cases, weakening assertions or hiding errors.

Default limit is three repair attempts for the same gate, adjustable by the current
user. Each attempt needs a new supported hypothesis. Stop earlier when no useful
new evidence is available. Counters span workers; switching skills is not a reset.
This bounded policy is not a background loop. Native Goals may supply continuation
only when available and activated for the authorized task.

Use nc_verifier for an independent audit when the task requires it; read-only agents
may be unable to run write-producing checks, which the permitted coordinator handles.
Return VERIFIED, PARTIAL or BLOCKED, plus evidence, uncovered scope and next step.
Never mark release-ready merely because selected local checks are green.
