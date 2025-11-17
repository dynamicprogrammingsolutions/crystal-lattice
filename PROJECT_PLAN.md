# AI Agent Platform - Project Plan

## Project Overview

### Purpose

Build a **modular, functional AI agent platform** that enables developers to:
- Create conversational AI applications with any LLM provider
- Extend functionality through a plugin system
- Support both Python and JavaScript ecosystems
- Stream responses in real-time
- Add features (web search, citations, tools) without modifying core
- Build locally-first applications with optional cloud deployment

### Target Users

1. **Developers** building AI applications
2. **Plugin authors** creating provider/feature integrations
3. **End users** interacting through web/CLI interfaces

### Key Value Propositions

- **Provider agnostic**: Switch between OpenAI, Anthropic, Google, local models
- **Extensible**: Add features without touching core code
- **Cross-language**: Develop in Python or JavaScript
- **Functional design**: Predictable, testable, composable
- **Streaming-first**: Real-time response display
- **Local-first**: Run entirely on localhost, no external dependencies required

### Porential Naming

**Crystal Lattice**
Meaning: Ordered arrangement of atoms in crystalline solid  
Why it works: Crystal = pure/clean, lattice = extensible structure; suggests clarity and organization  
Tagline: Pure architecture, infinite extension
available domains: crystal-lattice.ai, crystal-lattice.com

**Polymer Chain**
Meaning: Sequence of repeating monomer units
Why it works: Messages/plugins chain together; suggests growth and connection

**Quantum Lattice**
Meaning: Lattice structure in quantum mechanics (quantum field theory)

## Core Design Concepts

### 1. Functional Programming Paradigm

**Immutability:**

All transformations return new objects, never mutate. State changes are explicit and traceable.

**Pure Functions:**

Plugin methods (except I/O) are pure functions. Same input always produces same output. Easy to test, debug, and reason about.

**Composition:**

Small, focused functions compose into complex pipelines. Feature A + Feature B = Combined functionality. No hidden interactions or side effects.

### 2. Plugin Architecture

**Modularity:**

Core provides orchestration only. All provider/feature logic lives in plugins. Add/remove plugins without core changes.

**Two-Layer Plugin System:**

- Layer 1: Wrapper (holds state, same language as plugin)
- Layer 2: Adapter (protocol bridge, core language)
- Same-language = zero-overhead passthrough
- Cross-language = subprocess with JSON-RPC

**Single State Object:**

Each plugin has one state object containing:
- config: configuration values
- capabilities: what the plugin can do
- runtime_state: working data
- ui_state: current UI settings

Updated immutably, passed to all methods.

**Duck Typing:**

Plugin type determined by which functions it implements, not by inheritance. No required base class. Functional architecture without object-oriented constraints.

### 3. Streaming Architecture

**Dual Message Mode:**

Partial messages: streamed token-by-token during generation. Final messages: complete, with metadata (citations, etc.). Frontend shows partials, replaces with final when done.

**Provider Extension Model:**

Extensions enhance provider streaming. Process each chunk in hot path (same language required). Accumulate data (citations, traces) during streaming. Contribute to final message metadata.

**Performance Stratification:**

- Hot path (per-chunk): Must be native, same language
- Cold path (per-turn): Can be cross-language
- Streaming happens in provider's language
- Final processing can be any language

### 4. Configuration & State Management

**Unified State:**

config + capabilities + runtime_state + ui_state = plugin state. State initialized once via init(config). State updated via update_state(state, updates). State passed to all plugin methods.

**UI-Driven Updates:**

Frontend UI elements generated from plugin schemas. User interaction → state update → next request uses new state. Example: Toggle "Enable Web Search" → immediate effect.

**Configuration Hierarchy:**

Default provider config → Agent-specific overrides → Environment variables and file references. Application loads and resolves config, Core receives final resolved dict/object.

### 5. Cross-Language Strategy

**Native First:**

Python Core ←→ Python Plugins (default). JavaScript Core ←→ JavaScript Plugins (default). Zero serialization overhead, full language features.

**Cross-Language When Needed:**

Python Core ←→ JavaScript Plugin (via subprocess). JavaScript Core ←→ Python Plugin (via subprocess). Subprocess wrapper manages state internally. JSON-RPC over stdin/stdout.

**Performance Trade-offs:**

- Same language: ~0μs overhead per call
- Cross-language: ~1-5ms overhead per RPC
- Acceptable for cold path (once per turn)
- Not acceptable for hot path (hundreds of times per turn)

### 6. Low-Level Core API

**Separation of Concerns:**

Adding messages and sending requests are separate operations. Tool execution is application-level responsibility, not core. Messages, tool calls, and tool results are all just message types. Full control over conversation flow.

**Message Manipulation:**

Add, remove, or modify any message in conversation. Clear distinction between conversation state and API calls. Application decides when to call tools, core just handles messages.

### 7. Documentation & Testing Principles

**Documentation as Code:**

Documentation is not written after the fact—it's developed alongside the code as an integral part of development. Every function has docstrings, every plugin has a README, every API change updates the reference documentation.

**Test-Driven Development:**

Tests are written before or during implementation, not after. Each feature includes its test suite. Tests serve as living documentation of expected behavior. Code without tests is considered incomplete.

**Executable Examples:**

All examples in documentation are real, runnable code. Examples are tested as part of CI/CD to ensure they never go stale. If an example breaks, it's a bug.

**Layered Documentation:**

- **Code level**: Docstrings and type hints
- **Module level**: README explaining purpose and basic usage
- **API level**: Auto-generated reference from docstrings
- **Guide level**: Tutorials and how-tos for common tasks
- **Architecture level**: Design decisions and system overview

**Testing Strategy:**

- **Unit tests**: Pure functions, state transformations
- **Integration tests**: Plugin interactions, pipeline flows
- **End-to-end tests**: Complete request/response cycles
- **Examples as tests**: Documentation examples run in CI
- **Performance tests**: Benchmarks for critical paths

**Documentation-First Changes:**

When proposing a new feature or API change, start with documentation:
1. Write the documentation showing how it would work
2. Get feedback on the design
3. Implement to match the documentation
4. Tests verify implementation matches docs

**Quality Gates:**

Code cannot be merged without:
- Passing tests (minimum 80% coverage for new code)
- Updated documentation
- Type hints (Python) or TypeScript definitions (JavaScript)
- Docstrings for public APIs
- At least one executable example

