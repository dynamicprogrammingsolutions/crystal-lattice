# 955 - Tool Interceptor Interface Proposal (Metadata Array Model)

Short description: Final design proposal for task `010` that defines interception hooks, response directives, and immutable metadata-array persistence on existing assistant/tool messages.

Parent Task: tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/000-main.md
Depends On: tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/010-design-toolplugin-interceptor-contract-and-prompt-schema.md

## Current interface and conventions (baseline)

1. `ToolPlugin.execute_tool(...)` returns a dict, conventionally `{ "success": bool, ... }`.
2. `ToolPlugin.stream_tool(...)` yields dict chunks.
3. Core treats chunks with `"success"` as final result and chunks with `"part"` as partial UI stream.
4. Core emits final `role="tool"` messages with metadata including `tool_call_id`, `tool_name`, and optional `display` payload.
5. There are no interception hooks and no formal response directive model.

## Proposed ToolPlugin contract additions

### Identity and ordering

1. Add optional class-level `priority: int` to `ToolPlugin`.
2. Default priority is `100` when absent.
3. Interceptors execute in ascending priority order (lower number first).
4. Tie-breaker is stable registration order.

### Interception hooks

```python
class ToolPlugin(BasePlugin, Protocol):
    # Optional; default 100 when absent.
    priority: int

    def intercept_tool_call(
        self,
        payload: Dict[str, Any],
        context: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        ...

    def intercept_tool_result(
        self,
        payload: Dict[str, Any],
        context: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        ...
```

### Payload envelopes

1. `tool_call` interception payload:
`{ "tool_call_id", "tool_name", "arguments", "raw_call" }`.
2. `tool_result` interception payload:
`{ "tool_call_id", "tool_name", "arguments", "raw_call", "tool_result" }`.

### Response directive envelope

```python
{
  "kind": "continue" | "prompt" | "respond",

  # continue
  "tool_call": { ... },   # optional transformed tool_call payload
  "tool_result": { ... }, # raw tool-result dict: synthetic (tool_call phase) or transformed (tool_result phase)

  # prompt
  "prompt": {
    "id": "prompt_x",
    "title": "...",
    "message": "...",
    "inputs": [ ... ],
    "buttons": [ ... ]
  },

  # loop control
  "continue_loop": True | False,

  # context persisted for current/final phase only
  "phase_context": { ... }
}
```

Rules:

1. `kind="continue"` passes to next interceptor or default execution path.
2. `kind="prompt"` suspends phase execution and requires user answer.
3. `kind="respond"` short-circuits default execution for this phase and returns a tool-level outcome payload (not explicit message objects).
4. `phase_context` is plugin-defined opaque state and is persisted only in the current/final phase context slot (see metadata model below).
5. Interceptors cannot emit explicit message objects; core/application materializes tool messages from final tool result data.
6. `tool_result` may be returned from `intercept_tool_call` or `intercept_tool_result` (for example to inject an error result before execution, or to transform an existing result).
7. A single interceptor response must not provide both `tool_call` and `tool_result` at the same time.
8. `tool_result` is a raw result dictionary (the same conceptual layer as `execute_tool` output), not a pre-formatted string.
9. Tool message text/display are produced by the normal formatter path (`format_tool_result` and `to_display_format`) after interception completes.

## Prompt form and answer schema (generic)

### Prompt form

```python
{
  "id": "prompt_x",
  "title": "...",
  "message": "...",
  "inputs": [
    {"id": "max_bytes", "type": "integer", "label": "Max bytes", "required": False}
  ],
  "buttons": [
    {"id": "allow_once", "label": "Allow once", "default": True},
    {"id": "deny", "label": "Deny"}
  ],
  "metadata": { ... }
}
```

Validation:

1. Prompt must include at least one button.
2. Any button press is treated as submit.
3. Exactly one button must set `default == true` to capture default submit action (Enter key on desktop).
4. Inputs/buttons remain plugin-defined free-form dictionaries.
5. Core performs structural validation only.

### Prompt answer

```python
{
  "prompt_id": "prompt_x",
  "button_id": "deny",
  "values": {"max_bytes": 1200}
}
```

Resume semantics:

1. Prompt answer re-enters the same interception phase.
2. Re-entry `context` includes prompt form and answer.
3. Ordering restarts from the same interceptor chain with deterministic priority.

## Metadata persistence model (array + current context)

### Storage location on existing messages

1. `tool_call` phase metadata lives on the assistant message that contains the tool call.
2. `tool_result` phase metadata lives on the tool result message.
3. No new message role/type is required.

### Metadata keys

Use free-form message metadata keys:

1. `metadata.interception_phases`: array of immutable phase history entries.
2. `metadata.interception_current`: object containing current/final phase context only.

Visibility policy:

1. Interception metadata remains in message metadata as stored.
2. No special hiding/filtering is applied to interception metadata fields.

### `interception_phases` entry shape (event-style, no status field)

`interception_phases` is an immutable append-only event array. It records only:

1. User prompt exchanges (prompt + submitted answer).
2. Meaningful interceptor responses (`respond`, or `continue` with non-trivial data).

#### Entry type: `prompt_response`

