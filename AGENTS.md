# AGENTS.md

Repository guidance for `codex-config`.

## Purpose

- This repository stores reusable Codex configuration, agent presets, and project templates.
- Treat files here as source templates, not as instructions for a React application in this repository.

## Working Rules

- Keep changes focused and easy to copy into another project.
- Prefer reusable defaults over project-specific assumptions unless the file lives under a template folder.
- Do not rename or reorganize template files without a clear compatibility reason.
- When updating an existing preset, preserve intent and keep diffs small.
- Document assumptions in `README.md` when a template is tailored to a specific stack.

## Template Policy

- Put stack-specific guidance under `templates/`, not in the repository root.
- Keep root-level instructions neutral and applicable to a config repository.
- Avoid duplicating the same guidance across multiple presets unless the duplication is intentional for portability.
- Favor strong defaults, but leave room for per-project overrides.

## Validation

- Check formatting and file paths after edits.
- Re-read changed templates for internal consistency.
- If a template references commands, prefer realistic defaults and avoid inventing unsupported tools.
