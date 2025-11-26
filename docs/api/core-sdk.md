# Core SDK API Reference

## Overview

The AI Agent Platform Core SDK provides a **functional**, modular interface for building conversational AI applications with any LLM provider through an extensible plugin system.

**Key Principles:**
- **Functional Architecture**: Immutable data structures, pure functions
- **State Management**: Provider wrapper maintains a single shared state per request; extensions/features update it; tools manage their own state
- **Typed Interfaces**: Specialized wrappers for each plugin type (provider, feature, tool, extension)
- **Extensible**: Provider extensions for hot-path processing and stateless message transforms

## Installation

```bash
pip install agent-core
```

## Quick Start

```python
from agent_core import AgentCore
from plugins.openai_provider import OpenAICompatibleProvider

# Initialize core (stateless pipeline)
core = AgentCore()

# Register provider
core.register_provider(OpenAICompatibleProvider)

# Application manages config
config = {
    "provider": "openai_compatible",
    "model": "gpt-4o",
    "api_key": "sk-...",
}

# Create session (immutable)
session = core.create_session()

# Add messages (returns new session)
session = core.add_message(session, "user", "Hello!")

# Send request (returns new session + response)
session, messages = core.send_request(session, config)
print(messages[-1]["content"])
```

---

## AgentCore

Stateless processing pipeline for AI Agent Platform.

**Architecture:**
- Stores plugin adapters (not state)
- All methods are pure functions
- Takes session/config as parameters
- Returns new objects (immutable)

### Constructor

```python
AgentCore()
```

Initialize core with empty plugin pipeline.

**Example:**
```python
core = AgentCore()
```

### Methods

#### register_provider

```python
register_provider(
    plugin_class: type,
    extensions: Optional[List[type]] = None
) -> None
```

Register provider plugin class with optional extensions.

**Parameters:**
- `plugin_class` (type): Provider plugin class (instance methods)
- `extensions` (list, optional): List of provider extension classes

**Example:**
```python
from plugins.openai_provider import OpenAICompatibleProvider

core.register_provider(OpenAICompatibleProvider)

# With extensions
core.register_provider(
    OpenAICompatibleProvider,
    extensions=[ThinkingExtension, CitationExtension]
)
```

#### register_feature

```python
register_feature(plugin_class: type) -> None
```

Register feature plugin class.

**Parameters:**
- `plugin_class` (type): Feature plugin class (instance methods)

**Example:**
```python
core.register_feature(WebSearchFeature)
core.register_feature(ContextManager)
```

#### register_tool

```python
register_tool(plugin_class: type) -> None
```

Register tool plugin class.

**Parameters:**
- `plugin_class` (type): Tool plugin class (instance methods)

**Example:**
```python
core.register_tool(FileReaderTool)
core.register_tool(CalculatorTool)
```

#### discover_and_register

```python
discover_and_register(modules: List[str]) -> Dict[str, List[str]]
```

Discover plugins from Python modules and register them by duck typing.

- Provider: has `stream_api` or `call_api`
- Provider Extension: has `process_chunk` (and no tool/provider I/O methods)
- Tool: has `get_tool_schemas` and `execute_tool`
- Feature: otherwise

Returns a summary of registered plugin names by type.

**Example:**
```python
summary = core.discover_and_register([
    "plugins.openai_provider",
    "plugins.web_search_feature",
    "plugins.file_reader_tool",
])
print(summary)
# {"providers": ["openai_compatible"], "features": ["web_search"], "tools": ["file_reader"], "extensions": []}
```

#### create_session

```python
create_session(session_id: Optional[str] = None) -> Session
```

Create new empty session (convenience function).

**Parameters:**
- `session_id` (str, optional): Session identifier (auto-generated if not provided)

**Returns:**
- `Session`: New empty immutable session

**Example:**
```python
session = core.create_session()
session = core.create_session(session_id="user-123")
```

#### send_request

```python
send_request(
    session: Session,
    config: Dict[str, Any]
) -> Tuple[Session, List[Dict[str, Any]]]
```

Send request and return new session with response (pure function).

**Parameters:**
- `session` (Session): Current session
- `config` (dict): Provider and feature configuration. When multiple providers are registered, `config["provider"]` must select the provider (by name or fully-qualified class path).

