# Resolve Repeated Context-Helper Reserved-Key Warnings

Investigate the high volume of `context_reserved_key_clash_external` warnings during normal agent requests, correct unintended context layering where appropriate, and otherwise reduce or mute warnings that are expected and non-actionable without hiding genuine caller conflicts.

## Requirements checklist

- [ ] The source of the repeated `context_reserved_key_clash_external` warnings is identified for the affected request, tool, and rebuild context paths.
- [ ] Each observed collision is classified as either an unintended duplicate context handoff or an intentional precedence case.
- [ ] Unintended duplicate context propagation is corrected at the appropriate ownership boundary rather than hidden by logging changes.
- [ ] Expected, non-actionable collisions no longer produce repeated warning noise; use a lower level, deduplication, narrower warning condition, or another justified mechanism.
- [ ] Genuine caller attempts to override core- or application-owned context keys remain detectable with enough information to diagnose the conflict.
- [ ] Existing context precedence is preserved: specific-layer values override generic-layer values, and caller-provided extras cannot override owned keys.
- [ ] Request, rebuild, tool, lifecycle, and application-to-core context contents remain compatible for existing plugins and actions.
- [ ] Regression coverage demonstrates both a normal flow without warning noise and an actual external reserved-key clash with the intended diagnostic behavior.
- [ ] Representative agent/tool-loop verification completes without the previous repeated warning stream.

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