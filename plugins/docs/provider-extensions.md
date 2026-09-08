# Provider extensions (tools + reasoning)

Provider extensions (`ProviderExtensionPlugin`) are the recommended way to add **tool calling** and **reasoning/thinking** support to a provider without bloating the provider itself.

This page is a focused companion to [`plugins/docs/provider-plugins.md`](provider-plugins.md). It documents the runtime contracts that the tool loop and UIs rely on, and provides clean, copyable recipes.

For the portable boundary between provider transport and provider-specific
features, see the
[provider implementation standard](provider-implementation-standard/index.md).

Runtime references (source of truth):

- Protocols/docstrings: `core/python/agent_core/types.py`
- Provider wrapper + hot path: `core/python/agent_core/plugin/provider.py`
- Extension wrapper + defaults: `core/python/agent_core/plugin/extension.py`, `core/python/agent_core/plugin/adapters.py`
- Tool loop expectations: `core/python/agent_app/tool_loop.py`
- Terminal rendering expectations: `application/python/agent_terminal_app/event_rendering.py`

Reference implementations:

- Tools: `core/python/plugins/openai_tools_extension.py`
- Reasoning/thinking: `core/python/plugins/ollama_thinking_extension.py`

See also:

- [Tool interop flow](tool-interop.md)

---

## What extensions are for

Provider extensions run in the provider’s language and share the provider’s `state: dict`.

Typical responsibilities:

- **Request decoration:** add fields to `state["request"]["payload"]` (tools schemas, reasoning knobs, etc.).
- **Hot-path accumulation:** during streaming, accumulate deltas into the shared accumulator `state["accumulator"]`.
- **Interop mapping:** map provider-native fields ↔ core `message["metadata"]` so apps and the tool loop can work.

### Splitting compatible interpretation from provider-specific controls

When compatible endpoints share response and history semantics but only the
official API publishes a rich model-control contract, use two extensions:

- a baseline interpretation extension for streamed output, public metadata,
  signatures, and native-history reconstruction;
- a capability-gated controls extension for model capability normalization,
  exact settings/UI, and request shaping.

The controls extension may enrich model descriptors through `get_models` before
dependency resolution. The provider can then emit the tag required by that
extension for the selected enriched model or from explicit config.

Raw request options should run later and remain the final escape hatch. When
the controls extension uses regex fallbacks for known model IDs, package docs
should include equivalent copyable configuration variants.

---

## Enabling extensions with tags

Extensions can declare dependencies using `required_tags()`.

Those tags are computed per-request from:

- the provider’s `get_tags(config, models)`, and
- tags contributed by enabled extensions/features/tools.

If `required_tags()` is not satisfied, the extension is not enabled and its hooks will not run.

Runtime reference: `core/python/agent_core/core.py` (`_resolve_plugins_for_config`).

Example (hypothetical OpenAI-compatible reasoning extension):

```python
from __future__ import annotations

from typing import Any

from agent_core.types import ProviderExtensionPlugin


class MyReasoningExtension(ProviderExtensionPlugin):
    name = "my_reasoning"
    version = "0.1.0"

    def required_tags(self) -> list[str]:
        return ["provider:openai_compatible", "supports_reasoning"]

    def get_ui_elements(
        self,
        config: dict[str, Any],
        tags: list[str],
        models: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        # This check is optional: if the tag is missing, the extension
        # should not have been enabled.
        if "supports_reasoning" not in tags:
            return []

        return [{"type": "checkbox", "key": "enable_reasoning", "label": "Enable reasoning"}]
```

---

## Runtime interop contracts

### Canonical core metadata keys

Apps and the application-layer tool loop rely on these keys on **core messages**.

Assistant messages:

- `metadata["tool_calls"]`: list of tool calls in any format supported by the
  active tool interop accessors
- `metadata["reasoning"]`: reasoning/thinking text (optional)
- `metadata["reasoning_details"]`: provider-native detail blocks (optional; may be large)

Tool messages:

