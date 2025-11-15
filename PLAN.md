# AI Agent Platform - Architecture

## Plugin Types

```
1. PROVIDER PLUGIN (Base I/O)
   - API communication, message conversion
   - Has: config, state, chunk_processing
   - Language: Any
   
2. PROVIDER EXTENSION (Streaming Enhancement)
   - Extends provider's chunk processing
   - Has: config, state, chunk_processing, UI elements
   - Language: MUST match provider
   
3. FEATURE PLUGIN (Message/Request Transform)
   - Transforms messages, modifies requests
   - Has: config, state, UI elements, NO chunk_processing
   - Language: Any
   
4. TOOL PLUGIN (Tool Definition & Execution)
   - Defines tools, executes them
   - Has: config, state, UI elements, NO chunk_processing
   - Language: Any
```

## Two-Layer Plugin Architecture

```
┌─────────────────────────────────────────┐
│  CORE (Python or JavaScript)            │
└─────────────┬───────────────────────────┘
              │
┌─────────────┴───────────────────────────┐
│  PLUGIN ADAPTER (Core Language)         │
│  - Protocol translation                 │
│  - Passthrough (same language)          │
│  - Subprocess bridge (different)        │
└─────────────┬───────────────────────────┘
              │
┌─────────────┴───────────────────────────┐
│  PLUGIN WRAPPER (Plugin Language)       │
│  - Holds plugin state                   │
│  - Direct method calls to plugin        │
│  - State management                     │
└─────────────┬───────────────────────────┘
              │
┌─────────────┴───────────────────────────┐
│  PLUGIN (Plugin Language)               │  
│  - Pure logic, stateless methods        │
│  - Receives state, returns new state    │
└─────────────────────────────────────────┘
```

## Plugin State Object

```yaml
PluginState:
  config:            # Original config + any updates
    model: str
    api_key: str
    enabled: bool
    max_results: int
    ... (plugin-specific)
  
  capabilities: list[str]  # Detected/declared capabilities
  
  runtime_state:     # Plugin's working state
    ... (any plugin-specific data)
  
  ui_state:          # Current UI settings
    ... (reflects UI element values)
```

## Plugin Protocols

### Base Plugin Interface

```yaml
BasePlugin:
  # Schema & UI
  get_config_schema() → dict
  get_ui_elements() → list[UIElement]
  
  # Lifecycle
  init(config) → state
    # Called once, returns initial state with config embedded
  
  update_state(state, updates) → state
    # Called when UI changes or config updates
  
  # Capability
  can_handle(capability_id, state) → bool
```

### 1. Provider Plugin

```yaml
ProviderPlugin extends BasePlugin:
  # Pure functions
  to_native_messages(messages, state) → native_messages
  from_native_messages(native_messages, state) → messages
  build_request_body(messages, state) → body
  
  process_chunk(native_chunk, state) → (partial_content, new_state)
    # Returns: (text_to_stream, updated_state)
  
  finalize(state) → (final_message, metadata)
    # Called after streaming completes
  
  to_display_format(message, state) → display_dict
  
  # I/O functions
  detect_capabilities(config) → capabilities
  call_api(body, state) → response
  stream_api(body, state) → Iterator[native_chunk]
```

### 2. Provider Extension Plugin

```yaml
ProviderExtensionPlugin extends BasePlugin:
  # Must declare target provider
  target_provider: str
  
  # Chunk processing (hot path)
  process_chunk(native_chunk, provider_state, extension_state) 
    → (partial_content, new_extension_state)
    # Called per chunk by provider wrapper
    # Returns: (text_to_stream, updated_state)
  
  enhance_final_message(message, metadata, state) 
    → (enhanced_message, enhanced_metadata)
    # Called before final message sent
```

### 3. Feature Plugin

```yaml
FeaturePlugin extends BasePlugin:
  # Request/Message transforms
  modify_request_body(body, state) → body
  
  transform_messages(messages, state, direction: "to_compat" | "from_compat")
    → messages
  
  process_final_message(message, conversation_state, state)
    → message
    # Called after streaming completes
  
  format_display(display, message, state) → display
```

### 4. Tool Plugin

```yaml
ToolPlugin extends BasePlugin:
  # Tool definition
  get_tool_schemas(state) → list[ToolSchema]
  
  # Execution
  execute_tool(tool_name, arguments, state) → result
    # Can make external API calls
  
  format_tool_result(result, state) → formatted_result
```