## Architecture Overview

### System Layers

```
┌─────────────────────────────────────────────────────────┐
│  FRONTEND LAYER                                         │
│  - React/Vue/Svelte web UI                             │
│  - Renders streamed partials                           │
│  - Replaces with final message                         │
│  - Provides plugin UI elements (checkboxes, inputs)    │
└─────────────────────┬───────────────────────────────────┘
                      │ WebSocket (JSON messages)
┌─────────────────────┴───────────────────────────────────┐
│  APPLICATION LAYER                                      │
│  - HTTP/WebSocket server                               │
│  - Session management                                  │
│  - Configuration loading and resolution                │
│  - Tool execution logic                                │
│  - Calls Core SDK                                      │
│  - Routes messages to frontend                         │
└─────────────────────┬───────────────────────────────────┘
                      │ SDK function calls
┌─────────────────────┴───────────────────────────────────┐
│  CORE SDK LAYER                                         │
│  - Plugin orchestration                                │
│  - Pipeline composition                                │
│  - State management                                    │
│  - Message manipulation (add/remove)                   │
│  - Low-level API calls                                 │
│  - Does NOT execute tools                              │
│  - Does NOT make HTTP requests                         │
└─────────────────────┬───────────────────────────────────┘
                      │ Plugin interface
┌─────────────────────┴───────────────────────────────────┐
│  PLUGIN ADAPTER LAYER (Core Language)                  │
│  - PassthroughAdapter (same language)                  │
│  - SubprocessAdapter (different language)              │
│  - Protocol translation                                │
└─────────────────────┬───────────────────────────────────┘
                      │ Direct call or JSON-RPC
┌─────────────────────┴───────────────────────────────────┐
│  PLUGIN WRAPPER LAYER (Plugin Language)                │
│  - Holds plugin state                                  │
│  - Direct method calls to plugin                       │
│  - State lifecycle management                          │
└─────────────────────┬───────────────────────────────────┘
                      │ Method calls
┌─────────────────────┴───────────────────────────────────┐
│  PLUGIN LAYER (Plugin Language)                        │
│  - Pure logic, stateless methods                       │
│  - Provider plugins (API communication)                │
│  - Provider extensions (chunk processing)              │
│  - Feature plugins (transforms, final processing)      │
│  - Tool plugins (tool execution)                       │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Input
  ↓
Frontend → Application (WebSocket)
  ↓
Application → Core SDK (add_message)
  ↓
Application → Core SDK (send_request)
  ↓
Core → Feature Plugins (transform messages)
  ↓
Core → Provider Plugin (stream_api)
  ↓
Provider → LLM API (HTTP/HTTPS)
  ↓
LLM API → Provider (streaming chunks)
  ↓
Provider + Extensions → Core (partial messages)
  ↓
Core → Application → Frontend (stream partials)
  ↓
Provider + Extensions → Core (final message)
  ↓
Core → Feature Plugins (process final)
  ↓
Core → Application (final message, may include tool calls)
  ↓
Application: Decides to execute tools (application logic)
  ↓
Application → Core SDK (add tool results)
  ↓
Application → Core SDK (send_request again)
  ↓
[Loop continues until no more tool calls]
```

## Plugin Protocols

### Plugin Types (Determined by Duck Typing)

Plugins are identified by which functions they implement, not by inheritance:

**1. PROVIDER PLUGIN**
- Has: `stream_api()` or `call_api()` functions
- Handles API communication and message conversion
- Language: Any (Python or JavaScript)

**2. PROVIDER EXTENSION**
- Has: `process_chunk()` and `target_provider` property
- Must be same language as target provider
- Enhances streaming with citations, reasoning, etc.

**3. FEATURE PLUGIN**
- Has: `modify_request_body()` or `transform_messages()` or `process_final_message()`
- No chunk processing functions
- Language: Any

**4. TOOL PLUGIN**
- Has: `get_tool_schemas()` and `execute_tool()` functions
- Language: Any

### Base Plugin Properties (All Plugins)

Every plugin should provide:

```yaml
# Required
name: str             # Unique identifier
version: str          # Semantic version

# Optional
description: str      # Human-readable description
author: str          # Plugin author
repository: str      # Source code URL
```

All plugin methods follow these patterns:
- Configuration methods return schemas
- Lifecycle methods manage state
- Processing methods are pure (except I/O)

### 1. Provider Plugin Protocol

```yaml
ProviderPlugin:
  # Identity (required)
  name: str
  version: str
  
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
  
  can_handle(capability_id: str, state: dict) → bool
    # Check if capability supported
  
  # Pure Functions
  to_native_messages(messages: list, state: dict) → list
  from_native_messages(native_messages: list, state: dict) → list
  build_request_body(messages: list, state: dict) → dict
  
  process_chunk(native_chunk: dict, state: dict) → (str, dict)
    # Returns: (partial_content, new_state)
  
  finalize(state: dict) → (dict, dict)
    # Returns: (message, metadata)
  
  to_display_format(message: dict, state: dict) → dict
  
  # I/O Functions
  detect_capabilities(config: dict) → list[str]
  call_api(body: dict, state: dict) → dict
  stream_api(body: dict, state: dict) → Iterator[dict]
```

### 2. Provider Extension Protocol

```yaml
ProviderExtensionPlugin:
  # Identity (required)
  name: str
  version: str
  target_provider: str  # Which provider this extends
  
  # Configuration
  get_config_schema() → dict
  get_ui_elements() → list[dict]
  
  # Lifecycle
  init(config: dict) → state: dict
  update_state(state: dict, updates: dict) → dict
  can_handle(capability_id: str, state: dict) → bool
  
  # Chunk Processing (Hot Path)
  process_chunk(native_chunk: dict, provider_state: dict, extension_state: dict)
    → (str, dict)
    # Returns: (partial_content, new_extension_state)
  
  enhance_final_message(message: dict, metadata: dict, state: dict)
    → (dict, dict)
    # Returns: (enhanced_message, enhanced_metadata)
```

### 3. Feature Plugin Protocol

