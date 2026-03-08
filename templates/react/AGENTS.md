# AGENTS.md

Repository guidance for Codex working in this React + TypeScript + pnpm project.

## Working Agreements

- Use `pnpm` for installs, scripts, and workspace commands.
- Prefer the smallest safe change that solves the task.
- Preserve public APIs, route contracts, and component props unless the task explicitly requires changes.
- Avoid unrelated renames, refactors, or formatting churn.
- After edits, run the narrowest relevant validation commands.

## Common Commands

- Install: `pnpm install`
- Lint: `pnpm lint`
- Typecheck: `pnpm exec tsc --noEmit`
- Test: `pnpm test`
- Workspace package: `pnpm --filter <pkg> <command>`

## How To Navigate This Repo

- Start with the nearest route, feature folder, or package that owns the behavior.
- Reuse local patterns before introducing abstractions.
- Fill the docs below with project-specific rules after exploring the codebase.

## Project Guides

- React and component guidance: [docs/REACT.md](docs/REACT.md)
- Hooks and state guidance: [docs/STATE.md](docs/STATE.md)
- Testing guidance: [docs/TESTING.md](docs/TESTING.md)
- Styling and UI guidance: [docs/STYLING.md](docs/STYLING.md)
- Review and validation checklist: [docs/VALIDATION.md](docs/VALIDATION.md)
