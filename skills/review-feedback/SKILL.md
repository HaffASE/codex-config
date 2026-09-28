---
name: review-feedback
description: "Use when the user supplies pull-request comments, inline review feedback, requested changes, or a disputed technical suggestion."
---

# Review Feedback

Convert review comments into technically justified decisions before acting.

## Preserve authorization

Analysis, triage, or explanation requests do not authorize code changes. When
implementation is requested, apply accepted in-scope items only. Do not commit,
push, resolve remote threads, or post replies unless the user explicitly asks.

## Evaluate each item

1. Locate the exact current code and requirement the comment concerns. Check
   whether a later change has already resolved or invalidated it.
2. Identify the reviewer's premise and intended benefit: correctness,
   compatibility, security, maintainability, consistency, performance, or
   preference.
3. Verify that premise against the code, supported environments, specifications,
   repository conventions, and relevant tests.
4. Classify the item:
   - **accept** — correct, useful, and in scope;
   - **reject with evidence** — incorrect, unnecessary, incompatible, or harmful;
   - **clarify** — material ambiguity changes the implementation;
   - **already resolved** — current state no longer has the issue;
   - **out of scope** — valid idea that expands the requested work.
5. For accepted implementation work, make the smallest coherent change and
   verify the affected behavior.

Do not agree merely because the feedback is confident or comes from a reviewer.
Push back directly with technical evidence when needed. Do not focus on whether
the response contains gratitude or a preferred social phrase.

Process independent clear items without waiting on an unrelated ambiguity. Ask
one focused question for the blocked item when its alternatives materially
change the API, behavior, compatibility, or scope. Do not silently choose a
scope-expanding interpretation.

## Report

For every item, state:

- disposition;
- evidence and reasoning;
- action taken or proposed;
- validation result, if implemented;
- unresolved decision or scope boundary.

Stop when all items are classified and every authorized accepted change is
verified. Leave disputed, ambiguous, stale, and out-of-scope items visible
rather than reporting the entire review as resolved.
