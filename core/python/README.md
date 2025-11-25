# AI Agent Platform - Core SDK (Python)

A truly functional AI agent platform core SDK for building conversational applications with any LLM provider through an extensible plugin system.

## Functional Architecture

This SDK follows **pure functional programming** principles:

- **Immutable Data Structures** - All data types are frozen dataclasses
- **Pure Functions** - AgentCore methods take session/config and return new objects
- **Stateless Core** - Core stores only the processing pipeline (plugins), not runtime state
- **Application-Managed State** - Applications manage sessions and configuration
- **No Side Effects** - All transformations are explicit and traceable

## Features

- **Provider Agnostic**: Switch between OpenAI, Anthropic, Google, local models
- **Extensible**: Add features without touching core code
- **Functional Design**: Predictable, testable, composable
- **Streaming-First**: Real-time response display
- **Immutable**: All state changes return new objects

## Installation

### From Source

```bash
cd core/python
pip install -e .
```

### Development Installation

```bash
cd core/python
pip install -e ".[dev]"
```

## Quick Start

```python
from agent_core import AgentCore
from plugins import OpenAIProvider

# Core stores only processing pipeline (stateless)
core = AgentCore()
core.register_provider(OpenAIProvider)

# Application manages config
config = {
    "model": "gpt-4o",
    "api_key": "sk-..."
}

# Create session (immutable data structure)
session = core.create_session()

# Add messages (functional - returns new session)
session = core.add_message(session, "system", "You are a helpful assistant.")
session = core.add_message(session, "user", "What is 2+2?")

# Send request (functional - returns new session + final messages list)
session, messages = core.send_request(session, config)
print(messages[-1]["content"])  # "4"

# Original operations don't modify - they return new objects
print(len(session.messages))  # 3 (system + user + assistant)
```

## Streaming Example

```python
from agent_core import AgentCore
from plugins import OpenAIProvider

core = AgentCore()
core.register_provider(OpenAIProvider)

config = {"model": "gpt-4o", "api_key": "sk-..."}
session = core.create_session()
session = core.add_message(session, "user", "Write a short poem")

# Stream response (generator yields partials, then final session)
for chunk in core.send_request_stream(session, config):
    if chunk["type"] == "partial":
        print(chunk["message"]["content"], end="", flush=True)
    elif chunk["type"] == "final":
        # Get new session with response
        session = chunk["session"]
        print("\n[Done]")
```

## Core Concepts

### Immutable Session

Sessions are frozen dataclasses - pure data containers with no methods:

```python
from agent_core import Session, Message

# Create session
session = Session(
    session_id="my-session",
    messages=[
        Message(role="user", content="Hello"),
        Message(role="assistant", content="Hi there!")
    ]
)

# Cannot modify - it's frozen
# Avoid mutating session.messages directly; create a new Session instead
# session.session_id = "new"    # Error! Dataclass is frozen
```

### Functional Transformations

All transformations are pure functions that return new objects:

```python
# Add message (returns NEW session)
new_session = core.add_message(session, "user", "Hello")

# Original unchanged
assert len(session.messages) == 0
assert len(new_session.messages) == 1

# Send request (returns NEW session + response)
final_session, response = core.send_request(new_session, config)

assert len(new_session.messages) == 1  # Still 1
assert len(final_session.messages) == 2  # Has response
```

### Stateless Core

Core stores only the plugin pipeline, not runtime state:

```python
core = AgentCore()

# Register plugins (just classes, no config)
core.register_provider(OpenAIProvider)
core.register_feature(WebSearchFeature)
core.register_tool(CalculatorTool)

# Core doesn't store sessions or config
# Application manages them
session1 = core.create_session("user-1")
session2 = core.create_session("user-2")
config1 = {"model": "gpt-4"}
config2 = {"model": "gpt-3.5-turbo"}

# Same core, different sessions/configs
session1, resp1 = core.send_request(session1, config1)
session2, resp2 = core.send_request(session2, config2)
```

### Plugin Classes

Plugins are plain classes with instance methods (functional style; pass state explicitly). Note: keep methods stateless and treat any object attributes as per‑request only; instances are short‑lived and should not retain durable state. Example provider:

```python
from typing import Dict, Any, List, Tuple, Iterator

class MyProvider:
    name: str = "my_provider"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {"api_key": {"type": "string", "required": True}}

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        # Provider state is an opaque dict; this minimal example keeps
        # configuration under a single "config" key and is free to add
        # any other per-request data it needs.
        return {"config": config}


    def to_native_messages(self, messages: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [{"role": m["role"], "content": m["content"]} for m in messages]

    def initialize_request(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def call_api(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        # Return (final_messages, partial_messages, native_messages, new_state)
        return ([{"role": "assistant", "content": "Response"}], [], [], state)

    def finalize(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        # Return (final_messages, native_messages, new_state)
        return ([], [], state)

    def stream_api(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        yield from []
```

