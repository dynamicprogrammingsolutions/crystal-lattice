# Plugin Development

This guide explains how to build provider, provider extension, feature, and tool plugins for the AI Agent Platform. It includes minimal examples and links to the full API reference generated from docstrings.

- Core principles
  - Functional style: methods are pure; state is passed explicitly.
  - Immutability: core data structures (Message, Session) are frozen.
  - Shared provider state: provider, provider extensions, and features receive and may update the same per-request state dict (tools keep their own state).

See also
- Reference → [Types & Protocols](../reference/agent_core/types.md)
- Reference → [Provider Wrapper](../reference/agent_core/plugin/provider.md)
- Reference → [AgentCore](../reference/agent_core/core.md)
- Reference → [OpenAI-Compatible Provider](../reference/providers/openai_provider.md)

## Provider Plugin

Providers adapt LLM APIs and convert between core and provider-native messages. They can stream (hot path) and finalize (cold path).

Key methods (subset):
- `init(config) -> state` (required)
- `call_api(native_messages, state) -> (partials, finals, natives, state)` (required, or `stream_api` for streaming providers)
- `process_chunk(native_chunk, native_messages, state) -> (partials, finals, natives, state)` (required)
- `finalize(native_messages, state) -> (final, native, state)` (required)
- `to_native_messages(messages, state) -> list` (optional in Python; adapter defaults to identity mapping of `role` and `content`)
- `from_native_messages(native_messages, state) -> list` (optional in Python; adapter maps to core messages with empty `metadata`)
- `initialize_request(native_messages, state) -> state` (optional in Python; adapter returns state unchanged)
- `stream_api(native_messages, state) -> Iterator[chunk]` (optional but recommended for streaming providers)

Minimal example (echo):
```python
from typing import Any, Dict, List, Tuple
from agent_core.types import ProviderPlugin

class EchoProvider(ProviderPlugin):
    name = "echo"
    version = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {"model": {"type": "string", "default": "echo-1"}}

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        # Provider state is an opaque dict; this minimal example only
        # stores configuration.
        return {"config": config}

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        Dict[str, Any],
    ]:
        last_user = next(
            (m for m in reversed(native_messages) if m.get("role") == "user"),
            {"content": ""},
        )
        content = f"Echo: {last_user.get('content', '')}"
        final = [{"role": "assistant", "content": content, "metadata": {}}]
        # Return (final_messages, partial_messages, native_messages, new_state)
        return final, [], native_messages, state
```

In the Python SDK, adapter defaults handle `to_native_messages`, `from_native_messages`, `initialize_request`, `finalize`, and `stream_api` when they are omitted, so many providers only implement configuration, `init`, and one of the I/O entry points (`call_api` or `stream_api`).

### Recommended streaming pattern (accumulator-based)

Streaming providers are expected to follow a simple accumulator-based pattern for
`process_chunk` and `finalize`:

- `stream_api` yields raw provider-native chunks (as returned by the HTTP client).
- `process_chunk(native_chunk, native_messages, state)` is called for each
  chunk and must:
  - Extract a *delta* from the chunk (for example, the first entry in
    `choices[0]`).
  - Reduce that delta into:
    - A provider-native **partial** message for this chunk (or `None`).
    - An updated **accumulator** stored in `state["partial"]`.
  - Return `(partials, finals, native_messages, new_state)`, where:
    - `partials` is a list of provider-native partial messages (often at most
      one item per chunk).
    - `finals` is usually empty during streaming; the final message is produced
      in `finalize`.
    - `native_messages` is typically left unchanged during streaming; the full
      history is updated when finalization completes.
    - `new_state` is `state` with the updated accumulator under
      `state["partial"]`.
- `finalize(native_messages, state)` is called once after streaming completes
  and must:
  - Read the accumulated partial from `state["partial"]`.
  - If present, emit it as the single final provider-native assistant message.
  - Append that final to `native_messages` when returning.

A minimal accumulator-based `process_chunk`/`finalize` pair looks like this
(simplified from the OpenAI-compatible provider):

```python
class MyProvider(ProviderPlugin):
    ...

    def extract_delta(self, native_chunk: Dict[str, Any]) -> Dict[str, Any]:
        if "choices" in native_chunk and native_chunk["choices"]:
            return native_chunk["choices"][0]
        return {}

    def process_delta(self, delta: Dict[str, Any], accumulated: Dict[str, Any] | None):
        base = accumulated or {}
        content = delta.get("message") or delta.get("delta") or None
        if content is None:
            return None, base
        new_accumulated = {
            **base,
            "role": content.get("role", base.get("role", "assistant")),
            "content": (base.get("content", "") + content.get("content", "")),
        }
        return content, new_accumulated

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        partial, accumulated = self.process_delta(
            self.extract_delta(native_chunk), state.get("partial", {}),
        )
        partials = [partial] if partial else []
        finals: List[Dict[str, Any]] = []
        return partials, finals, native_messages, {**state, "partial": accumulated}

    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        partial = state.get("partial")
        if partial:
            return [partial], [*native_messages, partial], state
        return [], native_messages, state
```