```yaml
FeaturePlugin:
  # Identity (required)
  name: str
  version: str
  
  # Configuration
  get_config_schema() → dict
  get_ui_elements() → list[dict]
  
  # Lifecycle
  init(config: dict) → state: dict
  update_state(state: dict, updates: dict) → dict
  can_handle(capability_id: str, state: dict) → bool
  
  # Transformations (at least one required)
  modify_request_body(body: dict, state: dict) → dict
  
  transform_messages(messages: list, state: dict, direction: str) → list
    # direction: "to_compat" | "from_compat"
  
  process_final_message(message: dict, conversation_state: dict, state: dict)
    → dict
  
  format_display(display: dict, message: dict, state: dict) → dict
```

### 4. Tool Plugin Protocol

```yaml
ToolPlugin:
  # Identity (required)
  name: str
  version: str
  
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
  execute_tool(tool_name: str, arguments: dict, state: dict) → dict
    # Returns: {success: bool, result: any, error: str}
  
  format_tool_result(result: dict, state: dict) → str
```

## Plugin Examples

### Example 1: Basic OpenAI Provider

```python
# openai_provider.py

from dataclasses import dataclass
from typing import Dict, Any, Iterator, AsyncIterator

@dataclass
class OpenAIProvider:
    """
    OpenAI provider plugin (stateless)
    All methods are pure functions or I/O operations
    """
    
    name: str = "openai"
    version: str = "1.0.0"
    
    @staticmethod
    def get_config_schema() -> Dict[str, Any]:
        """Return configuration schema"""
        return {
            "model": {"type": "string", "required": True},
            "api_key": {"type": "string", "required": True},
            "base_url": {"type": "string", "default": "https://api.openai.com/v1"}
        }
    
    @staticmethod
    def get_capabilities() -> list[str]:
        """Return provider capabilities"""
        return ["text_generation", "streaming", "tool_calling"]
    
    @staticmethod
    def to_native_messages(messages: list[Dict], config: Dict) -> list[Dict]:
        """Convert to OpenAI format (pure function)"""
        return [
            {
                "role": msg["role"],
                "content": msg["content"],
                **msg.get("metadata", {})
            }
            for msg in messages
        ]
    
    @staticmethod
    def build_request_body(messages: list[Dict], config: Dict) -> Dict:
        """Build OpenAI request (pure function)"""
        return {
            "model": config["model"],
            "messages": messages,
            "stream": True
        }
    
    @staticmethod
    def process_chunk(native_chunk: Dict) -> str:
        """Process streaming chunk (pure function)"""
        delta = native_chunk.get("choices", [{}])[0].get("delta", {})
        return delta.get("content", "")
    
    @staticmethod
    def finalize_message(content: str, config: Dict) -> Dict:
        """Create final message (pure function)"""
        return {
            "role": "assistant",
            "content": content,
            "metadata": {}
        }
    
    @staticmethod
    async def stream_api(body: Dict, config: Dict) -> AsyncIterator[Dict]:
        """Make streaming API call (I/O operation)"""
        import httpx
        import json
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{config['base_url']}/chat/completions",
                json=body,
                headers={"Authorization": f"Bearer {config['api_key']}"},
                timeout=30.0
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        yield json.loads(data)
```

### Example 2: Provider Extension for Thinking Blocks

```python
# thinking_extension.py

name = "thinking_blocks"
version = "1.0.0"
target_provider = "openai"

def get_config_schema():
    return {
        "extract_thinking": {"type": "boolean", "default": True}
    }

def get_ui_elements():
    return [
        {
            "type": "checkbox",
            "key": "extract_thinking",
            "label": "Show Reasoning Process"
        }
    ]

def init(config):
    return {
        "config": config,
        "runtime_state": {
            "thinking_blocks": [],
            "current_thinking": ""
        }
    }

def update_state(state, updates):
    return {
        **state,
        "config": {**state["config"], **updates}
    }

def process_chunk(native_chunk, provider_state, extension_state):
    """Extract thinking blocks from chunks"""
    if not extension_state["config"]["extract_thinking"]:
        return "", extension_state
    
    # Check for thinking block markers
    delta = native_chunk.get("choices", [{}])[0].get("delta", {})
    content = delta.get("content", "")
    
    # Simple example: detect <thinking>...</thinking> tags
    if "<thinking>" in content:
        new_state = {
            **extension_state,
            "runtime_state": {
                **extension_state["runtime_state"],
                "in_thinking": True
            }
        }
        return "", new_state
    
    if extension_state["runtime_state"].get("in_thinking"):
        if "</thinking>" in content:
            # End of thinking block
            thinking = extension_state["runtime_state"]["current_thinking"]
            new_state = {
                **extension_state,
                "runtime_state": {
                    **extension_state["runtime_state"],
                    "thinking_blocks": extension_state["runtime_state"]["thinking_blocks"] + [thinking],
                    "current_thinking": "",
                    "in_thinking": False
                }
            }
            return "", new_state
        else:
            # Accumulate thinking content
            new_state = {
                **extension_state,
                "runtime_state": {
                    **extension_state["runtime_state"],
                    "current_thinking": extension_state["runtime_state"]["current_thinking"] + content
                }
            }
            return "", new_state
    
    return "", extension_state

def enhance_final_message(message, metadata, state):
    """Add thinking blocks to metadata"""
    thinking_blocks = state["runtime_state"]["thinking_blocks"]
    
    if thinking_blocks:
        enhanced_metadata = {
            **metadata,
            "thinking_blocks": thinking_blocks
        }
        return message, enhanced_metadata
    
    return message, metadata
```

### Example 3: Web Search Feature with Citations

```python
# web_search_feature.py

name = "web_search"
version = "1.0.0"

def get_config_schema():
    return {
        "web_search_enabled": {"type": "boolean", "default": False},
        "max_results": {"type": "integer", "default": 5}
    }

def get_ui_elements():
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

def init(config):
    return {
        "config": config,
        "capabilities": ["web_search"],
        "runtime_state": {}
    }

def update_state(state, updates):
    return {
        **state,
        "config": {**state["config"], **updates}
    }

def can_handle(capability_id, state):
    return (
        capability_id == "web_search" and
        state["config"]["web_search_enabled"]
    )

def modify_request_body(body, state):
    """Add search parameters to request"""
    if not state["config"]["web_search_enabled"]:
        return body
    
    return {
        **body,
        "search": {
            "enabled": True,
            "max_results": state["config"]["max_results"]
        }
    }

def process_final_message(message, conversation_state, state):
    """Extract and format citations from metadata"""
    if "citations" not in message.get("metadata", {}):
        return message
    
    citations = message["metadata"]["citations"]
    
    # Add citation markers to content
    content = message["content"]
    for i, citation in enumerate(citations, 1):
        content += f"\n[{i}] {citation['title']}: {citation['url']}"
    
    return {
        **message,
        "content": content,
        "metadata": {
            **message.get("metadata", {}),
            "formatted_citations": True
        }
    }

def format_display(display, message, state):
    """Enhance display with citation UI"""
    citations = message.get("metadata", {}).get("citations", [])
    
    if citations:
        return {
            **display,
            "citations": citations,
            "has_citations": True
        }
    
    return display
```