## Running Tests

```bash
cd core/python
pytest
```

### Run with Coverage

```bash
pytest --cov=agent_core --cov-report=html
```

## API Reference

### AgentCore

Stateless processing pipeline.

#### Methods

- `register_provider(plugin_class)` - Register provider plugin class
- `register_feature(plugin_class)` - Register feature plugin class
- `register_tool(plugin_class)` - Register tool plugin class
- `create_session(session_id=None)` - Create new empty session
- `add_message(session, role, content, metadata=None)` - Add message (returns new session)
- `send_request(session, config)` - Send request (returns new session + response)
- `send_request_stream(session, config)` - Stream request (yields partials, then final session)
- `send_request_stream_async(session, config)` - Async streaming
- `get_ui_schema()` - Get UI schema from plugins
- `get_tool_schemas(config)` - Get tool schemas
- `export_session(session, format="json")` - Export session to string
- `import_session(data, format="json")` - Import session from string

### Session (Dataclass)

Immutable session data structure.

#### Attributes

- `session_id: str` - Session identifier
- `messages: List[Message]` - Messages (treat as immutable; use pure updates)
- `metadata: Dict[str, Any]` - Session metadata

#### Methods

- `to_dict()` - Convert to dictionary
- `from_dict(data)` - Create from dictionary (classmethod)

### Message (Dataclass)

Immutable message structure.

#### Attributes

- `role: MessageRole` - "system" | "user" | "assistant" | "tool"
- `content: str` - Message content
- `metadata: Optional[Dict[str, Any]]` - Optional metadata

#### Methods

- `to_dict()` - Convert to dictionary
- `from_dict(data)` - Create from dictionary (classmethod)

## Architecture Principles

### 1. Immutability

All data structures are frozen dataclasses. Transformations return new instances:

```python
# Immutable message
msg = Message(role="user", content="Test")
# msg.role = "assistant"  # Error!

# Immutable session
session = Session(session_id="test", messages=[])
# session.messages.append(...)  # Error!

# Functional updates
new_session = Session(
    session_id=session.session_id,
    messages=[*session.messages, msg]
)
```

### 2. Pure Functions

Core methods are pure (same input → same output):

```python
session = core.create_session()
session = core.add_message(session, "user", "Hello")

# Same inputs produce same results
result1 = core.send_request(session, config)
result2 = core.send_request(session, config)

assert result1[1]["content"] == result2[1]["content"]
```

### 3. Explicit State

No hidden state - everything is passed explicitly:

```python
# Config passed explicitly (not stored in core)
session, response = core.send_request(session, config)

# Session passed explicitly (not stored in core)
new_session = core.add_message(session, "user", "Test")
```

### 4. Application Responsibility

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
session, response = core.send_request(
    sessions["user-1"],
    configs["smart"]
)
```

## Development

### Type Checking

```bash
mypy agent_core
```

### Code Formatting

```bash
black agent_core tests
```

### Linting

```bash
ruff check agent_core tests
```

## Functional vs Object-Oriented

### Before (OOP - Old)

```python
core.register_provider(plugin, config={...})
session = core.create_session()  # Core stores session
session.add_message("user", "Hello")  # Mutates session
response = session.send_request()  # Session has methods
```

### After (Functional - New)

```python
core.register_provider(PluginClass)  # Just class
config = {...}  # App manages config
session = core.create_session()  # Returns immutable Session
session = core.add_message(session, "user", "Hello")  # Returns new session
session, response = core.send_request(session, config)  # Pure function
```

## Complete Example

```python
from agent_core import AgentCore
from plugins import OpenAIProvider, WebSearchFeature

# Setup (stateless pipeline)
core = AgentCore()
core.register_provider(OpenAIProvider)
core.register_feature(WebSearchFeature)

# Application manages state
config = {
    "model": "gpt-4",
    "api_key": "sk-...",
    "web_search_enabled": True
}

# Functional conversation flow
session = core.create_session("user-123")
session = core.add_message(session, "system", "You are helpful")

# Chat loop
while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break
    
    # Functional updates
    session = core.add_message(session, "user", user_input)
    session, response = core.send_request(session, config)
    print(f"Assistant: {response['content']}")
    
    # Session grows immutably
    print(f"Messages: {len(session.messages)}")
```

## Version

Current version: `0.3.0` (Functional Architecture + Discovery)

## License

MIT License