**Returns:**
- `Tuple[Session, list]`: Tuple of (new_session, final_messages)

**Example:**
```python
config = {
    "provider": "openai_compatible",
    "model": "gpt-4o",
    "api_key": "sk-...",
}
session, messages = core.send_request(session, config)
print(messages[-1]["content"])
```

#### send_request_stream

```python
send_request_stream(
    session: Session,
    config: Dict[str, Any]
) -> Iterator[Dict[str, Any]]  # yields {"type": "partial"|"final", ...}
```

Stream request and yield partials, then final session (generator function).

**Parameters:**
- `session` (Session): Current session
- `config` (dict): Provider and feature configuration

**Yields:**
- `dict`: Chunk dictionaries:
  - `{"type": "partial", "message": {"role": "assistant", "content": "...", "metadata": {...}}}` - Streaming partial message
  - `{"type": "final", "session": new_session, "messages": [...]}` - Final result (list of final messages)

**Example:**
```python
for chunk in core.send_request_stream(session, config):
    if chunk["type"] == "partial":
        print(chunk["message"]["content"], end="", flush=True)
    elif chunk["type"] == "final":
        session = chunk["session"]
        print("\n[Done]")
```

#### send_request_stream_async

```python
async send_request_stream_async(
    session: Session,
    config: Dict[str, Any]
) -> AsyncIterator[Dict[str, Any]]
```

Async version of `send_request_stream()`.

**Parameters:**
- `session` (Session): Current session
- `config` (dict): Provider and feature configuration

**Yields:**
- `dict`: Same as `send_request_stream()`

**Example:**
```python
async for chunk in core.send_request_stream_async(session, config):
    if chunk["type"] == "partial":
        print(chunk["message"]["content"], end="", flush=True)
    elif chunk["type"] == "final":
        session = chunk["session"]
```

#### get_config_schema

```python
get_config_schema() -> Dict[str, Any]
```

Get combined config schema from all registered plugins.

**Returns:**
- `dict`: Mapping of plugin names to their config schemas

**Example:**
```python
schema = core.get_config_schema()
# {"openai": {...}, "web_search": {...}}
```

#### get_ui_schema

```python
get_ui_schema() -> Dict[str, Any]
```

Get combined UI schema from all registered plugins.

**Returns:**
- `dict`: Mapping of plugin names to their UI element definitions (includes provider, provider extensions, features, and tools)

**Example:**
```python
schema = core.get_ui_schema()
# {"openai": [{"type": "text", ...}], "web_search": [...], "file_reader": [...], ...}
```

#### get_tool_schemas

```python
get_tool_schemas(config: Dict[str, Any]) -> List[Dict[str, Any]]
```

Get tool schemas from all registered tool plugins.

**Parameters:**
- `config` (dict): Tool configuration

**Returns:**
- `list`: List of OpenAI-style function definitions

**Example:**
```python
schemas = core.get_tool_schemas(config)
# [{"type": "function", "function": {...}}, ...]
```

#### execute_tool_calls

```python
execute_tool_calls(tool_calls: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]
```

Execute a batch of tool calls via registered tool plugins and return core "tool" messages.

- Accepts OpenAI-style tool call shapes; `arguments` may be a JSON string or dict. The function normalizes inputs.
- Formats results using each tool's `format_tool_result`.

**Parameters:**
- `tool_calls` (list): `[{"id": str, "name": str, "arguments": dict | str}, ...]` (also accepts OpenAI `{function: {name, arguments}}`)
- `config` (dict): Application config passed to initialize tool state

**Returns:**
- `list[dict]`: Core messages with `role: "tool"`, `content` formatted string, and `metadata.tool_call_id` and `metadata.tool_name`.

**Example:**
```python
tool_calls = [
    {"id": "call_1", "name": "read_file", "arguments": {"file_path": "README.md"}},
]
results = core.execute_tool_calls(tool_calls, config)
# [{"role": "tool", "content": "File contents...", "metadata": {"tool_call_id": "call_1", "tool_name": "read_file"}}]
```

#### export_session

```python
export_session(session: Session, format: str = "json") -> str
```

Export session to string.

**Parameters:**
- `session` (Session): Session to export
- `format` (str): Export format ("json" supported)

