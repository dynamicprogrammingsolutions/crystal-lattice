# Resolve Repeated Context-Helper Reserved-Key Warnings

Investigate the high volume of `context_reserved_key_clash_external` warnings during normal agent requests, correct unintended context layering where appropriate, and otherwise reduce or mute warnings that are expected and non-actionable without hiding genuine caller conflicts.

## Requirements checklist

- [x] The source of the repeated `context_reserved_key_clash_external` warnings is identified for the affected request, tool, and rebuild context paths.
- [x] Each observed collision is classified as either an unintended duplicate context handoff or an intentional precedence case.
- [x] Unintended duplicate context propagation is corrected at the appropriate ownership boundary rather than hidden by logging changes.
- [x] Expected, non-actionable collisions no longer produce repeated warning noise; use a lower level, deduplication, narrower warning condition, or another justified mechanism.
- [x] Genuine caller attempts to override core- or application-owned context keys remain detectable with enough information to diagnose the conflict.
- [x] Existing context precedence is preserved: specific-layer values override generic-layer values, and caller-provided extras cannot override owned keys.
- [x] Request, rebuild, tool, lifecycle, and application-to-core context contents remain compatible for existing plugins and actions.
- [x] Regression coverage demonstrates both a normal flow without warning noise and an actual external reserved-key clash with the intended diagnostic behavior.
- [x] Representative agent/tool-loop verification completes without the previous repeated warning stream.

## Observed behavior

The task-guidance GLM fork smoke produced 57 warnings in:

`tmp/task-guidance-eval/logs/20260721-task-guidance-cli-fork-smoke-2.log`

After stripping terminal color codes, the warnings were distributed as follows:

| Count | Builder | Call path | Key | Winning layer |
|---:|---|---|---|---|
| 25 | `core` | `tool` | `config` | `specific` |
| 18 | `core` | `request` | `config` | `specific` |
| 7 | `core` | `rebuild` | `request_id` | `specific` |
| 7 | `core` | `rebuild` | `config` | `specific` |

The warnings occurred during otherwise successful, ordinary model/tool-loop execution rather than an explicitly adversarial context override.

## Current implementation

`core/python/agent_core/plugin/context_helper.py` owns `merge_context_layers(...)`.

Its current precedence contract is:

- Generic-layer keys are installed first.
- Specific-layer keys replace generic keys and emit `context_reserved_key_clash_internal`.
- Caller-provided `extra` values are additive only.
- An `extra` key that is already owned is ignored and emits `context_reserved_key_clash_external`.

The external warning is emitted at approximately lines 52–64 of that helper.

Core context construction is centralized in:

- `core/python/agent_core/core_context.py`
  - Request context: `CoreContext.build_request_context(...)`
  - Rebuild context: `CoreContext.build_rebuild_context(...)`
  - Tool context: `CoreContext.build_tool_context(...)`

Application context construction is centralized in:

- `core/python/agent_app/app_context.py`
  - Application-to-core handoff
  - Lifecycle, UI, session-action, and tool contexts

Likely investigation points include application contexts being passed into core builders as `extra` while already containing core-owned keys such as `config` or `request_id`.

## Existing coverage

`core/python/tests/test_feature_plugin_context_enrichment.py` currently verifies that:

- An actual caller collision retains the core-owned value.
- `context_reserved_key_clash_external` is emitted for that explicit conflict.
- Normal response-finalize enrichment does not emit an unexpected lifecycle clash.

Related application-level context enrichment tests are referenced from that test module and should be included when changing the application-to-core handoff.

## Decision criteria

Prefer fixing context ownership or filtering at the handoff boundary when a reserved key is redundantly forwarded by framework code.

Change the warning policy only when the collision is intentional and expected in normal framework operation. Any muting or deduplication must retain a diagnostic for unexpected external overrides and should document why the quieter behavior is safe.

Do not remove the precedence protection merely to silence the logs.

## Verification expectations

At minimum, verify:

- Focused unit tests for `merge_context_layers(...)`.
- Core context-enrichment tests.
- Application context-enrichment tests for the application-to-core and tool-loop boundaries.
- A representative request with tool calls or the task-guidance imported-session smoke.
- Captured logs showing that normal execution no longer emits the repeated warnings while a deliberate external clash still produces the intended diagnostic.

## Investigation findings

Fact: The isolated worktree branch
`task/20260721-resolve-context-helper-warning-noise` starts at local `develop`
commit `f4e6e94fce81d53fae1e660999db0ef35b1daa78`.

Fact: The original smoke log remains available in the primary checkout. Its
57 warnings match the counts recorded above. The warning stream was also
reproduced in the isolated worktree with deterministic tests:

- The 22 focused core/application context-enrichment tests passed but emitted
  ordinary request, tool, rebuild, lifecycle, session-action, and
  response-lifecycle `config` clashes.
- The deterministic non-streaming application tool-loop test passed but
  emitted four `core/tool/config` and two `core/request/config` warnings.
