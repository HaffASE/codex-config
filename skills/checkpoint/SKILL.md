---
name: checkpoint
description: "Save or resume a task handoff using actual artifacts and current source state. Does not restore native worker or Goal state from files."
---

# Checkpoint

For save: record objective, completion boundary and current authority; scope/non-goals; plan path/revision;
source HEAD plus relevant dirty-content identity; accepted decisions; completed/partial
slices; current verified brief, evidence links and limitations; fresh receipts;
live worker IDs only if actually known; blockers; next smallest
action. Update `status.md` in the task's requested folder, normally `.ai/tasks/<slug>/`.
Reference evidence rather than copying transcripts. Do not include credentials.
For a long task that benefits from machine-readable progress, the coordinator may
also keep a task-local `ledger.json` based on [the template](../../templates/ledger.example.json).
Keep entries descriptive and link evidence; `status.md` remains the readable handoff.
If waiting on an external condition, record its reference and the source check to run
before resuming; do not treat an old waiting note as proof that the condition changed.

For resume: read the actual status, plan, decisions and evidence. Recheck current
source identity, user instructions and authority. Reconcile drift before using old
conclusions. Do not repeat resolved decisions unless the source/scope really changed.
A reported past permission does not automatically authorize a new broader action.

Native Codex resumes thread/Goal state through its own user controls. This document
is not a runtime database, worker registry, scheduler or permission token. Do not
assume recorded workers still exist or restart a completed operation blindly.
If native continuation is unavailable, continue only in the current authorized session
and describe that limit. Never promise an unattended background process from a skill.

A checkpoint request itself does not authorize implementation. Output the saved path
or reconciled state, evidence freshness, blockers and next step; do not mark a partial
task complete just to produce a tidy handoff.
