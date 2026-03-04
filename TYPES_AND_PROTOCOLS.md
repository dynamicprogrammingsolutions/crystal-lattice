# AI Agent Platform - Types and Protocols

This document defines the language-neutral types and protocols for the AI Agent Platform. These definitions apply to all language implementations (Python, JavaScript, etc.).

## Core Data Types

### Message

Represents a single message in a conversation.

```yaml
Message:
  role: string                    # One of: "system", "user", "assistant", "tool"
  content: string                 # The text content of the message
  metadata: dict (optional)       # Additional data (tool_calls, tool_call_id, citations, etc.)
  
  # Immutability: Messages are immutable once created
```

### PartialMessage

Represents a streaming partial message being generated.

```yaml
PartialMessage:
  role: string                    # Message role
  content: string                 # Partial content (may be incomplete)
  metadata: dict (optional)       # Partial metadata
  
  # Immutability: Each partial is immutable; new partials are created as streaming progresses
```

### Session

Represents a conversation session containing a sequence of messages.

```yaml
Session:
  session_id: string              # Unique identifier for the session
  messages: list[Message]         # Immutable sequence of messages
  metadata: dict (optional)       # Session-level metadata
  
  # Immutability: Sessions are immutable. All transformations return new sessions.
```

### ModelDescriptor

Represents a model available for a given provider/config.

```yaml
ModelDescriptor:
  id: string                      # Model identifier (e.g., "gpt-4o", "llama3:8b")
  data: dict (optional)           # Provider/plugin-specific metadata (capabilities, context, etc.)
```

## State Model
 
Only the provider wrapper stores state during a request. A single, shared
provider state object (an opaque ``dict``) is passed to the provider plugin
and to all provider extensions and feature plugins. Each may return an
updated copy of this same state. Tools are the exception: each tool plugin
continues to manage its own independent state ``dict``.
 
The platform deliberately does **not** prescribe a concrete shape for these
state objects. Plugins are free to choose whatever nested structure they
need (for example, grouping configuration under a ``"config"`` key or using
plugin‑specific keys for runtime data), as long as they treat state as
immutable and return a new dict whenever it changes.
 
Implications:
- The provider wrapper owns the lifecycle and storage of the shared provider
  state object for each request/turn.
- Provider extensions and feature plugins receive ``state`` and may return
  ``new_state`` from their lifecycle methods; the wrapper propagates the
  latest value.
- Feature plugins do not process streaming chunks; they operate only on the
  cold path but may still update the shared ``state`` via ``init`` and
  ``initialize_request``.
- Tool plugins manage their own tool state dict between ``init``,
  ``execute_tool``, and ``format_tool_result``; the shape of this dict is a
  plugin concern, not part of the core protocol.
 
Note on instance lifecycle: Methods should remain stateless and operate on
provided ``state`` objects. Plugin instances may be constructed by wrappers
for convenience, but they are short‑lived and scoped to a single request,
just like the shared provider state. Do not rely on any implicit,
long‑lived object state across requests.


## Plugin Type Detection

Plugins are identified by which functions they implement (duck typing):

- Provider Plugin: has `stream_api()` or `call_api()`
- Provider Extension: has `process_chunk()` (and no tool/provider I/O methods)
- Feature Plugin: has `finalize()` (and may implement `initialize_request()`)
- Tool Plugin: has `get_tool_schemas()` and `execute_tool()`

## Base Plugin Properties

Every plugin should provide:

```yaml
BasePlugin:
  # Required
  name: string                    # Unique identifier
  version: string                 # Semantic version
  
  # Optional
  description: string             # Human-readable description
  author: string                  # Plugin author
  repository: string              # Source code URL
```

All plugin methods follow these patterns:
- Configuration methods return schemas
- Lifecycle methods manage state
- Processing methods are pure (except I/O)

## Plugin Protocols

