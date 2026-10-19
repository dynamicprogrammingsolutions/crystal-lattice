# Core SDK guide

## Overview

The Crystal Lattice Core SDK provides a modular interface for building
conversational applications with different model providers through an
extensible plugin system.

This hand-written guide covers selected workflows and public methods. It is not
an exhaustive member listing. Use the
[generated AgentCore reference](reference/core.md) for
complete signatures and the
[types and protocols overview](types-and-protocols.md) for the data and plugin
model.

Key principles:

- **Immutable conversation values:** operations return new `Session` and
  `Message` values; nested lists and dictionaries are treated as immutable by
  convention.
- **Explicit request inputs:** applications pass sessions and configuration
  into request operations.
- **Managed runtime state:** provider, extension, and feature state is scoped
  to request processing; tools own separate state, and `AgentCore` maintains
  registered wrappers and caches.
- **Extensible processing:** providers, extensions, features, and tools have
  distinct request-path responsibilities.

## Installation

From a repository checkout:

```bash
python -m pip install -e "core/python"
```

## Quick Start

Follow the [credential-free Core quickstart](quickstart.md) for an executable
first request and its expected output.

---

## AgentCore

Provider and plugin processing pipeline for Crystal Lattice.

**Architecture:**

- Stores registered plugin wrappers and Core-local caches.
- Accepts sessions and request configuration explicitly.
- Returns new conversation values rather than mutating the input session.
- Performs provider/tool I/O in request and tool-execution methods.

### Constructor

```python
AgentCore(model_cache: Optional[ModelDiscoveryCache] = None)
```

Initialize Core with an empty plugin pipeline. Passing the same
`ModelDiscoveryCache` to multiple instances shares provider model-discovery
results; dependency, tag, and prepared-tool caches remain Core-local.

**Example:**
```python
core = AgentCore()
```

### Methods

#### get_models

```python
get_models(config: Dict[str, Any]) -> List[Dict[str, Any]]
```

Discover models through the configured provider and registered extension and
feature hooks, using the same normalization and cache as the UI and request
pipeline. Descriptors contain a non-empty `id`; plugin-defined order and
additional metadata are preserved. Plugins may fetch a catalog internally,
but this method does not create a session or send an inference request.

```python
models = core.get_models({"provider": "configured-provider", "model": "default-model"})
for model in models:
    print(model["id"], model.get("name", ""))
```

