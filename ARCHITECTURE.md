# AI Agent Platform - Architecture

This document describes the architecture and core design principles of the AI Agent Platform.

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
│  - Provider wrapper holds shared provider state        │
│  - Extensions/features operate on shared state         │
│  - Tools hold their own state                          │
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
Core → Apply stateless transforms: Provider Extensions.to_native_messages(messages, native_messages)
  ↓
Core → Apply stateless transforms: Features.to_native_messages(messages, native_messages)
  ↓
Core → Provider.initialize_request(native_messages) → shared state
  ↓
Core → Each Feature.initialize_request(native_messages, state) → shared state
  ↓
Provider.stream_api(native_messages) → yields native chunks
  ↓
Provider.process_chunk + Extensions.process_chunk(state) → Core (partial/final/native)
  ↓
Core → Application → Frontend (stream partials)
  ↓
Provider.finalize(native_messages, state) → final/native outputs
  ↓
Core → Provider Extensions.finalize(final_messages, native_messages, state)
  ↓
Core → Features.finalize(final_messages, native_messages, state)
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

Here's the proposed directory structure for the agent platform (actual files may vary)

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
