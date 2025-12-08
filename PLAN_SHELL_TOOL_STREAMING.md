# Plan: Streaming Shell Tool Display & Tool Result Metadata

This document describes how to:

- Enable *streaming* shell tool output in the terminal app.
- Add a display-focused format for tool results (`{type: ..., content: ...}`) and partials (`{partial: {...}}`).
- Tag provider-native tool results with plugin metadata via a private `_metadata` field, attached/preserved by extensions and stripped by provider plugins before external API calls.

## Goals

1. **Streaming shell tool output**
   - While `ShellTool` runs a command, the terminal should receive incremental display updates.
   - Partial updates are *for display only*, not persisted into the session history.
   - Shape for display payloads:
     - Base: `{ "type": "text", "content": "..." }`.
     - Optionally wrapped to mark as partial: `{ "partial": { "type": "text", "content": "..." } }`.

2. **Display-aware tool results**
   - When a tool finishes, its formatted result (using `format_tool_result`) should also be convertible to a structured UI payload with `type` and `content` keys.
   - The core will call this display-conversion hook whenever a tool result is turned into a core `tool` message, provided the corresponding tool plugin is known.

3. **Link native messages back to tool plugins**
    - Provider-native history (e.g. `session.metadata["native_messages"]`) must keep a hint of which tool plugin produced which tool result.
    - A private provider-native `_metadata` key will carry this plugin hint and related display info and is a general-purpose extension point that other plugins can also read/write.
    - Provider plugins adopt a convention to strip `_metadata` from messages right before external API calls; core only wires providers/extensions and persists whatever `_metadata` they produce.


## Design Overview

### 1. Tool plugin streaming API

**New capability on `ToolPlugin` / `ToolWrapper`:**

- Add an optional streaming hook to the tool protocol, e.g.:

  ```python
  def stream_tool(
      self,
      tool_name: str,
      arguments: Dict[str, Any],
      state: Dict[str, Any],
  ) -> Iterator[Dict[str, Any]]:
      """Yield display-oriented partial results for a single tool call.

      Default implementation yields nothing, preserving existing behaviour.
      """
  ```

- `ToolWrapper` will:
  - Expose `stream_tool(...)` and delegate to the underlying plugin (via `ToolDefaultsAdapter`) if the method exists.
  - Provide a default implementation that yields nothing when the plugin does not implement streaming.

**ShellTool changes:**

- Add a streaming path that:
  - Uses `subprocess.Popen` with incremental reads from `stdout` and `stderr`.
  - Periodically yields partial display payloads shaped as either:
    - `{ "type": "text", "content": "<new chunk>" }`, or
    - `{ "partial": { "type": "text", "content": "<new chunk>" } }`.
  - Continues to produce a final result through the existing synchronous `execute_tool` (for the session’s `tool` message).

### 2. Application tool loop streaming

`core/python/agent_app/tool_loop.py` currently treats tools as synchronous:

- `_apply_tool_calls` calls `core.execute_tool_calls` once, appends all resulting `tool` messages to the session, and emits a single `tool_results` event.

**Planned changes:**

- Extend `_apply_tool_calls` to support streaming for tools that implement `stream_tool`:

  - Tool calls in a batch are processed **sequentially in list order** for now. The event schema (especially `tool_call_id` on `tool_partial` and final `tool` messages) allows future true concurrency without changing external APIs.

  - For each tool call:
    - If the responsible tool wrapper supports streaming, call `stream_tool` first and *yield* events as partials:
      - Event shape: for example
        ```python
        {
            "type": "tool_partial",
            "session_id": session.session_id,
            "request_id": rid,
            "tool_call_id": call_id,
            "payload": {"partial": {"type": "text", "content": chunk_text}},
        }
        ```
    - After streaming completes, call the standard `execute_tool` / `format_tool_result` path to obtain the final tool result content and append the resulting `tool` message to the session.

  - Preserve the existing `tool_calls` and `tool_results` events so that non-streaming behaviour remains unchanged from the perspective of callers that ignore `tool_partial`.

### 3. Terminal integration

`application/python/agent_terminal_app/terminal.py` already:

- Polls events via `_poll_events`.
- Renders them via `_render_event` (partial/final, tool_calls, tool_results, etc.).

**Planned changes:**

- Add handling of new streaming tool events in `_render_event`:

  - For `etype == "tool_partial"`:
    - Extract the display payload:
      - If wrapped: `ev["payload"]["partial"]`.
      - Else: `ev["payload"]`.
    - Expect `{"type": "text", "content": ...}` and write it directly to the terminal, e.g. `Shell (partial): <content>` or `Tool (partial): <content>`.

