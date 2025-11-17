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

## State Model

Only the provider wrapper stores state during a request. A single, shared provider state object is passed to the provider plugin and to all provider extensions and feature plugins. Each may return an updated copy of this same state. Tools are the exception: tool plugins continue to manage their own independent state.

```yaml
ProviderState:                    # Shared across provider + extensions + features
  config: dict                    # Configuration values in effect for this request
  capabilities: list[string]      # Capability flags detected/derived
  runtime_state: dict             # Working data that changes during execution
  ui_state: dict                  # Current UI settings from frontend
  
  # Immutability: State objects are immutable. All updates return new state objects.

ToolState:                        # Private to each tool plugin (unchanged)
  config: dict
  runtime_state: dict
  ui_state: dict
```

Implications:
- The provider wrapper owns the lifecycle and storage of `ProviderState`.
- Provider extensions and feature plugins receive `state` and may return `new_state` to be merged/propagated by the provider wrapper.
- Feature plugins do not process streaming chunks; they operate only on the cold path but still may update the shared `state` via `init` and `initialize_request`.
- Tool plugins are unchanged and continue to manage their own `ToolState`.

## Plugin Type Detection

Plugins are identified by which functions they implement (duck typing):

- Provider Plugin: has `stream_api()` or `call_api()`
- Provider Extension: has `process_chunk()` and `target_provider`
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

### 1. Provider Plugin Protocol

Handles communication with LLM APIs and message format conversion.

```yaml
ProviderPlugin:
  # Identity (required)
  name: string
  version: string
  
  # Configuration
  get_config_schema() → dict
    # Returns JSON schema for configuration
  
  get_ui_elements() → list[dict]
    # Returns UI elements for frontend
  
  # Lifecycle
  init(config: dict) → state: dict
    # Initialize with config, return provider state (owned by provider wrapper)
  
  update_state(state: dict, updates: dict) → dict
    # Update state immutably, return new state
  
  initialize_request(native_messages: list, state: dict) → dict
    # Called with provider-native messages; MUST return shared state (updated or unchanged)
  
  # Message Conversion (pure)
  to_native_messages(messages: list, state: dict) → list
    # Convert to provider's native format
  
  from_native_messages(native_messages: list, state: dict) → list
    # Convert from provider's native format
  
  # Hot Path Processing (pure)
  process_chunk(native_chunk: dict, messages: list, state: dict)
    → (final_messages: list, partial_messages: list, native_messages: list, new_state: dict)
    # Process a streaming chunk; may emit new partials/finals and native outputs
  
  finalize(native_messages: list, state: dict) (optional)
    → (final_messages: list, native_messages: list, new_state: dict)
    # Final processing after streaming completes; provider is first in the finalize chain
  
  to_display_format(message: dict, state: dict) → dict
    # Convert message to display-friendly format (optional)
  
  # I/O Functions
  detect_capabilities(config: dict) → list[string]
    # Detect available capabilities (optional)
  
  call_api(native_messages: list, state: dict)
    → (final_messages: list, partial_messages: list, native_messages: list, new_state: dict)
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
  target_provider: string         # Which provider this extends
  
  # Configuration
  get_config_schema() → dict
  get_ui_elements() → list[dict]
  
  # Lifecycle
  init(config: dict, state: dict) → dict
    # Initialize with config and shared state; return updated shared state (or the same state)
  
  initialize_request(native_messages: list, state: dict) (optional) → dict
    # Prepare for a new turn; MUST return a shared state (updated or unchanged)
  
  update_state(state: dict, updates: dict) → dict
    # Apply UI or other updates to the shared state; return new state
  
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
    messages: list,
    state: dict,
    partial_messages: list,
    final_messages: list,
    native_messages: list
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
  
  update_state(state: dict, updates: dict) → dict
    # Update shared state immutably (e.g., with UI settings), return new state
  
  initialize_request(native_messages: list, state: dict) (optional) → dict
    # Called with provider-native messages; MUST return shared state (updated or unchanged)
  
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
```

### 4. Tool Plugin Protocol

Provides tools that the LLM can call (file operations, web search, calculations, etc.). Tools are unchanged in this revision and maintain their own internal `ToolState`.

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
  update_state(state: dict, updates: dict) → dict
  
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
     - Provider.init(config) → state
     - For each Provider Extension: state = ext.init(config, state)
     - For each Feature: state = feat.init(config, state)
   - Apply UI settings (in the same order):
     - Provider.update_state(state, ui_state) → state
     - For each Provider Extension: state = ext.update_state(state, ui_state)
     - For each Feature: state = feat.update_state(state, ui_state)
   - Pre-request transforms (in the same order) to produce native_messages:
     - native_messages = Provider.to_native_messages(messages, state)
     - For each Provider Extension: native_messages = ext.to_native_messages(messages, native_messages)
     - For each Feature: native_messages = feat.to_native_messages(messages, native_messages)
   - Initialize request (no change in order):
     - Provider.initialize_request(native_messages, state) → state
     - For each Provider Extension (optional): state = ext.initialize_request(native_messages, state)
     - For each Feature (optional): state = feat.initialize_request(native_messages, state)
   - Provider.call_api(native_messages, state) → (final, partial, native, state)
   - Provider.finalize(native_messages, state) → (final_messages, native_messages, state)
   - Provider Extensions.finalize(final_messages, native_messages, state) in order
     → (final_messages, native_messages, state)
   - Features.finalize(final_messages, native_messages, state)
     → (final_messages, native_messages, state)
   - Purge internal shared state after request completes
5. Core returns (new_session, final_messages)
6. Application decides what to do next
```

Note: The provider wrapper discards the internal shared state after each completed request. Each request initializes state via init and then applies UI settings via update_state, ensuring request independence (REST-style).

### Streaming Flow

```
1. Application creates session and adds a user message
2. Application calls send_request_stream(session, config)
3. Core yields partial events as they arrive:
   {"type": "partial", "message": {...}}
4. During streaming (hot path):
   - For each provider-native chunk, ProviderExtension.process_chunk(
       native_chunk, messages, state, partial_messages, final_messages, native_messages)
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
- `messages`: always refers to core Message objects in the Session (role/content/metadata).
- `native_messages`: always refers to provider-native structures used over the wire.
- `final_messages`: assistant/tool core Message objects emitted this turn as final outputs.
- `partial_messages`: PartialMessage objects emitted during streaming.

## Plugin Examples

For complete, runnable examples of each plugin type, see PLUGIN_EXAMPLES.md.
