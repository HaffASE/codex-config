---
name: browser-debug
description: "Investigate local browser rendering, interaction or app wiring using tools actually available. Diagnosis by default; no synthetic screenshots or silent installs."
---

# Browser debug

Establish the expected behavior, URL/environment, relevant UI state, build/ref and
user-authorized scope. Inspect the actual installed browser tooling and dev-server
command. Start a local server only when permitted; do not install browsers/dependencies
or connect to production merely to make the workflow work.

Use available native/browser tools or the repository's installed browser test runner.
No mandatory MCP dependency is assumed. Without a real browser, return a static
hypothesis and explicitly leave visual/runtime verification open.

Reproduce the failing state and relevant viewport; inspect rendered DOM, console,
network, focus, accessible names, computed layout and screenshot as appropriate.
Trace the symptom to code/data. Distinguish CSS/rendering, request/cache, routing,
provider wiring and business-state causes. A page load alone does not prove its flows.
Use no private credentials or destructive real operations in a smoke test.

Diagnosis does not authorize code or test edits. Under repair authority, make the
smallest supported fix and repeat the actual failing interaction plus its nearest
regression. Record environment, commands, screenshot/trace references and limitations.
Use nc_browser for bounded investigation; the coordinator owns any written artifacts.
Do not claim a screenshot was inspected or an interaction passed unless it happened.
