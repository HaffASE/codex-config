---
name: security-review
description: "Review authorized code for concrete security failures across trust boundaries. Read-only; use evidence and do not mistake preferences for vulnerabilities."
---

# Security review

Establish scope, intended trust boundaries, actors/assets and the exact source snapshot.
Read applicable contracts and direct callers/consumers. Use nc_security for a native
independent pass when requested/required; absent tools mean labelled single-agent
analysis, not fabricated independence. No production exploitation or external probing.

Trace attacker-controlled input through validation, authorization, tenant isolation,
serialization, storage and execution. Inspect secrets handling, unsafe shell/SQL,
XSS, SSRF, filesystem boundaries and dependency concerns where reachable in scope.
A dependency version alone is not exploitability: verify affected version, call path,
preconditions and mitigations using primary sources when external research is allowed.

For every candidate show entry point, reachable path, violated protection, impact and
existing mitigations/counterevidence. Separate confirmed defect, hypothesis, hardening
and out-of-scope observation. No finding quota or automatic architecture prescription.
Never copy raw secrets into an artifact. A read-only sandbox does not itself prevent
confidential data from being read or sent; obey data-sharing restrictions explicitly.

Do not fix code, rotate credentials, alter policies or publish vulnerability reports
without current authorization. Return prioritized concrete findings, reviewed scope,
evidence, coverage gaps and smallest remediation direction. No absolute safety claim.
For a full multi-lane change review, use code-review rather than a second review runner.
