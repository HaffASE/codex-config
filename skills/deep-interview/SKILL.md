---
name: deep-interview
description: "Clarify materially ambiguous requirements after inspecting available facts. Planning and decisions only; no product changes."
---

# Deep interview

Start by reading the current request, applicable instructions and any prior decisions.
Inspect relevant code/documents before asking questions the repository can answer.
A request for analysis or interview never authorizes product code/test/config edits.
Write only requested planning artifacts, otherwise keep the result in conversation.

Identify the uncertainty that most changes scope, behavior, data contracts, UX,
compatibility, security or acceptance criteria. Ask one focused question at a time;
include known facts, two or three meaningful alternatives, consequences and a reasoned
recommendation. Use ordinary user conversation, not a special question tool or CLI.
Do not repeat answered questions, invent numerical ambiguity scores, or ask mechanical
approval after every step. Direct user decisions outrank agent recommendations.

Separate facts, assumptions, unanswered decisions and constraints. Reversible local
technical choices can be made within the delegated task and labelled. Do not choose
irreversible, scope-expanding or security-sensitive behavior by silence or timeout.
A request to decide autonomously is authority only within its stated boundaries.

Use at most one read-only nc_scout or nc_explorer when a specific code uncertainty
would materially improve the question. Use native spawning only when available;
single-agent investigation is an acceptable fallback, not simulated delegation.
Do not ask a council unless the user delegated the specific decision to it.

Record decisions with IDs, selected option, rationale, source of authority, affected
requirements and remaining caveats. For an existing feature-discovery run, return
these to the coordinator rather than creating a second registry or review loop.

Stop when all material choices are resolved or a named decision blocks the next
stage. Output task scope, non-goals, decision log, acceptance criteria, unresolved
items and recommended next step. Do not start implementation or a Goal automatically.