```python
{
  "entry_id": "iph_0001",
  "entry_type": "prompt_response",
  "phase_id": "phase_tool_call_call_1",
  "phase": "tool_call" | "tool_result",
  "tool_call_id": "call_1",
  "tool_name": "shell",
  "plugin": "shell_guard",
  "priority": 50,
  "prompt": { ... },
  "answer": {
    "prompt_id": "prompt_x",
    "button_id": "allow_once",
    "values": { ... }
  },
  "timestamp": "2026-03-01T12:34:56Z"
}
```

#### Entry type: `plugin_response`

```python
{
  "entry_id": "iph_0002",
  "entry_type": "plugin_response",
  "phase_id": "phase_tool_call_call_1",
  "phase": "tool_call" | "tool_result",
  "tool_call_id": "call_1",
  "tool_name": "shell",
  "plugin": "shell_guard",
  "priority": 50,
  "plugin_response": {
    "kind": "respond" | "continue",
    "continue_loop": True,
    "tool_call": { ... },
    "tool_result": { ... }
  },
  "timestamp": "2026-03-01T12:35:02Z"
}
```

Persistence rule for `continue`:

1. Do not append a `plugin_response` row for a no-op `continue` that only passes control.
2. Append a `plugin_response` row for `continue` only when it carries meaningful data (for example transformed `tool_call`/`tool_result` or explicit loop control fields).
3. Always append a `plugin_response` row for `respond`.

Materialization rule:

1. `plugin_response` is audit metadata only.
2. Core/application decides how to persist/render resulting tool messages.
3. If `tool_result` is provided, core/application stores it as a tool result message using the normal tool result materialization path.
4. Formatter ownership is the effective target tool for the call (after any transformed `tool_call`), not necessarily the interceptor plugin that produced `tool_result`.
5. If formatter resolution fails or formatting raises, fall back to default core formatting semantics.

### `interception_current` shape

```python
{
  "phase_id": "phase_tool_call_call_1",
  "phase": "tool_call" | "tool_result",
  "tool_call_id": "call_1",
  "plugin": "shell_guard",
  "context": { ... },
  "pending_prompt": {
    "id": "prompt_x",
    "title": "...",
    "message": "...",
    "inputs": [ ... ],
    "buttons": [ ... ]
  },
  "tool_call": { ... },
  "tool_result": { ... }
}
```

Purpose:

1. `interception_phases` keeps immutable history for audit/rendering and preserves user responses.
2. `interception_current` stores full context only for the current/final phase state, including pending prompt data and latest transformed `tool_call`/`tool_result` values.

### Immutability rules

1. Never mutate prior `interception_phases` array entries in place.
2. Append to `interception_phases` only for:
   - completed prompt exchange (`prompt_response`),
   - meaningful interceptor output (`plugin_response`).
3. `interception_current` is replaced as a whole when phase context changes.
4. When no active context is needed, `interception_current` is omitted or set to `null`.

Write timing:

1. On prompt emission: update `interception_current.pending_prompt`; do not append to `interception_phases` yet.
2. On user submit: append one `prompt_response` event containing both prompt and answer.
3. On interceptor return after run/re-run: append `plugin_response` when `respond` or meaningful `continue`.

This gives immutable phase history while avoiding full-context duplication.

## Frontend rendering contract

Frontend logic should be metadata-driven:

1. Read `metadata.interception_phases` on assistant/tool messages and render chronological phase chips/steps.
2. Render actionable prompt UI from `metadata.interception_current.pending_prompt`.
3. Render preserved answers from `prompt_response` entries (`answer.button_id`, `answer.values`) as read-only history.
4. For `tool_call` prompts, UI anchors to assistant message.
5. For `tool_result` prompts, UI anchors to tool result message.
6. Any button click submits; desktop Enter submits the button marked `default == true`.

No hardcoded policy labels are required in frontend code.

## Compatibility and migration notes

1. Existing tools that do not implement interception hooks behave exactly as today.
2. Existing tool result shape (`success` convention) remains supported.
3. Node tool host can add interception hooks as optional RPC methods in a backward-compatible way.

## How This Covers Required Outcomes

1. Keep original tool call:
No-op `continue` (not persisted in `interception_phases`).
2. Replace/modify tool call:
`continue` (or terminal `respond`) with transformed `tool_call`; persisted as `plugin_response` only when transformed data exists.
3. Transform/modify tool result:
`continue` or `respond` with transformed `tool_result` payload.
4. Convert to tool error (including pre-call):
`respond` with synthetic `tool_result` such as `{ "success": False, "error": "..." }`, even from `intercept_tool_call`.
5. Continue or stop loop:
`continue_loop` flag on interceptor response controls loop continuation.
6. Suspend/resume execution:
`prompt` writes pending prompt in `interception_current`, user submit appends `prompt_response`, then same phase re-runs.
7. No explicit message output from interceptor:
Interceptor returns only tool-level transforms/results; core/application owns message storage/rendering.
8. Multi-step prompt flows:
Plugins can implement multi-step prompting by intercepting repeatedly; each answered step appends a `prompt_response` event, and subsequent interceptions may emit additional prompts.
