# Frozen-packet review protocol

## Scope and evidence

The reviewer receives the revision's `manifest.json` and `packet/`, assigned role,
review rubric, original task, and authorized read access to the pinned sources.
It independently checks important source claims rather than only reading the
coordinator's interpretation. For promised independent parallel opinions, do not
feed another reviewer's conclusion before the first pass. A native sequential
Architect → Critic workflow may let Critic read the architect's reasoning: record
that information flow and do not call it blinded or cross-model by implication.
Use different instances; reports may then be reconciled by the coordinator.

The coordinator can serialize a returned report, but must retain the raw response
when available and must not invent the reviewer's identity, verdict or findings.
`reviewer_id` denotes an actual agent/session, not the role name.

## Rubric

Architect: coherent shared boundaries; actual backend execution; API/DTO semantics;
cache/request ownership; authorization; reference lifecycles; migration/compatibility;
backend/frontend dependencies; rejection of overengineering and copied abstractions.

Critic: requirement coverage; material unanswered questions; decision authority;
work that can be implemented in order; specific test-first oracles; mock blind spots;
missing errors/variants; contradictory documents; claims stronger than evidence;
conditions of start, completion and stopping. Do not ask for decorative documents.

Both report findings with an impact, concrete artifact/source location, and required
resolution. Use the same stable finding ID in later rounds. Severity means:
`blocker` prevents a meaningful/safe plan; `major` materially changes implementation
or acceptance; `minor` is editorial/non-blocking. Do not downgrade an old finding
just to pass. A mistaken material finding can be resolved with evidence and rationale.

## Report shape

Use `assets/review-template.json` from the skill root. Set actual provider/model,
instance identity, completion time, revision, digest, scope, summary, verdict,
and cumulative findings. The report is a declaration, not a signature.

The first review reads all packet files (`mode: full`). Every later snapshot declares
the required scope. A delta report must partition the current file set into
`reviewed_files` and `inherited_files`; changed and impacted files cannot be inherited.
List all deleted previous files in `acknowledged_deletions`.

For delta review, independently check the impact set against requirements, decisions,
API rows, tasks, tests, and cross-file references. Include changed nodes plus their
semantic dependents. The helper checks the declared scope, not its semantic completeness.
If impact is uncertain, run a full review. Any changed architecture/security decision
forces full review in the helper; an unregistered architectural change must also force
full review through the reviewer rubric.

Prior findings must remain in the role's cumulative ledger, including resolved ones.
Material findings require `status: resolved` and a concrete resolution. Only minor
findings can use `accepted-risk`; they need a rationale and must remain visible.
`verdict: accept` cannot coexist with an unresolved blocker/major finding.

## Identity and approval limits

The helper rejects a reviewer ID equal to an author ID and rejects reuse of one
instance for multiple final roles. This checks declarations, not real identity or
independence. Distinct providers/models are required only when configured, and
that too is based on reported metadata. No authenticity or anti-tamper authority is
claimed; trusted runtime receipts/signatures would require a separate integration.

SHA-256 binds a report to the bytes and review scope declared in a local manifest.
It detects accidental changes, additions, omissions and stale reports. It does not
prevent a malicious writer from replacing both artifacts and hashes.

## Outcomes

`READY`: planned work is reviewed; no declared external prerequisite is open.
`READY_WITH_PREREQUISITES`: reviewed plan with explicit owned prerequisites.
Neither means that the feature works, all runtime paths were tested, or implementation
was authorized. `NEEDS_WORK`: invalid artifacts, material gaps or rejected review.
`BLOCKED`: required access, reviewer or product authority is missing.

Stop after the configured total round budget and report the remaining findings. Minor
wording issues do not justify endless loops. All content edits, including wording,
require a new digest and fresh attestations; a narrow delta is enough when appropriate.

## Imported verdicts and chronology

An index reporting `WATCH`, `APPROVE`, exit 0 or matching SHA is not the underlying
verdict, receipt or manifest. Preserve the report as artifact evidence until the
actual reviewed bytes and reports are available and validated. A complete local
upload-link inventory is not approval either. The source-bundle helper always
emits `implementation_authorized: false` and `review_authenticity: not_verified`.

A later scoped execution handoff does not retroactively change earlier review
bytes. Record its date, direct-user-authority reference, allowed slices/repositories,
exclusions, actor-specific Git permissions and remaining gates separately. It may
explain what happened later; reading it alone does not authorize a new executor.
Use a separate, explicitly requested execution workflow rather than widening this
planning skill. Do not treat deferred subcases as passing tests.
