# Tool Plugin Interceptor And Prompt Lifecycle

Short description: Extend the `ToolPlugin` contract so a single tool plugin can both execute tools and intercept tool-call/tool-result phases with generic, plugin-defined user prompts, including suspend/resume behavior. Keep core semantics generic and avoid hardcoding decision labels.

## Subtasks

1. `tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/010-design-toolplugin-interceptor-contract-and-prompt-schema.md`
2. `tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/020-implement-toolplugin-interception-tool-loop-and-prompt-lifecycle-tests.md`
3. `tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/030-design-mobile-rendering-for-interceptor-prompts.md`
4. `tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/040-design-desktop-rendering-for-interceptor-prompts.md`
5. `tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/050-build-reference-interceptor-tool-plugin-scenario.md`
6. `tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/060-implement-tool-handler-and-formatter-upgrade-from-956.md`

Suggested execution order: `010` -> `020` -> (`030` and `040` in parallel) -> `050` -> `060`.

## General Description (Ticket Description)

We need to enhance tool execution so **tool plugins can act as interceptors**, not just executors.

Today, tools mainly run in a direct flow (`tool_call` -> execute -> `tool` message). The new behavior should allow plugins to intercept at two points:

1. **Before tool execution** (`tool_call` phase)
2. **After tool execution** (`tool_result` phase)

For both phases:

- Multiple plugins may intercept the same item.
- Interceptors are tried in **priority order** (lower number runs first).
- Tool plugins should support an optional class-level `priority` field (for example `priority = 100`) used by interception ordering when present.
- A plugin may return **directions** that control what happens next (continue, transform, block, stop, suspend, etc.).
- A plugin may emit a **prompt form** for the user.

Prompt requirements:

- Prompt schema must be generic and plugin-defined.
- A prompt can contain any number of inputs and buttons.
- At least one button is required.
- Any button press submits.
- Exactly one button should be marked as default submit (desktop Enter behavior).
- Core must not encode workflow-specific options (for example, no hardcoded `allow once`, `always allow`, `deny` enums in core types).

Prompt response handling:

- When the user answers, the flow should return to the **same interception phase** (`tool_call` or `tool_result`).
- The interception input should include the original phase payload plus prompt form and submitted answer.
- The same plugin (or a lower-priority-number interceptor) should get first opportunity again.

Outcome flexibility:

- Plugin-controlled outcomes must support combinations of:
  - keep original tool call
  - replace/modify tool call
  - convert to tool error message
  - emit no message
  - continue or stop loop
  - suspend/resume execution
- These behaviors must stay generic in core; interpretation remains plugin-owned.

Message model requirement:

- Prompt and prompt-response lifecycle must be persisted as **core messages** (with metadata), not only transient API state.

Example scope requirement:

- The "One use-case for the current tools" example (bash approval buttons, decide later, post-run truncation prompt) should be implemented as a **test/reference plugin implementation**, not as core semantics.

Required reference use-case (must be implemented as part of this task):

1. Create at least one concrete interceptor-enabled tool plugin fixture that exercises both interception phases (`tool_call` and `tool_result`).
2. In `tool_call` phase, for bash execution, plugin emits a prompt such as: "Do you allow running this bash command?" and provides plugin-defined submit buttons: `allow once`, `always allow bash`, `deny`, `deny and stop`, `decide later`.
3. When user picks `deny`, plugin converts the call to a tool error message and loop continues.
4. When user picks `deny and stop`, plugin converts the call to a tool error message and stops the loop.
5. When user picks `decide later`, plugin suspends execution and leaves the tool call unhandled for later resume.
6. In `tool_result` phase, if output exceeds configured threshold, the same plugin can either auto-truncate or emit a second prompt asking whether to truncate and optionally requesting target byte count.
7. All option labels and behavior above are plugin-defined test logic only; core must only transport generic prompt and interceptor directives.

## Goal

Add a generic interceptor-capable tool contract and tool-loop orchestration that enables plugin-defined prompt gating and post-processing without embedding policy-specific decision types in core.

## Non-Goals / Constraints

1. Do not hardcode specific approval choices in core/plugin protocol.
2. Do not implement business policy in core (only generic mechanics).
3. Do not break existing non-interceptor tool plugins.
4. Keep provider/model-facing behavior stable when interception is not used.

## Current State (What Exists Today)

### Tool plugin contract and conventions

- `ToolPlugin` protocol currently exposes execution/formatting hooks, not interception hooks.
  - `core/python/agent_core/types.py` (around `ToolPlugin` definition)
- Tool wrappers/adapters normalize defaults and state handling.
  - `core/python/agent_core/plugin/tool.py`
  - `core/python/agent_core/plugin/adapters.py`
- Core tool execution maps function name -> first matching tool and streams tool output.
  - `core/python/agent_core/core.py` (`iter_tool_messages`, `execute_tool_calls`)

### Application loop behavior

- Tool loop emits events and appends tool messages to session.
  - `core/python/agent_app/tool_loop.py`