## Plugin Wrapper (Holds State)

```python
# Python example
class PluginWrapper:
    """Wrapper in same language as plugin, manages state"""
    
    def __init__(self, plugin_instance, config):
        self.plugin = plugin_instance
        self.state = plugin_instance.init(config)
    
    def update_state(self, updates):
        """Update state (e.g., UI change)"""
        self.state = self.plugin.update_state(self.state, updates)
    
    def get_state(self):
        """Access current state"""
        return self.state
    
    # Delegate all methods, passing state
    
    def can_handle(self, capability_id):
        return self.plugin.can_handle(capability_id, self.state)
    
    def process_chunk(self, native_chunk):
        partial, new_state = self.plugin.process_chunk(native_chunk, self.state)
        self.state = new_state
        return partial
    
    def finalize(self):
        message, metadata = self.plugin.finalize(self.state)
        return message, metadata
    
    # ... other methods
```

## Plugin Adapter (Protocol Bridge)

### Passthrough Adapter (Same Language)

```python
class PassthroughAdapter:
    """For plugins in same language as core"""
    
    def __init__(self, plugin_wrapper):
        self.wrapper = plugin_wrapper
    
    # Direct delegation
    def can_handle(self, capability_id):
        return self.wrapper.can_handle(capability_id)
    
    def process_chunk(self, native_chunk):
        return self.wrapper.process_chunk(native_chunk)
    
    async def stream_api(self, body):
        async for chunk in self.wrapper.stream_api(body):
            yield chunk
```

### Subprocess Adapter (Different Language)

```python
class SubprocessAdapter:
    """For plugins in different language than core"""
    
    def __init__(self, command):
        self.command = command
        self.process = self._start_subprocess()
    
    def _start_subprocess(self):
        """Starts subprocess with plugin wrapper"""
        # Subprocess runs plugin wrapper which manages state
        return subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True
        )
    
    def can_handle(self, capability_id):
        """RPC call to subprocess"""
        return self._call("can_handle", {"capability_id": capability_id})
    
    def process_chunk(self, native_chunk):
        """RPC call to subprocess"""
        return self._call("process_chunk", {"native_chunk": native_chunk})
    
    def update_state(self, updates):
        """Update plugin state via RPC"""
        return self._call("update_state", {"updates": updates})
    
    async def stream_api(self, body):
        """Streaming RPC"""
        # Subprocess wrapper handles state internally
        async for response in self._stream_call("stream_api", {"body": body}):
            if response["type"] == "partial":
                yield response["content"]
            elif response["type"] == "final":
                yield response
```

## Request Flow

### Streaming Flow

```
1. Frontend: user message + UI state
   ↓
2. Application: send_message_stream(message, ui_updates)
   ↓
3. Core: Update plugin states from UI
   FOR EACH plugin adapter:
     adapter.update_state(ui_updates[plugin.name])
   ↓
4. Core: Transform messages
   FOR EACH feature plugin adapter:
     IF adapter.can_handle("message_transform"):
       messages = adapter.transform_messages(messages, "to_compat")
   ↓
5. Core: Build request
   provider_adapter.build_request_body(messages)
   FOR EACH feature plugin adapter:
     body = adapter.modify_request_body(body)
   ↓
6. Core: Stream from provider
   FOR EACH chunk FROM provider_adapter.stream_api(body):
     ├→ Provider Adapter → Provider Wrapper
     │    └→ Provider Wrapper: process_chunk() [updates state]
     │         ├→ Call provider extensions
     │         └→ Return partial
     ├→ IF partial: yield to Application
     │    └→ Application → Frontend: stream partial
     └→ IF final:
         ├→ Provider Adapter: finalize() [with extensions]
         ├→ Core: Process with feature plugins
         │    FOR EACH feature adapter:
         │      message = adapter.process_final_message(message)
         ├→ Core: Format display
         │    display = provider_adapter.to_display_format(message)
         │    FOR EACH feature adapter:
         │      display = adapter.format_display(display, message)
         └→ yield final to Application
              └→ Application → Frontend: replace partials
```

## Example: Provider with Extension (Same Language)

