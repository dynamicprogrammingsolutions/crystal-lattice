# Design ToolPlugin Interceptor Contract and Prompt Schema

Short description: Define the exact `ToolPlugin` interception contract (phases, prompt payloads, response directives, and ordering) while preserving backward compatibility and keeping core semantics generic.

Parent Task: tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/000-main.md
Depends On: none

## Status

- Completed.
- Final design outcomes for this subtask are documented in:
  - `tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/955-tool-interceptor-interface-proposal-metadata-array.md`
  - `tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/956-tool-handler-and-formatter-resolution-spec.md` (follow-up extension)

## Scope

- Define new `ToolPlugin` interception hooks for `tool_call` and `tool_result` phases.
- Define optional class-level `priority` support for tool plugins (lower number runs first).
- Define generic prompt form schema (arbitrary inputs/buttons, at least one button, exactly one default button).
- Define interceptor response/directive schema without hardcoded business labels.
- Define re-entry semantics when a prompt is answered (same phase, same context + answer payload).
- Design metadata-based persistence mechanics for interceptor runtime state in core messages (append-only events + current snapshot, prompt state, pending context, selected button, submitted inputs, resume correlation).
- Define ownership/chaining rules when multiple plugins intercept the same lifecycle item.
- Define backward compatibility behavior for existing tool plugins that implement only current execution hooks.

## Out Of Scope

- Implementing runtime orchestration or API endpoints.
- Frontend rendering implementation.

## Proposed Steps

1. Review current protocol/wrapper defaults and identify minimal additive interface changes.
2. Draft exact hook signatures and payload envelope fields for `tool_call` and `tool_result`.
3. Define directive model for `continue`/`prompt`/`respond` with generic transform and loop-control fields.
4. Define deterministic chain algorithm using `ToolPlugin.priority` (lower number first) plus tie-break rules.
5. Define prompt exchange schema and persistence points (`interception_current.pending_prompt` + `prompt_response` event entries).
6. Define metadata schema for append-only interceptor events (`prompt_response`, `plugin_response`) and current snapshot correlation (`request_id`, `tool_call_id`, interceptor/plugin id, phase, prompt id).
7. Define metadata write-timing mechanics:
   - prompt emission updates `interception_current` only,
   - user answer appends `prompt_response`,
   - meaningful plugin output appends `plugin_response`.
8. Document metadata visibility and prompt submit semantics:
   - no interception-specific metadata hiding,
   - any button submits,
   - exactly one default button captures desktop Enter submit.
9. Produce a compatibility matrix for old vs new plugins and mixed plugin sets.

## Deliverables

- Approved interface spec for interception hooks and directive schema.
- Approved prompt form and prompt-response payload schema.
- Approved metadata persistence design using `interception_phases` (event array) + `interception_current` snapshot.
- Priority and chaining semantics spec.
- Backward compatibility and migration notes.

## Success Criteria

1. Interception contract is specific enough for implementation without open signature-level ambiguity.
2. Contract supports plugin-defined prompts and plugin-defined decision semantics.
3. Contract explicitly forbids embedding workflow-specific labels in core types.
4. Metadata persistence mechanics are explicit enough to implement without adding new core message roles/types or status-enum coupling.
5. Compatibility behavior for non-interceptor tools is clearly documented.

## Context References

- `core/python/agent_core/types.py#L849`
- `core/python/agent_core/plugin/adapters.py#L526`
- `core/python/agent_core/plugin/tool.py#L15`
- `core/python/agent_app/tool_loop.py#L331`
- `core/python/agent_core/core.py#L2281`