For discovery through a configured Crystal Lattice agent, use the
[local runtime's `list_models`](../../../application/python/docs/headless-agent-runs.md#discover-available-models).

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
- If a module exposes multiple provider classes, discovery prefers one whose
  plugin name or snake_case class name matches the module basename.

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

#### modify_message

```python
modify_message(
    session: Session,
    index: int,
    content: str,
    config: Dict[str, Any] | None = None,
    *,
    context: Dict[str, Any] | None = None,
) -> Session
```

Modify the content of an existing message and return a new session.

- Supports only `"system"`, `"user"`, and `"assistant"` roles; attempting to
  modify `"tool"` messages raises `ValueError`.
- Keeps the message role and metadata unchanged; only `content` is updated.
- When provider-native history (`native_messages`) and per-message
  `metadata["native_indices"]` are present and form a 1:1 mapping for the
  targeted message, the corresponding native messages are updated using the
  provider + feature pipeline for the supplied `config` (or the single
  registered provider when `config` omits `provider`).
- When native history cannot be safely preserved (for example, missing or
  shared `native_indices`, multiple providers without a resolvable
  configuration, or conversion errors), the core falls back to a
  **core-only** modification:
  - All `native_messages`, `native_messages_integrity`, and per-message
    `native_indices` are removed.
  - Future requests will reconstruct provider-native history from core
    messages as needed.

**Example:**

```python
session = core.add_message(session, "user", "Original question")
# ... after one or more turns ...
session = core.modify_message(session, 1, "Edited question", config)
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
    config: Dict[str, Any],
    *,
    request_id: str | None = None,
    cancellation: Any | None = None,
    context: Dict[str, Any] | None = None,
) -> Tuple[Session, List[Dict[str, Any]]]
```

Send a provider request and return a new session with its final messages.

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
    config: Dict[str, Any],
    *,
    request_id: str | None = None,
    cancellation: Any | None = None,
    context: Dict[str, Any] | None = None,
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
    config: Dict[str, Any],
    *,
    request_id: str | None = None,
    cancellation: Any | None = None,
    context: Dict[str, Any] | None = None,
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
get_config_schema() -> List[Dict[str, Any]]
```

Get flattened config schema from all registered plugins.

Each plugin contributes its config keys to a shared flat list of
entries. Every entry includes:

- `key`: the top-level config key.
- `plugin`: the contributing plugin.
- Any additional schema fields such as `type`, `default`,
  `required`, or `description`.

Multiple plugins may contribute entries for the same `key`.

**Returns:**
- `list[dict]`: List of config schema entries, each with `key` and
  `plugin`.

**Example:**
```python
schema = core.get_config_schema()
# [
#   {"key": "model", "type": "string", "required": True, "plugin": "openai"},
#   {"key": "api_key", "type": "string", "plugin": "openai"},
#   {"key": "api_key", "type": "string", "plugin": "other_provider"},
# ]
```

#### get_ui_schema

```python
get_ui_schema(config: Dict[str, Any]) -> List[Dict[str, Any]]
```

Get combined (flattened) UI schema for the effective config.

The core computes capability tags, model descriptors, available tools, and
effective tools for the given config and passes them through the canonical
`get_ui_elements(config, context=None)` hook. Adapters continue to support
older hook signatures.

Each element in the returned list is a dictionary that describes a UI
element contributed by a provider, extension, feature, or tool. The
core treats these dictionaries as opaque and simply flattens and
annotates them; applications (such as the terminal client) decide how
to render or interpret each entry.

Plugins may include a `ui_type` field to classify elements:

- `"config"` (default): configuration inputs such as text fields,
  checkboxes, or selects. When `ui_type` is missing or falsy, the core
  normalizes the element to `"config"` and deduplicates by its `key`
  when combining schemas from multiple plugins.
- `"message_footer"`: per-message footer fields derived from individual
  messages (for example, timestamps or cached-token counters). These
  elements typically include a dotted JSON `data` path (such as
  `"metadata.timestamp"`) and an optional `template` string that a UI
  can use to format the value.
- `"status_bar"`: persistent status bar fields, often derived from the
  last assistant message in a session. The element shape generally
  mirrors `"message_footer"` entries (for example,
  `{ "ui_type": "status_bar", "data": "metadata.total_cost", "template": "Total: {{data}}" }`).
- Other `ui_type` values remain application-defined; Core flattens them
  without assigning presentation semantics.

The core annotates each element with a `plugin` field (when absent)
naming the contributing plugin and preserves the relative order of all
non-`"config"` elements.

**Returns:**
- `list[dict]`: Flattened list of UI element definitions (each with
  `ui_type` and `plugin` where available).

**Example:**
```python
schema = core.get_ui_schema(config)
# [
#   {"key": "model", "type": "text", "label": "Model"},
#   {"key": "reasoning_effort", "type": "select", "options": [...]},
# ]
```

#### get_completions

```python
get_completions(config: Dict[str, Any], text: str) -> List[Dict[str, Any]]
```

Collect completion suggestions from registered feature plugins for the
given input text. This is typically used by interactive applications
to implement context-aware autocomplete (for example, `@file:` path
expansion).

Each completion entry is a dictionary whose structure is
feature-defined and interpreted by the application. A common shape is:

```python
{
    "replacement": "text to insert",
    "start": 5,               # 0-based index in `text` to start replacing
    "display": "label",      # label shown in the UI
    "display_meta": "info",  # optional extra description
}
```

**Parameters:**
- `config` (dict): Resolved configuration for the current agent or request.
- `text` (str): Full input text before the cursor.

**Returns:**
- `list[dict]`: Flattened list of completion descriptors contributed by
  feature plugins.

#### apply_feature_completion

```python
apply_feature_completion(
    config: Dict[str, Any],
    text: str,
    completion: Dict[str, Any],
) -> str
```

Ask registered feature plugins to transform an accepted completion into
the final snippet to insert into the buffer.

This is typically used by interactive applications after they have
inserted a completion's `"replacement"` text into an input buffer.
The core iterates over feature plugins in registration order and
invokes their `apply_completion` hooks; the first non-empty string is
returned as the replacement snippet.

**Parameters:**
- `config` (dict): Resolved configuration for the current agent or request.
- `text` (str): Full buffer text after the completion has been applied.
- `completion` (dict): Completion descriptor that was accepted, as
  previously returned by `get_completions`.

**Returns:**
- `str`: Replacement snippet string, or an empty string when no feature
  chooses to handle the completion.

#### get_tool_schemas

```python
get_tool_schemas(config: Dict[str, Any]) -> List[Dict[str, Any]]
```

Get tool schemas from all registered tool plugins.

**Parameters:**
- `config` (dict): Tool configuration

**Returns:**
- `list`: List of tool schemas in whatever formats the active tool plugins expose

**Example:**
```python
schemas = core.get_tool_schemas(config)
# Could be chat-function, Responses function, or another accessor-supported shape
```

#### execute_tool_calls

```python
execute_tool_calls(
    tool_calls: List[Dict[str, Any]],
    config: Dict[str, Any],
    *,
    context: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]
```

Execute a batch of tool calls via registered tool plugins and return core "tool" messages.

- Tool calls are inspected through the active tool interop registry rather than one fixed wire shape.
- Built-in support includes OpenAI chat-completions function calls, OpenAI Responses `function_call` items, and Responses `custom_tool_call` items.
- The tool plugin receives the final payload object directly, along with optional payload metadata such as payload kind / format.
- Formats results using each tool's `format_tool_result`. The common path is a
  string tool message. Tools may also return an explicit
  `provider_native_tool_result` envelope for provider-specific structured
  content; providers interpret those envelopes during message conversion.

**Parameters:**
- `tool_calls` (list): tool-call dicts in any format supported by active call accessors
- `config` (dict): Application config passed to initialize tool state

**Returns:**
- `list[dict]`: Core messages with `role: "tool"`, `content` formatted string, and `metadata.tool_call_id` and `metadata.tool_name`.

**Example:**
```python
tool_calls = [
    {
        "id": "call_1",
        "type": "function",
        "function": {"name": "read_file", "arguments": {"file_path": "README.md"}},
    },
]
results = core.execute_tool_calls(tool_calls, config)
# [{"role": "tool", "content": "File contents...", "metadata": {"tool_call_id": "call_1", "tool_name": "read_file"}}]
```

Custom/freeform example:

```python
tool_calls = [
    {
        "type": "custom_tool_call",
        "call_id": "call_patch_1",
        "name": "apply_patch",
        "input": "*** Begin Patch\n*** End Patch",
    },
]
results = core.execute_tool_calls(tool_calls, config)
```

#### Tool Interop

`AgentCore` does not enforce a single canonical external tool schema or tool-call format.

Instead, tool interop is based on:

- schema accessors: inspect a schema and extract semantic fields like tool name
- call accessors: inspect a tool call and extract call id, tool name, payload, payload kind, and optional payload metadata
- schema adapters: convert schema objects between formats
- call adapters: convert tool-call objects between formats

Registry composition is additive:

- explicit interop contributions are tried first
- provider / extension / tool contributions are tried next
- built-in defaults are used as fallback

Providers and provider extensions can also declare which schema formats they accept and which tool-call formats they emit, allowing adapter selection to target actual provider capabilities.

#### execute_session_action

```python
execute_session_action(
    session: Session,
    config: Dict[str, Any],
    plugin_id: str,
    action_id: str,
    params: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> Tuple[Session, Dict[str, Any]]
```

Execute a session-scoped action on a feature plugin or provider extension.

This method provides the core-level entry point for plugin actions that operate on a single session's provider-native message history. Actions can modify native messages and/or patch session metadata.

**Parameters:**
- `session` (Session): Current session
- `config` (dict): Resolved configuration for the current agent
- `plugin_id` (str): Plugin identifier (e.g., `"my_feature"`)
- `action_id` (str): Action identifier defined by the plugin
- `params` (dict): Validated action parameters
- `context` (dict, optional): Additional execution context

**Returns:**
- `Tuple[Session, dict]`: Updated session and action result dictionary

**Context (Layer 1 - Core-level):**
```python
context = {
    "core": self,              # AgentCore instance
    "config": config,          # Current resolved config
    "trigger_source": "core",  # Where action was triggered
    "session": session.to_dict(),  # Serialized session
    "lifecycle": trigger,      # Lifecycle trigger name (if applicable)
    "request_context": {...},  # Request-initialized plugin context
    "request_runtime": {...},  # Request runtime helpers
}
```

Caller-provided `context` is additive only. Reserved keys owned by the
context builders are not overridden; on clashes the builder keeps the owned
value and emits a warning.

**Example:**
```python
# Execute a compaction action
session, result = core.execute_session_action(
    session,
    config,
    "gemini_compaction_feature",
    "compact_range",
    {"start": 0, "end": 10},
)

# Result contains:
# - native_messages: replacement provider-native history
# - session_metadata: patch for session.metadata
# - error: optional error information
if "error" not in result:
    print(f"Compacted {result.get('compaction_result', {}).get('message')}")
```

#### execute_lifecycle_actions

```python
execute_lifecycle_actions(
    session: Session,
    config: Dict[str, Any],
    trigger: str,
    *,
    context: Optional[Dict[str, Any]] = None
) -> Tuple[Session, List[Dict[str, Any]]]
```

Execute all registered lifecycle actions matching a trigger.

Lifecycle actions are plugin-defined actions with a `trigger` field that matches the given trigger name. This method is typically called by `AgentApplication` during session lifecycle events (create, save, request_prepare, etc.).

**Parameters:**
- `session` (Session): Current session
- `config` (dict): Resolved configuration for the current agent
- `trigger` (str): Lifecycle trigger name (e.g., `"session_create"`, `"request_prepare"`)
- `context` (dict, optional): Additional execution context

**Returns:**
- `Tuple[Session, list]`: Updated session and list of action results

**Context:**
Same as `execute_session_action`, with additional `lifecycle` key set to the trigger name.
Lifecycle and `response_finalize` action-style flows also receive
`request_context` and `request_runtime` so plugins can opt into the same
request initialization helpers that explicit session actions use.

**Example:**
```python
# Run lifecycle actions before a request
session, results = core.execute_lifecycle_actions(
    session,
    config,
    "request_prepare",
)

for result in results:
    plugin_id = result.get("plugin")
    action_id = result.get("action_id")
    print(f"Ran {plugin_id}.{action_id}")
```

**Standard lifecycle triggers:**
- `session_create`: After session creation
- `session_save_prepare`: Before session persistence
- `request_prepare`: Before LLM request
- `request_complete`: After successful request
- `request_error`: After failed request
- `session_fork`: After session fork
- `agent_switch_prepare`: Before agent switch
- `agent_switch_complete`: After agent switch
- `session_delete_prepare`: Before session deletion

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

Frozen message value. Nested metadata, multipart content, and tool-result
containers are treated as immutable by convention.

```python
@dataclass(frozen=True)
class Message:
    role: MessageRole  # "system" | "user" | "assistant" | "tool"
    content: Any
    metadata: Optional[Dict[str, Any]] = None
    multipart_content: Optional[List[Dict[str, Any]]] = None
    tool_result: Optional[Dict[str, Any]] = None
```

Dictionary serialization uses `multipartContent` and `toolResult` for the last
two fields.

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

Frozen session value. The nested message list and metadata dictionary are
treated as immutable by convention.

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

Plugin methods use explicit state parameters, and plugin instances are
short-lived per request rather than durable state stores. Providers,
extensions, and features share provider-wrapper state during a request. Tools
manage separate state dictionaries. Hook implementations may perform I/O where
their contracts permit it.

---

## Complete Examples

These examples illustrate composition. Names such as `ThinkingExtension`,
`CitationExtension`, `WebSearchFeature`, and `FileReaderTool` are placeholders
for registered plugin classes. Use the [tested examples](examples.md) for
complete runnable implementations.

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
    print(f"Assistant: {messages[-1]['content']}")
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

## Data and state model

### Immutability

Core conversation types are frozen dataclasses. Their nested lists and
dictionaries remain ordinary Python containers and must be treated as
immutable by convention:

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

### Immutable session updates

Session transformations return new values and leave their input session
unchanged. Provider responses are external I/O and are not guaranteed to be
deterministic:

```python
session = core.create_session("example")
updated = core.add_message(session, "user", "Hello")

assert len(session.messages) == 0
assert len(updated.messages) == 1
```

### Explicit State

Sessions and request configuration are passed explicitly. Registered plugin
wrappers and Core-local caches remain owned by the `AgentCore` instance:

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

## License

Apache License 2.0. See <https://www.apache.org/licenses/LICENSE-2.0>.