**Returns:**
- `str`: Serialized session data

**Example:**
```python
data = core.export_session(session)
```

#### import_session

```python
import_session(data: str, format: str = "json") -> Session
```

Import session from string.

**Parameters:**
- `data` (str): Serialized session data
- `format` (str): Import format ("json" supported)

**Returns:**
- `Session`: Imported immutable session

**Example:**
```python
session = core.import_session(data)
```

---

## Data Types

### Message

Immutable message structure.

```python
@dataclass(frozen=True)
class Message:
    role: MessageRole  # "system" | "user" | "assistant" | "tool"
    content: str
    metadata: Optional[Dict[str, Any]] = None
```

**Methods:**
- `to_dict() -> Dict[str, Any]`: Convert to dictionary
- `from_dict(data: Dict[str, Any]) -> Message`: Create from dictionary (classmethod)

**Example:**
```python
from agent_core import Message

msg = Message(
    role="user",
    content="Hello",
    metadata={"timestamp": "2025-01-01"}
)

# Cannot modify (frozen dataclass)
# msg.role = "assistant"  # Error!
```

### Session

Immutable session data structure (pure data container).

```python
@dataclass(frozen=True)
class Session:
    session_id: str
    messages: List[Message]  # Messages (treat as immutable)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

**Methods:**
- `to_dict() -> Dict[str, Any]`: Convert to dictionary
- `from_dict(data: Dict[str, Any]) -> Session`: Create from dictionary (classmethod)

**Example:**
```python
from agent_core import Session, Message

session = Session(
    session_id="test",
    messages=[
        Message(role="user", content="Hello"),
        Message(role="assistant", content="Hi!")
    ]
)

# Cannot modify (frozen dataclass)
# Avoid mutating session.messages directly; create a new Session instead
```

### MessageRole

Type alias for message roles.

```python
MessageRole = Literal["system", "user", "assistant", "tool"]
```

---

## Plugin Infrastructure

Specialized wrappers and defaulting adapters provide typed, intuitive interfaces for each plugin type.

- Provider: `ProviderWrapper` (owns shared state) + `ProviderDefaultsAdapter`
- Feature: `FeatureWrapper` (shared-state lifecycle) + `FeatureDefaultsAdapter`
- Tool: `ToolWrapper` + `ToolDefaultsAdapter`
- Provider extension: `ExtensionWrapper` (shared-state lifecycle, stateless transforms) + `ProviderExtensionDefaultsAdapter`

In the Python SDK these adapters supply sensible defaults for many conversion and lifecycle hooks when plugin classes omit them, so plugin authors can implement only the subset of methods they actually need.

Note: Methods remain stateless (pure) and use explicit state parameters. Plugin instances are short‑lived (per request) and should not hold durable mutable state. The provider wrapper discards shared state after each request. Tools manage their own state dicts passed in/out explicitly.

---

## Complete Examples

### Basic Chat Application

```python
from agent_core import AgentCore
from plugins.openai_provider import OpenAICompatibleProvider

# Setup
core = AgentCore()
core.register_provider(OpenAICompatibleProvider)

# Application manages config and sessions
config = {
    "provider": "openai_compatible",
    "model": "gpt-4o",
    "api_key": "sk-...",
}

# Create session
session = core.create_session()
session = core.add_message(session, "system", "You are helpful")

# Chat loop
while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break
    
    # Functional updates
    session = core.add_message(session, "user", user_input)
    session, messages = core.send_request(session, config)
    print(f"Assistant: {response['content']}")
```

### Streaming with Progress

```python
from agent_core import AgentCore
from plugins.openai_provider import OpenAICompatibleProvider

core = AgentCore()
core.register_provider(OpenAICompatibleProvider)

config = {
    "provider": "openai_compatible",
    "model": "gpt-4o",
}
session = core.create_session()
session = core.add_message(session, "user", "Write a story")

print("Assistant: ", end="", flush=True)
for chunk in core.send_request_stream(session, config):
    if chunk["type"] == "partial":
        print(chunk["message"]["content"], end="", flush=True)
    elif chunk["type"] == "final":
        session = chunk["session"]
        print("\n")
```

### Provider with Extensions

```python
from agent_core import AgentCore
from plugins.openai_provider import OpenAICompatibleProvider

