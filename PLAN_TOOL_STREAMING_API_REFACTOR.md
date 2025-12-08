# Tool Streaming API Refactor Plan

## Overview

We will make streaming the primary API for tool execution while preserving a simple, final-only wrapper for backwards compatibility. This change eliminates double execution during streaming and unifies the execution path for both streaming and non‑streaming tools.

- New public API: `AgentCore.iter_tool_messages(...)` (streaming/iterator)
- Compatibility wrapper: `AgentCore.execute_tool_calls(...)` (final-only)
- Tool contract: `stream_tool(...)` yields tool result dicts; the last yield is the final result
- Default adapter wraps non‑streaming tools into streaming
- Tool loop uses the streaming API to emit `tool_partial` events and then the final `tool_results`

## Goals

- Avoid executing tools twice when streaming.
- Make streaming the underlying mechanism; non‑stream callers ignore partials and keep only finals.
- Keep existing simple call sites working via `execute_tool_calls` (returns only final messages).
- Keep current metadata propagation (`tool_plugin`, `tool_name`, `display`) and provider `_metadata` convention.

## Public APIs

### 1) New primary API: streaming

```python
class AgentCore:
    def iter_tool_messages(
        self,
        tool_calls: List[Dict[str, Any]],
        config: Dict[str, Any],
    ) -> Iterator[Dict[str, Any]]:
        """Yield a mixed stream of partial display payloads and final core 'tool' messages.

        Contract:
        - Tools stream via `stream_tool(tool_name, arguments, state)`.
        - Tools may yield any number of PARTIAL display payloads as:
                    {"part": {"type": "text", "content": <chunk>}}
                  (or a similarly tiny shape keyed by "part"). These are display-only and
                  forwarded AS-IS.
        - Tools may yield one or more RESULT dicts (detected by presence of a "success" key; the value may be True or False).
          - `iter_tool_messages` records the latest RESULT dict encountered while forwarding PARTIAL payloads.
          - After the tool stream completes for that call, only the last RESULT dict is transformed:
            formatted_text = format_tool_result(result, state)
            display = to_display_format(formatted_text, result, state)
          and emitted as a core tool message:

            {
              "role": "tool",
              "content": formatted_text,
              "metadata": {
                "tool_call_id": <id>,
                "tool_name": <name>,
                "tool_plugin": <tool_wrapper.name>,
                "display": display,
              },
            }
        - Non-stream tools are wrapped to yield a single FINAL result only (no PARTIALs).
        """
```

### 2) Compatibility wrapper: final-only

```python
class AgentCore:
    def execute_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        config: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Return only the final core 'tool' message per tool call.

        Internally iterates `iter_tool_messages([call], config)` and keeps only the last
        yielded message per call. If the iterator yields nothing, synthesizes an error message.
        """
```

## Tool plugin contract

### Semantics

- `stream_tool(tool_name, arguments, state) -> Iterator[Dict[str, Any]]`
  - Yields zero or more PARTIAL display payloads as:
    - `{"part": {"type": "text", "content": <chunk>}}` (or equivalent keyed by `part`).
    - These are display-only; they are NOT passed through `format_tool_result` or `to_display_format`.
  - May yield one or more RESULT dicts at any time (detected by the presence of a `success` key; value may be True or False).
    - Only RESULT dicts are transformed by `format_tool_result` and `to_display_format`.
    - The runtime keeps the last RESULT dict encountered during the stream for that call.

- `format_tool_result(result, state) -> str`
  - Formats the RESULT dict into user‑visible text (applies whether `success` is True or False).

- `to_display_format(text, result, state) -> Dict[str, Any]`
  - Converts the formatted text and the raw RESULT into a UI payload, e.g. `{ "type": "text", "content": text }`.

### Default adapter behavior

- For tools that don’t implement streaming, the adapter provides:

  ```python
  def stream_tool(tool_name, arguments, state):
      # No partials; yield only the final result dict.
      result = self.execute_tool(tool_name, arguments, state)
      yield result  # single final yield (contains "success")
  ```

- This ensures non‑streaming plugins work transparently under the new streaming API and that
  partial payloads are never fabricated by the adapter.

## Application layer (ToolLoopRunner)

- `_apply_tool_calls` runs per batch and becomes a generator that streams events:
  - Yield a `tool_calls` event first (unchanged shape).
  - For each `tool_call` (sequentially in list order):
    - Iterate `core.iter_tool_messages([call], config)`.
    - For each yielded item:
      - If the item is a PARTIAL display payload (has `"part"` key):
        - If `stream=True`, yield a `tool_partial` event containing the partial as-is:
          `{ "type": "tool_partial", "tool_call_id": <id>, "payload": {"part": {...}} }`.
        - Do not transform or append to session.
      - If the item is a core `tool` message (FINAL, no `"part"`):
        - Treat it as a candidate final for this call; keep the latest one
          and postpone appending to the session until the end of this call’s stream.
    - When the stream for this call finishes, append the last candidate FINAL tool message to the session via `core.add_message` and accumulate it into the batch finals list.
  - After the batch completes, yield a single `tool_results` event with the list of final tool messages and the updated session snapshot.