- The terminal continues to handle standard `tool_results` events as a summary (“[tools] tool results applied”) and full `tool` messages remain in the session for later listing.

### 4. Tool result display conversion API

`ToolPlugin` currently defines:

- `get_tool_schemas`, `execute_tool`, `format_tool_result`.

**New method on `ToolPlugin` / `ToolWrapper`:**

- Add a display conversion hook, for converting formatted text back into a structured UI shape:

  ```python
  def to_display_format(
      self,
      text: str,
      result: Dict[str, Any],
      state: Dict[str, Any],
  ) -> Dict[str, Any]:
      """Convert a tool result into a UI display payload.

      Default: {"type": "text", "content": text}.
      """
  ```

- `ToolWrapper` will implement `to_display_format(...)` and forward to the underlying plugin if present, otherwise fallback to a simple text payload.

**ShellTool implementation:**

- For final results:
  - Use the full formatted text and return:

    ```python
    {"type": "text", "content": formatted_text}
    ```

- For streaming partials (from `stream_tool`):
  - Reuse this shape for each chunk, optionally wrapped as `{"partial": {...}}` at the event level.

### 5. Native `_metadata` hint and plugin-level handling

We need to associate provider-native messages with the tool plugin that produced them, even when only native history is available, and we want other plugins to be able to reuse the same channel.

**Provider-native `_metadata` field (generic extension point):**

- `_metadata` is a provider-native dict on each message that plugins can use to stash opaque data:
  - Tool-call extensions will use it to preserve:
    - `tool_plugin` (string identifier, e.g. tool wrapper name).
    - `tool_name` (function name).
    - `display` (tool result display payload, see §4).
  - Other extensions/features may also read/write `_metadata` for their own purposes.

**Where `_metadata` is attached (core → native):**

- `AgentCore.add_message` appends tool results via `_append_single_message_with_native`, which calls `_core_messages_to_native_for_config`.
- `_core_messages_to_native_for_config` runs:
  - `provider.to_native_messages(core_messages, state)`
  - then `provider.apply_extension_transforms(core_messages, native_messages)`
  - then feature `to_native_messages`.
- Tool-call extensions will be enhanced here:
  - `OpenAIToolsExtension.to_native_messages(...)`
  - `OpenRouterToolsExtension.to_native_messages(...)`
- For each relevant core message:
  - For `role == "tool"`:
    - Read `msg["metadata"]` (which now includes `tool_plugin`, `tool_name`, `display` from §6).
    - Attach (or merge) into `nm["_metadata"]` on the provider-native message:
      ```python
      nm["_metadata"] = {
          **(nm.get("_metadata") or {}),
          "tool_plugin": md.get("tool_plugin"),
          "tool_name": md.get("tool_name"),
          "display": md.get("display"),
      }
      ```
  - For `role == "assistant"` with `metadata["tool_calls"]`:
    - Optionally propagate any relevant `_metadata` (e.g. per-call hints) so that subsequent tool results can be matched if needed.

**Where `_metadata` is propagated back (native → core):**

- When core converts provider-native messages back to core (`send_request`, `send_request_stream`, `_rebuild_core_from_native`), it uses:
  - `provider.from_native_messages(native_messages, state)`
  - then extension `from_native_messages`, including:
    - `OpenAIToolsExtension.from_native_messages(...)`
    - `OpenRouterToolsExtension.from_native_messages(...)`
- These extensions will be extended to:
  - Continue copying `native["tool_calls"]` into `metadata["tool_calls"]` (existing behaviour).
  - Additionally, if `native.get("_metadata")` exists:
    - Merge it into the core message metadata:
      ```python
      md = dict(msg.get("metadata") or {})
      extra = native.get("_metadata") or {}
      if extra:
          md.update(extra)
      enhanced.append({**msg, "metadata": md})
      ```

**Where `_metadata` is stripped before external API calls:**

- Provider plugins will own the responsibility of stripping `_metadata` from the payload they send to external APIs:
  - `OpenRouterProvider._sanitize_history(...)` will be extended to:
    - Drop any `_metadata` keys from each message in `history` in addition to the existing `refusal` and `tool_calls[index]` cleanup.
  - `OpenAIProvider` call paths will sanitize similarly:
    - Before `requests.post(...)`, build `messages_to_send` from `native_messages` with `_metadata` removed from each message object.
