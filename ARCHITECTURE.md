# AI Agent Platform - Architecture

This document describes the architecture and core design principles of the AI Agent Platform.

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

Partial messages: streamed token-by-token during generation. Final messages: complete, with metadata (citations, etc.). Frontend shows partials, replaces with final when done. Partials are distinct `PartialMessage` objects `{role, content, metadata}`.

**Provider Extension Model:**

Extensions enhance provider streaming. They can observe and transform provider outputs per-chunk and at finalize.

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

## System Architecture

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
Application → Core SDK (send_request or send_request_stream)
  ↓
Core → Provider.to_native_messages(messages)
  ↓
Core → Provider.initialize_request(native_messages)
  ↓
Core → Each Feature.initialize_request(native_messages)
  ↓
Provider.stream_api(native_messages) → yields native chunks
  ↓
Provider.process_chunk + Extensions.process_chunk → Core (partial/final/native)
  ↓
Core → Application → Frontend (stream partials)
  ↓
Provider.finalize (optional) → final/native outputs
  ↓
Core → Features.finalize(messages, {final_messages, native_messages})
  ↓
Core → Application (final messages, may include tool calls)
  ↓
Application: Decides to execute tools (application logic)
  ↓
Application → Core SDK (add tool results)
  ↓
Application → Core SDK (send_request/send_request_stream again)
  ↓
[Loop continues until no more tool calls]
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

**Example configuration structure:**

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

**Core SDK receives flat config:**

All plugin config mixed into single flat dictionary with no nested structure and no mandatory keys.

**Config is passed to every plugin method:**

Each plugin extracts what it needs from the flat config dict.

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
