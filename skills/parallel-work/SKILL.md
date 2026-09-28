---
name: parallel-work
description: "Coordinate independent bounded work through native Codex subagents with explicit file ownership. No tmux, mailbox or alternate worker runtime."
---

# Parallel work

Use parallelism only when tasks are independent enough to benefit. A single local
edit does not need a team. Native Codex owns spawning, waiting, messaging and closing;
use the live tool schema rather than an assumed signature. This skill provides task
contracts, not a new scheduler, daemon, state server or persistence guarantee.

Read [the worker contract](references/worker-contract.md). Build a compact ownership
table: task ID, dependencies, assigned role, read roots, exclusively owned write files,
shared contract/version, output and acceptance checks. Include user constraints and
accepted decisions explicitly; workers cannot recover missing decisions by guessing.

Keep at most three child threads open under this skill, or fewer under host limits.
Delegate read-only discovery/review freely within scope; writable work requires
current implementation authority. Use nc_implementer / nc_test_writer for bounded
writes; nc_scout / nc_explorer / nc_tests / nc_reviewer for analysis. Children never
spawn grandchildren. Do not impersonate missing agents or run a second CLI instead.

Native subagents may share a filesystem. Different conversations do not isolate
writes. Serialize any overlapping file, shared contract or integration surface.
The coordinator owns shared status, lockfiles, exported interfaces and integration.
Use independent worktrees only if already provided or expressly authorized, and
record their actual paths/refs rather than assuming that spawn creates one.

Collect substantive outputs and fresh evidence. A completion notification alone is
not acceptance. Verify changed files remain inside ownership, resolve conflicts
without discarding user changes, then run integrated tests against the final tree.
Close only this workflow's completed children; do not cancel unrelated sessions.

Without native tools, run sequentially and disclose that mode. If independent review
is a required gate, sequential self-review does not satisfy it. On interruption record
completed/partial tasks and actual worker state. A task file does not restore workers.
