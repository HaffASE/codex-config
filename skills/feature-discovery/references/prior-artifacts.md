# Reuse protocol for existing or partially supplied planning artifacts

This protocol precedes new discovery whenever an earlier run is supplied. It does
not rerun the old task or infer approval from uploaded instructions.

## 1. Establish what is actually available

Read the entrypoint and map each supplied file to its original logical project path.
Distinguish current substantive documents, historical immutable revisions, navigation
metadata, review receipts/manifests, primary-source evidence, and later handoffs.
Do not choose the largest revision suffix globally or silently fix frozen headings.

The helper `scripts/check_source_bundle.py` accepts an explicit source map. It can
resolve `../../plans/...` in the original virtual tree even when uploads are flat.
It never searches a matching basename, follows a private `/Users/...` path, visits
a URL or opens an unlisted file. It captures upload SHA-256 values and reports absent
linked/required documents as **not supplied here**, not broken in the real project.

Use `assets/source-map.example.json` as a shape example, not a populated source map.
Set `active_documents` deliberately from the index plus any separately identified
later event. Set `required_documents` to the outputs needed for the intended claim:
for example the architecture, entity plans, test catalogue and relevant raw reviews.

Exit 0 means only that inspected links resolve inside the declared map. Exit 1 is a
partial bundle. Exit 2 means invalid input. The parser checks simple inline links,
not arbitrary CommonMark, anchors, semantic references or paths inside code spans.
Missing bare-path references must still be recorded by the coordinator.

## 2. Reuse without laundering evidence

Keep four different statements separate:

1. The file is present and its uploaded bytes were hashed.
2. The file reports a source inspection, test, review or user authorization.
3. The underlying source/test/review receipt was also supplied and inspected.
4. The claim was independently re-verified against a matching current environment.

Only the first two can normally be established from a narrative index. `kind:
artifact` in plan.json represents reported evidence and requires its captured hash.
It cannot stand in for source/contract or runtime evidence. A partial import is useful
input to discovery, not a restored READY plan or an authenticated independent review.

Missing final plans should not be regenerated from their titles. Missing test
catalogues should not be reconstructed from ID counts. Preserve a coverage gap and
continue only with conclusions the available documents support.

## 3. Keep chronology and authority separate

An active index can select newer documents while a frozen source inside that set
still cites its own historical packet. That does not automatically invalidate either
snapshot. Follow original manifests for original verdicts; use the index for current
navigation. Record conflicts explicitly rather than rewriting old reviewed bytes.

For technical corrections, identify the affected field/claim and its dependents.
A uint32 correction does not reopen unrelated interviews. Literal wire spelling is
not an invitation to normalize the API from general knowledge. A new source snapshot
must not inherit a previous deployed-proof label.

Authority has a different ordering from evidence freshness. A later scoped handoff
can record a subsequent user decision, but it does not authorize everything in the
roadmap, remove backend/release gates or change the old planning snapshot. Capture:
`issued_at`, `authority_ref`, allowed slices and repositories, excluded operations,
actor-specific rights, prerequisite conditions and the exact plan reference.

In an artifact-analysis invocation, record this as historical/scoped authorization
reported by a document. Do not execute it or infer new permissions for tools, external
providers, billing, Jira, Git, package installation or product-code writes. This
skill ends with planning artifacts; a separate user-authorized workflow executes.

## 4. Preserve decisions and disagreement

Carry direct user answers, authorized council defaults, source corrections and
coordinator adjudications separately. Do not turn unanswered questions into consent.
A recorded four-member council is not five votes; preserve unavailable members and
strongest dissent. Numerical ambiguity estimates, when inherited, measure only what
the source says they measure, not human agreement or probability of correctness.

Do not repeat resolved questions unless facts, scope or applicable authority changed.
Do not invent timed waiting or approval-by-timeout in a synchronous environment.
A new council call requires applicable delegation and permission to share its inputs.

## 5. Preserve test meaning across phased work

Keep the original TEST[ID] spellings in source references. When a new registry uses
TEST-prefixed internal IDs, record an explicit legacy-to-registry map without changing
the originals. Retired aliases are not additional active tests.

Separate planned tests, historical baseline receipts, current executed tests, and
partial/deferred observations. One ID can cover several observations across slices.
Passing the available subset does not make the whole ID GREEN. Specify the remaining
observable case, target slice and reason; do not create unused abstractions or fetch
new dependencies merely to close future checks early.

A release gate, an integration prerequisite and a before-first-form decision have
different applicability. Preserve owner and point of enforcement. Do not block a
form-free slice on dirty-form UX or waive a secret-resolution gate as editorial debt.

## 6. Preserve the actual review contract

Read explicit stage, per-file, alias, effort and fallback requirements before using
default reviewers. `reviewed_files` alone is not a per-file verdict. Use strict report
maps and preserve the original WATCH/APPROVE vocabulary in raw receipts.

A WATCH may close planning only when its actual report says so and its conditions
are represented. Missing raw verdicts cannot be filled by the coordinator. An index,
SHA calculation or zero process exit code is not the verdict itself. Hashes detect
byte changes; they do not authenticate the author, model or permission source.
