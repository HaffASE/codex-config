---
name: code-review
description: "Review a diff, branch, commit or file scope with independent native Codex agents; validate findings and report coverage. No fixes or publishing."
---

# Code review

Read [the full protocol](references/protocol.md) before reviewing.
It is the review contract, including snapshot semantics, independent discovery,
candidate validation, contradiction pass, and verdict versus completeness.
Use the user's language. Bare invocation is full review; quick must be requested.
This skill never changes product files, tests, Git state or remote review state.

## Native role mapping

| Logical lane | Configured agent |
| --- | --- |
| Code reviewer | nc_reviewer |
| Architect | nc_architect |
| Test engineer | nc_tests |
| Critic/security | nc_security |
| Neutral exploration | nc_scout |
| Final verifier | nc_verifier |

Use actual native tools. Batch at most three open children; verifier runs after
independent discovery and leader triage. Required lanes cannot disappear because a
slot is unavailable. Without native spawning, return a labelled single-agent partial
review, never an independent/full approval. Do not invoke another Codex CLI as a worker.
Do not use invented tool signatures or force a model that was not configured.

Pass the same pinned input packet, neutral context, exact constraints and selected
checklists to each lane. Initial lanes must not see peer findings. A fresh instance
is not automatically a different model or an isolated worktree. Return actual IDs.

## Specialist checklists

Read only the applicable files under [dimensions](references/dimensions/index.md).
They preserve the prior review-kit's frontend, backend, contracts, reliability,
security and test checks without installing a second review runner or 20 global skills.
Send a lane at most three adjacent dimensions. A checklist is not a new orchestrator.

## Output

Lead with validated actionable findings, then verdict and review completeness,
reviewed snapshot, actual lane coverage, commands/results and unresolved gaps.
APPROVE is a report result for the reviewed scope, never a remote approval action.
Zero findings is valid; zero test discovery or failed tools is not evidence of success.
