---
name: implementation-plan
description: "Turn an already clear task into a bounded executable plan. For ambiguous or cross-repository work use feature-discovery instead. No implementation."
---

# Implementation plan

This is the lightweight planning path for a clear, bounded change. It does not create
or modify product code/tests, install dependencies, mutate Git, or grant execution.
Read current code, relevant tests and repository commands before prescribing edits.
Reuse accepted requirements and decisions; do not re-interview an already clear task.

If unresolved cross-repository behavior or material product choices dominate, explain
the gap and use the feature-discovery workflow instead of inventing a complete plan.
Do not require that larger workflow for a trivial, well-specified local change.

Produce `plan.md` in the requested task folder, default `.ai/tasks/<slug>/`, containing:
objective/non-goals; current-source evidence; accepted decisions; ordered vertical
slices; exact owned files/modules; dependency edges; observable acceptance criteria;
verification commands verified against this repository; risks, rollback and blockers.
Map requirement IDs to tasks and planned verification. Do not invent exact line
numbers, package scripts, new shared abstractions, or a successful RED/GREEN run.
A plan explains outcomes and boundaries, not every keystroke or guessed future code.

For nontrivial changes use nc_planner for synthesis and a fresh nc_critic for a
bounded challenge. The coordinator writes the plan. Reconcile concrete concerns,
not majority votes. Allow one revision after critique; escalate unresolved material
issues rather than looping. When native review is unavailable, label self-review
and the missing independent evidence. A simple local plan can remain single-agent.

End with READY_TO_IMPLEMENT, NEEDS_DECISION, or BLOCKED, with evidence and limitations.
READY_TO_IMPLEMENT is a planning assessment, not user authorization. Only a subsequent
explicit implementation request, or authority already clearly included in a broader
current task, permits execution. Do not activate a Goal from a planning-only request.