- `metadata["tool_call_id"]`: id linking tool output back to an assistant tool call
- `metadata["tool_name"]`: tool name (produced by core tools)
- `metadata["display"]`: optional display payload for UIs (produced by tools)

### Tool call shape

The generic tool loop no longer assumes a single canonical tool-call shape.
Core inspects tool calls via the active tool interop registry and extracts a
semantic view consisting of:

- tool name, when available
- tool call id, when available
- final payload value
- payload kind (for example `object` or `text`)
- optional payload format and metadata

OpenAI-style chat-completions function calls remain a common and well-supported
shape:

```python
tool_calls = [
    {
        "id": "call_1",
        "type": "function",
        "function": {"name": "read_file", "arguments": "{\"file_path\": \"README.md\"}"},
    }
]
```

Responses-native custom/freeform calls are also valid when the active accessors
support them:

```python
tool_calls = [
    {
        "type": "custom_tool_call",
        "call_id": "call_patch_1",
        "name": "apply_patch",
        "input": "*** Begin Patch\n*** End Patch",
    }
]
```

Provider/extension authors should preserve whichever tool-call shape they
actually receive or emit rather than forcing everything into OpenAI chat format
unless a concrete target API requires that conversion.

### Tool call sanitization

When LLMs return corrupted JSON in tool call `arguments` fields, the corrupted
data can be stored in history and cause subsequent API calls to fail. The tool
interop system provides sanitization to prevent this.

#### `ToolCallAccessor.sanitize_call(call)`

Each accessor implements `sanitize_call(call: JsonObject) -> JsonObject` that
returns a sanitized copy of the tool call with valid arguments:

```python
class OpenAIChatToolCallAccessor:
    def sanitize_call(self, call: JsonObject) -> JsonObject:
        """Return a sanitized copy with valid JSON arguments.
        
        If arguments contain invalid JSON, returns a copy with
        arguments set to "{}". Otherwise returns the call unchanged.
        """
        fn = call.get("function")
        if not isinstance(fn, dict):
            return call
        arguments = fn.get("arguments")
        if isinstance(arguments, str):
            try:
                json.loads(arguments)
            except (json.JSONDecodeError, Exception):
                return {
                    **call,
                    "function": {**fn, "arguments": "{}"},
                }
        return call
```

For custom tool calls with text payloads (not JSON), `sanitize_call` returns
the call unchanged:

```python
class OpenAIResponsesCustomToolCallAccessor:
    def sanitize_call(self, call: JsonObject) -> JsonObject:
        # Text payload, no JSON sanitization needed
        return call
```

#### `ToolInteropRegistry.sanitize_tool_call(call)`

The registry provides a convenience method that delegates to the appropriate
accessor:

```python
sanitized_call = registry.sanitize_tool_call(corrupted_call)
```

If the call format is not recognized, the call is returned unchanged.

#### When to sanitize

Provider extensions should sanitize tool calls in their `finalize` method
before they are stored in history:

```python
from agent_core.tool_interop import get_registry_from_context


class OpenAICompatibleToolsExtension(ProviderExtensionPlugin):
    # ... other methods ...

    def finalize(
        self,
        final_messages: list[dict[str, Any]],
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
        """Sanitize tool_calls before storing in history."""
        accumulator = state.get("accumulator")
        if isinstance(accumulator, dict):
            tool_calls = accumulator.get("tool_calls")
            if isinstance(tool_calls, list):
                registry = get_registry_from_context(context)
                sanitized_calls = [
                    registry.sanitize_tool_call(tc)
                    for tc in tool_calls
                    if isinstance(tc, dict)
                ]
                accumulator["tool_calls"] = sanitized_calls
        return final_messages, native_messages, state
```

This ensures that corrupted JSON arguments are replaced with valid empty JSON
objects (`"{}"`) before being stored in native history and sent back to the API.

---

## Lifecycle: what each hook is for

Practical guidance (not exhaustive):

- `init(config, state) -> state`
  - Store derived config into shared state. Keep it small and serializable.

- `initialize_request(native_messages, state) -> (native_messages, state)`
  - Per-turn boundary. The provider usually builds `state["request"]`; extensions typically *modify* its payload.