- The OpenAI Responses request-prepare rebuild test passed with its
  `integration and openai` gate explicitly enabled but emitted request,
  lifecycle, rebuild, and tool `config` warnings.

Fact: Commit `6d25d843` added the effective `config` to application-to-core,
session-action, and tool contexts to fix MCP action configuration. The final
effective configuration is required by existing plugins and tools. Removing it
from all application context builders would regress that behavior or require
parallel handoff-only builder variants.

The observed collisions are classified as follows:

| Path and key | Classification | Cause |
|---|---|---|
| `core/request/config` | Intentional same-value precedence | `ApplicationContext.build_core_handoff_context(...)` carries the effective configuration and `CoreContext.build_request_context(...)` independently owns the same effective configuration. |
| `core/tool/config` | Intentional same-value precedence | The application tool context carries the effective configuration for tool compatibility, while the core tool context independently owns the same configuration. |
| `core/rebuild/config` | Intentional same-value precedence | A complete framework context is reused during native-history reconstruction while the rebuild context independently reconstructs the same configuration. |
| `core/rebuild/request_id` | Unintended ownership/propagation | The generic plugin context inserts `request_id=None` during a rebuild. `CoreContext.build_rebuild_context(...)` reserves that placeholder, warns about the real request ID in `extra`, and retains `None`. |

Fact: A direct rebuild probe reproduced both rebuild warnings and showed the
behavioral defect: an additive `request_id="req-123"` was discarded in favor
of the rebuild-specific `None`, while unrelated extra context remained
available.

Fact: A direct `merge_context_layers(...)` probe showed that equal and
different external values currently produce indistinguishable warnings. The
owned value wins in both cases.

Recommendation: Treat an equal-value repetition as an idempotent handoff, not
an attempted override. Keep the existing warning for a differing external
value. Separately, stop reserving the synthetic rebuild `request_id=None` so a
real request ID can propagate as an additive key.

This is preferable to globally removing `config` from application contexts:
it preserves the effective-config contract introduced for MCP and applies the
diagnostic distinction consistently to request, tool, rebuild, lifecycle, and
action contexts. It is also preferable to warning deduplication because it
removes non-actionable events at their semantic source while every genuine
value conflict remains individually diagnosable.

## Execution plan

Status: Approved

Adjust external-clash detection in `merge_context_layers(...)` so an extra key
whose value is equal to the already-owned value is ignored without a warning.
The owned value and all existing precedence rules remain unchanged. Use a
small defensive equality helper so identity matches are cheap and unusual
equality implementations cannot break context construction. Do not log
context values, because configuration can contain credentials and other
sensitive data.

Keep `context_reserved_key_clash_external` at warning level for differing
values, with the existing builder, call path, key, and winning-layer fields.
This retains a diagnostic for actual caller attempts to replace an owned key.

Correct rebuild ownership in `CoreContext.build_rebuild_context(...)` by
excluding the synthetic `request_id` from the rebuild-specific plugin-context
layer. Rebuild has no authoritative request-ID argument of its own, so a
request ID supplied through context becomes additive instead of replacing an
owned value. The rebuild-owned configuration remains authoritative.

Add focused regression coverage at three boundaries:

1. Context-layer unit coverage proves equal-value repetition is quiet,
   different-value repetition still warns, the owned value always wins, and
   unrelated extras remain additive.
2. Core rebuild coverage proves a real request ID and custom context survive
   without warnings while the core-owned configuration remains authoritative.
3. Application request/tool-loop coverage proves effective configuration and
   application-owned keys still reach plugins and tools, and a normal
   tool-bearing request emits no reserved-key warning stream.

Run the focused core and application context tests first, then the
deterministic non-streaming tool-loop reproduction with captured output.
Finally run the fast core and application suites in proportion to the
cross-layer change. The original cloud smoke need not be rerun if the
deterministic request/tool/rebuild paths provide the required evidence; if it
is rerun, treat it as additional hosted verification rather than a prerequisite
for the local fix.

### Implementation decisions and open questions

- Recommended decision: Equal-value external repetition is non-conflicting and
  silent; differing external values remain warning-level conflicts.
- Recommended decision: Rebuild does not own `request_id` when its only
  candidate value is the generic plugin-context placeholder `None`.
- No requirement question remains open. Approval of this plan authorizes these
  two behavior changes.

### Documentation

No public user-documentation change is expected because plugin-visible
effective configuration and precedence remain compatible. Update the
`merge_context_layers(...)` docstring and focused test names/assertions so the
equal-value diagnostic policy and rebuild request-ID ownership are explicit.
Keep this task's implementation and completion evidence current during
execution.

### Task checklist

- [x] Add defensive equal-value detection for external context repetitions.
- [x] Preserve warning-level diagnostics for differing external values.
- [x] Remove the synthetic rebuild `request_id` from the owned specific layer.
- [x] Add focused context-helper and rebuild regression tests.
- [x] Add or strengthen application request/tool-loop no-noise coverage.
- [x] Run focused and package-level verification.
- [x] Record implementation findings and completion evidence.