These protocol definitions describe the full logical surface area for each plugin type. Language implementations may provide their own default behaviors for some methods. In the Python SDK, adapters in `agent_core.plugin.adapters` implement identity/default behaviors for many conversion and lifecycle hooks when plugin classes omit them, so plugin authors can often implement only the small subset of methods they actually need.

All plugin types also share a common UI hook, `get_ui_elements() → list[dict]`,
which allows them to contribute configuration and display-oriented UI
elements. Each element is a plain dictionary; the core flattens these
via `AgentCore.get_ui_schema()` and annotates them with a `plugin`
field. Plugins may include a `ui_type` field to classify entries:

- `"config"` (default) – configuration inputs such as text fields,
  checkboxes, and selects (typically including keys like `type`, `key`,
  `label`, `description`, and optional `options`). When `ui_type` is
  missing or falsy, the core treats the element as `"config"` and
  deduplicates by `key`.
- `"message_footer"` – per-message footer fields derived from individual
  messages. These elements usually include a dotted JSON path in `data`
  (for example, `"metadata.timestamp"`) and may include a simple
  `template` string that UIs can use to format the value.
- `"status_bar"` – persistent status bar fields, often derived from the
  last assistant message in a session, with a similar shape to
  `"message_footer"` entries (for example,
  `{ "ui_type": "status_bar", "data": "metadata.total_cost", "template": "Total: {{data}}" }`).

Additional keys beyond those described above are allowed and are left
to applications to interpret.

### 1. Provider Plugin Protocol

Handles communication with LLM APIs and message format conversion.

```yaml
ProviderPlugin:
  # Identity (required)
  name: string
  version: string
  
  # Configuration
  get_config_schema() → dict
  get_ui_elements() → list[dict]
  
  # Lifecycle
  init(config: dict) → state: dict
    # Initialize with config, return provider state (owned by provider wrapper)
  
  initialize_request(native_messages: list, state: dict)
    → (native_messages: list, state: dict)
    # Called with provider-native messages; MUST return (native_messages, shared state)
  
  # Message Conversion (pure)
  to_native_messages(messages: list, state: dict) → list
    # Convert to provider's native format
  
  from_native_messages(native_messages: list, state: dict) → list
    # Convert from provider's native format
  
  # Models and capabilities
  get_models(config: dict) → list[ModelDescriptor]
    # Optional; returns models available for this provider/config
  
  get_tags(config: dict, models: list[ModelDescriptor]) → list[string]
    # Return capability/environment tags for this provider
  
  # Hot Path Processing (pure)
  process_chunk(native_chunk: dict, native_messages: list, state: dict)
    → (partial_messages: list, final_messages: list, native_messages: list, new_state: dict)
    # Process a streaming chunk; may emit new partials/finals and native outputs

  
  finalize(native_messages: list, state: dict) (optional)
    → (final_messages: list, native_messages: list, new_state: dict)
    # Final processing after streaming completes; provider is first in the finalize chain
  
  to_display_format(message: dict, state: dict) → dict
    # Convert message to display-friendly format (optional)
  
  # I/O Functions
  call_api(native_messages: list, state: dict)
    → (partial_messages: list, final_messages: list, native_messages: list, new_state: dict)
    # Make non-streaming API call; may also return partials
  
  stream_api(native_messages: list, state: dict) → Iterator[dict]
    # Make streaming API call; yields provider-native chunks
```


### 2. Provider Extension Protocol

Enhances provider streaming with additional processing (citations, reasoning extraction, etc.). Runs in the provider's language on the hot path. Provider extensions do not own separate state; they receive and update the shared provider `state`.