This pattern keeps all accumulation in `state["partial"]` and makes it easy for
extensions to collaborate by reading and updating the same accumulator.

## Provider Extension Plugin

Provider extensions run beside the provider on the hot path and the cold path. They do not own separate state; they receive and update the shared provider state.

Key methods (subset):
- `init(config, state) -> state` (required)
- `process_chunk(native_chunk|None, partial_messages, final_messages, native_messages, state) -> (partials, finals, natives, state)` (required)
- `finalize(final_messages, native_messages, state) -> (finals, native, state)` (required)
- `to_native_messages(messages, native_messages) -> list` (optional in Python; adapter defaults to identity)
- `from_native_messages(native_messages, messages) -> list` (optional in Python; adapter defaults to identity)
- `initialize_request(native_messages, state) -> state` (optional in Python; adapter returns state unchanged)

Minimal example (prefix finals):
```python
from typing import Any, Dict, List, Tuple, Optional
from agent_core.types import ProviderExtensionPlugin

class PrefixExtension(ProviderExtensionPlugin):
    name = "prefix"
    version = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {"prefix": {"type": "string", "default": "[EXT]"}}

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {**state, "config": {**state.get("config", {}), **config}}

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        state: Dict[str, Any],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> Tuple[
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        Dict[str, Any],
    ]:
        pfx = state.get("config", {}).get("prefix", "[EXT]")
        finals = [{**m, "content": f"{pfx} {m['content']}"} for m in final_messages]
        return partial_messages, finals, native_messages, state
```

As with providers, extension adapters supply default identity implementations for the stateless conversion and `initialize_request` hooks when they are not defined on the class.

### Recommended streaming pattern (extensions)

For streaming providers that use an accumulator in `state["partial"]`,
extensions are encouraged to follow a similar pattern:

- Treat `partial_messages` as provider-native partials for the current chunk.
- Use `state["partial"]` as the shared accumulator for extension-specific
  fields (for example, `tool_calls`, `reasoning`, or provider-native metadata).
- Prefer updating only:
  - The last entry in `partial_messages` (to enrich the current partial), and
  - The accumulator in `state["partial"]`.
- Avoid mutating `final_messages` or `native_messages` during streaming unless
  there is a very strong reason; use `finalize` for cold-path adjustments.

A minimal accumulator-based extension looks like this:

```python
from typing import Any, Dict, List, Tuple, Optional
from agent_core.types import ProviderExtensionPlugin


class MyStreamingExtension(ProviderExtensionPlugin):
    name = "my_ext"
    version = "1.0.0"

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def extract_delta(self, native_chunk: Dict[str, Any]) -> Dict[str, Any]:
        if "choices" in native_chunk and native_chunk["choices"]:
            return native_chunk["choices"][0]
        return {}

    def process_delta(
        self,
        delta: Dict[str, Any],
        current_partial: Dict[str, Any] | None,
        accumulated: Dict[str, Any] | None,
    ) -> Tuple[Dict[str, Any] | None, Dict[str, Any]]:
        base = accumulated or {}
        d = delta.get("message") or delta.get("delta") or {}
        if not isinstance(d, dict):
            return current_partial, base
        # Example: accumulate a "reasoning" field
        new_partial = dict(current_partial or {})
        if "reasoning" in d:
            new_partial["reasoning"] = (new_partial.get("reasoning", "") + d["reasoning"])
            base["reasoning"] = base.get("reasoning", "") + d["reasoning"]
        return new_partial, base

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        delta = self.extract_delta(native_chunk or {})
        accumulated = state.get("partial", {})

        new_partials = partial_messages
        if new_partials:
            last = new_partials[-1]
            updated_last, accumulated = self.process_delta(delta, last, accumulated)
            new_partials[-1] = updated_last or last

        return new_partials, final_messages, native_messages, {**state, "partial": accumulated}

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        # Most extensions can simply return finals/native unchanged; the provider
        # already baked accumulator state into the final provider-native message.
        return final_messages, native_messages, state
```

This keeps streaming logic simple and predictable: the provider owns the final
message shape, and extensions collaborate by enriching partials and the shared
accumulator.

## Feature Plugin

Features operate on the cold path only. They see the shared provider state and can transform provider-native or core messages during finalize.

