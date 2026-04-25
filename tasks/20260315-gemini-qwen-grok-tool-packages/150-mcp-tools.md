# 150 — MCP Tool Plugins

Short description: Implement Model Context Protocol (MCP) tool support with one shared helper package and five vendor-specific tool plugins (Gemini, Qwen, Grok, Kimi, Codex), each matching their respective CLI's tool naming, schema handling, and result formatting.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On:
- `tasks/20260315-gemini-qwen-grok-tool-packages/140-async-tool-initialization.md`

## Goal

Enable the platform to discover and use tools from MCP (Model Context Protocol) servers, with vendor-specific plugins that match the exact tool naming conventions, schema sanitization, and response formatting of each major CLI implementation.

## Background

MCP is an open protocol for connecting AI models to external tools and resources. Major CLIs (Gemini CLI, Qwen Code, Grok CLI, Codex CLI, Kimi CLI) all support MCP but with different:

1. **Tool naming conventions** - How MCP tools are prefixed when exposed to the LLM
2. **Schema sanitization** - How MCP input schemas are adapted for provider compatibility
3. **Result formatting** - How MCP tool results are formatted for the LLM
4. **Server lifecycle** - How local stdio servers are started and managed

This task implements MCP support through:
- A shared helper package (not a plugin itself)
- Five vendor-specific tool plugins

## Package Structure

```
plugins/
├── mcp-shared/                    # Shared MCP infrastructure (NOT a plugin package)
│   pyproject.toml
│   src/mcp_shared/
│     __init__.py
│     client_manager.py            # MCP client lifecycle management
│     server_config.py             # Server configuration loading
│     schema_adapter.py            # JSON Schema sanitization helpers
│     content_converter.py         # MCP content blocks -> provider content parts
│     cache.py                     # Tool schema caching
│     discovery.py                 # Background tool discovery
│     errors.py                    # MCP-specific exceptions
│
├── gemini-tools/                  # Existing package - add MCP support
│   src/gemini_tools/
│     ...
│     mcp_tool.py                  # Gemini-style MCP tool plugin
│
├── qwen-tools/                    # Existing package - add MCP support
│   src/qwen_tools/
│     ...
│     mcp_tool.py                  # Qwen-style MCP tool plugin
│
├── grok-tools/                    # Existing package - add MCP support
│   src/grok_tools/
│     ...
│     mcp_tool.py                  # Grok-style MCP tool plugin
│
├── kimi-tools/                    # Existing package - add MCP support
│   src/kimi_tools/
│     ...
│     mcp_tool.py                  # Kimi-style MCP tool plugin
│
└── codex-tools/                   # NEW package
    pyproject.toml
    src/codex_tools/
      __init__.py
      mcp_tool.py                  # Codex-style MCP tool plugin
      tool_names.py                # Codex tool name constants
```

## Requirements

### Shared Helper Package (`plugins/mcp-shared/`)

#### Client Manager

```python
class MCPClientManager:
    """Manages MCP server connections and tool discovery.
    
    Handles:
    - Starting stdio servers (command + args + env)
    - Connecting to HTTP/SSE servers
    - Discovering tools via list_tools()
    - Caching discovered schemas
    - Executing tool calls
    """
    
    async def initialize(
        self,
        server_configs: Dict[str, MCPServerConfig],
        context: Dict[str, Any],
    ) -> None:
        """Connect to servers and discover tools.
        
        Uses cache if available to avoid re-connecting on every startup.
        """
    
    async def list_tools(self) -> List[MCPToolInfo]:
        """Return all discovered tools from all servers."""
    
    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> MCPToolResult:
        """Execute a tool call on the appropriate server."""
    
    async def cleanup(self) -> None:
        """Disconnect all servers."""
```

#### Server Configuration

```python
@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server."""
    name: str
    # Stdio transport
    command: Optional[str] = None
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    cwd: Optional[str] = None
    # HTTP transport
    url: Optional[str] = None
    http_url: Optional[str] = None  # Streamable HTTP
    transport_type: Optional[str] = None  # "stdio", "sse", "http"
    # Auth
    headers: Dict[str, str] = field(default_factory=dict)
    auth: Optional[str] = None  # "oauth"
    # Timeouts
    timeout: Optional[int] = None


def load_mcp_config(config_path: Path) -> Dict[str, MCPServerConfig]:
    """Load MCP server configs from JSON file."""
```

#### Schema Adapter

```python
def sanitize_mcp_schema(
    schema: Dict[str, Any],
    *,
    style: str = "default",  # "gemini", "qwen", "grok", "kimi", "codex"
) -> Dict[str, Any]:
    """Sanitize MCP input schema for provider compatibility.
    
    Common sanitizations:
    - Ensure "type" field exists (default "string")
    - Ensure "properties" exists for objects
    - Handle "integer" -> "number" normalization
    - Remove unsupported JSON Schema keywords
    """
```

#### Content Converter