- `process_chunk(native_chunk, partial_messages, final_messages, native_messages, state) -> (...)`
  - Hot path for streaming. Keep work minimal. Prefer updating `state["accumulator"]` (the shared accumulator).

- `finalize(final_messages, native_messages, state) -> (...)`
  - Cold path after provider finalize. Useful for last-mile normalization.

- `to_native_messages(messages, native_messages)` / `from_native_messages(native_messages, messages)`
  - Stateless mapping between provider-native fields and core metadata.
  - Must handle both full-history conversions and **single-message lists** (e.g. `AgentCore.add_message`).

---

## Shared streaming accumulator: `state["accumulator"]`

The default streaming pattern in this repo uses a shared accumulator:

- Providers build the assistant message over time in `state["accumulator"]`.
- Extensions add their own accumulated fields into the same dict (`tool_calls`, `reasoning`, `usage`, etc.).
- Returned `partial_messages` are chunk-local stream emissions. They should
  contain only data introduced by the current chunk.

Critical interop rule:

- Providers must merge deltas in a way that **preserves unknown keys** already present in the accumulator.
- Extensions must update `state["accumulator"]` by **merging**, not by replacing it.
- Extensions must not create a new partial from accumulated state when
  `partial_messages` is empty. If the provider did not emit a current-chunk
  partial, update only the accumulator.

Provider-side merge pattern (the important part is `**current`):

```python
def merge_partial(current: dict, delta: dict) -> dict:
    return {
        **current,  # preserves keys written by extensions
        "role": delta.get("role", current.get("role", "assistant")),
        "content": (current.get("content") or "") + (delta.get("content") or ""),
    }
```

---

## Generic accumulator pattern for extensions (provider-style)

This mirrors the provider “accumulator” streaming path from the provider docs.

In the template, these helpers live in `plugins/template-python-provider/src/template_python_provider/extension.py`.

```python
from __future__ import annotations

from typing import Any, Iterable


def _merge_delta_content(
    current: dict[str, Any],
    delta: dict[str, Any],
    *,
    override: Iterable[str] = (),
    accumulate: Iterable[str] = (),
) -> dict[str, Any]:
    return {
        **current,
        **{k: delta.get(k, current.get(k, "")) for k in override},
        **{k: (current.get(k) or "") + (delta.get(k) or "") for k in accumulate},
    }


class AccumulatorExtensionMixin:
    """Generic process_chunk that delegates extract_delta + process_delta."""

    def extract_delta(self, native_chunk: dict[str, Any]) -> dict[str, Any]:  # pragma: no cover
        raise NotImplementedError

    def process_delta(
        self,
        delta: dict[str, Any],
        accumulated: dict[str, Any] | None,
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:  # pragma: no cover
        raise NotImplementedError

    def process_chunk(
        self,
        native_chunk: dict[str, Any] | None,
        partial_messages: list[dict[str, Any]],
        final_messages: list[dict[str, Any]],
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
    ):
        delta = self.extract_delta(native_chunk or {})
        acc = state.get("accumulator") if isinstance(state.get("accumulator"), dict) else {}
        patch, acc = self.process_delta(delta, acc)

        # Optional: patch the provider's current partial so streaming UIs can render it.
        # Do not synthesize a partial from acc when partial_messages is empty.
        new_partials = partial_messages
        if isinstance(patch, dict) and patch and partial_messages:
            new_partials = [*partial_messages[:-1], {**partial_messages[-1], **patch}]

        return new_partials, final_messages, list(native_messages), {**state, "accumulator": acc}
```

---

## Recipe: tools extension (OpenAI-compatible deltas)

### 1) Inject tool schemas into the request payload

Tools are injected into provider config as `config["tools"]`.

In `initialize_request`, merge them into `state["request"]["payload"]`:

```python
tools = state.get("config", {}).get("tools")
if tools:
    payload = {**payload, "tools": tools, "tool_choice": payload.get("tool_choice", "auto")}
```

### 2) Accumulate streaming `delta.tool_calls`