- This makes `_metadata`:
  - Fully available inside core-managed native history (`session.metadata["native_messages"]`) and between plugins.
  - Never sent over the wire to external providers, with the stripping implemented as a provider-level convention rather than core logic.

### 6. Execute-tool path integration

`AgentCore.execute_tool_calls` currently:

- Initializes all tools once per batch.
- For each call, finds the first tool whose `execute_tool` reports `success`, then calls `format_tool_result` and constructs a single `tool` message with string `content` and basic metadata (`tool_call_id`, `tool_name`).

**Planned augmentation:**

- After `format_tool_result(result, state)`:
  - Call `tool.to_display_format(text, result, state)` to get a structured payload.
  - Add this to the message metadata:

    ```python
    display_payload = tool.to_display_format(formatted_content, result, state)

    results.append(
        {
            "role": "tool",
            "content": formatted_content or "",
            "metadata": {
                "tool_call_id": call_id,
                "tool_name": name,
                "tool_plugin": tool.name,  # identifier
                "display": display_payload,
            },
        }
    )
    ```

- When converting the core `tool` message to provider-native, tool-call extensions (`OpenAIToolsExtension.to_native_messages`, `OpenRouterToolsExtension.to_native_messages`) will copy the relevant parts of this metadata into the provider-native `_metadata` field as described in §5.

**Data flow for a single tool result:**

1. Provider returns an assistant message with native `tool_calls`; tools extensions copy these into `metadata["tool_calls"]` on the core assistant message (`from_native_messages`).
2. `ToolLoopRunner._extract_tool_calls` pulls `tool_calls` from that assistant metadata, and `_apply_tool_calls` calls `AgentCore.execute_tool_calls`.
3. `execute_tool_calls` runs the tool plugin, formats the result, computes `display`, and returns a core `"tool"` message with enriched metadata (`tool_call_id`, `tool_name`, `tool_plugin`, `display`).
4. `_apply_tool_calls` appends that message to the session via `AgentCore.add_message`, which routes through `_append_single_message_with_native` and `_core_messages_to_native_for_config`.
5. Inside `_core_messages_to_native_for_config`, the provider and tools extensions run; the tools extensions read the enriched core metadata and attach it to the provider-native message’s `_metadata` field so it is available in `session.metadata["native_messages"]` and for future reconstructions.

## Additional Tests

To validate this design, we should add or extend tests in these areas:

1. **Core tool execution & display conversion**
   - New unit tests in `core/python/tests/test_core_execute_tool_calls.py` (or a new test file) to verify:
     - `execute_tool_calls` attaches `tool_plugin` and `display` metadata to resulting `tool` messages.
     - `to_display_format` is called on the appropriate tool plugin.

2. **Native `_metadata` handling**
    - Tests around `_core_messages_to_native_for_config` / `_rebuild_core_from_native` and the tools extensions to ensure:
      - Provider-native messages produced from `tool` core messages carry `_metadata` with `tool_plugin`, `tool_name`, and `display` when the tools extensions are active.
      - Provider plugins (`OpenAIProvider`, `OpenRouterProvider`) strip `_metadata` from the messages they actually send over HTTP.
      - Rebuilding from `native_messages` with `_metadata` via tools extensions preserves or can reconstruct display-related metadata on core messages.


3. **Tool streaming events**
   - New tests for `ToolLoopRunner` to confirm:
     - For a dummy streaming tool plugin, `run(..., stream=True)` produces `tool_partial` events with the expected shapes, followed by a `tool_results` event.
     - Non-streaming tools still work as before.

4. **ShellTool streaming**
   - Tests in `core/python/tests/test_shell_tool.py` to cover:
     - `ShellTool.stream_tool` yields partials while a command runs and terminates correctly.
     - Partial payloads follow the agreed shape (with `type` and `content`, optionally wrapped under `partial`).

5. **Terminal rendering**
   - Integration-style tests (or lightweight unit tests with a fake `EventStore`) to validate:
     - `_render_event` displays `tool_partial` events properly.
     - Existing events (`partial`, `final`, `tool_calls`, `tool_results`, etc.) continue to render unchanged.

---

This plan is intentionally structured so that:

- Existing tools and providers keep working without modification (all new hooks have safe defaults).
- `_metadata` is introduced as a **provider-native** hint managed by extensions/providers and is stripped by provider implementations before external I/O, while remaining available in core-managed native history.
- The terminal app gets streaming shell output and rich, structured tool display data without changing its session storage model.
