# Frontend test audit rubric

## Scoring Rubric

Maximum: 10.

- 1.2: public intention, not private implementation.
- 1.4: scenario coverage.
- 1.2: deliberate test boundary.
- 1.2: determinism and isolation.
- 1.2: meaningful assertions.
- 1.0: reliable async.
- 0.8: setup/fixtures quality.
- 0.8: correct environment.
- 0.7: type safety and maintainability.
- 0.5: performance/debuggability.

Hard caps:

- committed `.only`: max 6.
- no meaningful assertion: max 6.
- unawaited async assertion: max 6.5.
- real external network/time/random affecting result: max 7.5.
- private implementation-only tests: max 8.
- shared mutable state causing order dependence: max 8.
- snapshot-only specification: max 8.

## Audit Report Format

Use this structure:

```md
# Vitest Test Audit

## Score

<x>/10

## Summary

<2-5 sentences>

## Evidence

- <file/test>: <what it verifies well>
- <file/test>: <risk or missing behavior>

## Hard Caps

- <none or cap + reason>

## Missing Scenarios

- <scenario>

## Flakiness / Determinism Risks

- <risk>

## Boundary Issues

- <over-mocking/under-mocking/network/time/env/global issue>

## Recommended Fix Plan To Reach 9/10+

1. <fix>
2. <fix>
3. <fix>

## Verification

- Command: <command or not run + reason>
- Result: <pass/fail/not run>
```