- Pending tool calls can already be resumed when assistant tool calls are present without matching tool messages.
  - `core/python/agent_app/tool_loop.py`

### Frontend/server surfaces

- Current event types do not yet model generic prompt lifecycle for tool interception.
  - `packages/frontend-sdk/src/types/events.ts`
- Terminal/mobile dialog components currently assume mostly simple OK/Cancel action shape.
  - `packages/frontend-rn-components/src/ApplicationActionDialog.tsx`
- HTTP server has request/event endpoints but no dedicated prompt-response flow for tool interception.
  - `application/python/agent_terminal_app/server.py`

## High-Level Plan

1. Extend `ToolPlugin` protocol with interception hooks.
- Add generic pre/post interception methods for `tool_call` and `tool_result` phases.
- Add optional class-level `priority` convention to `ToolPlugin` (matching existing plugin priority style) and use it for deterministic interception ordering (lower number first).
- Keep return contract generic (no hardcoded policy labels).

2. Add adapter/wrapper support for new optional hooks.
- Update defaults so existing plugins continue to work unchanged.
- Ensure wrappers route interception calls with proper tool state.

3. Implement interception chain in tool loop.
- Run call-phase interceptors before tool execution.
- Run result-phase interceptors after tool execution.
- Apply short-circuit/ownership rules and priority ordering (lower number first).
- Support transform/block/stop/suspend directives in a plugin-driven way.

4. Add generic prompt lifecycle persistence as core messages.
- Persist prompt creation and prompt response as messages with structured metadata.
- Keep enough correlation metadata (`request_id`, `tool_call_id`, plugin id, prompt id, phase) for resume and auditing.
- Ensure message handling is compatible with existing history/native integrity mechanics.

5. Add prompt-response API + event flow.
- Add endpoints/events to list pending prompts and submit responses.
- On response, resume the same interception phase with original context + response payload.
- Keep event schema generic (form/buttons/inputs are opaque plugin payloads with minimal structural validation).

6. Update frontend/terminal prompt rendering.
- Support variable button sets and arbitrary input fields.
- Submit button id + input payload back to backend.
- Avoid hardcoded semantic behavior in client.

7. Add required reference implementation for the example scenario.
- Implement at least one test/fixture tool plugin that handles both pre-tool approval and post-tool truncation prompting.
- Use plugin-defined button semantics (`allow once`, `always allow bash`, `deny`, `deny and stop`, `decide later`) only in test plugin logic.
- Keep these semantics in tests/fixtures, not core protocol enums.

8. Add tests and docs.
- Unit tests for hook ordering and directive handling.
- Integration tests for suspend/resume and same-phase re-entry on prompt answer.
- Protocol docs for interception hooks and generic prompt payload conventions.

## Success Criteria

1. A single tool plugin can both execute a tool and intercept tool-call/tool-result phases.
2. Priority ordering is deterministic and test-covered.
3. Prompt schema remains fully plugin-defined (arbitrary inputs/buttons; at least one submit button).
4. Core contains no hardcoded decision labels from the example workflow.
5. Prompt request/response are persisted in core messages with lifecycle metadata.
6. Prompt response resumes the same phase and can lead to plugin-defined transform/block/continue/stop/suspend outcomes.
7. Existing tools continue to work without implementing new hooks.
8. A reference test plugin is delivered that implements the required bash approval + oversized-output truncation use-case end-to-end.

## Proposed Core Touchpoints

- `core/python/agent_core/types.py`
  - Extend `ToolPlugin` protocol with interception hooks + optional class-level `priority`.
- `core/python/agent_core/plugin/adapters.py`
  - Add safe defaults/adaptation for new optional methods.
- `core/python/agent_core/plugin/tool.py`
  - Expose wrapper methods for interception calls.
- `core/python/agent_app/tool_loop.py`
  - Implement interception chain orchestration and prompt-driven suspend/resume.
- `application/python/agent_terminal_app/server.py`
  - Add prompt list/respond endpoints and resume wiring.
- `packages/frontend-sdk/src/types/events.ts`
  - Add generic prompt lifecycle event types.
- `packages/frontend-rn-components/src/ApplicationActionDialog.tsx`
  - Render arbitrary prompt forms/buttons.
- `docs/plugins/development.md`
  - Document updated tool plugin contract and conventions.

## Notes From Feasibility Review

- Feasibility is high; existing loop already has pending tool-call resume behavior that can be leveraged.
- Biggest design risk is getting generic prompt-message persistence right while avoiding accidental model-side semantic leakage.
- Backward compatibility should be preserved by making interception hooks optional with no-op defaults.

## Open Questions To Resolve Before Implementation

1. Exact schema for interceptor directive payloads.
2. Exact metadata schema for prompt and response core messages.
3. Whether prompt messages are always model-visible or conditionally filtered by metadata.
4. Chain semantics when multiple plugins want to keep intercepting after a response.
5. Exact ownership/delegation rules between interceptors for one tool-call lifecycle.
