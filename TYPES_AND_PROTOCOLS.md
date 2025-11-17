# AI Agent Platform - Types and Protocols

This document defines the language-neutral types and protocols for the AI Agent Platform. These definitions apply to all language implementations (Python, JavaScript, etc.).

> **Breaking Change Notice (2025-11): Provider/Feature Lifecycle Update**
>
> Recent updates have changed the lifecycle methods for provider and feature plugins:
> 
> **Provider Changes:**
> - New `initialize_request(messages, state)` method returns updated state for the turn
> - `call_api(native_messages, state)` and `stream_api(native_messages, state)` now take native messages directly
> - `process_chunk(native_chunk, messages, state)` returns `(final_messages, partial_messages, native_messages, new_state)`
> - Optional `finalize(messages, state)` method returns `(final_messages, native_messages, new_state)`
> - Non-streaming `call_api` may also return `partial_messages` for reuse: `(final_messages, partial_messages, native_messages, new_state)`
>
> **Message Types:**
> - `PartialMessage` is now a distinct type: `{role, content, metadata}`
> - Frontend receives partials as-is in stream events: `{"type":"partial","message":{...}}`
> - Provider extensions can observe and modify via `process_chunk(native_chunk|None, messages, provider_state, extension_state, partial_messages, final_messages, native_messages)`
>
> **Feature Changes:**
> - Features now only implement `finalize(messages, output, state)` with option to modify/discard outputs
> - Output shape: `{final_messages, native_messages}`
> - Features may also implement `initialize_request`
>
> All examples and tests reflect these changes.

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
  runtime_state: dict            # Working data that changes during execution
  ui_state: dict                 # Current UI settings from frontend
  
  # Immutability: State objects are immutable. All updates return new state objects.
```

## Plugin Type Detection

Plugins are identified by which functions they implement (duck typing):

- **Provider Plugin**: Has `stream_api()` or `call_api()` functions
- **Provider Extension**: Has `process_chunk()` and `target_provider` property
- **Feature Plugin**: Has `transform_messages()` or `process_final_message()` or `finalize()` functions
- **Tool Plugin**: Has `get_tool_schemas()` and `execute_tool()` functions

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
  
  can_handle(capability_id: string, state: dict) → bool
    # Check if capability supported
  
  initialize_request(messages: list, state: dict) → dict
    # Returns updated state for the turn
  
  # Pure Functions
  to_native_messages(messages: list, state: dict) → list
    # Convert to provider's native format
  
  from_native_messages(native_messages: list, state: dict) → list
    # Convert from provider's native format
  
  build_request_body(messages: list, state: dict) → dict
    # Build request body for API
  
  process_chunk(native_chunk: dict, messages: list, state: dict)
    → (final_messages: list, partial_messages: list, native_messages: list, new_state: dict)
    # Process streaming chunk and return updated messages and state
  
  finalize(messages: list, state: dict) (optional)
    → (final_messages: list, native_messages: list, new_state: dict)
    # Final processing after streaming completes
  
  to_display_format(message: dict, state: dict) → dict
    # Convert message to display-friendly format
  
  # I/O Functions
  detect_capabilities(config: dict) → list[string]
    # Detect available capabilities
  
  call_api(native_messages: list, state: dict)
    → (final_messages: list, partial_messages: list, native_messages: list, new_state: dict)
    # Make non-streaming API call
  
  stream_api(native_messages: list, state: dict) → Iterator[dict]
    # Make streaming API call, yields native chunks
```

### 2. Provider Extension Protocol

Enhances provider streaming with additional processing (citations, reasoning extraction, etc.).

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
  can_handle(capability_id: string, state: dict) → bool
  
  # Chunk Processing (Hot Path - Must be same language as provider)
  process_chunk(
    native_chunk: dict | None,
    messages: list,
    provider_state: dict,
    extension_state: dict,
    partial_messages: list,
    final_messages: list,
    native_messages: list
  ) → (
    new_extension_state: dict,
    updated_partial_messages: list,
    updated_final_messages: list,
    updated_native_messages: list
  )
    # Observe and modify provider outputs per-chunk
  
  finalize(messages: list, provider_state: dict, extension_state: dict) (optional)
    → (enhanced_messages: list, new_extension_state: dict)
    # Final enhancement after streaming completes
