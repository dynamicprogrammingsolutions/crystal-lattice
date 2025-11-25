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
- `init(config) -> state`
- `to_native_messages(messages, state) -> list`
- `from_native_messages(native_messages, state) -> list`
- `initialize_request(native_messages, state) -> state`
- `call_api(native_messages, state) -> (final, partial, native, state)`
- `stream_api(native_messages, state) -> Iterator[chunk]`
- `process_chunk(native_chunk, native_messages, state) -> (final, partial, native, state)`
- `finalize(native_messages, state) -> (final, native, state)`

Minimal example (echo):
```python
from typing import Any, Dict, List, Tuple, Iterator
from agent_core.types import ProviderPlugin

class EchoProvider(ProviderPlugin):
    name = "echo"
    version = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {"model": {"type": "string", "default": "echo-1"}}

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        # Provider state is an opaque dict; this minimal example only
        # needs configuration.
        return {"config": dict(config)}

    def to_native_messages(self, messages: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return list(messages)

    def from_native_messages(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return list(native_messages)

    def initialize_request(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def call_api(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        last_user = next((m for m in reversed(native_messages) if m.get("role") == "user"), {"content": ""})
        content = f"Echo: {last_user.get('content', '')}"
        final = [{"role": "assistant", "content": content}]
        return final, [], [*native_messages, *final], state

    def stream_api(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        yield from []

    def process_chunk(self, native_chunk: Dict[str, Any], native_messages: List[Dict[str, Any]], state: Dict[str, Any]):
        return [], [], native_messages, state

    def finalize(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]):
        return [], native_messages, state
```

## Provider Extension Plugin

Provider extensions run beside the provider on the hot path and the cold path. They do not own separate state; they receive and update the shared provider state.

Key methods (subset):
- `init(config, state) -> state`
- `to_native_messages(messages, native_messages) -> list` (stateless)
- `from_native_messages(native_messages, messages) -> list` (stateless)
- `initialize_request(native_messages, state) -> state`
- `process_chunk(native_chunk|None, state, partial_messages, final_messages, native_messages) -> (partials, finals, native, state)`
- `finalize(final_messages, native_messages, state) -> (finals, native, state)`

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

    def to_native_messages(self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return native_messages

    def from_native_messages(self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return messages

    def initialize_request(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def process_chunk(self, native_chunk: Optional[Dict[str, Any]], state: Dict[str, Any], partial_messages: List[Dict[str, Any]], final_messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]):
        pfx = state.get("config", {}).get("prefix", "[EXT]")
        finals = [{**m, "content": f"{pfx} {m['content']}"} for m in final_messages]
        return partial_messages, finals, native_messages, state

    def finalize(self, final_messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]], state: Dict[str, Any]):
        return final_messages, native_messages, state
```

## Feature Plugin

Features operate on the cold path only. They see the shared provider state and can transform provider-native or core messages during finalize.

Key methods (subset):
- `init(config, state) -> state`
- `to_native_messages(messages, native_messages) -> list` (stateless)
- `from_native_messages(native_messages, messages) -> list` (stateless)
- `initialize_request(native_messages, state) -> state`
- `finalize(final_messages, native_messages, state) -> (finals, native, state)`

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

    def to_native_messages(self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return native_messages

    def from_native_messages(self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return messages

    def initialize_request(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def finalize(self, final_messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]], state: Dict[str, Any]):
        finals = [{**m, "metadata": {**m.get("metadata", {}), "tag": True}} for m in final_messages]
        return finals, native_messages, state
```

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
from plugins.providers.openai.python.openai_provider import OpenAICompatibleProvider

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