OpenAI-compatible streams send tool calls incrementally, keyed by `index`, with `function.arguments` arriving as string fragments.

Helper functions (generic enough to copy):

```python
from __future__ import annotations

from typing import Any


def _merge_shallow(
    current: dict[str, Any],
    delta: dict[str, Any],
    *,
    exclude: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {**current, **{k: v for k, v in delta.items() if k not in exclude}}


def _merge_tool_call(current: dict[str, Any], delta: dict[str, Any]) -> dict[str, Any]:
    out = _merge_shallow(current, delta, exclude=("index", "function"))
    func_delta = delta.get("function")
    if isinstance(func_delta, dict):
        func_current = out.get("function")
        func_current = func_current if isinstance(func_current, dict) else {}
        out["function"] = _merge_delta_content(
            func_current,
            func_delta,
            override=("name",),
            accumulate=("arguments",),
        )
    return out


def _merge_tool_calls(existing: list[dict[str, Any]], deltas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged = [dict(tc) for tc in existing]
    for d in deltas:
        if not isinstance(d, dict):
            continue
        i = d.get("index")
        i = i if isinstance(i, int) and i >= 0 else len(merged)
        while len(merged) <= i:
            merged.append({})
        merged[i] = _merge_tool_call(merged[i], d)
    return merged
```

### 3) Full tools extension skeleton

```python
from __future__ import annotations

from typing import Any

from agent_core.types import ProviderExtensionPlugin


class OpenAICompatibleToolsExtension(AccumulatorExtensionMixin, ProviderExtensionPlugin):
    name = "my_tools"
    version = "0.1.0"

    def required_tags(self) -> list[str]:
        return ["provider:openai_compatible", "supports_tools"]

    def init(self, config: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        tools = config.get("tools")
        return {**state, "_tools": tools if isinstance(tools, list) else []}

    def initialize_request(self, native_messages: list[dict[str, Any]], state: dict[str, Any]):
        tools = state.get("_tools") or []
        if not tools:
            return native_messages, state
        req = state.get("request") or {}
        payload = dict(req.get("payload") or {})
        payload |= {"tools": tools, "tool_choice": payload.get("tool_choice", "auto")}
        return native_messages, {**state, "request": {**req, "payload": payload}}

    def extract_delta(self, native_chunk: dict[str, Any]) -> dict[str, Any]:
        choice = (native_chunk.get("choices") or [{}])[0]
        return choice if isinstance(choice, dict) else {}

    def process_delta(self, delta: dict[str, Any], accumulated: dict[str, Any] | None):
        base = accumulated or {}
        d = delta.get("delta") or delta.get("message") or {}
        tool_deltas = d.get("tool_calls") if isinstance(d, dict) else None
        if not isinstance(tool_deltas, list) or not tool_deltas:
            return None, base

        existing = base.get("tool_calls") if isinstance(base.get("tool_calls"), list) else []
        merged = _merge_tool_calls(
            existing=[tc for tc in existing if isinstance(tc, dict)],
            deltas=[tc for tc in tool_deltas if isinstance(tc, dict)],
        )
        new_acc = {**base, "tool_calls": merged}
        return {"tool_calls": merged}, new_acc

    def to_native_messages(self, messages: list[dict[str, Any]], native_messages: list[dict[str, Any]]):
        if len(messages) != len(native_messages):
            return native_messages

        out: list[dict[str, Any]] = []
        for msg, nm in zip(messages, native_messages):
            nm = dict(nm)
            md = msg.get("metadata") or {}

            if msg.get("role") == "assistant" and isinstance(md.get("tool_calls"), list):
                nm["tool_calls"] = md["tool_calls"]

            if msg.get("role") == "tool" and isinstance(md.get("tool_call_id"), str):
                nm["tool_call_id"] = md["tool_call_id"]

            out.append(nm)
        return out

    def from_native_messages(self, native_messages: list[dict[str, Any]], messages: list[dict[str, Any]]):
        if len(messages) != len(native_messages):
            return messages

        out: list[dict[str, Any]] = []
        for msg, nm in zip(messages, native_messages):
            md = dict(msg.get("metadata") or {})
            if isinstance(nm.get("tool_calls"), list) and nm["tool_calls"]:
                md["tool_calls"] = nm["tool_calls"]
            if isinstance(nm.get("tool_call_id"), str) and nm["tool_call_id"]:
                md.setdefault("tool_call_id", nm["tool_call_id"])
            out.append({**msg, "metadata": md})
        return out
```

