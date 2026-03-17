# AGENTS.md

## Workflow

For non-trivial tasks:

1. Start with `explorer_fast`.
2. Escalate to `explorer_deep` if the area is broad, ambiguous, or spans multiple subsystems.
3. Use `repo_scout` in parallel when quick evidence about routes, providers, tests, stories, flags, fixtures, or package boundaries would help.
4. Use `docs_researcher` when the task depends on external library, framework, browser, platform, or API documentation.
5. Use `planner` after discovery.
6. Use `implementer` only after a plan exists.
7. Use `unit_test_writer` when behavior changes or regression risk exists.
8. Use `browser_debugger` for browser reproduction and evidence only.
9. Use `reviewer` before finalizing meaningful changes.

## Subagent delegation

- The main agent owns the plan, critical path, integration, validation, and final task tracking.
- Subagents are helpers for bounded side tasks only. They do not own a full phase or end-to-end workstream.
- Before spawning a subagent, define:
  - the exact task boundary
  - the expected output
  - the validation command, if relevant
  - the merge point where the result will be reviewed
- Delegate only work that can proceed in parallel without blocking the next local step.
- Good delegation targets:
  - read-only repo surveys
  - isolated module changes with a clear file boundary
  - disjoint test work in named files
  - docs updates that do not overlap active code edits
  - external documentation research
- Do not delegate vague, overlapping, or tightly coupled work.
- When a subagent returns, review its output before continuing overlapping local work.
- Do not ignore returned work. Integrate it, amend it, or reject it with a concrete reason.
- Validate subagent output before treating it as complete.
- If local work and subagent work overlap, the main agent reconciles the final canonical version.

## Repo rules

- Prefer the smallest viable change.
- Preserve public APIs, route contracts, exported types, and component interfaces unless the task explicitly requires changes.
- Avoid broad refactors, unrelated renames, formatting-only churn, and library swaps.
- Reuse existing patterns before introducing new abstractions.
- Keep accessibility and existing UI states intact.
- When UI behavior changes, account for loading, error, empty, success, disabled, and retry states when relevant.

## Commands

- Inspect `package.json` scripts first.
- Prefer `pnpm`.
- Prefer the smallest relevant workspace- or package-scoped command.
- Do not invent commands when repo scripts already exist.

## Validation

- Run the smallest relevant checks for changed behavior.
- Update nearby tests when practical.
- Report commands run and remaining risks.
- Validate changed behavior before treating the task as complete.

## Planning

- Keep plans concise and action-oriented.
- Start from current behavior and constraints, not the desired solution.
- Prefer plans that preserve current contracts unless the task explicitly requires change.
- End each plan with unresolved questions, if any.
