# 956 - Tool Handler And Formatter Resolution Spec

Short description: Finalized follow-up design to `955` that keeps metadata persistence semantics and adds a dedicated post-interception tool handler phase, deterministic formatter ownership, and formatted-output interception.

Parent Task: tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/000-main.md
Depends On: tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/955-tool-interceptor-interface-proposal-metadata-array.md

## Scope

1. Keep all decisions from `955`.
2. Keep `can_handle_tool_call` + `handle_tool_call` as the primary execution path for the main tool call.
3. Treat `format_tool_result` and `to_display_format` as deprecated compatibility hooks.
4. Make `handle_tool_call` final output use the same response envelope shape as interceptors.
5. Allow prompt+result/format combinations from `handle_tool_call` and define deterministic continuation rules.
6. Keep non-execution hooks (`intercept_tool_call`, `intercept_tool_result`, `intercept_tool_output`) fast and lightweight.

## Baseline Kept From 955

1. Metadata keys remain `metadata.interception_phases` and `metadata.interception_current`.
2. Metadata visibility remains unchanged (no interception-specific hiding/filtering).
3. Prompt behavior remains:
   - any button press submits,
   - exactly one button has `default == true` for desktop Enter.
4. `tool_result` remains a raw dict payload (not preformatted text).
5. Plugins do not emit explicit message objects; core/application materializes messages.

## Updated ToolPlugin Interface

```python
class ToolPlugin(BasePlugin, Protocol):
    priority: int  # optional class attr, default 100

    # Stage A: pre-call interception (chain)
    def intercept_tool_call(
        self,
        payload: Dict[str, Any],
        context: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        ...

    # Stage B: optional capability probe for execution handler
    def can_handle_tool_call(
        self,
        payload: Dict[str, Any],
        context: Dict[str, Any],
        state: Dict[str, Any],
    ) -> bool:
        ...

    # Stage C: main execution handler (potentially long-running)
    def handle_tool_call(
        self,
        payload: Dict[str, Any],
        context: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Iterator[Dict[str, Any]]:
        ...

    # Stage D: raw-result interception (chain)
    def intercept_tool_result(
        self,
        payload: Dict[str, Any],
        context: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        ...

    # Stage E: formatted-output interception (chain)
    def intercept_tool_output(
        self,
        payload: Dict[str, Any],
        context: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        ...

    # Deprecated compatibility hooks (fallback path only)
    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        ...

    def to_display_format(
        self,
        text: str,
        result: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        ...
```

## Common Response Envelope

Used by `intercept_tool_call`, `intercept_tool_result`, `intercept_tool_output`, and by the final terminal output from `handle_tool_call`.

```python
{
  "kind": "continue" | "prompt" | "respond",

  # optional payload transforms/outcomes
  "tool_call": { ... },
  "tool_result": { ... },
  "formatted_content": "...",
  "display": { ... },

  # optional prompt
  "prompt": {
    "id": "prompt_x",
    "title": "...",
    "message": "...",
    "inputs": [ ... ],
    "buttons": [ ... ]
  },

  # optional formatter owner override
  "formatter_plugin": "plugin_name",

  # optional loop control
  "continue_loop": True | False,

  # opaque runtime state for current/final context only
  "phase_context": { ... }
}
```

Rules:

1. At most one of `tool_call` and `tool_result` may be present.
2. `formatted_content` and `display` may be provided together or separately.
3. If `formatted_content` is provided, it is treated as already formatted model-facing text.
4. `tool_result` may be synthetic (pre-execution) or transformed (post-execution).
5. No explicit message objects are returned by plugins.

## `handle_tool_call` Output Contract

`handle_tool_call` may yield two kinds of chunks:

1. Partial stream chunk:

```python
{"part": { ... }}
```

2. Terminal response chunk using the common response envelope:

```python
{"kind": "respond", "tool_result": { ... }}
```

Meaningful handler response:

1. emits at least one `part`, or
2. emits a terminal response with meaningful payload (`prompt`, `tool_result`, `formatted_content`, `display`, transformed `tool_call`, or loop-control override).

No-op handler pass-through:

1. no chunks emitted, or
2. terminal `continue` with no meaningful payload.

Selection rule:

1. plugins are checked in `(priority asc, registration order)` order,
2. first plugin with meaningful handling becomes `handler_plugin`,
3. later handlers are not invoked.

## Payload Shapes

### Tool call payload

```python
{
  "tool_call_id": "call_1",
  "tool_name": "shell",
  "arguments": { ... },
  "raw_call": { ... }
}
```

### Raw tool result payload

```python
{
  "tool_call_id": "call_1",
  "tool_name": "shell",
  "arguments": { ... },
  "raw_call": { ... },
  "tool_result": { ... }
}
```

### Formatted output payload

```python
{
  "tool_call_id": "call_1",
  "tool_name": "shell",
  "tool_result": { ... },
  "formatted_content": "...",
  "display": { ... }
}
```

## Deterministic Pipeline And Continuation Routing