### Example 4: File Reader Tool Plugin

```python
# file_reader_tool.py
import os

name = "file_reader"
version = "1.0.0"

def get_config_schema():
    return {
        "allowed_paths": {
            "type": "array",
            "items": {"type": "string"},
            "default": ["."],
            "description": "Allowed base paths for file reading"
        },
        "max_file_size": {
            "type": "integer",
            "default": 1048576,  # 1MB
            "description": "Maximum file size in bytes"
        }
    }

def get_ui_elements():
    return [
        {
            "type": "text",
            "key": "allowed_paths",
            "label": "Allowed Paths (comma-separated)"
        }
    ]

def init(config):
    return {
        "config": config,
        "runtime_state": {}
    }

def update_state(state, updates):
    return {
        **state,
        "config": {**state["config"], **updates}
    }

def get_tool_schemas(state):
    """Return tool definition for LLM"""
    return [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read contents of a text file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to read"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        }
    ]

def execute_tool(tool_name, arguments, state):
    """Execute file read operation"""
    if tool_name != "read_file":
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}"
        }
    
    file_path = arguments.get("file_path")
    
    # Security: Check if path is allowed
    allowed_paths = state["config"]["allowed_paths"]
    if not any(file_path.startswith(base) for base in allowed_paths):
        return {
            "success": False,
            "error": f"Access denied: {file_path} not in allowed paths"
        }
    
    # Check file size
    try:
        file_size = os.path.getsize(file_path)
        if file_size > state["config"]["max_file_size"]:
            return {
                "success": False,
                "error": f"File too large: {file_size} bytes"
            }
    except OSError as e:
        return {
            "success": False,
            "error": f"Cannot access file: {str(e)}"
        }
    
    # Read file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "success": True,
            "result": content
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error reading file: {str(e)}"
        }

def format_tool_result(result, state):
    """Format result for LLM"""
    if result["success"]:
        return f"File contents:\n{result['result']}"
    else:
        return f"Error: {result['error']}"
```

## Core SDK Protocol

### Core SDK Interface

**IMPORTANT: Functional Architecture**

The Core SDK follows pure functional programming principles:
- **AgentCore** stores only the processing pipeline (registered plugins)
- **Session** is an immutable dataclass (pure data, no methods)
- **Config** is managed by the application layer
- All transformations are pure functions that return new objects
- The application manages state (sessions, config)

```python
@dataclass(frozen=True)
class Session:
    """
    Immutable session data structure
    Pure data container with no transformation logic
    """
    session_id: str
    messages: tuple[Message, ...]  # Immutable tuple
    metadata: dict = field(default_factory=dict)


class AgentCore:
    """
    Stateless processing pipeline for AI Agent Platform
    
    Stores only the plugin pipeline (processing logic), not runtime state.
    All methods are pure functions that take session/config and return new objects.
    """
    
    # ========================================
    # Initialization
    # ========================================
    
    def __init__(self):
        """
        Initialize core with empty plugin pipeline
        No configuration or state storage
        """
    
    # ========================================
    # Plugin Management (Pipeline Definition)
    # ========================================
    
    def register_provider(self, plugin_class: type) -> None:
        """Register provider plugin class"""
    
    def register_feature(self, plugin_class: type) -> None:
        """Register feature plugin class"""
    
    def register_tool(self, plugin_class: type) -> None:
        """Register tool plugin class"""
    
    def get_ui_schema(self) -> dict:
        """Get combined UI schema from all registered plugins"""
    
    # ========================================
    # Pure Transformation Functions
    # ========================================
    
    def add_message(
        self,
        session: Session,
        role: str,
        content: str,
        metadata: dict = None
    ) -> Session:
        """
        Add message to session (returns new session)
        
        Args:
            session: Current session
            role: Message role
            content: Message content
            metadata: Optional metadata
            
        Returns:
            New session with added message
        """
    
    def send_request(
        self,
        session: Session,
        config: dict
    ) -> tuple[Session, dict]:
        """
        Send request and return new session with response
        
        Args:
            session: Current session
            config: Provider and feature configuration
            
        Returns:
            Tuple of (new_session, response_message)
        """
    
    def send_request_stream(
        self,
        session: Session,
        config: dict
    ) -> Iterator[dict | tuple[Session, dict]]:
        """
        Stream request and yield partials, then final session
        
        Args:
            session: Current session
            config: Provider and feature configuration
            
        Yields:
            Partial chunks: {"type": "partial", "content": "..."}
            Final result: {"type": "final", "session": new_session, "message": {...}}
        """
    
    async def send_request_stream_async(
        self,
        session: Session,
        config: dict
    ) -> AsyncIterator[dict | tuple[Session, dict]]:
        """Async version of send_request_stream"""
    
    # ========================================
    # Utility Functions
    # ========================================
    
    def get_tool_schemas(self, config: dict) -> list[dict]:
        """Get tool schemas from registered tool plugins"""
    
    def create_session(self, session_id: str = None) -> Session:
        """Create new empty session (convenience function)"""
    
    def export_session(self, session: Session, format: str = "json") -> str:
        """Export session to string"""
    
    def import_session(self, data: str, format: str = "json") -> Session:
        """Import session from string"""
```

### Data Types

