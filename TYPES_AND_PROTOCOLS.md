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

### Plugin State

Each plugin maintains state containing configuration, capabilities, runtime data, and UI settings.

```yaml
PluginState:
  config: dict                    # Configuration values for the plugin
  capabilities: list[string]      # List of capabilities the plugin provides
  runtime_state: dict             # Working data that changes during execution
  ui_state: dict                  # Current UI settings from frontend
  
  # Immutability: State objects are immutable. All updates return new state objects.
```

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
    # Initialize with config, return state
  
  update_state(state: dict, updates: dict) → dict
    # Update state, return new state
  
  initialize_request(native_messages: list, state: dict) → dict
    # Called with provider-native messages; prepare for a new turn and return updated state
  
  # Message Conversion (pure)
  to_native_messages(messages: list, state: dict) → list
    # Convert to provider's native format
  
  from_native_messages(native_messages: list, state: dict) → list
    # Convert from provider's native format
  
  # Hot Path Processing (pure)
  process_chunk(native_chunk: dict, messages: list, state: dict)
    → (final_messages: list, partial_messages: list, native_messages: list, new_state: dict)
    # Process a streaming chunk; may emit new partials/finals and native outputs
  
  finalize(messages: list, state: dict) (optional)
    → (final_messages: list, native_messages: list, new_state: dict)
    # Final processing after streaming completes
  
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

Enhances provider streaming with additional processing (citations, reasoning extraction, etc.). Runs in the provider's language on the hot path.

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
  init(config: dict) → state: dict
  update_state(state: dict, updates: dict) → dict
  
  # Chunk Processing (Hot Path)
  process_chunk(
    native_chunk: dict | None,
    messages: list,
    provider_state: dict,
    extension_state: dict,
    partial_messages: list,
    final_messages: list,
    native_messages: list
  ) → (
    updated_partial_messages: list,
    updated_final_messages: list,
    updated_native_messages: list,
    new_extension_state: dict
  )
    # Observe/modify provider outputs per chunk; called with native_chunk=None during finalize
```

### 3. Feature Plugin Protocol

Transforms final outputs or coordinates per-turn behavior. Features operate on the cold path only.

```yaml
FeaturePlugin:
  # Identity (required)
  name: string
  version: string
  
  # Configuration
  get_config_schema() → dict
  get_ui_elements() → list[dict]
  
  # Lifecycle
  init(config: dict) → state: dict
  update_state(state: dict, updates: dict) → dict
  initialize_request(native_messages: list, state: dict) (optional) → dict
    # Called with provider-native messages; prepare for a new turn and return updated state
  
  # Finalization (required)
  finalize(messages: list, output: dict, state: dict) → dict
    # Modify or discard outputs from provider
    # output: {final_messages: list, native_messages: list}
```

### 4. Tool Plugin Protocol

Provides tools that the LLM can call (file operations, web search, calculations, etc.).

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
   - Provider.to_native_messages(messages)
   - Provider.initialize_request(native_messages)
   - Each Feature.initialize_request(native_messages) (optional)
   - Provider.call_api(native_messages) → (final, partial, native, state)
   - Provider Extensions post-process outputs
   - Features.finalize(messages, {final_messages, native_messages})
5. Core returns (new_session, final_messages)
6. Application decides what to do next
```

### Streaming Flow

```
1. Application creates session and adds a user message
2. Application calls send_request_stream(session, config)
3. Core yields partial events as they arrive:
   {"type": "partial", "message": {...}}
4. After stream completes:
   - Provider.finalize(messages)
   - Features.finalize(messages, {final_messages, native_messages})
5. Core yields final event:
   {"type": "final", "session": new_session, "messages": [...]}
```

### Tool Calling Flow

```
1. Application sends request
2. Final messages may include tool_calls in metadata
3. Application executes tools (not Core responsibility)
4. Application adds tool results as messages
5. Application sends request again with tool results
6. Loop continues until no more tool calls
```

## Plugin Examples

For complete, runnable examples of each plugin type, see PLUGIN_EXAMPLES.md.
