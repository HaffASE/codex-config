---
name: testing-code-changes
description: "Use when a feature, bug fix, refactor, migration, configuration change, or review fix needs a test strategy or regression proof."
---

# Testing Code Changes

Choose the smallest credible evidence that observes the changed behavior and its
material risks.

## Select evidence by change

- **Reproducible bug:** Confirm the failing case before the repair. Prefer a
  regression test through public behavior when the existing harness can express
  it. Verify that the case fails for the intended reason and passes after the
  fix.
- **Stable new behavior:** Prefer test-first when the contract is clear and the
  repository has a suitable harness. Test externally visible behavior rather
  than implementation structure.
- **Legacy refactor:** Add or identify characterization coverage for behavior
  that must remain stable, then use targeted tests to protect the changed
  boundary.
- **Configuration, schema, or migration:** Prefer parsing, schema validation,
  dry-runs, migration checks, or consumer contracts. Do not add a unit test that
  merely repeats a configuration value.
- **UI or visual change:** Combine relevant code checks with rendered browser,
  Storybook, screenshot, or geometry evidence at affected states and viewports.
  Lint, snapshots, and unit tests alone do not prove visual correctness.
- **Unavailable external integration:** Use the strongest local, contract, or
  simulated evidence available and report the exact production gap.
- **Documentation or trivial metadata:** Use focused formatting, link, schema,
  or content checks. Do not invent executable tests.

Inspect repository scripts, nearby tests, and established patterns before
choosing commands. Start with the narrowest relevant check; broaden according to
the change's blast radius and the claim you need to make.

Do not delete correct implementation merely because a test was written later.
Do not require a dedicated test for every method, generated artifact, or
mechanical edit. A test must be capable of failing when the protected behavior
regresses.

## Report

State:

- changed behavior and material risk;
- selected evidence and why it observes that risk;
- commands or inspection performed and result;
- broader checks not run;
- remaining untested or external scope.

Stop when the evidence supports the requested change at its actual risk level,
not when every possible test has run.
