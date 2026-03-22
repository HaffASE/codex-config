# AGENTS.md

## Workflow

For non-trivial tasks:

1. Start with `explorer_fast`.
2. Escalate to `explorer_deep` if the area is broad, ambiguous, or spans multiple subsystems.
3. Use `repo_scout` only when quick evidence about routes, providers, tests, stories, flags, fixtures, or package boundaries is needed for the next concrete step. For the top-level main agent, treat this delegation as blocking and wait for the result before continuing task work.
4. Use `docs_researcher` when the task depends on external library, framework, browser, platform, or API documentation.
5. Use `planner` only when the main agent is blocked on an implementation plan that cannot be completed safely from existing discovery.
6. Do not use `planner` for redundant checklists, restating an accepted plan, or non-blocking side work.
7. If the user already provided or approved a complete plan, do not spawn `planner`.
8. Use `implementer` only after a plan exists and only for a bounded write task.
9. Use `unit_test_writer` when behavior changes or regression risk exists.
10. Use `reviewer` before finalizing meaningful changes.

## Subagent delegation

- The main agent owns the plan, critical path, integration, validation, and final task tracking.
- `Main agent` means the root agent directly serving the user in the current thread.
- Subagents are helpers for bounded side tasks only. They do not own a full phase or end-to-end workstream.
- Before spawning a subagent, define the task boundary, expected output, validation command if relevant, and merge point.
- Default the main agent to blocking delegation.
- The main agent may spawn a subagent only when that subagent's result is required for the next concrete step.
- The main agent must not spawn multiple subagents in parallel.
- After spawning a subagent, the main agent must wait for that result before continuing task work.
- While waiting for a subagent, the main agent must not continue unrelated exploration, planning, implementation, or additional delegation.
- The main agent must not keep background subagents running while continuing the task locally.
- Child agents may spawn child agents in parallel when useful and within their assigned scope.
- Good delegation targets include read-only repo surveys, isolated module changes, disjoint test work in named files, non-overlapping docs updates, and external documentation research.
- Do not delegate vague, overlapping, tightly coupled, or non-critical work.
- Do not spawn exploratory subagents for coverage; spawn them only when their result is expected to influence a real decision.
- The main agent must use at most one exploratory or planning subagent at a time.
- When an explorer-style subagent is surveying an area, the main agent must not perform a second broad survey of the same area while waiting for that result.
- When a subagent returns, review and validate its output before treating it as complete.
- Do not ignore returned work. Integrate it, amend it, reject it with a concrete reason, or explicitly mark it unnecessary.
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
