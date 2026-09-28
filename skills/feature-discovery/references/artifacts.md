# Artifact contract v1

Keep one run folder. `draft/plan.json` is the canonical ID/relationship registry;
Markdown explains behavior and tradeoffs by referring to its IDs, not by maintaining
competing registries. The frozen packet is the reviewed source of truth.

```text
<run>/
  index.md
  draft/
    plan.json
    brief.md
    analysis.md
    implementation.md
    tests.md
    entities/                 # optional
    evidence/                 # optional, redacted text only
  revisions/
    r01/
      manifest.json
      packet/                 # captured draft, never edited in place
  reviews/
    r01.architect.json
    r01.critic.json
```

`index.md` is navigation outside the reviewed packet; always link the authoritative
snapshot/report instead of treating a hand-edited status in the index as approval.
Review reports are outside the packet to avoid a self-referential digest. All files
inside a packet are hashed, not just Markdown or a manually supplied allowlist.

## Registry

Use `assets/run-template/plan.json`. It is deliberately incomplete and must fail
validation until filled with real evidence and decisions. Stable IDs have prefixes
`REPO-`, `REQ-`, `EVD-`, `DEC-`, `TASK-`, `TEST-`, `API-`, `Q-`, `PRE-`.
References are arrays of IDs, not duplicated prose. Do not renumber IDs after review.

Repositories contain an ID, full Git commit, worktree status, scope, and a separate
snapshot reference for dirty trees. Unavailable repos cannot support source-confirmed
claims. Relevant dirty/untracked files must be captured by the host; Git HEAD alone
and a bare `git status` are not a content snapshot.

Evidence kinds: source, contract, runtime, user, inference, artifact. Source/contract entries
need repository ID and matching commit; ref should identify path + symbol/line.
Runtime entries additionally need environment, observation time, build/ref and a
redacted result reference. Store comparisons and uncertainty in `analysis.md`.
Imported-document evidence uses `kind: artifact`, `artifact_sha256` and `observed_at`.
It records what the supplied document says. It cannot satisfy source-confirmed or
runtime-confirmed API coverage; reopening the primary source needs a separate entry.
The helper validates metadata, not the truth or availability of these source refs.

Decisions contain origin, category (`architecture`, `product`, `security`, `local`),
acceptance, authority reference, and evidence IDs. Council decisions additionally
need an allowed topic under explicit run-level delegation. Unaccepted decisions may
be reviewed as a candidate but cannot support a READY implementation task. Only
reversible local assumptions can be accepted without new authority.

Tasks contain requirements, decisions, prerequisites through `depends_on`, tests,
owner, affected files/modules and observable outcome. Dependencies must be a DAG.
Each in-scope requirement needs a task, and each task needs tests covering all its
requirements. Cross-entity links use IDs and the common decisions, not copied text.

Tests are always `status: planned`. Fields describe stage (`test-first`, `regression`,
`manual`, `contract`), level (`unit`, `integration`, `contract`, `e2e`, `manual`), method
and expected behavior. For test-first cases, include `red_oracle` describing the
specific missing behavior that makes the first test fail. Put the red→green→regression
sequence in `tests.md`. Execution evidence belongs in evidence entries, not this list.

API inventory declares its authoritative scope and evidence IDs. Each operation or
variant has a disposition, requirement/task links, and exactly five coverage layers:
contract, handler, persistence, execution, ui. Missing/unknown layers need a reason
and resolution tasks unless explicitly excluded. N/A needs a domain reason.
Runtime-confirmed requires runtime-kind evidence, not a DTO, test mock or inference.
This checks declared coverage; the reviewer must reconcile it with the actual API.

Questions record materiality, status and decision IDs. A delegated but unanswered
material question remains blocking. Prerequisites name an owner, completion
condition, resolution tasks, blocked tasks and evidence when satisfied.

## Mechanical commands

From a host where `SKILL` is the installed skill directory and `RUN` is the run root:

```bash
python3 "$SKILL/scripts/validate_plan.py" "$RUN" --draft
python3 "$SKILL/scripts/freeze_plan.py" "$RUN" --revision r01
# Actual independent reviewers now produce reviews/r01.<role>.json.
python3 "$SKILL/scripts/validate_plan.py" "$RUN" --revision r01
```

For a second round after updating only `draft/`:

```bash
python3 "$SKILL/scripts/freeze_plan.py" "$RUN" --revision r02 \
  --mode delta \
  --impact implementation.md --impact tests.md --impact analysis.md \
  --reason "Recheck changed slice, affected acceptance cases and shared dependencies."
```

Final closure also requires the latest revision and an unchanged working draft.
A changed draft cannot reuse an old snapshot's READY result.

The helper requires previous reports, including rejected ones, before advancing to
another revision. It never creates successful reviews or fetches tools/providers.
A full rerun still carries forward the cumulative findings ledger. Policy and budget
cannot change mid-run; choose them explicitly in preflight.

Python 3.10+ and the standard library are sufficient. No network calls or subprocesses.
Packet files are UTF-8 `.md`, `.json`, `.txt`, up to 5 MiB per file; symlinks inside a
packet are rejected. Local links must use simple inline Markdown. Common heading
anchors and explicit HTML anchors are checked; reference-style links are rejected.
Complex nested Markdown-link syntax is outside this lightweight checker. External
URLs are not fetched. Use code spans, not local hyperlinks, for source paths outside
the packet. The helper does not scan secrets, run product tests or enforce a sandbox.

A leftover `.freeze.lock` means capture was interrupted or another capture is active.
Inspect the process/run before manually removing it; never auto-delete another
coordinator's lock. The snapshot protocol assumes a single writer and no concurrent
manual edits. The checked final packet, not the earlier draft, is the review input.

## Optional strict-review extension (backward-compatible schema 1)

New run templates set `review_policy.per_file_verdicts: true`. Legacy schema-1 runs
without that flag retain their older aggregate-report behavior; enabling the flag
mid-run is rejected as a policy change. Select the policy before the first freeze.
Every report then needs `file_verdicts` keyed by exactly all packet paths. Each entry
contains its file `sha256`, `verdict` (`accept`, `watch`, `request_changes`),
`finding_ids` and `prerequisite_ids`. No file may disappear under an aggregate verdict.

`watch` requires an explicit unresolved nonblocking finding or an open prerequisite.
An unresolved major/blocker requires `request_changes`. Packet `accept` is only
planning acceptance; it may coexist with file `watch` but not file `request_changes`.
Open findings must be attributed to files. Inherited file verdicts may not change
without that file being included in the new review scope. Original raw vocabulary
and responses remain in receipts; never synthesize missing per-file opinions.

`review_policy.reviewer_constraints` optionally maps configured role names to exact
`provider`, `model`, `model_alias`, and/or `effort` strings. Only specified fields
are compared. `model_alias` denotes the actual invoked alias; `model` denotes the
reported model identity. Metadata checks do not authenticate the provider/session.
Missing a required alias/effort is a failed requirement, not permission to fall back.

An explicit per-stage review requirement is also a coordinator obligation: list
stage packets and receipts in the passport. The local helper validates each frozen
packet, not the existence or completeness of an external orchestration history.
`max_rounds` bounds local snapshot revisions; total advisor/upstream budgets remain
coordinator-tracked and must not be silently reset or described as script-enforced.

## Native migration note

The field layout remains schema_version 1, but native preflight uses the capability
IDs in integrations.md. Old reviewed packets are historical evidence, not inputs to
be rewritten in place. Prepare a new native draft and new review records. These files
are task artifacts, not Codex runtime state. Local checks do not authenticate agents,
execute tests, enforce filesystem permissions, or grant implementation authority.