- `run(stream=True|False)`
  - In `stream=False`, iterate `iter_tool_messages` internally but ignore PARTIAL items; only append finals and yield `tool_results`.
  - In `stream=True`, yield `tool_partial` events for PARTIAL items and then `tool_results` at the end of the batch.

## Message and metadata shape

- Yielded items from `iter_tool_messages` are a mixed stream:
  1) PARTIAL display payloads (pass-through):
     ```json
     { "part": { "type": "text", "content": "..." } }
     ```
     - Not transformed, not appended to session.

  2) FINAL core tool messages (after transforming the final result dict):
     ```json
     {
       "role": "tool",
       "content": "<formatted_text>",
       "metadata": {
         "tool_call_id": "...",
         "tool_name": "...",
         "tool_plugin": "...",
         "display": {"type": "text", "content": "..."}
       }
     }
     ```

- Tool-call extensions continue to copy tool metadata from final core `tool` messages into provider-native `_metadata` (where applicable). Providers continue to strip `_metadata` before HTTP I/O.

## Error handling and edge cases

- If a streaming tool yields no items for a call:
  - Synthesize a single error `tool` message with `content` like `"Error: no tool handled '<name>'"` and appropriate metadata.
  - Append that final error message to the session and include it in `tool_results`.

- If a streaming tool raises during iteration:
  - Treat the call as failed and synthesize a single error `tool` message.

- Timeouts and cancellation:
  - The streaming plugin implementation should handle timeouts and emit a final result that reflects timeout semantics (or raise, which becomes an error message as above).

## Backwards compatibility

- Existing non‑stream tool plugins continue to work because the adapter exposes a 1‑yield `stream_tool` wrapper for `execute_tool`.
- `AgentCore.execute_tool_calls` stays available and returns only one final `tool` message per tool call.
- Application code that relied on `execute_tool_calls` can remain unchanged.
- Application code that wants streaming partials should switch to the `ToolLoopRunner` event stream (`tool_partial`, then `tool_results`).

## Test plan

- Core:
  - New tests for `iter_tool_messages`:
    - For a streaming tool: ensure it yields a mixed stream:
      - PARTIAL payloads with `{ "part": ... }`, possibly before and after results.
      - One FINAL core `tool` message per call, built from the last RESULT dict encountered (with metadata).
    - For a non‑stream tool: ensure it yields exactly one FINAL core `tool` message and no PARTIALs.
  - Ensure final tool message metadata contains `tool_call_id`, `tool_name`, `tool_plugin`, and `display`.
  - Ensure `execute_tool_calls` returns only the FINAL tool message per call by consuming `iter_tool_messages` and ignoring PARTIALs.

- Application layer:
  - In non‑streaming mode (`stream=False`): assert no `tool_partial`, only `tool_results`.
  - In streaming mode (`stream=True`): assert presence of `tool_partial` events (payload contains `{ "part": ... }`) followed by `tool_results`; append only finals to session.

- Plugins:
  - For a streaming tool (e.g. `ShellTool`): verify multiple PARTIAL payloads then a FINAL `result` dict; only the FINAL is transformed by `format_tool_result`/`to_display_format`.
  - For a non‑stream tool (dummy): verify single final yield from the adapter wrapper.

## Migration notes for plugin authors

- If your tool is non‑streaming, nothing to change.
- To support streaming:
  - Implement `stream_tool(...)` and yield result dicts as work progresses.
  - Ensure the last yield is the final result with all necessary fields set.
  - You can reuse your existing `format_tool_result` for final formatting and potentially provide a richer `to_display_format` for partials.

## Rollout steps

1. Add `iter_tool_messages` to `AgentCore`; refactor current `execute_tool_calls` to consume it and return finals.
2. Update `ToolLoopRunner._apply_tool_calls` to use `iter_tool_messages` and emit `tool_partial` events.
3. Keep existing terminal behavior; it already knows how to render `tool_partial` and `tool_results`.
4. Update and run tests per the test plan.

## Non‑goals

- Changing provider or extension responsibilities around `_metadata` (they already propagate and strip it correctly).
- Introducing parallel execution; execution remains sequential per the plan. The event shape and `tool_call_id` support future concurrency if desired.
