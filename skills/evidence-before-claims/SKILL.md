---
name: evidence-before-claims
description: "Use immediately before claiming that work is complete, fixed, passing, safe, merge-ready, or otherwise verified."
---

# Evidence Before Claims

Make each material claim no broader than direct, current evidence supports.

## Build the proof

1. List the claims the final response will make.
2. For each claim, identify the command, observation, or artifact that would
   directly prove it. A related check is not automatically proof.
3. Check freshness: the evidence must describe the state after the latest
   mutation relevant to that claim.
4. Run the smallest sufficient verification. Broaden it when the claim or risk
   is broad:
   - a targeted test can prove one behavior;
   - a suite can support its covered surface;
   - merge readiness also depends on the repository's relevant gates, current
     diff, and unresolved review or integration state;
   - visual correctness requires inspected rendered evidence.
5. Read the result, exit status, and relevant output. Do not infer success from
   starting a command or from the absence of visible errors.
6. Match the final wording to what passed.

Treat worker or tool summaries as inputs, not automatic proof of the current
integrated state. Use their logs or rerun the affected check when the evidence
is unavailable, ambiguous, or stale.

A later mutation invalidates only evidence that could be affected. A Markdown
edit does not automatically invalidate code tests; a source change may
invalidate tests, build output, screenshots, or generated artifacts that depend
on it.

Do not run every possible check for a narrow claim. Do not describe work as
failed merely because optional proof is unavailable. Narrow the claim and state
the remaining uncertainty.

## Report

For each material conclusion, provide:

- claim;
- evidence and result;
- scope covered;
- freshness relative to the latest relevant change;
- material scope not verified.

Stop when each reported claim has sufficient fresh evidence or has been
explicitly narrowed to the evidence available. `$code-review` still owns
independent review and `$verify-work` owns requested verification coordination when those
workflows are requested.
