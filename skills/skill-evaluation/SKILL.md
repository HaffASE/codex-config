---
name: skill-evaluation
description: "Use when deciding whether to accept, reject, or narrow a proposed agent skill or substantial SKILL.md rewrite based on baseline evidence, trigger risk, context cost, and runtime ownership boundaries."
---

# Skill Evaluation

Keep a skill only when it improves a repeated, non-obvious outcome more than its
trigger risk and context cost.

## Establish the target

Start from an observed model failure, a confirmed repeated workflow, or a
capability requiring stable domain instructions. Do not create a skill for a
one-off simple edit that the agent can perform and verify directly.

Define:

- target behavior and representative requests;
- observable success and failure;
- user authorization and stop boundaries;
- runtime or tool ownership the skill must not duplicate;
- expected output contract.

## Write the candidate

Make frontmatter concise and trigger-focused. Put workflow details in the body.
State each rule once. Preserve explicit user values and real invariants; remove
persuasion, anecdotes, generic exhortations, repeated discipline, and tool
instructions already supplied by the runtime.

Use conditional rules tied to observable situations. Reserve unconditional
language for safety, authorization, format, or other actual invariants. Ask for
approval only when an unresolved choice materially changes outcome or when an
action is externally mutating or communicative, destructive, costly, or
scope-expanding.

Keep runtime lifecycle ownership with native Codex. A supporting skill may produce evidence
or decisions, but should not create a second mode, state store, team lifecycle,
worktree workflow, review workflow, or publication pipeline.

## Evaluate before accepting

Run the same representative cases without and with the candidate. Include:

- normal triggers;
- pressure and ambiguity cases;
- near misses that should not trigger;
- trivial work that should remain autonomous;
- unavailable tools or external evidence.

Compare outcome quality, unsupported claims, unnecessary questions or approval
gates, false triggers, context cost, duplicated orchestration, and new
regressions. Syntax validation alone and one successful happy path do not prove
improvement.

Revise only to correct an observed failure. Remove a rule when baseline already
handles it reliably or when its side effects exceed its benefit. Do not require
fixed repetition counts, commits, pushes, pull requests, or a contribution
workflow as evidence of skill quality.

## Report

Record target behavior, baseline evidence, candidate change, scenario results,
false-trigger risk, context cost, and remaining gaps. Stop when the candidate
shows repeatable improvement without a material boundary or compatibility
regression; otherwise narrow it or reject the skill.
