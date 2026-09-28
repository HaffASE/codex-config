---
name: git-message
description: "Draft commit or MR text using the user’s frontend/backend Jira conventions. Text only; no Git or remote mutations."
---

# Git message

Inspect the supplied diff/task or authorized local repository context before writing.
Determine frontend versus backend and the actual Jira key from evidence; never invent
an issue ID. For frontend: `feat(JIRA-123): English imperative title`, substituting the
correct conventional type (fix, refactor, test, docs, chore, etc.). For backend:
`[JIRA-123]: English imperative title`. Apply the same title convention to commits.

For an MR description write in Russian, using `Что поменялось`, `Зачем`, and `Тесты`
when tests actually ran or their omission needs disclosure. Preserve the existing
`Closed JIRA-123` section and its actual key; do not duplicate an automatically created
section. Distinguish executed tests from planned tests and unavailable checks.

Return draft text only. Do not stage, commit, create branches, push, create/edit an MR,
resolve review threads or publish comments unless the current user requests that
separate action. If the Jira key or required classification is genuinely unavailable,
state the missing value rather than outputting a plausible fake key.
