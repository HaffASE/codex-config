# AGENTS.md

## Workflow

For non-trivial tasks:

1. Start with `explorer_fast`.
2. Escalate to `explorer_deep` if the area is broad, ambiguous, or spans multiple subsystems.
3. Use `repo_scout` in parallel when quick evidence about routes, providers, tests, stories, flags, fixtures, or package boundaries would help.
4. Use `docs_researcher` when the task depends on external library, framework, browser, or platform documentation.
5. Use `planner` after discovery.
6. Use `implementer` only after a plan exists.
7. Use `unit_test_writer` when behavior changes or regression risk exists.
8. Use `browser_debugger` for browser reproduction and evidence only.
9. Use `reviewer` before finalizing meaningful changes.

## Repo rules

- Prefer the smallest viable change.
- Preserve public APIs, route contracts, exported types, and component interfaces unless the task explicitly requires changes.
- Avoid broad refactors, unrelated renames, formatting-only churn, and library swaps.
- Reuse existing patterns before introducing new abstractions.
- Keep accessibility and existing UI states intact.

## Commands

- Inspect `package.json` scripts first.
- Prefer `pnpm`.
- Prefer the smallest relevant workspace- or package-scoped command.
- Do not invent commands when repo scripts already exist.

## Validation

- Run the smallest relevant checks for changed behavior.
- Update nearby tests when practical.
- Report commands run and remaining risks.

## Planning

- Keep plans concise.
- End each plan with unresolved questions, if any.