```python
from typing import Literal, Tuple, Dict, Any, Optional
from dataclasses import dataclass, field

MessageRole = Literal["system", "user", "assistant", "tool"]

@dataclass(frozen=True)
class Message:
    """
    Immutable message structure representing a single conversation message.
    
    Attributes:
        role: Message role ("system", "user", "assistant", or "tool")
        content: Message content text
        metadata: Optional metadata dict containing tool_calls, tool_call_id, citations, etc.
    """
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass(frozen=True)
class Session:
    """
    Immutable session data structure (pure data container).
    
    Contains only data, no transformation logic. All transformations
    are performed by AgentCore functions that return new sessions.
    
    Attributes:
        session_id: Unique identifier for this session
        messages: Immutable tuple of messages
        metadata: Optional session-level metadata
    """
    session_id: str
    messages: Tuple[Message, ...] = field(default_factory=tuple)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

## Configuration System

### Configuration Structure

The application loads and resolves configuration from JSON files, then passes the final resolved config to Core.

**Important principles:**
- Configuration is a flat dictionary passed to plugins
- Each plugin defines its own config schema (via `get_config_schema()`)
- Plugin-specific config is mixed into the main config object
- Agent configuration has no mandatory keys (fully flexible)
- There is no configuration for tools or plugins enabled for an agent, it will be added later

```json
{
  "core": {
    "language": "python",
    "plugin_paths": ["./plugins", "~/.agent-plugins"],
    "log_level": "INFO"
  },
  
  "providers": {
    "openai": {
        "api_key": "${env:OPENAI_API_KEY}",
        "base_url": "https://api.openai.com/v1",
        "timeout": 30
    },
    "anthropic": {
        "api_key": "${file:~/.anthropic_key}",
        "base_url": "https://api.anthropic.com"
    }
  },
  
  "agents": {
    "default": {
      "provider": "openai",
      "model": "gpt-4o",
      "temperature": 0.7,
      "max_tokens": 4096,
      "web_search_enabled": true,
      "max_results": 5,
      "extract_thinking": true
    },
    
    "research_agent": {
      "provider": "openai",
      "model": "gpt-4-search",
      "api_key": "${env:OPENAI_RESEARCH_KEY}",
      "temperature": 0.3,
      "web_search_enabled": true,
      "max_results": 10
    }
  }
}
```

### Configuration Resolution

**Special Syntax:**
- `${env:VAR_NAME}` - Replace with environment variable
- `${file:path/to/file}` - Replace with file contents
- Agent-specific config overrides provider defaults

**Example Resolution:**
```json
// Before resolution
{
  "api_key": "${env:OPENAI_API_KEY}",
  "data": "${file:./prompt.txt}"
}

// After resolution (done by Application layer)
{
  "api_key": "sk-actual-key-value",
  "data": "System prompt from file..."
}
```

**Application Layer Responsibility:**
1. Load JSON config file
2. Resolve `${env:...}` references
3. Resolve `${file:...}` references
4. Merge provider defaults with agent-specific overrides
5. Pass final resolved flat dict to Core SDK

**Core SDK receives flat config dict:**
```python
# All plugin config mixed into single flat dict
# No nested structure, no mandatory keys
resolved_config = {
    "provider": "openai",
    "model": "gpt-4o",
    "api_key": "sk-resolved-actual-key",
    "temperature": 0.7,
    "web_search_enabled": True,
    "max_results": 5,
    "extract_thinking": True,
    # ... all resolved and flattened
}
```

**Config is passed to every plugin method:**
```python
# Provider receives full config
provider.call_api(body, config)

# Feature receives full config
feature.transform_messages(messages, config)

# Each plugin extracts what it needs
class DummyFeature:
    @staticmethod
    def transform_messages(messages, config):
        # Extract only what this feature needs
        if config.get("web_search_enabled"):
            max_results = config.get("max_results", 5)
            # ...
```

## Example Usage

### Example 1: Basic Low-Level API Usage (Python)

```python
from agent_core import AgentCore
from plugins import OpenAIProvider

# Initialize core (stateless pipeline)
core = AgentCore()

# Register provider (just the class, no config)
core.register_provider(OpenAIProvider)

# Application manages config
config = {
    "model": "gpt-4o",
    "api_key": "sk-..."
}

# Application creates and manages session (immutable)
session = core.create_session()

# Add messages (returns new session each time)
session = core.add_message(session, "system", "You are a helpful assistant.")
session = core.add_message(session, "user", "What is 2+2?")

# Send request (returns new session with response)
session, response = core.send_request(session, config)
print(response["content"])  # "4"

# Messages now include the response
print(len(session.messages))  # 3

# Add another message (functional - returns new session)
session = core.add_message(session, "user", "What about 3+3?")

# Send again
session, response = core.send_request(session, config)
print(response["content"])  # "6"
```

### Example 2: Streaming with Low-Level API

```python
from agent_core import AgentCore
from plugins import OpenAIProvider

# Core stores only pipeline
core = AgentCore()
core.register_provider(OpenAIProvider)

# Application manages config and session
config = {"model": "gpt-4o", "api_key": "sk-..."}
session = core.create_session()
session = core.add_message(session, "user", "Write a short poem")

# Stream response (functional - returns new session at end)
for chunk in core.send_request_stream(session, config):
    if chunk["type"] == "partial":
        print(chunk["content"], end="", flush=True)
    elif chunk["type"] == "final":
        # Get new session with response message
        session = chunk["session"]
        print("\n[Done]")
```

### Example 3: Tool Calls (Application-Level Logic)

```python
from agent_core import AgentCore
from plugins import OpenAIProvider, FileReaderTool
import json

core = AgentCore()
core.register_provider(OpenAIProvider)
core.register_tool(FileReaderTool)

# Application manages config
config = {
    "model": "gpt-4",
    "api_key": "sk-...",
    "allowed_paths": ["."]  # Tool config mixed in
}

session = core.create_session()
session = core.add_message(session, "user", "Read the contents of README.md")

# Application handles tool loop
max_iterations = 5
for i in range(max_iterations):
    # Send request (functional)
    session, response = core.send_request(session, config)
    
    # Check for tool calls
    tool_calls = response.get("metadata", {}).get("tool_calls", [])
    
    if not tool_calls:
        # No tools, we're done
        print("Assistant:", response["content"])
        break
    
    # Execute tools (application responsibility)
    for tool_call in tool_calls:
        tool_name = tool_call["function"]["name"]
        arguments = json.loads(tool_call["function"]["arguments"])
        
        # Execute tool (stateless - pass config)
        result = FileReaderTool.execute_tool(tool_name, arguments, config)
        formatted = FileReaderTool.format_tool_result(result, config)
        
        # Add tool result as message (functional)
        session = core.add_message(
            session,
            "tool",
            formatted,
            metadata={
                "tool_call_id": tool_call["id"],
                "name": tool_name
            }
        )
    
    # Loop continues with tool results in conversation