```yaml
  ProviderExtensionPlugin:
   # Identity (required)
   name: string
   version: string

  
  # Configuration
  get_config_schema() → dict
  get_ui_elements() → list[dict]
  
  # Lifecycle
  init(config: dict, state: dict) → dict
    # Initialize with config and shared state; return updated shared state (or the same state)
  
  initialize_request(native_messages: list, state: dict) (optional)
    → (native_messages: list, state: dict)
    # Prepare for a new turn; MUST return (native_messages, shared state)
  
  # Models and capabilities
  get_models(config: dict, models: list[ModelDescriptor]) → list[ModelDescriptor]
    # Optional; transform or supply model descriptors
  
  get_tags(config: dict, models: list[ModelDescriptor]) → list[string]
    # Capability/environment tags contributed by this extension
  
  required_tags() → list[string]
    # Tags that must be present for this extension to be enabled
  
  # Message Transformation (pure, stateless)
  to_native_messages(messages: list, native_messages: list) → list
    # Transform native_messages using visibility of core messages; may add/alter/remove or drop
    # Must not depend on state or configuration; deterministic
  
  from_native_messages(native_messages: list, messages: list) → list
    # Transform provider-native messages; may add/alter/remove or drop
    # Must not depend on state or configuration; deterministic
  
  # Chunk Processing (Hot Path)
  process_chunk(
    native_chunk: dict | None,
    partial_messages: list,
    final_messages: list,
    native_messages: list,
    state: dict
  ) → (
    updated_partial_messages: list,
    updated_final_messages: list,
    updated_native_messages: list,
    new_state: dict
  )
    # Observe/modify provider outputs per chunk; return updated shared state
    # Called with native_chunk=None during provider finalize (optional)
  
  # Finalization (cold path for extensions)
  finalize(
    final_messages: list,
    native_messages: list,
    state: dict
  ) → (
    final_messages: list,
    native_messages: list,
    new_state: dict
  )
    # Called after provider streaming/finalize; can adjust final/native outputs deterministically
```

### 3. Feature Plugin Protocol

Transforms final outputs or coordinates per-turn behavior. Features operate on the cold path only and do not process streaming chunks. Features receive and may update the shared provider `state` during initialization.

```yaml
FeaturePlugin:
  # Identity (required)
  name: string
  version: string
  
  # Configuration
  get_config_schema() → dict
  get_ui_elements() → list[dict]
  
  # Lifecycle
  init(config: dict, state: dict) → dict
    # Initialize with config and shared state; return updated shared state (or the same state)
  
  initialize_request(native_messages: list, state: dict) (optional)
    → (native_messages: list, state: dict)
    # Called with provider-native messages; MUST return (native_messages, shared state)
  
  # Models and capabilities
  get_models(config: dict, models: list[ModelDescriptor]) → list[ModelDescriptor]
    # Optional; transform or supply model descriptors
  
  get_tags(config: dict, models: list[ModelDescriptor]) → list[string]
    # Capability/environment tags contributed by this feature
  
  required_tags() → list[string]
    # Tags that must be present for this feature to be enabled
  
  # Message Transformation (pure, stateless)
  to_native_messages(messages: list, native_messages: list) → list
    # Transform native_messages using visibility of core messages; may add/alter/remove or drop
    # Must not depend on state or configuration; deterministic
  
  from_native_messages(native_messages: list, messages: list) → list
    # Transform provider-native messages; may add/alter/remove or drop
    # Must not depend on state or configuration; deterministic
  
  # Finalization (required)
  finalize(
    final_messages: list,
    native_messages: list,
    state: dict
  ) → (
    final_messages: list,
    native_messages: list,
    new_state: dict
  )
    # Modify or discard outputs from provider; returns updated outputs and shared state

  # Optional template / completion hooks
  get_template(config: dict) → str
    # Optional hook that returns a feature-specific template string used
    # by applications (for example, to construct editor snippets). May
    # return an empty string when not applicable.

  get_completions(config: dict, text: str) → list[dict]
    # Optional hook that returns completion suggestions for the given
    # input text. Each entry is a feature-defined dictionary typically
    # containing keys like "replacement", "start", "display", and
    # "display_meta". Returns an empty list when no completions apply.

  apply_completion(config: dict, text: str, completion: dict) → str
    # Optional hook that is called when an application accepts a
    # completion previously returned by get_completions. It receives
    # the full buffer text after the completion has been applied and
    # the original completion descriptor. Returns a replacement
    # snippet string to insert in place of the completion text, or an
    # empty string/falsey value to indicate no special handling.
```