```

### 3. Feature Plugin Protocol

Transforms messages or adds features (web search, content filtering, etc.).

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
  can_handle(capability_id: string, state: dict) → bool
  
  initialize_request(messages: list, state: dict) (optional) → dict
    # Returns updated state for the turn
  
  # Transformations (at least one required)
  transform_messages(messages: list, state: dict, direction: string) → list
    # direction: "to_compat" | "from_compat"
  
  finalize(messages: list, output: dict, state: dict) → dict | None
    # Modify or discard outputs
    # output: {final_messages: list, native_messages: list}
    # Returns modified output or None to discard
  
  format_display(display: dict, message: dict, state: dict) → dict
    # Enhance display with additional UI elements
  
  # Legacy Methods (deprecated, will be removed)
  modify_request_body(body: dict, state: dict) → dict
    # Modify request body before API call
  
  process_final_message(message: dict, conversation_state: dict, state: dict) → dict
    # Process final message after API call
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

**Important:** The Core SDK follows functional programming principles:
- `AgentCore` stores only the processing pipeline (registered plugins)
- `Session` is an immutable data structure
- Configuration is managed by the application layer
- All transformations are pure functions that return new objects

```yaml
AgentCore:
  # ========================================
  # Initialization
  # ========================================
  
  __init__()
    # Initialize core with empty plugin pipeline
  
  # ========================================
  # Plugin Management (Pipeline Definition)
  # ========================================
  
  register_provider(plugin_class: type) → None
    # Register provider plugin class
  
  register_feature(plugin_class: type) → None
    # Register feature plugin class
  
  register_tool(plugin_class: type) → None
    # Register tool plugin class
  
  get_ui_schema() → dict
    # Get combined UI schema from all registered plugins
  
  # ========================================
  # Pure Transformation Functions
  # ========================================
  
  add_message(
    session: Session,
    role: string,
    content: string,
    metadata: dict (optional)
  ) → Session
    # Add message to session (returns new session)
  
  send_request(
    session: Session,
    config: dict
  ) → (Session, dict)
    # Send request and return new session with response
    # Returns: (new_session, response_message)
  
  send_request_stream(
    session: Session,
    config: dict
  ) → Iterator[dict]
    # Stream request and yield partials, then final session
    # Yields:
    #   Partial chunks: {"type": "partial", "message": {...}}
    #   Final result: {"type": "final", "session": new_session, "message": {...}}
  
  send_request_stream_async(
    session: Session,
    config: dict
  ) → AsyncIterator[dict]
    # Async version of send_request_stream
  
  # ========================================
  # Utility Functions
  # ========================================
  
  get_tool_schemas(config: dict) → list[dict]
    # Get tool schemas from registered tool plugins
  
  create_session(session_id: string (optional)) → Session
    # Create new empty session (convenience function)
  
  export_session(session: Session, format: string = "json") → string
    # Export session to string
  
  import_session(data: string, format: string = "json") → Session
    # Import session from string
```

### Stream Event Format

**Partial Event:**
```yaml
PartialEvent:
  type: "partial"
  message:
    role: string
    content: string               # Partial text so far
    metadata: dict
```

**Final Event:**
```yaml
FinalEvent:
  type: "final"
  session:
    session_id: string
    messages: list[Message]
  message:
    role: string
    content: string               # Complete response text
    metadata: dict                # May include tool_calls, citations, etc.
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

**Important principles:**
- Configuration is application-managed, not stored in Core
- Each request receives its current configuration
- Plugins extract only the keys they need
- No nested structure - flat dictionary for simplicity
- No validation in Core - plugins validate their own config

## Usage Flow Patterns

### Basic Request Flow

```
1. Application creates session
2. Application adds user message to session (returns new session)
3. Application calls send_request(session, config)
4. Core orchestrates plugins:
   - Feature plugins may transform messages
   - Provider plugin converts to native format
   - Provider plugin calls LLM API
   - Provider extensions process response
   - Feature plugins process final message
5. Core returns (new_session, response_message)
6. Application decides what to do next
```

### Streaming Flow

```
1. Application creates session
2. Application adds user message
3. Application calls send_request_stream(session, config)
4. Core yields partial events as they arrive:
   {"type": "partial", "message": {...}}
5. Application forwards partials to frontend
6. Core yields final event:
   {"type": "final", "session": new_session, "message": {...}}
7. Application processes final message
```

### Tool Calling Flow

```
1. Application sends request
2. Response includes tool_calls in metadata
3. Application executes tools (not Core responsibility)
4. Application adds tool results as messages
5. Application sends request again with tool results
6. Loop continues until no more tool calls
```

## Plugin Examples

For complete, runnable examples of each plugin type, see [PLUGIN_EXAMPLES.md](PLUGIN_EXAMPLES.md).
