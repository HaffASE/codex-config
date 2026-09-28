# Sources, compatibility, and provenance

Documentation inspected on 2026-09-27. The kit targets the documented local native
Codex skill and standalone custom-agent surfaces, not a claimed universal minimum
version. The user's installed client, account, model availability and permissions
were not observed. Runtime capabilities must be checked in the actual session.

## Official references

- Skills, local discovery, symlink support, manual invocation policy and duplicates:
  https://developers.openai.com/codex/skills
  (currently redirects to https://learn.chatgpt.com/docs/build-skills).
  Applied to SKILL.md, agents/openai.yaml and global ~/.agents/skills installation.
- Native subagents and standalone TOML custom agents:
  https://developers.openai.com/codex/subagents
  (currently redirects to https://learn.chatgpt.com/docs/agent-configuration/subagents).
  Applied to nc_* TOML fields, standalone discovery, model inheritance, concurrency,
  actual-tool delegation, and parent live permission override caveats.
- Native configuration reference:
  https://developers.openai.com/codex/config-reference
  Applied to the optional [agents] fragment; no user config is auto-rewritten.
- Global/project instruction layering and AGENTS.override.md:
  https://developers.openai.com/codex/guides/agents-md
  Applied to the optional marked global-guidance merge and override refusal.
- Goals and their limits:
  https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex
  Applied to optional goal-driven execution, pause/resume/clear, bounded continuation.
  The documented 0.128.0 floor is for Goals only, not all agent formats in this kit.
- Native hooks:
  https://developers.openai.com/codex/hooks
  Native hooks exist, but this kit does not install hooks or emulate a lifecycle runtime.
- Lean skills and prompts:
  https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra
  Used as design guidance for small entrypoints and load-on-demand references;
  no specific model name or effort is forced by the package.

## User artifacts actually used

SHA256 values of the exact retrieved inputs are in
`migration/source-manifest.json` (paths relative to the build input, not the user's host).

| Input | Contribution | Treatment |
| --- | --- | --- |
| feature-discovery-kit-v0.2.0.zip | Planning contracts, templates, BFF CRUD profile, Python guards and 95 tests | Native integration and preflight capability IDs changed; review/evidence safeguards retained |
| SKILL(5).md (codex-agent-review) | Review snapshot, independent lanes, findings/contradiction protocol | Native roles mapped, max three concurrent children, runtime ownership replaced |
| review-kit-v0.1.0.zip | 14 thematic review dimensions | Methods and false-positive guidance retained; old orchestration/CLI runner not installed |
| SKILL.md | testing-code-changes | Native manual entrypoint |
| SKILL_2.md | debug-by-evidence | Native manual entrypoint |
| SKILL_3.md | skill-evaluation | Native runtime ownership |
| SKILL_4.md | evidence-before-claims | Removed old QA-runtime reference |
| SKILL_5.md | review-feedback | Native manual entrypoint |
| SKILL(3).md | Frontend test audit rubric | Supporting reference for frontend-tests |

The previous scoped execution-handoff and planning records informed the authority
boundaries. No original production repository, deployed API, historical model run,
private external tool or local user configuration was revalidated in this build.
User-specific code/credentials and unrelated Library files are not included.

## Deliberate non-equivalence

The new kit is not an OMX compatibility runtime. No tmux Team, mailbox, mission,
HUD, managed external model routing or Ultragoal lifecycle ledger is implemented.
Native same-model separate-instance review is not cross-provider review.
Local validators check bytes/relationships/declared metadata; they do not attest
identity, runtime behavior, permission enforcement or user authorization.
The retained Python code is deterministic local tooling, not an agent coordinator.

The package has no marketplace manifest: local authoring/global installation is the
supported path here. Existing verified plugin distribution may use its skills tree,
but standalone agents still need to be installed/configured via the actual native
surface. Do not distribute duplicate active copies under the same skill names.