```

### Example 4: Message Manipulation

```python
from agent_core import AgentCore
from plugins import OpenAIProvider

core = AgentCore()
core.register_provider(OpenAIProvider)

config = {"model": "gpt-4", "api_key": "sk-..."}

session = core.create_session()

# Add multiple messages (functional chaining)
session = core.add_message(session, "system", "You are a helpful assistant.")
session = core.add_message(session, "user", "Hello")
session = core.add_message(session, "assistant", "Hi! How can I help?")
session = core.add_message(session, "user", "What's the weather?")

# Remove last message (functional)
from agent_core.types import Session
session = Session(
    session_id=session.session_id,
    messages=session.messages[:-1],
    metadata=session.metadata
)

# Add different message
session = core.add_message(session, "user", "Tell me a joke")

# Send request with modified history
session, response = core.send_request(session, config)

# Clear conversation and start fresh (functional)
session = Session(
    session_id=session.session_id,
    messages=(),
    metadata=session.metadata
)
session = core.add_message(session, "user", "New conversation")
```

### Example 5: Configuration Updates (Application Managed)

```python
from agent_core import AgentCore
from plugins import OpenAIProvider, WebSearchFeature

core = AgentCore()

# Register plugins (no config)
core.register_provider(OpenAIProvider)
core.register_feature(WebSearchFeature)

session = core.create_session()

# Application manages config
config1 = {
    "model": "gpt-4o",
    "api_key": "sk-...",
    "web_search_enabled": False
}

# Initial request without search
session = core.add_message(session, "user", "Latest AI news")
session, response = core.send_request(session, config1)

# User enables search in UI - application updates config
config2 = {
    **config1,
    "web_search_enabled": True,
    "max_results": 10
}

# Next request uses search
session = core.add_message(session, "user", "More AI news")
session, response = core.send_request(session, config2)
```

### Example 6: Full Application with Tool Loop (Python Backend)

```python
from fastapi import FastAPI, WebSocket
from agent_core import AgentCore
from plugins import openai_provider, web_search_feature, file_reader_tool
import json

app = FastAPI()

# Load and resolve config (application responsibility)
import os

def resolve_config(config):
    """Resolve ${env:...} and ${file:...} references"""
    resolved = {}
    for key, value in config.items():
        if isinstance(value, str):
            if value.startswith("${env:"):
                var_name = value[6:-1]
                resolved[key] = os.getenv(var_name)
            elif value.startswith("${file:"):
                file_path = value[7:-1]
                with open(os.path.expanduser(file_path)) as f:
                    resolved[key] = f.read().strip()
            else:
                resolved[key] = value
        else:
            resolved[key] = value
    return resolved

# Load config from file
with open("config.json") as f:
    config = json.load(f)

# Initialize core
core = AgentCore()

# Register plugins (just classes, no config)
core.register_provider(openai_provider)
core.register_feature(web_search_feature)
core.register_tool(file_reader_tool)

# Application resolves and merges config
def get_agent_config(agent_name):
    """Resolve and merge config for an agent."""
    agent_config = config["agents"][agent_name]
    provider_name = agent_config.get("provider", "openai")
    
    # Start with provider defaults
    merged = resolve_config(config["providers"]["defaults"][provider_name].copy())
    
    # Merge agent-specific config (flat structure)
    merged.update(resolve_config(agent_config))
    
    return merged

