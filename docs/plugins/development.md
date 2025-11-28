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
        return {"config": dict(config)}

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

## Feature Plugin

Features operate on the cold path only. They see the shared provider state and can transform provider-native or core messages during finalize.

Key methods (subset):
- `init(config, state) -> state` (required)
- `finalize(final_messages, native_messages, state) -> (finals, native, state)` (required)
- `to_native_messages(messages, native_messages) -> list` (optional in Python; adapter defaults to identity)
- `from_native_messages(native_messages, messages) -> list` (optional in Python; adapter defaults to identity)
- `initialize_request(native_messages, state) -> state` (optional in Python; adapter returns state unchanged)

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

## Tool Plugin

Tools expose callable functions to the model and manage their own tool state.

Key methods (subset):
- `init(config) -> state`
- `get_tool_schemas(state) -> list`
- `execute_tool(tool_name, arguments, state) -> dict`
- `format_tool_result(result, state) -> str`

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

- Run unit tests: `pytest core/python/tests -q`
- Run example tests: `pytest core/python/examples/tests -qs`
- Lint/format/typecheck: `ruff`, `black`, `pyright` per AGENTS.md

For full method details and signatures, see the [Types & Protocols](../reference/agent_core/types.md) and [Provider Wrapper](../reference/agent_core/plugin/provider.md) references.
