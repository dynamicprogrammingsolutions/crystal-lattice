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
from plugins.openai_provider import OpenAICompatibleProvider

# Core stores only processing pipeline (stateless)
core = AgentCore()
core.register_provider(OpenAICompatibleProvider)

# Application manages config
config = {
    "provider": "openai_compatible",
    "model": "gpt-4o",
    "api_key": "sk-...",
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
from plugins.openai_provider import OpenAICompatibleProvider

core = AgentCore()
core.register_provider(OpenAICompatibleProvider)

config = {
    "provider": "openai_compatible",
    "model": "gpt-4o",
    "api_key": "sk-...",
}
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

### Provider Selection

When you register multiple providers with `AgentCore`, each request selects a provider via the `provider` key in the config dict passed to `send_request` / `send_request_stream` / `send_request_stream_async`.

- When exactly one provider is registered, `provider` is optional (the single provider is used by default), but it is recommended to set it for clarity.
- When multiple providers are registered, `provider` is required and may be either the provider's configured name (for example `"openai_compatible"`) or a fully-qualified class path such as `"plugins.openai_provider.OpenAICompatibleProvider"`.

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
core.register_provider(OpenAICompatibleProvider)
core.register_feature(WebSearchFeature)
core.register_tool(CalculatorTool)

# Core doesn't store sessions or config
# Application manages them
session1 = core.create_session("user-1")
session2 = core.create_session("user-2")
config1 = {"provider": "openai_compatible", "model": "gpt-4"}
config2 = {"provider": "openai_compatible", "model": "gpt-3.5-turbo"}

# Same core, different sessions/configs
session1, resp1 = core.send_request(session1, config1)
session2, resp2 = core.send_request(session2, config2)
```

### Plugin Classes

Plugins are plain classes with instance methods (functional style; pass state explicitly). Note: keep methods stateless and treat any object attributes as per‑request only; instances are short‑lived and should not retain durable state. Example provider:

```python
from typing import Dict, Any, List, Tuple

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
        # Return (final_messages, partial_messages, native_messages, new_state)
        msg = {"role": "assistant", "content": "Response"}
        return ([msg], [], [*native_messages, msg], state)
```

In the Python SDK, adapter classes (for example `ProviderDefaultsAdapter`) supply default implementations for hooks like `to_native_messages`, `from_native_messages`, `initialize_request`, `finalize`, and `stream_api` when they are omitted, so most providers only need to implement configuration, `init`, and one of the I/O entry points (`call_api` or `stream_api`).

## Running Tests

```bash
cd core/python
pytest
```

By default pytest is configured with `-m 'not integration'`, so tests marked as integration are skipped unless explicitly selected. Useful commands:

- `pytest tests -m integration -q` – run all integration tests
- `pytest tests -m ollama -q` – run only Ollama tests

OpenRouter integration tests live under `plugins/openrouter/tests` (repo root) and are marked with `openrouter`.

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
- `add_message(session, role, content, metadata=None, config=None)` - Add message (returns new session)
- `modify_message(session, index, content, config=None)` - Modify existing message content (returns new session)
- `send_request(session, config)` - Send request (returns new session + response)
- `send_request_stream(session, config)` - Stream request (yields partials, then final session)
- `send_request_stream_async(session, config)` - Async streaming
- `get_ui_schema()` - Get UI schema from plugins
- `get_completions(config, text)` - Get feature-driven completion suggestions
- `apply_feature_completion(config, text, completion)` - Let features turn an accepted completion into a snippet
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

### Debug Logging

The SDK includes structured logging using [structlog](https://www.structlog.org/) with powerful filtering capabilities via environment variables.

#### Quick Start

```bash
# Enable debug logging
LOG_LEVEL=DEBUG pytest tests/

# Filter logs by logger name (core, provider, etc.)
LOG_LEVEL=DEBUG LOG_SCOPE=provider pytest tests/

# Show only specific data fields
LOG_LEVEL=DEBUG LOG_DATA="chunk,partials" pytest tests/

# Hide all extra fields (show only standard fields)
LOG_LEVEL=DEBUG LOG_DATA="" pytest tests/

# Custom filtering with JSONPath support
LOG_LEVEL=DEBUG LOG_FILTER="messages[0].role:equals:system" pytest tests/

# Use in your application
LOG_LEVEL=DEBUG python your_app.py
```

**Structlog note:** The SDK uses structlog's bound logger API, where the first positional argument to methods like `logger.debug()` is already the `event` field. Do not also pass an `event=...` keyword argument (for example, `logger.debug("message", event="partial")`), as this will raise a `TypeError` about multiple values for `event`. Use a different key such as `event_type` or `kind` instead.

#### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |
| `LOG_SCOPE` | Filter by logger name (e.g., `core`, `provider`) | All |
| `LOG_DATA` | Comma-separated whitelist of fields to show | All fields |
| `LOG_FILTER` | Filter expressions (comma-separated, AND logic) | None |
| `LOG_COLORS` | Enable/disable ANSI colors in structlog output | Enabled |

#### LOG_DATA Field Whitelist

Controls which data fields are displayed:

```bash
# Not set - show ALL fields (default)
LOG_LEVEL=DEBUG pytest tests/

# Empty string - show ONLY standard fields (event, timestamp, level, logger)
LOG_DATA="" LOG_LEVEL=DEBUG pytest tests/

# Whitelist - show ONLY specified fields + standard fields
LOG_DATA="chunk,partials" LOG_LEVEL=DEBUG pytest tests/
LOG_DATA="messages,native_messages" LOG_LEVEL=DEBUG pytest tests/
```

**Available data fields:**
- `chunk` - Raw streaming chunk from provider
- `partials` - Partial messages extracted from chunk
- `finals` - Final messages from provider
- `core_partials` - Partials converted to core format
- `messages` - Core message list
- `native_messages` - Provider-native message list
- `final_native` - Final provider-native messages
- `final_core` - Final core messages

#### LOG_FILTER Custom Expressions

**Condition Types:**
- `field:exists` - Field must exist
- `field:nonempty` - Field must be non-empty (strings, lists, dicts)
- `field:equals:value` - Field must equal value
- `field:contains:substring` - Field must contain substring

**Path Types:**
- Simple: `chunk.reasoning`
- Array index: `messages[0].content` (JSONPath)
- Nested: `chunk.choices[0].delta.role`

**Examples:**

```bash
# Simple field check
LOG_FILTER="chunk:exists"

# Nested field
LOG_FILTER="chunk.reasoning:nonempty"

# Array indexing with JSONPath
LOG_FILTER="messages[0].role:equals:system"
LOG_FILTER="messages[1].content:contains:file"

# Multiple conditions (AND logic)
LOG_FILTER="chunk:exists,partials:nonempty"
LOG_FILTER="messages[0].role:equals:system,messages[1].content:exists"
```

#### Logger Scopes

Available logger names for `LOG_SCOPE`:
- `core` - Core SDK streaming and request processing
- `provider` - Provider wrapper chunk processing
- `extension` - Extension-specific operations
- `feature` - Feature plugin operations

#### Example Output

**Compact (default):**
```
2025-12-01 14:56:36 [debug    ] starting stream request       [core] extensions=[] features=[] provider=dummy_provider
2025-12-01 14:56:36 [debug    ] processing chunk              [provider] chunk={'content': 'E'} provider=dummy_provider
```

**With LOG_DATA whitelist:**
```bash
LOG_DATA="chunk,partials" LOG_LEVEL=DEBUG pytest tests/
```
```
2025-12-01 14:56:52 [debug    ] processing chunk              [provider] chunk={'content': 'E'} 
2025-12-01 14:56:52 [debug    ] provider processed chunk      [provider] partials=[{'role': 'assistant', 'content': 'E'}]
```

**Clean output (no extra fields):**
```bash
LOG_DATA="" LOG_LEVEL=DEBUG pytest tests/
```
```
2025-12-01 14:56:44 [debug    ] starting stream request       [core]
2025-12-01 14:56:44 [debug    ] processing chunk              [provider]
```

#### Advanced Examples

**Debug specific message content:**
```bash
# Show logs where first message is from system
LOG_FILTER="messages[0].role:equals:system" \
LOG_DATA="messages" \
LOG_LEVEL=DEBUG \
pytest tests/
```

**Debug reasoning in chunks:**
```bash
# Only show chunks with non-empty reasoning
LOG_FILTER="chunk.reasoning:nonempty" \
LOG_DATA="chunk" \
LOG_LEVEL=DEBUG \
pytest tests/
```

**Track tool calls:**
```bash
# Show logs with tool calls in messages
LOG_FILTER="messages[2].metadata:exists" \
LOG_DATA="messages" \
LOG_LEVEL=DEBUG \
pytest tests/
```

**Combine multiple filters:**
```bash
# Provider scope + specific message + show only relevant fields
LOG_SCOPE=provider \
LOG_FILTER="chunk:exists,partials:nonempty" \
LOG_DATA="chunk,partials,provider" \
LOG_LEVEL=DEBUG \
pytest tests/
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
from plugins.openai_provider import OpenAICompatibleProvider
from plugins import WebSearchFeature

# Setup (stateless pipeline)
core = AgentCore()
core.register_provider(OpenAICompatibleProvider)
core.register_feature(WebSearchFeature)

# Application manages state
config = {
    "provider": "openai_compatible",
    "model": "gpt-4",
    "api_key": "sk-...",
    "web_search_enabled": True,
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
