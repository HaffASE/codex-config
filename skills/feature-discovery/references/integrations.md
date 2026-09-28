# Native Codex integration contract

The active tool schemas and effective host permissions are authoritative.
Use only native Codex subagent spawning, waiting, messaging and closing facilities
actually exposed in the current session. Tool names/signatures may vary by build;
never write a fake call, invoke a missing tool, or execute a slash command in Bash.

| Capability ID | Native implementation | Boundary |
| --- | --- | --- |
| native-analysis | coordinator; nc_scout / nc_explorer | Read evidence, no product edits |
| user-interaction | ordinary user conversation | Ask only unresolved material decisions |
| native-planning | coordinator; nc_planner | Planning artifacts owned by coordinator |
| native-council | separate native advisory instances | Off without topic-scoped delegation |
| independent-review | nc_architect and nc_critic | Separate actual instances; frozen packet |

Use an exposed compatible built-in agent if the configured role is unavailable and
no exact-role requirement forbids it; copy the narrow role contract into its task.
Report actual execution identity. If no native spawning is available, the draft can
continue but independent review is unavailable. Sequential self-review is not a
replacement for that gate. No external CLI, provider proxy, tmux or MCP state runtime.

One coordinator owns budgets, artifact writes and final adjudication. Children never
spawn grandchildren or write shared ledgers. Planning agents are configured read-only,
but parent live permission overrides may take precedence; inspect actual permissions.
The coordinator needs only permitted planning-artifact writes. A blanket read-only
parent cannot also persist a run: return artifacts in chat or report that limitation.
Do not weaken the sandbox automatically to make a helper run.

Native /goal is optional for authorized execution, not used to bypass planning-only
mode or product decisions. A Goal belongs to the thread, not this artifact directory.
A status file neither revives workers nor resumes a Goal. The user controls native
pause/resume/clear. Use normal Codex controls for cancellation.

## Worker envelope

Provide task and scope; repository/ref and dirty snapshot; permitted read/write roots;
assigned question; acceptance criteria; prior decisions; exact source/artifact links;
data-sharing limits; output schema; and explicit no-product-write/no-delegation rules.
Require investigated paths, claims versus inferences, evidence references, gaps,
affected requirement IDs, command results if actually run, and recommended next steps.
Do not assume a child received the entire parent conversation or all decisions.

## Requested model diversity

Default native reviewers may use the same model in separate instances. That is
independent-context review, not cross-provider review or statistically independent
samples. Inherit configured models/effort; do not force account-dependent names.
Preserve exact explicit model/provider requirements. Native-only mode cannot silently
substitute Codex for a required external reviewer or fabricate its verdict.
The JSON validator checks declared identity constraints, not provider authenticity.

## External systems and old records

Read private issues only through authorized connected access or supplied text.
Do not search public web for private task content. Publication is off unless current
user authorization specifies the affected system and action. Preserve unrelated data,
perform readback and report actual status. No credentials belong in artifacts.
Imported old capability records and packet hashes stay unchanged. This native revision
uses new capability IDs: create a new native draft, never mutate a reviewed old packet.