For providers that accept multiple tool schema formats, prefer using the active
tool interop runtime context plus the provider / extension
`accepted_tool_schema_formats(...)` hooks rather than hardcoding one source
schema format. In `initialize_request(...)`, use
`context["tool_interop"]["registry"]` and
`context["tool_interop"]["schema_target_formats"]` so core-owned, request-specific
interop contributions are respected. That allows:

- already-native schemas to pass through unchanged
- explicit adapters to be additive rather than exclusive
- custom/freeform tool schemas to coexist with legacy function schemas

---

## Recipe: reasoning/thinking extension (OpenAI-compatible deltas)

OpenAI-compatible chunks may carry a `delta.reasoning` string fragment.

Note on request options:

- Some OpenAI-compatible servers only emit reasoning/thinking deltas when a provider-specific request option is enabled.
- Because the request schema is not fully standardized across OpenAI-compatible implementations, prefer a conservative pattern:
  - accept an explicit provider-specific config knob (for example Ollama uses `config["think"]: bool`) and
  - only add the corresponding request payload field when that knob is enabled.

Skeleton:

```python
from __future__ import annotations

from typing import Any

from agent_core.types import ProviderExtensionPlugin


class OpenAICompatibleReasoningExtension(AccumulatorExtensionMixin, ProviderExtensionPlugin):
    name = "my_reasoning"
    version = "0.1.0"

    def required_tags(self) -> list[str]:
        return ["provider:openai_compatible", "supports_thinking"]

    def get_config_schema(self) -> dict[str, Any]:
        # Keep the knob provider-specific. For Ollama's OpenAI-compatible
        # endpoint, this is commonly `think: true`.
        return {"think": {"type": "boolean", "required": False, "default": False}}

    def initialize_request(self, native_messages: list[dict[str, Any]], state: dict[str, Any]):
        if not state.get("config", {}).get("think"):
            return native_messages, state
        req = state.get("request") or {}
        payload = dict(req.get("payload") or {})
        payload["think"] = True
        return native_messages, {**state, "request": {**req, "payload": payload}}

    def extract_delta(self, native_chunk: dict[str, Any]) -> dict[str, Any]:
        choice = (native_chunk.get("choices") or [{}])[0]
        return choice if isinstance(choice, dict) else {}

    def process_delta(self, delta: dict[str, Any], accumulated: dict[str, Any] | None):
        base = accumulated or {}
        d = delta.get("delta") or delta.get("message") or {}
        frag = d.get("reasoning") if isinstance(d, dict) else None
        if not isinstance(frag, str) or not frag:
            return None, base

        new_acc = _merge_delta_content(base, {"reasoning": frag}, accumulate=("reasoning",))
        return {"reasoning": frag}, new_acc

    def from_native_messages(self, native_messages: list[dict[str, Any]], messages: list[dict[str, Any]]):
        if len(messages) != len(native_messages):
            return messages

        out: list[dict[str, Any]] = []
        for msg, nm in zip(messages, native_messages):
            md = dict(msg.get("metadata") or {})
            reasoning = nm.get("reasoning")
            if isinstance(reasoning, str) and reasoning:
                md["reasoning"] = reasoning
            out.append({**msg, "metadata": md})
        return out
```

### Optional: `reasoning_details`

If your provider emits structured `reasoning_details` (sometimes streamed), preserve it on assistant metadata as `metadata["reasoning_details"]`.

Keep the merge rule conservative:

- match entries by `id` when present
- otherwise match by `(type, index)`
- concatenate common string content fields

When in doubt, prefer preserving provider-native blocks unchanged via native history retention.

---