### 4. Tool Plugin Protocol

Provides tools that the LLM can call (file operations, web search, calculations, etc.). Tools manage their own internal state dicts; the core does not prescribe a particular structure.

```yaml
ToolPlugin:
  # Identity (required)
  name: string
  version: string
  
  # Configuration
  get_config_schema() → dict
  get_ui_elements() → list[dict]
  
  # Lifecycle
  init(config: dict) → state: dict
  
  # Models and capabilities
  get_tags(config: dict, models: list[ModelDescriptor]) → list[string]
    # Capability/environment tags contributed by this tool
  
  required_tags() → list[string]
    # Tags that must be present for this tool to be exposed
  
  # Tool Definition
  get_tool_schemas(state: dict) → list[dict]
    # Returns OpenAI-style function definitions
  
  # Execution (I/O)
  execute_tool(tool_name: string, arguments: dict, state: dict) → dict
    # Returns: {success: bool, result: any, error: string}
  
  format_tool_result(result: dict, state: dict) → string
    # Format result for LLM consumption
```

## Core SDK Protocol

The Core SDK provides the main interface for applications to interact with the agent platform.

### Core SDK Interface

Important principles:
- `AgentCore` stores only the processing pipeline (registered plugins)
- `Session` is an immutable data structure
- Provider wrapper owns and propagates a single shared provider `state`
- Configuration is managed by the application layer
- All transformations are pure functions that return new objects

```yaml
AgentCore:
  # Initialization
  __init__()

  # Plugin Management
  register_provider(plugin_class: type) → None
  register_feature(plugin_class: type) → None
  register_tool(plugin_class: type) → None

  get_ui_schema() → dict

  # Pure Transformations
  add_message(session: Session, role: string, content: string, metadata?: dict) → Session

  send_request(session: Session, config: dict) → (Session, list)
    # Returns: (new_session, final_messages)

  send_request_stream(session: Session, config: dict) → Iterator[dict]
    # Yields:
    #   Partial chunks: {"type": "partial", "message": {...}}
    #   Final result: {"type": "final", "session": new_session, "messages": [...]} 

  send_request_stream_async(session: Session, config: dict) → AsyncIterator[dict]

  # Utilities
  get_tool_schemas(config: dict) → list[dict]
  create_session(session_id?: string) → Session
  export_session(session: Session, format: string = "json") → string
  import_session(data: string, format: string = "json") → Session
```

### Stream Event Format

Partial Event:
```yaml
PartialEvent:
  type: "partial"
  message:
    role: string
    content: string               # Partial text so far
    metadata: dict
```

Final Event:
```yaml
FinalEvent:
  type: "final"
  session:
    session_id: string
    messages: list[Message]
  messages: list[Message]          # Final messages emitted this turn
```

### Configuration Format

Configuration is a flat dictionary passed to all plugin methods. There are no mandatory keys - each plugin extracts what it needs.

```yaml
Config:
  # Example configuration (all keys optional)
  provider: string                # Provider to use (e.g., "openai")
  model: string                   # Model identifier
  api_key: string                 # API key
  temperature: number             # Temperature parameter
  web_search_enabled: bool        # Feature-specific config
  max_results: integer            # Feature-specific config
  extract_thinking: bool          # Extension-specific config
  allowed_paths: list[string]     # Tool-specific config
  # ... any other plugin-specific keys
```

Important principles:
- Configuration is application-managed, not stored in Core
- Each request receives its current configuration
- Plugins extract only the keys they need
- Flat dictionary for simplicity; plugins validate their own config

## Usage Flow Patterns