core = AgentCore()

# Register provider with extensions
core.register_provider(
    OpenAICompatibleProvider,
    extensions=[ThinkingExtension, CitationExtension]
)

config = {
    "provider": "openai_compatible",
    "model": "gpt-4o",
    "api_key": "sk-...",
    "extract_thinking": True,  # Extension config
    "extract_citations": True,
}

session = core.create_session()
session = core.add_message(session, "user", "Explain quantum physics")

for chunk in core.send_request_stream(session, config):
    if chunk["type"] == "final":
        message = chunk["messages"][-1]
        # Extensions added metadata
        if "thinking_blocks" in message.get("metadata", {}):
            print("Thinking:", message["metadata"]["thinking_blocks"])
        if "citations" in message.get("metadata", {}):
            print("Citations:", message["metadata"]["citations"])
```

### Multi-Feature Setup

```python
from agent_core import AgentCore
from plugins.openai_provider import OpenAICompatibleProvider

core = AgentCore()

# Register plugins
core.register_provider(OpenAICompatibleProvider)
core.register_feature(WebSearchFeature)
core.register_feature(ContextManager)
core.register_tool(FileReaderTool)

config = {
    "provider": "openai_compatible",
    "model": "gpt-4",
    "api_key": "sk-...",
    "web_search_enabled": True,
    "max_results": 5,
    "allowed_paths": ["./workspace"],
}

session = core.create_session()
session = core.add_message(session, "user", "Search for AI news")
session, messages = core.send_request(session, config)
```

### Async Streaming

```python
import asyncio
from agent_core import AgentCore
from plugins.openai_provider import OpenAICompatibleProvider

async def chat():
    core = AgentCore()
    core.register_provider(OpenAICompatibleProvider)
    
    config = {
        "provider": "openai_compatible",
        "model": "gpt-4o",
    }
    session = core.create_session()
    session = core.add_message(session, "user", "Hello")
    
    async for chunk in core.send_request_stream_async(session, config):
        if chunk["type"] == "partial":
            print(chunk["message"]["content"], end="", flush=True)
        elif chunk["type"] == "final":
            session = chunk["session"]

asyncio.run(chat())
```

---

## Functional Architecture

### Immutability

All data structures are frozen dataclasses:

```python
# Messages are immutable
msg = Message(role="user", content="Test")
# msg.role = "assistant"  # Error!

# Sessions are immutable
session = Session(session_id="test", messages=[])
# Avoid mutating session.messages directly; create a new Session instead

# Functional updates
new_session = Session(
    session_id=session.session_id,
    messages=[*session.messages, msg]
)
```

### Pure Functions

Core methods are pure (same input → same output):

```python
session = core.create_session()
session = core.add_message(session, "user", "Hello")

# Same inputs work consistently
result1 = core.send_request(session, config)
result2 = core.send_request(session, config)

# Both produce same results (compare last message)
assert result1[1][-1]["content"] == result2[1][-1]["content"]

# Original session unchanged
assert len(session.messages) == 1
```

### Explicit State

No hidden state - everything passed explicitly:

```python
# Config passed explicitly (not stored in core)
session, messages = core.send_request(session, config)

# Session passed explicitly (not stored in core)
new_session = core.add_message(session, "user", "Test")
```

### Application Responsibility

Applications manage state (sessions, config):

```python
# Application manages sessions
sessions = {
    "user-1": core.create_session("user-1"),
    "user-2": core.create_session("user-2")
}

# Application manages config
configs = {
    "fast": {"model": "gpt-3.5-turbo"},
    "smart": {"model": "gpt-4"}
}

# Application decides which to use
session, messages = core.send_request(
    sessions["user-1"],
    configs["smart"]
)
```

---

## Error Handling

### Common Exceptions

- `RuntimeError`: No provider registered, plugin not initialized
- `AttributeError`: Plugin doesn't implement required method
- `ValueError`: Unsupported format, invalid configuration
- `TypeError`: Invalid method arguments

**Example:**
```python
try:
    session, messages = core.send_request(session, config)
except RuntimeError as e:
    print(f"Error: {e}")  # "No provider registered"
```

---

## Version

Current version: `0.3.0` (Functional Architecture with Plugin Wrappers + Discovery)

## License

MIT License
