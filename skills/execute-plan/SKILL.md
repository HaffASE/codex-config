---
name: execute-plan
description: "Implement an authorized plan in bounded slices with native Codex agents, current verification and durable handoff. Does not grant its own authority."
---

# Execute plan

Read the current request and the actual plan, accepted decisions, prerequisites and
latest handoff. Do not implement from an index summary or an unavailable local path.
A user request to execute a specified plan is implementation authority for that scope;
no redundant approval is needed. A planning READY label or historical quote is not.
Resolve conflicts by the current authorized scope; stop only the blocked part.

## Preflight

Inspect applicable instructions, Git status, pinned plan/source versions, affected
manifests and tests. Preserve pre-existing changes. Revalidate material source drift
before applying old decisions. Record allowed files/slices, dependency and Git limits,
acceptance criteria, exact repository commands and required review/verification.
For feature-discovery packets, run that skill's retained validator when the needed
reports exist; it validates planning integrity, not user authority or runtime truth.

Write `execution-handoff.md` with current authority reference, plan path/revision,
allowed and excluded scope, actor-specific rights, prerequisites and stop conditions.
This records authority; it does not manufacture it. Keep `status.md` current.
Do not modify frozen planning packets during execution; a scope/contract change needs
a new decision and, when required, a revised plan and review.

## Execute and verify

Work in dependency order. Use the shortest adequate path: one agent for a small
change; delegate only independent bounded work to nc_implementer / nc_test_writer.
Pass each worker the exact scope, accepted decisions, owned files, contracts, current
snapshot, test commands and prohibited actions. Workers do not delegate, commit,
publish, update shared status, or edit outside ownership. The coordinator integrates.

Shared-worktree agents are not isolated. Parallel writes require disjoint files and
stable shared contracts. Serialize edits to manifests, lockfiles, shared types,
exports, providers and shared fixtures. Do not create worktrees without authorization.
Use the parallel-work ownership protocol for nontrivial concurrent execution.

For a reproducible bug, capture the failure where feasible, fix the supported cause,
and verify the original scenario and adjacent regressions. For established new behavior,
prefer test-first when the repository harness fits; do not destroy correct code merely
to stage a ceremonial RED. Honor explicit no-new-tests instructions and report the gap.
Run only existing permitted tools; no package/browser downloads or production probes
without authority. Verify non-zero discovery and actual exit/output, not a worker claim.

After each slice record changes, command/exit/counts, limitations and next task in
`receipts/`. Mark incomplete/deferred observations honestly; a partial TEST ID is not
fully GREEN. A later relevant edit invalidates affected evidence and requires rerun.
For a long multi-slice task, the coordinator may use a task-local `ledger.json` from
[the template](../../templates/ledger.example.json) to index slice state and receipts.
Reconcile it with the current source and evidence before resuming; it grants no authority.
Perform the required independent code review, address validated in-scope defects,
and run final relevant integration gates on the actual integrated state.

## Persistence and stopping

Use native /goal only when the user activated it or explicitly authorized goal-driven
execution. The goal is a scoped outcome plus verification and limits, not permission
to ignore blockers. Use only goal tools exposed by the host; never run slash commands
in a shell or build a substitute endless loop. Without Goals, work within the current
session and leave a checkpoint at its boundary; do not promise automatic continuation.
Do not recreate workers from saved IDs after a restart without checking actual state.

Pause on unresolved material decisions, unavailable required tools/evidence, ownership
conflicts, scope expansion, or repeated failure without new evidence. Report attempted
paths and what unlocks the next step. No hidden retry-budget reset via child agents.

End with COMPLETE, PARTIAL, or BLOCKED; scope implemented; fresh evidence; actual
review coverage; remaining risks; and next action. COMPLETE requires every in-scope
criterion, required gate and review to be satisfied. Commit, push, MR creation and
remote approval require separately applicable user authority.