### Basic Request Flow

```
1. Application creates session
2. Application adds user message to session (returns new session)
3. Application calls send_request(session, config)
4. Core orchestration per turn:
   - Initialize (in order):
     - For each Tool (optional):
       - tool_state = tool.init(config)
       - tool_schemas += tool.get_tool_schemas(tool_state)
       - (Core injects tool_schemas into provider config under `tools`)
     - Provider.init(config) → state
     - For each Provider Extension: state = ext.init(config, state)
     - For each Feature: state = feat.init(config, state)
   - Pre-request transforms (in the same order) to produce native_messages:
     - native_messages = Provider.to_native_messages(messages, state)
     - For each Provider Extension: native_messages = ext.to_native_messages(messages, native_messages)
     - For each Feature: native_messages = feat.to_native_messages(messages, native_messages)
   - Initialize request (no change in order):
     - (native_messages, state) = Provider.initialize_request(native_messages, state)
       - Provider plugin runs first, then each enabled Provider Extension runs (in order).
     - For each Feature (optional):
       - (native_messages, state) = feat.initialize_request(native_messages, state)
   - Provider.call_api(native_messages, state) → (partial_messages, final_messages, native_messages, state)
    - Provider.finalize(native_messages, state) → (final_messages, native_messages, state)
    - Provider Extensions.finalize(final_messages, native_messages, state) in order
      → (final_messages, native_messages, state)
    - Features.finalize(final_messages, native_messages, state)
      → (final_messages, native_messages, state)
    - Convert combined provider-native finals to core via provider.from_native_messages, then apply extension.from_native_messages and feature.from_native_messages before appending to the session
    - Purge internal shared state after request completes
 5. Core returns (new_session, final_messages)
 6. Application decides what to do next
```

Note: The provider wrapper discards the internal shared state after each
completed request. Each request initializes state via ``init`` using the
current configuration, ensuring request independence (REST-style).

### Streaming Flow

```
1. Application creates session and adds a user message
2. Application calls send_request_stream(session, config)
3. Core yields partial events as they arrive:
   {"type": "partial", "message": {...}}
4. During streaming (hot path):
   - For each provider-native chunk:
     - Provider.process_chunk(native_chunk, native_messages, state)
       → (partial_messages, final_messages, native_messages, state)
     - For each Provider Extension (in order):
       - ext.process_chunk(native_chunk, partial_messages, final_messages, native_messages, state)
         → (partial_messages, final_messages, native_messages, state)
   - Shared state is updated by the provider wrapper if returned
5. After stream completes (cold path):
   - Provider.finalize(native_messages, state) → (final_messages, native_messages, state)
   - Provider Extensions.finalize(final_messages, native_messages, state) in order
     → (final_messages, native_messages, state)
   - Features.finalize(final_messages, native_messages, state)
     → (final_messages, native_messages, state)
6. Core yields final event:
   {"type": "final", "session": new_session, "messages": [...]} 
```

Notes on nomenclature:
- Context: In plugin protocols, `final_messages` refers to provider-native deltas emitted this turn; `native_messages` is the full provider-native history.
- Context: In core API stream events, `chunk["messages"]` within the final event are core messages returned to the application.
- `messages`: core Message dictionaries representing the session history.
- `partial_messages`: partial outputs (provider-native) used on the hot path and surfaced as core-friendly partial events by the provider wrapper.

### Session Metadata Retention

- After each request, the core saves provider-native history to `session.metadata.native_messages` and keeps a verification object in `session.metadata.native_messages_integrity`.
- When `native_messages` is present, the next request trusts it as input; otherwise the core reconstructs native messages from core `messages` via the provider and stateless transforms.
- When adding a message via `add_message`, if native history is present, the core converts only the new message to native and appends it to `native_messages`.

## Plugin Examples

For complete, runnable examples of each plugin type, see EXAMPLES.md and the code under `core/python/examples`.
