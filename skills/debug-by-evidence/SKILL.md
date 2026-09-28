---
name: debug-by-evidence
description: "Use when the cause of a runtime, test, build, integration, performance, or state failure is unknown or disputed."
---

# Debug by Evidence

Find the narrowest supported cause before proposing a durable repair.

## Boundary

Preserve the user's requested scope. A diagnosis or review request authorizes
inspection and safe read-only checks, not edits. If the cause is already
established by a reliable reproducer and direct evidence, skip the investigation
loop and move to the requested repair.

## Evidence loop

1. State the observed symptom without embedding a cause.
2. Reproduce it, or identify the exact environment and event where it occurs.
   A successful local run does not disprove an intermittent or
   environment-specific failure.
3. Locate the narrowest known boundary: input, component, transition, external
   dependency, or commit range.
4. List only plausible hypotheses supported by current facts. Select the
   smallest check whose result distinguishes the leading alternatives.
5. Run one discriminating check at a time. Update confidence from its result;
   do not collect only confirming evidence.
6. Call something the root cause only when evidence connects it to the symptom
   and explains the relevant observations.
7. If a fix is requested, make the smallest root-cause repair and verify the
   original failure plus the nearest regression surface.

Do not change retries, timeouts, tracing, logging, configuration, or code during
diagnosis-only work. Recommend such instrumentation when needed and state why.

Distinguish an emergency mitigation from a root-cause repair. A mitigation may
be appropriate, but do not present it as eliminating the cause.

## Output

Report:

- observation and reproduction status;
- evidence gathered;
- leading cause or hypotheses with confidence;
- proposed or completed action;
- verification result;
- remaining evidence gaps.

Stop when the cause is supported to the level needed for the requested action,
or when a specific unavailable observation is the next necessary discriminator.
