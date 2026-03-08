# codex-config

Repository for reusable Codex configuration, agent presets, and project templates.

## Structure

- `.codex/`: example project-level Codex config.
- `agents/`: reusable role presets for Codex multi-agent setups.
- `templates/`: stack-specific files that should be copied into real projects.

## React Template

Use the React template when setting up Codex for a React + TypeScript + pnpm codebase.

Files to copy into a target project:
- `.codex/config.toml`
- `agents/*.toml`
- `templates/react/AGENTS.md` -> `AGENTS.md`

## Example Prompts

Explorer:
- `Use the explorer agent to map how authentication works: routes, providers, API calls, storage usage, and the smallest set of related files.`
- `Use the explorer agent to inspect the settings page and explain where form state, validation, and save actions are handled.`

Planner:
- `Use the planner agent to propose a minimal implementation plan for adding a password visibility toggle, including validation steps and rollback risks.`
- `Use the planner agent to turn the explorer findings into a step-by-step plan for fixing duplicate API requests on page load.`

Implementer:
- `Use the implementer agent to add a clear button to the search input with the smallest defensible diff and run relevant checks after editing.`
- `Use the implementer agent to fix the stale state bug in the filter panel without broad refactoring.`

Unit test writer:
- `Use the unit_test_writer agent to add focused tests for the useDebouncedValue hook, including timing behavior and cleanup.`
- `Use the unit_test_writer agent to update tests for the modal so they cover keyboard close, submit, and error state behavior.`

Reviewer:
- `Use the reviewer agent to review the current diff for correctness, regressions, accessibility issues, and missing tests.`
- `Use the reviewer agent to inspect the new search flow and call out edge cases or broken async UI states.`

Browser debugger:
- `Use the browser_debugger agent to reproduce the checkout button bug, collect console and network evidence, and identify likely files without editing code.`
- `Use the browser_debugger agent to reproduce the login redirect issue and report exact steps, observed behavior, and suspected root cause areas.`

Typical sequences:
- `Use the explorer agent first, then the planner agent, for adding inline editing to the profile form.`
- `Use the browser_debugger agent to reproduce the issue, then the implementer agent to apply the smallest fix.`
- `Use the implementer agent for the fix, the unit_test_writer agent for targeted coverage, and the reviewer agent for final review.`

## Notes

- Root-level `AGENTS.md` in this repository is intentionally neutral and only describes how to maintain this config repo.
- Stack-specific behavior belongs under `templates/` so this repository does not inject the wrong context into Codex runs here.
