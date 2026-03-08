# AGENTS.md

Repository guidance for Codex working in a React + TypeScript + pnpm codebase.

## Working Agreements

- Understand the local architecture before editing. Check package boundaries, entry points, providers, and existing tests first.
- Prefer the smallest change that satisfies the request.
- Keep unrelated code untouched. No drive-by renames, moves, or formatting churn.
- Preserve public APIs, exported types, route contracts, and component props unless a change is explicitly requested.
- Reuse existing patterns before adding abstractions.
- Document assumptions when intent is unclear.
- When behavior changes, update tests in the same change whenever practical.
- Validate after edits with the smallest relevant `pnpm` commands.

## Code Change Policy

- Default to narrow diffs and feature-local edits.
- Extend existing files and modules before creating new layers.
- Avoid broad refactors during bug fixes or medium-sized feature work.
- Do not switch libraries, state patterns, or styling approaches unless the task requires it.
- Do not touch generated files or lockfiles unless the change genuinely requires it.
- If the repo is a workspace, prefer package-scoped commands such as `pnpm --filter <pkg> ...`.

## React Component Guidelines

- Keep components focused. Split orchestration from presentation only when the current file is becoming hard to reason about.
- Prefer explicit props and derived values over duplicated local state.
- Use semantic HTML first. Reach for ARIA only when semantics are insufficient.
- Treat loading, empty, error, success, disabled, and retry states as part of the component contract when async data is involved.
- Match existing controlled vs uncontrolled input patterns unless there is a bug or a clear product reason to change.
- Do not add memoization by default. Use `useMemo` or `useCallback` only when there is a concrete rendering or dependency problem.
- Keep components easy to test: stable labels, clear visible text, and predictable roles.

## Hooks Guidelines

- Follow the Rules of Hooks strictly. No conditional hook calls.
- Use custom hooks for reusable stateful behavior, not as generic dumping grounds.
- Prefer deriving values during render over syncing redundant state in effects.
- Keep side effects in `useEffect` and keep dependencies honest.
- Prevent stale closures in async callbacks, subscriptions, and event handlers.
- Return stable, explicit shapes from hooks, especially for `data`, `error`, `isLoading`, and actions.

## State Management Guidance

- Prefer local state for local UI concerns.
- Lift state only when multiple consumers actually need a shared source of truth.
- Preserve the repo's existing state tools and boundaries.
- Do not duplicate server state across component state, context, and stores without a strong reason.
- Keep URL state, form state, and server state responsibilities separate.
- Handle async races intentionally. Cancel, ignore, or sequence stale requests when relevant.

## Accessibility Expectations

- Every interactive element must have a clear accessible name.
- Use `button` for actions and `a` for navigation.
- Associate form controls with labels and error text.
- Maintain keyboard access and visible focus states.
- Preserve logical heading order and landmark structure.
- Use accessible roles and labels that support reliable testing.
- Announce async status or validation feedback when users would otherwise miss it.

## Testing Expectations

- Prefer React Testing Library queries by role, label, and visible text.
- Avoid brittle selectors and overuse of test ids.
- Test behavior, not implementation details.
- Cover loading, error, empty, success, and interaction states when relevant.
- For hooks and business logic, test observable outcomes rather than private internals.
- Keep mocks narrow and deterministic.
- Avoid snapshot-heavy testing unless the repo already relies on it for a specific area.
- When behavior changes, update existing tests before adding broad new coverage.

## Styling Guidance

- Follow the existing styling system, tokens, and file conventions.
- Keep style changes scoped to the requested UI.
- Avoid one-off values when the codebase already has tokens or utilities.
- Do not restyle neighboring components without a product reason.
- Check responsive behavior, overflow, truncation, and focus visibility when touching UI.

## Performance Guidance

- Measure or identify the bottleneck before optimizing.
- Avoid redundant state and avoid passing unstable props without need.
- Memoize only when justified by expensive computation or avoidable re-renders.
- Keep list keys stable and meaningful.
- Be careful with effect-driven re-render loops, especially around fetches, filters, and derived state.
- Prefer simple data flow over clever indirection.

## Git and Change-Scope Rules

- Keep each task to one focused diff.
- Do not revert or clean up unrelated local changes.
- Do not rename files, move modules, or reorder exports unless it materially helps the requested change.
- Leave the branch easier to review than you found it.
- If a task implies a larger refactor than requested, say so before expanding scope.

## Validation Checklist After Changes

- Run the narrowest lint command that covers touched files.
- Run the narrowest typecheck that covers touched packages.
- Run targeted tests for changed hooks, components, and business logic.
- If UI behavior changed, do a quick manual or browser-assisted verification.
- Check affected accessibility surfaces: labels, roles, keyboard behavior, focus, and status messaging.
- Report any validation you could not run.

Useful command patterns:
- Single package: `pnpm lint`, `pnpm exec tsc --noEmit`, `pnpm test -- <pattern>`
- Workspace package: `pnpm --filter <pkg> lint`, `pnpm --filter <pkg> exec tsc --noEmit`, `pnpm --filter <pkg> test -- <pattern>`