## Session actions

Provider extensions can define session-scoped actions that operate on provider-native history. These actions are similar to feature plugin actions but run in the provider's context with access to shared provider state.

### Action definitions

```python
def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "id": "compact_native_history",
            "label": "Compact native history",
            "description": "Compress provider-native history for this session.",
            "inputs": {
                "instructions": {"type": "string", "required": False},
            },
            # Optional: trigger on lifecycle events
            "trigger": ["session_save_prepare"],
        }
    ]
```

### execute_action signature

```python
def execute_action(
    self,
    action_id: str,
    session: Session,
    native_messages: List[Dict[str, Any]],
    params: Dict[str, Any],
    context: Optional[Dict[str, Any]],
    state: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute a session-scoped provider-native action."""
```

### Return value contract

Provider extension actions return:

```python
{
    # Required: replacement native messages
    "native_messages": [...],  # Full provider-native history
    
    # Optional: session metadata patch
    "session_metadata": {
        "last_compaction": "2025-01-15T10:30:00",
    },
    
    # Optional: error information
    "error": {"type": "disabled", "message": "..."},
}
```

---

## Context in `execute_action`

Provider extensions receive layered context that provides access to runtime capabilities.

Caller-supplied context is additive only. Reserved keys owned by the
context builders are not overridden; if a caller reuses one of those keys,
the builder keeps the owned value and emits a warning.

### Layer 1: Core-level context (always present)

```python
context = {
    "core": self,              # AgentCore instance
    "config": config,          # Current resolved config
    "trigger_source": "core",  # Where action was triggered
    "session": session.to_dict(),  # Serialized session
    "lifecycle": trigger,      # Lifecycle trigger name (if applicable)
}
```

| Key | Type | Description |
|-----|------|-------------|
| `core` | `AgentCore` | Core instance for session/message operations |
| `config` | `dict` | Current resolved request configuration |
| `trigger_source` | `str` | Where action was triggered (`"core"`, `"application"`) |
| `session` | `dict` | Serialized session |
| `lifecycle` | `str` | Lifecycle trigger name (for lifecycle-triggered actions) |
| `request_context` | `dict` | Request-initialized plugin context for action-style flows |
| `request_runtime` | `dict` | Request runtime helpers (`provider`, `features`) for action-style flows |

### Layer 2: Application-level context (when called from AgentApplication)

When called from `AgentApplication.execute_session_action()` or `AgentApplication.run_session_lifecycle()`:

```python
context = {
    # Layer 1 (from core)
    "core": core,
    "config": effective_config,
    "trigger_source": "application",
    "session": session.to_dict(),

    # Layer 2 (from application)
    "app": self,             # AgentApplication instance
    "application": self,     # Alias
    "base_config": self._config,  # Full base config
}
```

### Checking for capabilities

Provider extensions should check for capabilities before using them:

```python
def execute_action(
    self,
    action_id: str,
    session: Session,
    native_messages: List[Dict[str, Any]],
    params: Dict[str, Any],
    context: Optional[Dict[str, Any]],
    state: Dict[str, Any],
) -> Dict[str, Any]:
    # Core is always available
    core = context.get("core")
    config = context.get("config", {})
    
    # Application is optional
    app = context.get("app")
    base_config = context.get("base_config", config)
    
    if app is not None:
        # Application-level capabilities available
        pass
    else:
        # Core-only mode
        pass
```

Provider-extension actions that launch long-running application-owned work can
use the shared
[managed background process registry](managed-background-processes.md) when
`context["app"]` is available. The concrete process remains responsible for
provider calls, notifications, cancellation, and late-result safety.

---

## Testing strategy

Recommended layers:

1) Unit tests for reducers/mappers (offline)
   - `_merge_tool_calls` merges `function.arguments` fragments by index
   - reasoning accumulator concatenates fragments
   - mapping to/from core metadata is stable

2) Integration scaffolds (networked; optional)
   - Use the template scaffolding in `plugins/template-python-provider/tests/`
   - For a comprehensive real-world suite, see `plugins/openrouter/tests/`