### Requirement verification

- Warning-source identification and collision classification: review the
  recorded path-by-path findings and regression-test fixtures against the
  original 57-warning distribution.
- Correct ownership and precedence: focused rebuild tests must show that a real
  request ID propagates, core configuration remains authoritative, specific
  values still override generic values, and differing extras cannot override
  owned keys.
- Compatibility: application context-enrichment and tool-context tests must
  show that effective `config`, application services, session/request fields,
  lifecycle support, and custom additive keys remain available to existing
  plugin/action boundaries.
- Noise reduction and genuine diagnostics: captured output from normal
  request, rebuild, and tool flows must contain no
  `context_reserved_key_clash_external`; a deliberate differing-value clash
  must emit that event with builder, call path, key, and winning layer.
- Representative behavior: the deterministic application request with a
  pending tool call must complete successfully without the previous reserved
  key warning stream.

### Additional implementation verification

- Run the focused context-enrichment, tool-context, tool-preparation, rebuild,
  and application tool-loop tests.
- Run `pytest core/python/tests -q`.
- Run `pytest application/python/tests -q`.
- If the OpenAI Responses fake-client rebuild test is retained as focused
  evidence, enable its gate explicitly with
  `-m 'integration and openai'` and verify that it is collected and passes.
- Inspect captured warning counts rather than relying only on passing
  assertions.

## Implementation Notes

- During focused implementation verification, the application and core
  configuration mappings proved intentionally related but not always equal.
  Core can resolve a full application config to a provider config or enrich an
  effective config with request-only fields such as `tools`.
- The implementation therefore also corrects the application-to-core
  ownership boundary: core handoff and tool handoff contexts no longer forward
  `config`, while core continues to install its authoritative effective
  configuration before plugin and tool hooks execute.
- Application-owned session-action contexts retain effective `config`, which
  preserves the MCP action behavior introduced by `6d25d843`. Regression
  coverage checks the final prepared-tool context rather than relying only on
  an intermediate handoff mapping.

## Completion Notes

Implemented context ownership and diagnostics without weakening precedence:

- Application-to-core request and tool handoffs no longer forward `config`.
  AgentCore installs its authoritative resolved or tool-enriched configuration
  before plugin and tool hooks execute.
- Application-owned session-action contexts still carry effective `config`;
  the focused MCP test confirms effective configuration remains preferred over
  base configuration.
- Equal-value external repetitions are treated as idempotent and quiet.
  Differing external values remain ignored with a warning containing builder,
  call path, key, and winning layer.
- Rebuild no longer reserves the synthetic plugin-context `request_id=None`
  against a real incoming request ID. A real ID now survives as additive
  context, while rebuilds without one retain the compatible
  `request_id=None` shape.

Requirement evidence:

- Five focused context-helper tests cover equal and differing values, unusual
  equality behavior, internal specific-over-generic precedence, rebuild
  request-ID propagation, additive extras, and the compatible no-request
  shape.
- The 29-test focused core/application context run passed. It includes normal
  response-finalize and deterministic non-streaming tool-loop assertions that
  no `context_reserved_key_clash_external` event is emitted, plus final tool
  effective-configuration checks.
- The deterministic tool-loop reproduction that previously emitted four
  `core/tool/config` and two `core/request/config` warnings passed with zero
  reserved-key warnings.
- The gated OpenAI Responses fake-client request/rebuild test passed with
  `-m 'integration and openai'` and emitted no reserved-key warnings.
- The MCP effective-config regression passed.
- The full post-change core default suite passed: 469 passed, 26 deselected by
  default markers, and 1 expected failure.
- Ruff, Black, and `git diff --check` passed for the changed files. Pyright was
  unavailable in the environment (`pyright: command not found`).

Additional application verification:

- With the worktree's `application/python` and `core/python` forced first on
  `PYTHONPATH`, application-suite slices produced 324 passes and 90 default
  marker deselections.
- Four application tests remain blocked before exercising context behavior.
  Their isolated plugin environments resolve `openai 3.3.1` and then fail to
  import because the available `aiohttp` module lacks
  `SocketTimeoutError`. The same dependency-resolution error affects two
  ChatGPT-auth UI tests, one Claude default-config system-message test, and one
  default-config tool-image test. No product or test workaround was made for
  this unrelated environment failure.
- An initial application run also imported `agent_terminal_app` from the
  separate main worktree due the active editable installation. Serial reruns
  with explicit worktree `PYTHONPATH` passed all eight affected bridge and CLI
  tests, confirming that those failures were not regressions.

No public documentation was changed because final plugin/tool context and
precedence contracts remain compatible. The helper docstring and regression
tests document the quieter equal-value policy and the handoff ownership
boundary.
