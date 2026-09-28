---
name: frontend-tests
description: "Audit or improve React/TypeScript tests using the repository’s Vitest/RTL/browser setup. Audit by default; edits only when requested."
---

# Frontend tests

Inspect package.json, pnpm lockfile, Vitest projects/config, setupTests and nearby tests.
Discover the actual unit/browser/E2E commands and installed versions. Prefer pnpm
where the repository uses it; do not assume `pnpm test:unit` exists or run downloading
npx/pnpm dlx commands. Do not add libraries, providers or Playwright browsers silently.
A test audit is read-only. Write tests only when requested or included in an authorized
implementation task; preserve explicit no-new-tests and dependency restrictions.

Choose evidence at the changed boundary. Pure transforms/validation: unit tests.
React UI/hooks: the existing RTL/provider harness. Network: the existing request
boundary mock (such as installed MSW), not blanket mocks of React Query. Routing and
app wiring: integration or browser tests. Layout, focus, real visibility and browser
APIs: the actual browser environment, not jsdom assertions pretending to prove them.
Vitest Browser Mode, RTL and Playwright have different APIs; do not mix their imports.

Test public behavior, meaningful branches, errors/loading/empty states and lifecycle.
For RHF/Yup inspect defaults/reset, transform/validation semantics, submit duplication
and server errors. For React Query isolate each test's client/cache, control retries
where needed, and check keys, invalidation, cancellation and tenant/context switches.
For async work await user actions/assertions; replace sleeps with controlled signals
or the installed tool's retry mechanism. Restore mocks, timers, globals and environment.
Avoid `.only`, assertion-free tests, snapshot-only contracts and private-call coupling.
Honor existing TEST[ID] conventions and preserve partial/deferred subcases separately.

Read [the audit rubric](references/audit-rubric.md) when scoring is requested. A score
is a rubric judgment, not measured coverage or an independently verified safety level.
For a new bug test prove it can fail for the intended cause when feasible; do not
claim a pre-fix run happened if it did not. Run targeted checks first, then relevant
repository gates. Report non-zero discovery, actual results and unavailable checks.

Output covered behavior, concrete weaknesses/missing scenarios, smallest justified
changes, command results, optional before/after rubric score and remaining gaps.
Do not rewrite a whole suite or add a test per method to satisfy a numerical quota.