Key methods (subset):
- `init(config, state) -> state` (required)
- `finalize(final_messages, native_messages, state) -> (finals, native, state)` (required)
- `to_native_messages(messages, native_messages) -> list` (optional in Python; adapter defaults to identity)
- `from_native_messages(native_messages, messages) -> list` (optional in Python; adapter defaults to identity)
- `initialize_request(native_messages, state) -> state` (optional in Python; adapter returns state unchanged)
- `get_template(config) -> str` (optional; returns a feature-specific template string for UIs)
- `get_completions(config, text) -> list[dict]` (optional; returns completion suggestions for interactive apps)
- `apply_completion(config, text, completion) -> str` (optional; turns an accepted completion into a final snippet)

Minimal example (add tag):
```python
from typing import Any, Dict, List, Tuple
from agent_core.types import FeaturePlugin

class TagFeature(FeaturePlugin):
    name = "tag"
    version = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {"enabled": {"type": "boolean", "default": True}}

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        finals = [
            {**m, "metadata": {**m.get("metadata", {}), "tag": True}}
            for m in final_messages
        ]
        return finals, native_messages, state
```

Feature adapters mirror extension adapters: if a feature omits the stateless conversion and `initialize_request` hooks, the Python SDK supplies identity/default behaviors.

### Feature templates and completions

Feature plugins can participate in interactive editing experiences by
implementing `get_template`, `get_completions`, and
`apply_completion`:

- `get_template(config) -> str`
  - Returns a feature-specific template string for applications that
    need to render snippets (for example, when expanding a file or
    web-context marker).
  - The template is an arbitrary string; many features use Python
    `str.format`-style placeholders such as `{path}`, `{range}`, or
    `{lang}` so they can be combined with completion metadata.
  - May safely return an empty string when the feature does not use
    templates.

- `get_completions(config, text) -> list[dict]`
  - Called by applications (via `AgentCore.get_completions`) with the
    full input `text` before the cursor.
  - Returns a list of feature-defined dictionaries describing
    available completions. A common minimal shape is:

    ```python
    {
        "replacement": "text to insert",
        "start": 5,  # 0-based index in `text` where replacement begins
        "display": "label",  # label shown in the UI
        "display_meta": "info",  # optional extra description
    }
    ```

  - Features are free to attach additional keys that are useful when
    applying the completion later (for example, `"url"`, `"path"`, or
    parsed range information). These extra fields are passed through
    unchanged to `apply_completion`.
  - Should return an empty list when no completions apply for the
    current `text`/`config`.

- `apply_completion(config, text, completion) -> str`
  - Optional hook invoked when a user accepts a completion that was
    previously returned by `get_completions`.
  - `text` is the full buffer *after* the completion's
    `"replacement"` has been inserted by the UI.
  - `completion` is the original descriptor dict from
    `get_completions` (including any custom keys you attached).
  - Returns a string that applications can insert into the buffer in
    place of the just-applied completion text (for example, expanding
    a marker into a multi-line snippet). Returning an empty string (or
    other falsey value) indicates that the feature does not wish to
    override the completion.

Minimal example (marker completion):

```python
from typing import Any, Dict, List
from agent_core.types import FeaturePlugin


class MarkerFeature(FeaturePlugin):
    name = "marker"
    version = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def finalize(self, final_messages, native_messages, state):
        return final_messages, native_messages, state

    def get_completions(self, config: Dict[str, Any], text: str) -> List[Dict[str, Any]]:
        if not text.endswith("@tag:"):
            return []
        # Offer a fixed tag; UIs use "replacement"/"start" to
        # update the buffer, and pass this dict back to
        # apply_completion when accepted.
        return [
            {
                "replacement": "@tag:important",
                "start": len(text) - len("@tag:"),
                "display": "@tag:important",
                "display_meta": "Insert 'important' tag",
                "tag": "important",
            }
        ]

    def apply_completion(
        self,
        config: Dict[str, Any],
        text: str,
        completion: Dict[str, Any],
    ) -> str:
        tag = completion.get("tag", "")
        if not tag:
            return ""
        # Replace the marker with a rendered snippet.
        return f"[tagged:{tag}] "
```

Applications such as the terminal UI typically:

- Call `AgentCore.get_completions(config, text)` to gather candidate
  completions from all registered features.
- When a completion is accepted, insert its `"replacement"` into the
  buffer and then call `AgentCore.apply_feature_completion(config, text, completion)`;
  the first non-empty string returned by a feature's
  `apply_completion` is used as the final snippet.

### UI elements and `ui_type`

All plugin kinds (providers, extensions, features, and tools) can
optionally expose UI metadata via `get_ui_elements() -> list[dict]`.
These dictionaries are flattened by `AgentCore.get_ui_schema()` and
left to applications (for example, the terminal client) to render.

Common patterns:

