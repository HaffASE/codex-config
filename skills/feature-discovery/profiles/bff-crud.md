# BFF CRUD profile

This is a domain checklist, not a second workflow or an assumption that a project
already implements a particular architecture. Apply it inside `feature-discovery`.

## Project conventions to verify

For the user's first profile, investigate Snack UI, function-first + widgets +
fractal slices, and reference implementations in VPN/admin-vpn. These are supplied
planning preferences/reference targets, not facts established from source here.
Locate their actual packages/directories and versions before citing them. Do not
silently replace them with feature-first/FSD or import code from unavailable repos.

Compare representative list, create, edit, and detail flows in the reference project.
Record which pieces are reusable, which need adapters, and which are only visual
references. Do not turn a convention into a shared abstraction without two real uses.

## Inventory by operation and data variant

Include only operations actually needed or exposed by the authoritative scope:
list/detail/create/update/delete, reference pickers, validation endpoints, execution
or preview actions, status/history, and polling. Record exclusions with reasons.

For discriminated/nested values, include each meaningful variant: defaults, null vs
absent, enum/union branches, IDs/references, read-only fields, zero/false/empty values,
unknown server values, versioning, and round-trip preservation. Do not infer update
semantics (PUT/PATCH, replacement/merge, immutable fields) from a TypeScript type.

Every inventory row requires five independent coverage entries:

| Layer | Questions |
| --- | --- |
| Contract | Method/path, DTO/schema, auth, project scope, errors, paging/filtering |
| Handler | Validation, ownership checks, transformations, actual registered routes |
| Persistence | Schema, migrations, defaults, references, constraints, delete behavior |
| Execution | Where saved values are consumed, resolved, enforced and reported |
| UI | Routes, forms, detail/list states, data flow, permissions, feedback |

Use `source-confirmed`, `runtime-confirmed`, `missing`, `unknown`, or
`not-applicable`. Explain missing/unknown/N/A; cite actual evidence for confirmations.
Unknown is not absent. A mock response is not a deployed runtime observation.

## Execution is a separate requirement

For `SecretReference`, inspect creation/storage AND downstream use: reference
resolution, secret provider, access identity, project isolation, unsupported types,
missing/deleted references, rotation/caching, and redaction in logs/errors/DTOs.
Trace the scenario controller/runner path only where it actually exists.

The reported reference-run gap is an investigation hypothesis until its source is
read. Do not assert the same bug exists in another revision. A frontend cannot fix
missing backend resolution by saving a correctly shaped object. Plan the backend
change, contract verification, and the affected integration gate separately.
Never copy actual secret values into planning artifacts or external advisor inputs.

## Shared decisions before entity plans

Document request/cache ownership; key scope including project and filters;
invalidation after mutations; DTO ↔ domain/form adapters; normalization vs UI
validation; async reference selection; stale results/cancellation; submission errors;
loading/empty/not-found/forbidden/error states; and supported partial functionality.

For Snack UI forms, examine the existing RHF/Yup/UI-kit bridge when present. Do not
assume those dependencies exist merely from the user's other repositories. Verify
label/help/error behavior, focus management, keyboard use, dirty-close warnings,
disabled vs forbidden actions, and destructive-action confirmation.

For function-first + widgets + fractal slices, identify existing public APIs and
import boundaries. Define ownership and composition; avoid duplicated data-fetching,
entity-to-entity horizontal imports, or an unrequested architecture migration.

## Entity plan content

Use `assets/entity-plan.md` from the skill root only when a separate file helps.
Include fields/variants, operation/API IDs, observable behavior, affected modules,
shared decision IDs, backend prerequisites, error/permission cases, and test IDs.
Do not clone shared architecture into each entity document. Split by implementation
cohesion, not mechanically one document per endpoint.

## Test-first and regression coverage

Specify one failing behavioral example before each substantive implementation slice.
Use unit tests for DTO transformations, schemas, discriminated variants, query keys,
and error mapping; component/integration tests for forms, mutation flows, state
transitions and invalidation; real contract/provider checks for backend assumptions.

Expand regression tests after the initial vertical slice. Include list/detail wiring,
route params/project context, references, delete conflicts, permission changes,
empty/partial results, and run/preview flows where applicable. Avoid blanket coverage
percentages without a measured baseline. Establish the existing test command before
proposing `pnpm test:unit` or a Playwright invocation; never invent package scripts.

## Failure modes learned from the supplied reference artifacts

Use these as questions to investigate in the current repository, not established
facts about an uninspected revision. The optional case note is
[the source-bounded reference-run analysis](../references/reference-run-lessons.md).

- **Operation coverage is not variant coverage.** Inventory RPCs separately from
  request union branches, response alternatives and actual runtime conversions.
  Keep full roadmap, first typed increment, storage-only support, execution gates
  and explicit exclusions separate. Count distinct output variants, not switch cases.
- **Wire payload is not a generated argument name.** Trace HTTP body mapping,
  optional presence, replacement vs preservation, oneof validity, empty/false/zero
  and round-trip readback. Derive numeric bounds per concrete field from canonical
  schema; not every field described as a version needs a decimal-string adapter.
  Preserve literal wire names even when they appear misspelled; never silently fix
  them from general protocol knowledge.
- **Validation, stored representation and execution can disagree independently.**
  Trace protocol flags, defaults, conversion wrappers, widths/overflow, ignored
  controls and read/write asymmetry through the actual consumer. Define an explicit
  storage-authoring policy per variant; a warning is not a universal remedy. Secret
  authoring may require server rejection or a resolver, while a different variant
  may permit expressly authorized storage-only editing with a runtime warning.
- **No disclosure means no automatic retrieval, not hidden columns.** For sensitive
  or heavy DTOs, test that a list does not issue hidden detail requests. Deliberate
  detail navigation is a distinct capability. Rich rows require an approved safe
  summary source; UI masking does not undo transport/cache exposure.
- **Bounded enrichment needs an owner and a unit.** Specify page size, maximum
  concurrent requests, eligible entities, cancellation on page/project switch,
  per-row errors and cache lifetime. Enforce fetch policy in the entity model,
  never inside a presentation-only table. Do not bake page-size 10/cap 4 into
  every unrelated product; they are decisions from one reference run.
- **Same package namespace is not shared provider/cache identity.** Inspect direct
  dependencies, actual table imports, generated hooks and transport contexts
  separately. A provider-agnostic table must not be blamed for a generated-hook
  major-version mismatch. Do not install missing packages without permission.
- **Status codes are not business fixtures.** Separate declared, source-mapped,
  test-inspected, test-executed and deployed-observed errors. A declared 409 with
  unknown trigger permits a generic recovery test; it does not justify an invented
  dependency-conflict scenario. Path-project mismatch alone is not proof of an
  authorization bypass when another ACL boundary exists.
- **Lifecycle and ordering are cross-entity behavior.** Investigate implicit project
  creation, prerequisite resource creation, last-resource deletion, referenced
  deletes, canonicalized scheduler readback and best-effort runtime cleanup.
  Plan catalog/workspace reconciliation without claiming immediate runtime stop.
- **Defer at the first real consumer, not forever.** Before-form guards, new form
  dependencies and shared factories need an owner and an applicable slice. A
  table-only increment must not invent forms or install packages to satisfy a
  future gate. Keep later work explicitly deferred with its remaining observations.