All chain iterations use `(priority asc, registration order)`.

1. Run pre-call chain: `intercept_tool_call`.
2. If still unresolved, execute handler-selection + `handle_tool_call`.
3. Determine next stage from latest meaningful response:

   - Case A: `formatted_content` present:
     - run `intercept_tool_output` only,
     - skip raw-result interception and deprecated formatter hooks.

   - Case B: `tool_result` present and `formatted_content` absent:
     - run `intercept_tool_result`,
     - then formatting fallback path (deprecated hooks) if formatted output is still missing,
     - then run `intercept_tool_output`.

   - Case C: no `tool_result` and no `formatted_content`:
     - remain in pre-call stage,
     - continue via `intercept_tool_call` flow.

4. Prompt combinations and resume stage:

   - `prompt` only:
     - suspend,
     - resume at pre-call stage (`intercept_tool_call`).

   - `prompt` + `tool_result` (no formatted):
     - suspend,
     - resume at raw-result stage (`intercept_tool_result`).

   - `prompt` + `formatted_content` (with or without `tool_result`):
     - suspend,
     - resume at formatted-output stage (`intercept_tool_output`).

5. Materialize final tool message via normal core/application path.

## Formatter Ownership And Deprecated Fallback

Formatter ownership precedence:

1. explicit `formatter_plugin` from latest meaningful response,
2. `handler_plugin`,
3. effective target tool from final `tool_call.tool_name`,
4. core default fallback.

Deprecated fallback path:

1. `format_tool_result` and `to_display_format` are compatibility-only.
2. They are invoked only when `formatted_content` is still absent after handler/interceptor stages.
3. New implementations should prefer:
   - direct `formatted_content`/`display` from `handle_tool_call`, or
   - `intercept_tool_result` / `intercept_tool_output` hooks.

## Metadata Persistence

Use the same persistence model as `955`.

1. `metadata.interception_phases` remains append-only.
2. `metadata.interception_current` remains current/final snapshot.
3. `tool_call` phase metadata attaches to assistant tool-call message.
4. `tool_result` phase metadata attaches to tool message.

`interception_phases` entries:

1. `prompt_response`:
   - appended only when user submits,
   - stores prompt + answer.
2. `plugin_response`:
   - appended for `respond`,
   - appended for meaningful `continue`,
   - skipped for no-op pass-through `continue`.

Recommended `plugin_response.stage` values:

```python
"intercept_tool_call" | "handle_tool_call" | "intercept_tool_result" | "intercept_tool_output"
```

`interception_current` recommended shape:

```python
{
  "phase_id": "phase_tool_call_call_1",
  "phase": "tool_call" | "tool_result",
  "stage": "intercept_tool_call" | "handle_tool_call" | "intercept_tool_result" | "intercept_tool_output",
  "tool_call_id": "call_1",
  "handler_plugin": "...",
  "formatter_plugin": "...",
  "context": { ... },
  "pending_prompt": { ... },
  "tool_call": { ... },
  "tool_result": { ... },
  "formatted_content": "...",
  "display": { ... }
}
```

## Compatibility Wrapper For Existing Tools

For tools without the new hooks:

1. `can_handle_tool_call`:
   - true only when call name matches tool schema names.
2. `handle_tool_call`:
   - delegate to `stream_tool` when available,
   - map legacy final result chunks to terminal envelope:
     `{"kind": "respond", "tool_result": legacy_result_dict}`,
   - if streaming yields no final result, call `execute_tool` and emit the same terminal envelope.
3. `intercept_*` defaults:
   - no-op `continue`.
4. Deprecated formatter hooks:
   - preserved unchanged for fallback compatibility.

## Recommended Authoring Patterns

1. Handler-owned formatting (single-plugin control):
   - `handle_tool_call` returns all of:
     - `tool_result`,
     - `formatted_content`,
     - `display`.

2. Interceptor-owned formatting pipeline:
   - `handle_tool_call` returns raw `tool_result`,
   - one or more `intercept_tool_result` plugins transform raw result,
   - optional `intercept_tool_output` plugins shape final formatted text/display.

## How This Covers Required Outcomes

1. Keep original tool call:
   - no-op `continue` in pre-call stage.
2. Replace/modify tool call:
   - transformed `tool_call` from pre-call interception or handler terminal response.
3. Produce synthetic tool result before execution:
   - return `tool_result` in pre-call stage.
4. Transform raw tool result:
   - `intercept_tool_result` chain.
5. Provide formatted output directly from execution:
   - `handle_tool_call` can return `formatted_content` and `display`.
6. Truncate/redact after formatting:
   - `intercept_tool_output` chain.
7. Prompt + staged resume:
   - prompt-only resumes pre-call,
   - prompt+result resumes raw-result,
   - prompt+formatted resumes output stage.
8. Multi-step prompts:
   - repeated interceptions/handling can emit additional prompts across retries/stages; each answer appends a `prompt_response` event.
9. No explicit message emission from plugins:
   - core/application remains the sole message materializer.