# Application manages sessions
sessions = {}

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    if session_id not in sessions:
        sessions[session_id] = core.create_session(session_id)
    session = sessions[session_id]
    
    # Application manages config
    agent_config = get_agent_config("default")
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "message":
                # Add user message (functional)
                session = core.add_message(session, "user", data["content"])
                
                # Tool loop (application logic)
                max_iterations = 5
                for i in range(max_iterations):
                    # Stream response (functional - pass config)
                    full_message = None
                    async for chunk in core.send_request_stream_async(session, agent_config):
                        if chunk["type"] == "partial":
                            await websocket.send_json({
                                "type": "partial",
                                "content": chunk["content"]
                            })
                        elif chunk["type"] == "final":
                            session = chunk["session"]
                            full_message = chunk["message"]
                    
                    # Check for tool calls
                    tool_calls = full_message.get("metadata", {}).get("tool_calls", [])
                    
                    if not tool_calls:
                        # Done
                        await websocket.send_json({
                            "type": "final",
                            "message": full_message
                        })
                        break
                    
                    # Execute tools
                    for tool_call in tool_calls:
                        tool_name = tool_call["function"]["name"]
                        arguments = json.loads(tool_call["function"]["arguments"])
                        
                        # Notify frontend
                        await websocket.send_json({
                            "type": "tool_call",
                            "name": tool_name,
                            "arguments": arguments
                        })
                        
                        # Execute (stateless - just pass config)
                        result = file_reader_tool.execute_tool(
                            tool_name,
                            arguments,
                            agent_config
                        )
                        formatted = file_reader_tool.format_tool_result(
                            result,
                            agent_config
                        )
                        
                        # Add tool result (functional)
                        session = core.add_message(
                            session,
                            "tool",
                            formatted,
                            metadata={
                                "tool_call_id": tool_call["id"],
                                "name": tool_name
                            }
                        )
                    
                    # Continue loop with tool results
            
            elif data["type"] == "update_config":
                # Application updates its config
                agent_config = {**agent_config, **data["updates"]}
                sessions[session_id] = session  # Store updated session
    
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()
```

## Documentation Types

**Auto-Generated (from docstrings):**
- API Reference: Classes, functions, parameters, return types
- Tools: Sphinx (Python), TypeDoc (TypeScript), JSDoc (JavaScript)
- Format: Google-style, NumPy-style, or reStructuredText docstrings

**Manually Written:**
- Guides and tutorials
- Architecture documentation
- Examples and how-tos
- Getting started
- Design decisions

## Implementation Roadmap

> **Note:** This roadmap is a living document and will evolve during development. Timelines, features, and priorities may change based on implementation discoveries, user feedback, and technical constraints.

> **Testing & Documentation Standard:** Every item in this roadmap must include tests and documentation unless explicitly noted otherwise. This includes: unit tests for pure functions, docstrings for all public APIs, type hints/definitions, and at least one runnable example. Items marked with specific testing or documentation needs indicate additional requirements beyond the standard.

### Stage 1: Working MVP (Core + Basic UI)

**Goal:** Create a functional system we can use ourselves immediately.

**Core SDK:**
- [ ] Implement basic data types (Message, ConversationState, PluginState)
- [ ] Create plugin wrapper and passthrough adapter
- [ ] Build session management with low-level message API
- [ ] Implement send_request, send_request_stream
- [ ] Create plugin registry and discovery
- [ ] Integration tests for complete request/response cycle
- [ ] API reference documentation

**Plugins (One of Each Type):**
- [ ] Openrouter provider plugin (basic, working streaming)
- [ ] Thinking blocks provider extension for openrouter
- [ ] Web search feature plugin (basic version)
- [ ] File reader tool plugin
- [ ] Plugin development quick start guide (tutorial showing how to create each type)

**Application Layer:**
- [ ] Configuration loading with ${env:...} and ${file:...} resolution
- [ ] Basic FastAPI/Express server
- [ ] WebSocket handler for streaming
- [ ] Tool execution loop (application-level)
- [ ] Session management
- [ ] Integration tests for WebSocket streaming
- [ ] Configuration guide with example config files

**Frontend:**
- [ ] Basic React UI
- [ ] Message list display
- [ ] Text input for user messages
- [ ] Display streaming partials
- [ ] Replace with final message
- [ ] Show tool calls in progress
- [ ] Basic styling
- [ ] Component tests for message handling

**Configuration:**
- [ ] JSON config file support
- [ ] No UI configuration yet (manual JSON editing)
- [ ] Support multiple agent configurations
- [ ] Example config.json with inline comments

**Documentation:**
- [ ] README with setup instructions and quick start (5 minutes to working chat)
- [ ] Basic architecture diagram
- [ ] Example: basic message manipulation
- [ ] Example: streaming vs non-streaming
- [ ] Example: tool execution flow
- [ ] Troubleshooting guide

**Documentation Tooling:**
- [ ] Sphinx setup for Python (with autodoc extension)
- [ ] TypeDoc/JSDoc setup for JavaScript/TypeScript
- [ ] Auto-generated API reference published to docs site
- [ ] Docstring format guide for contributors

**Testing:**
- [ ] CI/CD pipeline setup (run on Python 3.9+, test coverage reporting)
- [ ] End-to-end test: user message → streaming → tool call → response
- [ ] Manual testing checklist

**Deliverable:** A working chat interface where we can:
- Send messages and get streaming responses
- See tool calls happen automatically
- Switch between different agent configs
- Use it for actual work
- **All features documented and tested**

### Stage 2: Production Polish (More Plugins + Features)

**Providers:**
- [ ] Anthropic provider
- [ ] Google Gemini provider
- [ ] Local model provider (Ollama)
- [ ] Provider capability detection
- [ ] Provider comparison guide

**Features:**
- [ ] Advanced web search with better citation handling
- [ ] Content filtering
- [ ] Context window management (smart trimming)
- [ ] Message transformation utilities
- [ ] Feature composition guide (using multiple features together)

**Tools:**
- [ ] Web search tool
- [ ] Code execution tool (sandboxed)
- [ ] API call tool
- [ ] Tool development guide (security considerations, best practices)

**Provider Extensions:**
- [ ] Citation extraction
- [ ] Token counter
- [ ] Reasoning trace parser

**Frontend:**
- [ ] Markdown rendering for messages
- [ ] Code syntax highlighting
- [ ] Better citation display
- [ ] Tool execution visualization
- [ ] Message editing
- [ ] Conversation branching
- [ ] Component tests with Storybook for visual documentation
- [ ] Accessibility tests
- [ ] Frontend user guide

**Configuration:**
- [ ] UI for plugin configuration (no more manual JSON)
- [ ] Live config updates
- [ ] Config presets/templates
- [ ] Tests for state update propagation
- [ ] User guide for configuration UI

**Testing:**
- [ ] Plugin test utilities and mock provider for plugin testing
- [ ] End-to-end tests for full conversation flows and multi-agent scenarios
- [ ] Performance benchmarks (baseline documented, regression tests)
- [ ] Test coverage: 90%+ for core, 80%+ for plugins

**Documentation:**
- [ ] Complete plugin development guide (step-by-step for each type, best practices, common pitfalls)
- [ ] Architecture deep-dive (design decisions, component diagrams, data flow)
- [ ] Complete API reference (examples for every public method)
- [ ] Example applications: research assistant, code review bot, customer support agent (all documented and tested)
- [ ] Video tutorials (getting started, building first plugin, advanced features)

### Stage 3: Cross-Language Support

**Core:**
- [ ] JavaScript/TypeScript Core SDK implementation
- [ ] Feature parity with Python core
- [ ] Subprocess adapter implementation
- [ ] JSON-RPC protocol
- [ ] Plugin wrapper as subprocess server
- [ ] Cross-language integration tests (Python core + JS plugin, JS core + Python plugin)
- [ ] Protocol compliance tests

**Testing:**
- [ ] Test all plugin types in both directions (Python↔JavaScript)
- [ ] Performance benchmarks: native vs cross-language overhead
- [ ] Compatibility test matrix documenting all combinations

**Documentation:**
- [ ] Cross-language plugin guide (when to use, performance considerations, debugging)
- [ ] JSON-RPC protocol specification
- [ ] Performance characteristics document with benchmarks
- [ ] Migration guides (Python plugin → JavaScript, JavaScript plugin → Python)
- [ ] Example: creating a cross-language plugin

### Stage 4: Ecosystem & Distribution

**Plugin System:**
- [ ] Plugin marketplace/registry
- [ ] Plugin discovery and installation CLI tool
- [ ] Version management with semantic versioning
- [ ] Plugin dependencies with dependency resolution
- [ ] Security scanning process
- [ ] Plugin submission guide

**Distribution:**
- [ ] PyPI package with installation guide and release checklist
- [ ] npm package with installation guide and release checklist
- [ ] Docker images with deployment guide
- [ ] Pre-built binaries
- [ ] Docker Compose examples

**Community:**
- [ ] Plugin template repositories (all types, fully documented with example tests)
- [ ] Example applications (customer support bot, research assistant, code review tool, data analysis agent, meeting summarizer)
- [ ] Tutorial series (beginner to advanced)
- [ ] Community guidelines (code of conduct, contribution guide, documentation standards, testing requirements)

**Advanced Features:**
- [ ] Multi-modal support (images, audio) with guide and examples for each modality
- [ ] Conversation persistence with serialization and database integration tests
- [ ] Cloud deployment guides (AWS, GCP, Azure, Kubernetes - all tested)
- [ ] Monitoring and observability with metrics collection and logging guide

> **Note:** Stage completion requires all tests passing with adequate coverage, all features documented, examples updated and tested, API reference current, and any migration guides written for breaking changes.

---

**Testing & Documentation Standards:**

All contributions must include:
1. **Tests**: Unit and integration tests for new functionality
2. **Documentation**: Docstrings, README updates, examples
3. **Type Hints**: Python type hints or TypeScript definitions
4. **Examples**: At least one executable example
5. **Coverage**: Minimum 80% test coverage for new code

These are not optional—they are part of the definition of "done" for any feature.

## Project Structure

```
agent-platform/
├── core/
│   ├── python/
│   │   ├── agent_core/
│   │   │   ├── __init__.py
│   │   │   ├── core.py           # AgentCore, Session
│   │   │   ├── types.py          # Data types
│   │   │   ├── plugin/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── wrapper.py    # PluginWrapper
│   │   │   │   ├── adapter.py    # Passthrough/Subprocess adapters
│   │   │   │   └── protocol.py   # JSON-RPC protocol
│   │   │   ├── pipeline.py       # Transformation pipeline
│   │   │   └── session.py        # Session management
│   │   ├── tests/
│   │   │   ├── test_core.py
│   │   │   ├── test_session.py
│   │   │   ├── test_plugins.py
│   │   │   └── test_integration.py
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   └── javascript/
│       ├── src/
│       │   ├── core.ts
│       │   ├── types.ts
│       │   ├── plugin/
│       │   │   ├── wrapper.ts
│       │   │   ├── adapter.ts
│       │   │   └── protocol.ts
│       │   ├── pipeline.ts
│       │   └── session.ts
│       ├── tests/
│       ├── package.json
│       ├── tsconfig.json
│       └── README.md
│
├── plugins/
│   ├── providers/
│   │   ├── openai/
│   │   │   ├── python/
│   │   │   │   ├── openai_provider.py
│   │   │   │   ├── tests/
│   │   │   │   └── README.md
│   │   │   └── javascript/
│   │   │       ├── src/openai-provider.ts
│   │   │       ├── tests/
│   │   │       └── README.md
│   │   ├── anthropic/
│   │   ├── google/
│   │   └── ollama/
│   │
│   ├── extensions/
│   │   ├── thinking-blocks/
│   │   │   ├── python/thinking_extension.py
│   │   │   └── javascript/src/thinking-extension.ts
│   │   ├── citations/
│   │   └── token-counter/
│   │
│   ├── features/
│   │   ├── web-search/
│   │   │   ├── python/web_search_feature.py
│   │   │   └── javascript/src/web-search-feature.ts
│   │   ├── content-filter/
│   │   └── context-manager/
│   │
│   └── tools/
│       ├── file-reader/
│       │   ├── python/file_reader_tool.py
│       │   └── javascript/src/file-reader-tool.ts
│       ├── web-search-tool/
│       ├── calculator/
│       └── code-executor/
│
├── applications/
│   ├── web-ui/
│   │   ├── backend/
│   │   │   ├── main.py             # FastAPI server
│   │   │   ├── config_loader.py    # Config resolution
│   │   │   ├── websocket.py        # WebSocket handler
│   │   │   └── requirements.txt
│   │   ├── frontend/
│   │   │   ├── src/
│   │   │   │   ├── App.jsx
│   │   │   │   ├── components/
│   │   │   │   │   ├── MessageList.jsx
│   │   │   │   │   ├── MessageInput.jsx
│   │   │   │   │   ├── ConfigPanel.jsx
│   │   │   │   │   └── ToolCallDisplay.jsx
│   │   │   │   └── hooks/
│   │   │   │       └── useWebSocket.js
│   │   │   ├── package.json
│   │   │   └── vite.config.js
│   │   ├── config.json.example
│   │   └── docker-compose.yml
│   │
│   ├── cli/
│   │   ├── agent_cli.py
│   │   └── README.md
│   │
│   └── examples/
│       ├── basic_usage.py
│       ├── tool_calling.py
│       ├── streaming.py
│       └── multi_agent.py
│
├── docs/
│   ├── README.md
│   ├── architecture.md
│   ├── getting-started.md
│   ├── configuration.md
│   ├── plugin-development/
│   │   ├── overview.md
│   │   ├── provider-plugin.md
│   │   ├── provider-extension.md
│   │   ├── feature-plugin.md
│   │   └── tool-plugin.md
│   ├── api-reference/
│   │   ├── core-sdk.md
│   │   ├── session.md
│   │   └── plugin-protocols.md
│   └── examples/
│       ├── simple-chatbot.md
│       ├── research-agent.md
│       └── code-assistant.md
│
├── .gitignore
├── LICENSE
└── README.md
```

## Success Criteria

### Stage 1 Success (MVP)
- ✅ Can have a conversation with an LLM
- ✅ Streaming works and displays correctly
- ✅ Tool calls work automatically
- ✅ Can configure via JSON file
- ✅ Tests pass for Core SDK
- ✅ We use it ourselves for actual work

### Stage 2 Success (Production)
- ✅ Support 3+ providers
- ✅ 10+ plugins available
- ✅ Markdown rendering works
- ✅ Plugin configuration via UI
- ✅ Comprehensive documentation
- ✅ Others can use it without our help

### Stage 3 Success (Cross-Language)
- ✅ JavaScript core works
- ✅ Can use Python plugins from JavaScript core
- ✅ Can use JavaScript plugins from Python core
- ✅ Performance is acceptable for cross-language

### Stage 4 Success (Ecosystem)
- ✅ Plugin marketplace exists
- ✅ Available on PyPI and npm
- ✅ Community contributing plugins
- ✅ Multiple example applications
- ✅ Growing user base

---

**Living Document Notice:** This project plan represents our current understanding and intentions. As we build and learn, we will update this document to reflect new insights, changed priorities, and evolved designs. Implementation details, API designs, and architectural decisions are subject to change based on real-world usage, performance requirements, and developer feedback.