```python
def convert_mcp_content(
    content: List[Dict[str, Any]],
    *,
    style: str = "default",
) -> List[Dict[str, Any]]:
    """Convert MCP content blocks to provider-native content parts.
    
    Handles:
    - text -> text part
    - image -> inline_data or image_url
    - audio -> inline_data or audio_url
    - resource -> text or inline_data
    - resource_link -> text reference
    """
```

### Vendor-Specific Plugins

Each vendor plugin implements a single `ToolPlugin` class that:
1. Uses `initialize()` (async) to discover MCP tools
2. Returns schemas with vendor-specific naming in `get_tool_schemas()`
3. Formats results with vendor-specific style in `format_tool_result()`

#### Gemini MCP Tool Plugin

**Naming**: `server__tool` (double underscore)

Example: MCP tool `read_file` from server `filesystem` becomes `filesystem__read_file`

```python
# plugins/gemini-tools/src/gemini_tools/mcp_tool.py

class GeminiMCPToolPlugin(ToolPlugin):
    """Gemini-style MCP tool plugin.
    
    Naming: server__tool (double underscore, no "mcp" prefix)
    Schema: Gemini-style sanitization (LenientJsonSchemaValidator pattern)
    Format: Gemini-style result formatting
    """
    
    name = "gemini_mcp_tools"
    version = "0.1.0"
    
    async def initialize(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        # Load server configs
        # Create MCPClientManager
        # Discover tools
        # Store in state
    
    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Return schemas with server__tool naming
        # Apply Gemini-style schema sanitization
```

#### Qwen MCP Tool Plugin

**Naming**: `mcp__server__tool` (triple underscore with mcp prefix)

Example: MCP tool `read_file` from server `filesystem` becomes `mcp__filesystem__read_file`

```python
# plugins/qwen-tools/src/qwen_tools/mcp_tool.py

class QwenMCPToolPlugin(ToolPlugin):
    """Qwen-style MCP tool plugin.
    
    Naming: mcp__server__tool (mcp prefix, triple underscore)
    Schema: Qwen-style sanitization (properties enforcement)
    Format: Qwen-style result formatting
    """
```

#### Grok MCP Tool Plugin

**Naming**: `mcp__server__tool` (same as Qwen)

```python
# plugins/grok-tools/src/grok_tools/mcp_tool.py

class GrokMCPToolPlugin(ToolPlugin):
    """Grok-style MCP tool plugin.
    
    Naming: mcp__server__tool
    Schema: Minimal sanitization (pass-through mostly)
    Format: Grok-style formatting
    """
```

#### Kimi MCP Tool Plugin

**Naming**: `tool` (bare name, no prefix!)

Note: Kimi CLI exposes MCP tools with their original names, which can cause conflicts.

```python
# plugins/kimi-tools/src/kimi_tools/mcp_tool.py

class KimiMCPToolPlugin(ToolPlugin):
    """Kimi-style MCP tool plugin.
    
    Naming: tool (bare name, NO prefix)
    Schema: Minimal sanitization
    Format: Kimi ToolReturnValue structure
    """
```

#### Codex MCP Tool Plugin

**Naming**: `mcp__server__tool` (same as Qwen/Grok)

**Language**: Note that Codex CLI is Rust-based, but we implement Python plugin

```python
# plugins/codex-tools/src/codex_tools/mcp_tool.py

class CodexMCPToolPlugin(ToolPlugin):
    """Codex-style MCP tool plugin.
    
    Naming: mcp__server__tool
    Schema: OpenAI Responses API sanitization (strictest)
    Format: Codex-style with McpToolCallOutput structure
    """
```

### MCP Library Choice

Use the official Python MCP SDK: `mcp` package

```toml
# plugins/mcp-shared/pyproject.toml
dependencies = [
    "mcp>=1.0.0",
]
```

The `mcp` package provides:
- `Client` class for connecting to servers
- `StdioClientTransport` for local process spawning
- `SSEClientTransport` for SSE endpoints
- Tool/resource/prompt discovery
- Tool execution

## Source References

### Gemini CLI (TypeScript)

- MCP client implementation:
  - `../gemini-cli/packages/core/src/tools/mcp-client.ts`
- MCP tool wrapper:
  - `../gemini-cli/packages/core/src/tools/mcp-tool.ts`
- MCP client manager:
  - `../gemini-cli/packages/core/src/tools/mcp-client-manager.ts`
- Tool naming (MCP_QUALIFIED_NAME_SEPARATOR):
  - `../gemini-cli/packages/core/src/tools/mcp-tool.ts:17`
- Schema validator (LenientJsonSchemaValidator):
  - `../gemini-cli/packages/core/src/tools/mcp-client.ts:540-565`
- Transport creation (stdio/http/sse):
  - `../gemini-cli/packages/core/src/tools/mcp-client.ts:1996-2074`

### Qwen Code (TypeScript, fork of Gemini)