- **Configuration elements** (default `ui_type == "config"`):

  ```python
  {
      "type": "checkbox" | "text" | "number" | "select" | ...,
      "key": "config_key",          # stable configuration key
      "label": "Human label",       # short caption
      "description": "Help text",   # optional
      "options": [                   # for select-like fields
          "value" | {"value": "v", "label": "Display"},
      ],
  }
  ```

  When `ui_type` is omitted or falsy, the core normalizes the element to
  `"config"` and deduplicates configuration entries by `key` when
  combining schemas from multiple plugins.

- **Per-message footers** (`ui_type == "message_footer"`):

  ```python
  {
      "ui_type": "message_footer",
      "data": "metadata.timestamp",   # dotted JSON path into messages
      "template": "{{data}}",         # optional; simple placeholder
  }
  ```

  Applications such as the terminal client use these to render compact
  gray footers under each message (for example, timestamps or cached
  token counts).

- **Status bar fields** (`ui_type == "status_bar"`):

  ```python
  {
      "ui_type": "status_bar",
      "data": "metadata.total_cost",
      "template": "Total: {{data}}",
  }
  ```

  These are typically derived from the last assistant message in a
  session and are rendered in a persistent status bar.

Plugins are free to attach additional keys suited to their needs; the
core treats these element dictionaries as immutable and opaque when
flattening the UI schema.

## Tool Plugin

Tools expose callable functions to the model and manage their own tool state.

Key methods (subset):
- `init(config) -> state`
- `get_tool_schemas(state) -> list`
- `execute_tool(tool_name, arguments, state) -> dict`
- `format_tool_result(result, state) -> str`
 - `stream_tool(tool_name, arguments, state) -> Iterator[dict]` (optional)
 - `to_display_format(text, result, state) -> dict` (optional)

Minimal example (calculator):
```python
from typing import Any, Dict, List
from agent_core.types import ToolPlugin

class Calculator(ToolPlugin):
    name = "calculator"
    version = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return []

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [{"type": "function", "function": {"name": "add", "parameters": {"type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}}, "required": ["a", "b"]}}}]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "add":
            return {"success": True, "result": arguments.get("a", 0) + arguments.get("b", 0)}
        return {"success": False, "error": f"Unknown tool: {tool_name}"}

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        return f"Result: {result['result']}" if result.get("success") else f"Error: {result.get('error')}"

    # Optional: provide streaming and display hooks
    #
    # def stream_tool(
    #     self,
    #     tool_name: str,
    #     arguments: Dict[str, Any],
    #     state: Dict[str, Any],
    # ) -> Iterator[Dict[str, Any]]:
    #     """Yield partial payloads plus a final result dict.
    #
    #     When omitted, the default adapter wraps ``execute_tool`` and
    #     yields a single RESULT dict with no partials. Implement this
    #     when your tool produces long-running or incremental output.
    #     Each yielded dict with a ``"part"`` key is treated as a
    #     display-only partial; a dict with ``"success"`` is treated as
    #     the final result.
    #     """
    #     yield {"part": {"type": "text", "content": "working..."}}
    #     yield {"success": True, "result": 42}

    # def to_display_format(
    #     self,
    #     text: str,
    #     result: Dict[str, Any],
    #     state: Dict[str, Any],
    # ) -> Dict[str, Any]:
    #     """Convert the tool result into a UI display payload.
    #
    #     ``text`` is the string from ``format_tool_result``; ``result``
    #     is the raw result dict from ``execute_tool`` / ``stream_tool``.
    #     The adapter attaches this payload under
    #     ``metadata.display`` on the resulting ``tool`` message so UIs
    #     can show richer output (for example, the executed shell
    #     command, working directory, or full patch text) without
    #     changing what the model sees in ``content``.
    #     """
    #     return {"type": "text", "content": text}
```

## Registering Plugins

```python
from agent_core import AgentCore
from plugins.openai_provider import OpenAICompatibleProvider

core = AgentCore()
core.register_provider(OpenAICompatibleProvider, extensions=[PrefixExtension])
core.register_feature(TagFeature)
core.register_tool(Calculator)

config = {
    "provider": "openai_compatible",
    "model": "gpt-4o",
    "api_key": "sk-...",
}

session = core.create_session()
session = core.add_message(session, "user", "Hello")
session, finals = core.send_request(session, config)
```

## Testing & Validation

- Run unit tests (unit + ollama; integration skipped by default): `pytest core/python/tests -q`
- Run OpenRouter integration tests: `pytest core/python/tests -m openrouter -q`
- Run all integration tests: `pytest core/python/tests -m integration -q`
- Run example tests: `pytest core/python/examples/tests -qs`
- Lint/format/typecheck: `ruff`, `black`, `pyright` per AGENTS.md

For full method details and signatures, see the [Types & Protocols](../reference/agent_core/types.md) and [Provider Wrapper](../reference/agent_core/plugin/provider.md) references.
