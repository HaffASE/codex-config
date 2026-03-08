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
- `templates/react/docs/*.md` -> `docs/*.md`

This template follows the progressive-disclosure approach described in [A Complete Guide To AGENTS.md](https://www.aihero.dev/a-complete-guide-to-agents-md): keep root `AGENTS.md` short and move stack-specific detail into linked docs.

## Fill Prompt

After copying the starter files into a real project, run a prompt like this inside that project:

```text
You are filling out the AGENTS.md starter files for this repository.

Context:
- This project already contains:
  - AGENTS.md
  - docs/REACT.md
  - docs/STATE.md
  - docs/TESTING.md
  - docs/STYLING.md
  - docs/VALIDATION.md
- These files are starter templates and contain TODO placeholders.
- Your job is to replace placeholders with project-specific guidance based on the actual codebase.
- Keep the root AGENTS.md short. Do not turn it into a giant instruction dump.
- Follow progressive disclosure: broad rules in AGENTS.md, detailed rules in the docs files.

What to do:
1. Explore the repository in read-only mode first.
2. Detect the actual stack, package layout, scripts, routing, state management, testing setup, and styling approach.
3. Fill each docs/*.md file with concrete rules taken from the codebase.
4. Keep guidance practical and specific to this repo.
5. Remove TODOs that you can confidently replace.
6. If something is unclear, keep a short assumption note instead of guessing.
7. Preserve minimal diffs and do not create extra docs unless necessary.

Output requirements:
- AGENTS.md must stay compact and only point to the detailed docs.
- docs/REACT.md should cover component structure, forms, async UI states, and performance notes.
- docs/STATE.md should cover hooks, effects, state ownership, shared state, and data fetching.
- docs/TESTING.md should cover test stack, query style, coverage expectations, mocking, and reliability.
- docs/STYLING.md should cover styling system, component styling, responsive behavior, and accessibility.
- docs/VALIDATION.md should cover required commands, targeted checks, manual verification, and review checklist.

At the end:
- summarize what you filled,
- list assumptions,
- list commands you used to inspect the repo.
```

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