- MCP client implementation:
  - `../qwen-code/packages/core/src/tools/mcp-client.ts`
- MCP tool wrapper:
  - `../qwen-code/packages/core/src/tools/mcp-tool.ts`
- Tool naming (mcp__ prefix):
  - `../qwen-code/packages/core/src/tools/mcp-tool.ts:48`

### Grok CLI (TypeScript)

- MCP manager:
  - `../grok-cli/src/mcp/client.ts`
- MCP config:
  - `../grok-cli/src/mcp/config.ts`
- MCP transports:
  - `../grok-cli/src/mcp/transports.ts`
- Tool naming (mcp__ prefix):
  - `../grok-cli/src/mcp/client.ts:55`

### Codex CLI (Rust)

- MCP handler:
  - `../codex/codex-rs/core/src/tools/handlers/mcp.rs`
- MCP client (rmcp SDK):
  - `../codex/codex-rs/rmcp-client/src/rmcp_client.rs`
- MCP tool call handling:
  - `../codex/codex-rs/core/src/mcp_tool_call.rs`
- MCP connection manager:
  - `../codex/codex-rs/core/src/mcp_connection_manager.rs`
- Tool naming (mcp__ prefix):
  - `../codex/codex-rs/core/src/mcp_connection_manager.rs:67-70`
- Schema sanitization:
  - `../codex/codex-rs/core/src/tools/spec.rs:1624-1668`

### Kimi CLI (Python)

- MCP tool loading:
  - `../kimi-cli/src/kimi_cli/soul/toolset.py:130-230`
- MCP tool class (MCPTool):
  - `../kimi-cli/src/kimi_cli/soul/toolset.py:260-300`
- MCP content conversion:
  - `../kimi-cli/packages/kosong/src/kosong/tooling/mcp.py`
- CLI commands:
  - `../kimi-cli/src/kimi_cli/cli/mcp.py`
- ACP MCP conversion:
  - `../kimi-cli/src/kimi_cli/acp/mcp.py`

### MCP Specification

- Protocol specification: https://modelcontextprotocol.io/
- Python SDK: https://github.com/modelcontextprotocol/python-sdk
- Rust SDK: https://github.com/modelcontextprotocol/rust-sdk

## Behavior Requirements

### Server Lifecycle

1. **Stdio servers**: Spawn child process with command/args/env, communicate via stdin/stdout
2. **HTTP servers**: Connect to HTTP endpoint with optional headers
3. **SSE servers**: Connect to SSE endpoint
4. **Background discovery**: Start servers async during `initialize()`
5. **Cache schemas**: Store discovered schemas to avoid re-connecting every session
6. **Cleanup**: Properly terminate child processes on shutdown

### Tool Discovery

1. Call `tools/list` on each connected server
2. Cache results keyed by server URL/command hash
3. Invalidate cache when config changes
4. Handle tool list change notifications (advanced)

### Tool Execution

1. Route tool call to correct server based on tool name prefix
2. Strip prefix before sending to MCP server
3. Handle progress notifications (advanced)
4. Handle errors and timeouts
5. Convert MCP content blocks to provider format

### Error Handling

1. Server startup failure -> log warning, skip server's tools
2. Tool not found -> error result
3. Tool execution timeout -> timeout error
4. Tool returns error -> format as error result

## Test Plan

### Shared Package Tests

1. Server config loading from JSON
2. Schema sanitization for each vendor style
3. Content conversion for each content type
4. Cache hit/miss behavior

### Vendor Plugin Tests

1. **Naming tests**: Assert exact tool name format per vendor
   - Gemini: `server__tool`
   - Qwen/Grok/Codex: `mcp__server__tool`
   - Kimi: `tool` (bare)
2. **Schema tests**: Assert vendor-specific schema sanitization
3. **Result formatting tests**: Match vendor CLI output style

### Integration Tests

1. Connect to simple test MCP server (stdio)
2. Discover tools
3. Execute tool call
4. Verify result format

### Cache Tests

1. First run: no cache, discovers from server
2. Second run: cache hit, instant startup
3. Config change: cache invalidated

## Deliverables

1. `plugins/mcp-shared/` package with shared helpers
2. `plugins/gemini-tools/src/gemini_tools/mcp_tool.py`
3. `plugins/qwen-tools/src/qwen_tools/mcp_tool.py`
4. `plugins/grok-tools/src/grok_tools/mcp_tool.py`
5. `plugins/kimi-tools/src/kimi_tools/mcp_tool.py`
6. `plugins/codex-tools/` new package with MCP support
7. Documentation in each vendor plugin README
8. Tests for shared helpers and each vendor plugin

## Out of Scope

- OAuth authentication for MCP servers (requires browser integration)
- MCP resources (read_resource, list_resources)
- MCP prompts
- Tool approval/confirmation flows (application-layer feature)
- Background process management beyond basic cleanup
- Tool list change notifications (dynamic tool updates)