```python
# Provider Plugin (stateless methods)
class OpenAIProvider:
    def get_config_schema(self):
        return {
            "model": {"type": "string", "required": True},
            "api_key": {"type": "string", "required": True}
        }
    
    def init(self, config):
        """Initialize state with config"""
        capabilities = self._detect_capabilities(config)
        return {
            "config": config,
            "capabilities": capabilities,
            "runtime_state": {
                "request_count": 0
            }
        }
    
    def process_chunk(self, native_chunk, state):
        """Process chunk, return partial and new state"""
        delta = native_chunk.get("choices", [{}])[0].get("delta", {})
        partial = delta.get("content", "")
        
        # Update state
        new_state = {
            **state,
            "runtime_state": {
                **state["runtime_state"],
                "last_chunk": native_chunk
            }
        }
        
        return partial, new_state
    
    async def stream_api(self, body, state):
        """I/O function - streams from API"""
        async for chunk in self._call_openai(body, state["config"]):
            yield chunk


# Provider Extension Plugin
class CitationExtension:
    target_provider = "openai"
    
    def get_config_schema(self):
        return {
            "extract_citations": {"type": "boolean", "default": True}
        }
    
    def get_ui_elements(self):
        return [
            {
                "type": "checkbox",
                "key": "extract_citations",
                "label": "Extract Citations"
            }
        ]
    
    def init(self, config):
        return {
            "config": config,
            "runtime_state": {
                "citations": [],
                "content_buffer": ""
            }
        }
    
    def process_chunk(self, native_chunk, provider_state, extension_state):
        """Process each chunk"""
        if not extension_state["config"]["extract_citations"]:
            return "", extension_state
        
        # Extract citations from chunk
        citations = native_chunk.get("citations", [])
        
        new_state = {
            **extension_state,
            "runtime_state": {
                **extension_state["runtime_state"],
                "citations": extension_state["runtime_state"]["citations"] + citations
            }
        }
        
        return "", new_state  # No partial content from extension
    
    def enhance_final_message(self, message, metadata, state):
        """Add citations to final message"""
        enhanced_metadata = {
            **metadata,
            "citations": state["runtime_state"]["citations"]
        }
        return message, enhanced_metadata


# Provider Wrapper (holds state)
class ProviderWrapperWithExtensions:
    def __init__(self, provider, extensions, config):
        self.provider = provider
        self.extensions = extensions
        
        # Initialize states
        self.provider_state = provider.init(config)
        self.extension_states = {
            ext: ext.init(config) for ext in extensions
        }
    
    def update_state(self, updates):
        """Update from UI changes"""
        # Update provider state
        self.provider_state = self.provider.update_state(
            self.provider_state, 
            updates
        )
        
        # Update extension states
        for ext in self.extensions:
            self.extension_states[ext] = ext.update_state(
                self.extension_states[ext],
                updates
            )
    
    async def stream_with_extensions(self, body):
        """Stream with extension processing"""
        async for native_chunk in self.provider.stream_api(body, self.provider_state):
            # Provider processes chunk
            partial, new_provider_state = self.provider.process_chunk(
                native_chunk,
                self.provider_state
            )
            self.provider_state = new_provider_state
            
            # Extensions process chunk
            for ext in self.extensions:
                ext_partial, new_ext_state = ext.process_chunk(
                    native_chunk,
                    self.provider_state,
                    self.extension_states[ext]
                )
                self.extension_states[ext] = new_ext_state
                partial += ext_partial
            
            # Yield partial
            if partial:
                yield {"type": "partial", "content": partial}
        
        # Finalize
        message, metadata = self.provider.finalize(self.provider_state)
        
        # Extensions enhance final message
        for ext in self.extensions:
            message, metadata = ext.enhance_final_message(
                message,
                metadata,
                self.extension_states[ext]
            )
        
        yield {"type": "final", "message": message, "metadata": metadata}
```

## Example: Feature Plugin (Cross-Language OK)

```python
class WebSearchFeature:
    def get_config_schema(self):
        return {
            "web_search_enabled": {"type": "boolean", "default": False},
            "max_results": {"type": "integer", "default": 5}
        }
    
    def get_ui_elements(self):
        return [
            {
                "type": "checkbox",
                "key": "web_search_enabled",
                "label": "Enable Web Search"
            },
            {
                "type": "number",
                "key": "max_results",
                "label": "Max Results",
                "condition": {"web_search_enabled": True}
            }
        ]
    
    def init(self, config):
        return {
            "config": config,
            "capabilities": [],  # Will be checked against provider
            "ui_state": {
                "web_search_enabled": config.get("web_search_enabled", False)
            }
        }
    
    def update_state(self, state, updates):
        """Update when UI changes"""
        new_config = {**state["config"], **updates}
        return {
            **state,
            "config": new_config,
            "ui_state": {**state["ui_state"], **updates}
        }
    
    def can_handle(self, capability_id, state):
        """Check if applicable"""
        return (
            state["ui_state"]["web_search_enabled"] and
            capability_id == "web_search"
        )
    
    def modify_request_body(self, body, state):
        """Add search parameters"""
        if not state["ui_state"]["web_search_enabled"]:
            return body
        
        return {
            **body,
            "search": {
                "enabled": True,
                "max_results": state["config"]["max_results"]
            }
        }
    
    def process_final_message(self, message, conversation_state, state):
        """Process after streaming completes"""
        if "citations" in message.metadata:
            # Format citations
            formatted = self._format_citations(
                message,
                state["config"]["max_results"]
            )
            return formatted
        return message
```

## State Update Flow (UI Interaction)

```
1. Frontend: User toggles "Enable Web Search"
   ↓
2. Frontend → Application: update_config({web_search_enabled: true})
   ↓
3. Application → Core: update_plugin_states(updates)
   ↓
4. Core: FOR EACH plugin adapter:
   adapter.update_state(updates)
   ↓
5. Adapter → Wrapper: update_state(updates)
   ↓
6. Wrapper: Updates plugin state
   new_state = plugin.update_state(current_state, updates)
   ↓
7. Next request uses updated state
```

## Core Plugin Management (Compact)

```python
class Core:
    def __init__(self):
        self.provider_adapter = None
        self.feature_adapters = []
        self.tool_adapters = []
    
    def register_provider(self, plugin, config):
        """Register provider with extensions"""
        # Create wrapper
        wrapper = ProviderWrapperWithExtensions(
            plugin.provider,
            plugin.extensions,
            config
        )
        
        # Create adapter (passthrough or subprocess)
        if is_same_language(plugin, self):
            self.provider_adapter = PassthroughAdapter(wrapper)
        else:
            self.provider_adapter = SubprocessAdapter(wrapper.command)
    
    def register_feature(self, plugin, config):
        """Register feature plugin"""
        wrapper = PluginWrapper(plugin, config)
        
        if is_same_language(plugin, self):
            adapter = PassthroughAdapter(wrapper)
        else:
            adapter = SubprocessAdapter(wrapper.command)
        
        self.feature_adapters.append(adapter)
    
    def update_plugin_states(self, updates):
        """Update all plugin states from UI"""
        self.provider_adapter.update_state(updates)
        for adapter in self.feature_adapters:
            adapter.update_state(updates)
        for adapter in self.tool_adapters:
            adapter.update_state(updates)
    
    async def send_message_stream(self, message, ui_updates=None):
        """Stream message with current plugin states"""
        # Update states if UI changed
        if ui_updates:
            self.update_plugin_states(ui_updates)
        
        # Transform messages
        messages = self._transform_messages([message])
        
        # Build request
        body = self.provider_adapter.build_request_body(messages)
        for adapter in self.feature_adapters:
            body = adapter.modify_request_body(body)
        
        # Stream
        async for item in self.provider_adapter.stream_api(body):
            if item["type"] == "partial":
                yield item
            elif item["type"] == "final":
                # Process final
                message = item["message"]
                for adapter in self.feature_adapters:
                    message = adapter.process_final_message(message)
                
                yield {"type": "final", "message": message}
```

## Summary

**Key Changes:**
1. **Single state object** per plugin (includes config, capabilities, runtime state)
2. **Model in config** (not separate parameter)
3. **Two-layer architecture**: Wrapper (holds state) + Adapter (protocol)
4. **Three plugin types**: Provider Extension, Feature, Tool
5. **State updates** from UI interactions
6. **Passthrough adapter** for same-language (zero overhead)
7. **Subprocess adapter** for cross-language (state managed in subprocess)

**Performance:**
- Same language: Direct calls through passthrough adapter
- Different language: State kept in subprocess, minimal RPC calls