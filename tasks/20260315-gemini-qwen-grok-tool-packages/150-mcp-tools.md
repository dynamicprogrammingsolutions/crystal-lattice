# 150 — MCP Tool Plugins

Short description: Implement Model Context Protocol (MCP) tool support with one shared helper package and five vendor-specific tool plugins (Gemini, Qwen, Grok, Kimi, Codex), each matching their respective CLI's tool naming, schema handling, and result formatting.

## Requirements checklist

- [x] Investigate upstream MCP behavior in the source CLIs and local plugin/UI conventions
- [x] Produce a phased implementation plan aligned to Codex first, then Kimi, then Gemini
- [x] Implement the first slice: shared MCP runtime package, Codex MCP tool plugin, and MCP observability application plugin
- [x] Install the Python MCP SDK and verify the shared runtime against a real MCP server process
- [x] Add MCP plugin/config wiring to the default config, disabled by default
- [x] Simplify the default config by factoring shared Codex MCP settings into a mixin
- [x] Keep Codex plugin local shared-package dependencies declared in plugin-installable packaging metadata
- [x] Add a real API + real MCP e2e test at the server/application level that enables MCP through the same UI/config path used by real clients
- [x] Add a frontend-SDK real MCP e2e that exercises session UI schema, application UI schema, overrides, and application actions through `RestAgentBackend`
- [x] Run all targeted MCP-related tests, including the new real e2e coverage
- [ ] Implement the second slice: Kimi MCP tool plugin on top of the shared runtime package
- [ ] Implement the third slice: Gemini MCP tool plugin on top of the shared runtime package

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

## Execution plan

Added during task completion after investigation. This plan supersedes the earlier all-vendors-at-once assumptions in this file where they conflict with the requested slice order and the clarified shared-package boundary.

### Updated implementation direction

Updated during implementation after proving the real MCP integration path:

- keep `runtime_store` generic and application-owned
- add an application-owned persistent async host so async plugin hooks can run automatically on one shared loop
- keep MCP-specific lifetime/caching logic in an `MCPRegistry` object stored inside `runtime_store`
- make sync request/tool execution transparently bridge async tool hooks through the application host
- keep wrapper plugins responsible only for config parsing, naming, schema shaping, and result formatting

This supersedes the earlier intermediate workaround where the Codex MCP wrapper stored only status snapshots and created a fresh runtime manager per tool call.

#### Checkpoint 1A: Generic runtime foundations

Deliverables:

- replace the old namespace-based tool runtime holder with a generic `RuntimeStore`
- expose `runtime_store` in application-built plugin context
- keep `tool_runtime` as a compatibility alias during transition
- add an application-owned persistent async host in `AgentApplication`
- make sync tool execution automatically use async hooks through that host when a plugin implements them

Implementation expectations:

- plugin authors should be able to implement `prepare_async(...)` and `execute_tool_async(...)` and use normal async libraries without managing event loops themselves
- all async tool-hook calls for one `AgentApplication` should run on the same shared loop

#### Checkpoint 1B: MCP registry on top of runtime_store

Deliverables:

- add `MCPRegistry` in `plugins/mcp-shared`
- store one registry instance in `runtime_store`, keyed flatly as `mcp_registry`
- move Codex MCP wrapper runtime reuse onto `MCPRegistry`
- move `mcp-runtime-app` status / clear / reconnect actions onto `MCPRegistry`

Implementation expectations:

- `RuntimeStore` remains generic and MCP-agnostic
- `MCPRegistry` owns MCP-specific runtime caching keyed by normalized config fingerprint
- live MCP runtimes persist across tool loops in one `AgentApplication`

#### Checkpoint 1C: Real integration verification

Deliverables:

- real filesystem MCP server integration coverage against the official Python MCP SDK
- default-config real API + real MCP e2e test using `gpt-5.4-nano`
- coverage proving sync tool-loop execution can successfully use async-only MCP wrapper hooks through the shared application host

### 1. Scope and slice order

Implement MCP support in three slices:

1. Codex
2. Kimi
3. Gemini

Qwen and Grok remain deferred. The first slice should include not only the Codex MCP tool wrapper, but also an application plugin for MCP runtime observability and operator actions.

### 2. Shared package boundary

Create `plugins/mcp-shared/` as a non-plugin helper package, following the same packaging intent as `plugins/tool-compat-shared/`: importable by vendor plugin bundles, but never directly enabled by users and never listed in `agent_plugin.json`.

The shared package must remain vendor-neutral:

- No Codex/Kimi/Gemini-specific tool naming logic
- No vendor-specific schema sanitization
- No vendor-specific result formatting
- No vendor-specific config-key parsing
- No agent/provider-facing UI generation

The shared package should own only:

- MCP transport/client lifecycle management
- stdio/http/sse connection startup
- raw MCP tool discovery
- raw MCP tool execution
- runtime state tracking
- JSON-like data models for discovered tools and raw call results
- runtime reuse helpers keyed through application-owned `tool_runtime`
- optional cache/fingerprint helpers that are still vendor-neutral

Recommended shared interfaces:

```python
@dataclass(frozen=True)
class MCPServerRuntimeSpec:
    name: str
    enabled: bool
    transport: Literal["stdio", "sse", "http"]
    command: str | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    cwd: str | None = None
    url: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    startup_timeout_seconds: int | None = None
    tool_timeout_seconds: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MCPRuntimeConfig:
    servers: dict[str, MCPServerRuntimeSpec]
    fail_on_startup_error: bool = False
    reuse_runtime: bool = True


@dataclass(frozen=True)
class MCPDiscoveredTool:
    server_name: str
    raw_name: str
    description: str
    input_schema: dict[str, Any]
    annotations: dict[str, Any]
    meta: dict[str, Any]


@dataclass(frozen=True)
class MCPToolCallResult:
    is_error: bool
    content: list[dict[str, Any]]
    structured_content: dict[str, Any] | None = None
    meta: dict[str, Any] | None = None


class MCPRuntimeManager:
    async def start(self, config: MCPRuntimeConfig) -> None: ...
    async def list_tools(self) -> list[MCPDiscoveredTool]: ...
    async def call_tool(
        self,
        *,
        server_name: str,
        tool_name: str,
        arguments: dict[str, Any],
        timeout_seconds: int | None = None,
    ) -> MCPToolCallResult: ...
    async def close(self) -> None: ...
```

The package may also expose small neutral helpers such as:

- `fingerprint_runtime_config(config) -> str`
- `normalize_transport_name(value) -> Literal["stdio", "sse", "http"]`
- `coerce_empty_object_schema(schema) -> dict[str, Any]`

Those helpers must remain formatting-agnostic and wrapper-agnostic.

### 3. Wrapper tool plugin responsibilities

Each vendor MCP wrapper tool plugin should own the full "shape" layer:

- parse effective config keys from the agent/provider config
- normalize those keys into `MCPRuntimeConfig`
- decide tool naming visible to the model
- decide collision policy
- decide wrapper-specific schema sanitization
- decide wrapper-specific error wording
- decide wrapper-specific `format_tool_result()` shape
- decide wrapper-specific UI elements

The wrapper tool should use the new preparation path already available in the core:

- `init(config)` returns static local state only
- `prepare_async(config, state, context=...)` parses wrapper config, obtains or creates runtime managers via application `tool_runtime`, discovers raw tools, and returns only JSON-like prepared catalog data
- `get_tool_schemas(state, prepared=...)` derives tool schemas from the prepared catalog
- `execute_tool_async(..., prepared=...)` routes through the live runtime manager
- `format_tool_result(...)` is entirely wrapper-specific

This aligns with the current `prepare` / `prepare_async` protocol and the application-owned `tool_runtime` context already present in the codebase.

### 4. Shared config keys across wrappers

Per user direction, remove vendor prefixes from the MCP config keys. Different vendor MCP wrappers may use the same config keys because they are not expected to coexist in a single agent.

Recommended common config keys:

```json
{
  "mcp_enabled": true,
  "mcp_fail_on_startup_error": false,
  "mcp_reuse_runtime": true,
  "mcp_servers": {
    "filesystem": {
      "enabled": true,
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
      "cwd": "${env:WORKING_DIR}",
      "env": {},
      "startup_timeout_seconds": 30,
      "tool_timeout_seconds": 120
    },
    "linear": {
      "enabled": false,
      "transport": "http",
      "url": "https://mcp.linear.app/mcp",
      "headers": {
        "Authorization": "Bearer ${env:LINEAR_MCP_TOKEN}"
      }
    }
  }
}
```

Notes:

- `mcp_enabled` gates all MCP servers for the wrapper
- `mcp_servers.<server>.enabled` gates each individual server
- server definitions remain nested config objects
- wrapper plugins may accept compatibility aliases internally if useful, but the shared package should receive only canonical normalized runtime config

### 5. Single-wrapper validation / conflict handling

Because multiple wrappers may now reuse the same config keys, the catalog should reject enabling more than one MCP wrapper family at the same time with a clear error.

Proposed extension:

- add an optional plugin identity declaration such as `conflict_keys = ["mcp_wrapper"]` or a protocol-level `conflict_key()` / `conflict_keys()` hook
- validate per-agent merged plugin catalogs after spec resolution and ID dedupe, before building the final enabled-plugin runtime
- if more than one enabled plugin shares the same conflict key, fail config resolution with a clear message listing:
  - the conflict key
  - the conflicting plugin ids
  - the agent id

Recommended placement for validation:

- application layer, after per-agent plugin spec resolution and plugin-id dedupe in `AgentApplication`, because that is where the merged per-agent catalog already exists

This should be treated as a small supporting framework change for the MCP work, not as part of `mcp-shared`.

### 6. UI shape

The wrapper tool plugin UI should remain intentionally small:

1. one global on/off toggle for all MCP servers
2. one on/off toggle per configured MCP server

Do not attempt to expose full nested server editing UI in the first pass.

Recommended UI element shape:

```python
[
    {
        "type": "checkbox",
        "key": "mcp_enabled",
        "label": "Enable MCP tools",
        "description": "Enable tools discovered from configured MCP servers.",
    },
    {
        "type": "checkbox",
        "key": "mcp_servers.filesystem.enabled",
        "config_path": "mcp_servers.filesystem.enabled",
        "label": "Enable MCP server: filesystem",
        "description": "Expose tools from the filesystem MCP server.",
    },
    {
        "type": "checkbox",
        "key": "mcp_servers.linear.enabled",
        "config_path": "mcp_servers.linear.enabled",
        "label": "Enable MCP server: linear",
        "description": "Expose tools from the linear MCP server.",
    },
]
```

The wrapper plugin should generate one per-server toggle dynamically from the configured server names.

### 7. Observability application plugin in slice 1

Add a small application plugin in the first slice dedicated to MCP runtime observability and operator controls.

Suggested package direction:

- `plugins/mcp-runtime-app/`

Suggested responsibilities:

- inspect application-owned `tool_runtime`
- show connected / failed / disconnected server state
- show discovered tool counts
- allow reconnecting and clearing runtime state
- return generic `display` payloads for frontends

Suggested actions:

- `mcp_show_status`
- `mcp_reconnect_servers`
- `mcp_clear_runtime`

Suggested session UI:

```python
{
    "ui_type": "session_action",
    "id": "mcp_show_status",
    "label": "MCP status",
    "icon": "plug",
    "order": 70,
    "action_id": "mcp_show_status",
    "fixed_params": {},
    "param_map": {"session_id": "$session.session_id"},
}
```

```python
{
    "ui_type": "session_action",
    "id": "mcp_reconnect_servers",
    "label": "Reconnect MCP servers",
    "icon": "refresh",
    "order": 71,
    "action_id": "mcp_reconnect_servers",
    "fixed_params": {},
    "param_map": {"session_id": "$session.session_id"},
}
```

```python
{
    "ui_type": "session_action",
    "id": "mcp_clear_runtime",
    "label": "Clear MCP runtime",
    "icon": "trash",
    "order": 72,
    "action_id": "mcp_clear_runtime",
    "fixed_params": {},
    "param_map": {"session_id": "$session.session_id"},
}
```

These actions should use the documented generic `display` payload contract rather than plugin-specific ad hoc response fields.

### 8. Staged implementation checkpoints

#### Checkpoint 1: Shared runtime + Codex + observability app

Deliverables:

- `plugins/mcp-shared/` vendor-neutral runtime package
- `plugins/codex-tools/src/codex_tools/mcp_tool.py`
- Codex MCP registration in `plugins/codex-tools/agent_plugin.json`
- optional Codex MCP naming helper module if that improves local organization
- `plugins/mcp-runtime-app/` application plugin with MCP status/reconnect/clear actions
- application/runtime cleanup support so MCP runtimes are closed on shutdown

Codex wrapper behavior:

- model-visible naming: `mcp__server__tool`
- raw server/tool identity preserved separately for execution
- Responses-safe name sanitization
- collision disambiguation and length constraints modeled after Codex behavior
- Codex/OpenAI Responses-style result formatting
- any Codex-specific schema masking or metadata handling stays in the Codex wrapper, not `mcp-shared`

This is the first fully testable vertical slice and should be used to validate the shared runtime boundary and the observability application plugin against a real MCP-backed tool wrapper.

Additional verification work for this checkpoint:

- install the official Python MCP SDK in the local environment used for testing
- verify the shared runtime against a real MCP server process, not only fake managers
- add disabled-by-default MCP wiring to the shipped default config
- add a real API + real MCP e2e test that:
  - uses the default config
  - enables MCP through the same session UI/config discovery path a real client would use
  - launches a real MCP server from config
  - sends a real model request using `gpt-5.4-nano`
  - avoids test-only shortcuts or hidden knowledge unavailable to normal clients

#### Checkpoint 2: Kimi + single-wrapper safety

Deliverables:

- `plugins/kimi-tools/src/kimi_tools/mcp_tool.py`
- Kimi MCP registration in `plugins/kimi-tools/agent_plugin.json`
- conflict-key validation so only one MCP wrapper family can be active per agent

Kimi wrapper behavior:

- bare tool-name exposure
- explicit collision policy handled in the Kimi wrapper
- Kimi-style output formatting built from raw MCP results
- same shared `mcp_*` config keys parsed by the Kimi wrapper and normalized into canonical runtime config

Single-wrapper safety should be introduced in this checkpoint rather than Checkpoint 1, so it can be verified against two real MCP wrappers instead of being added speculatively.

#### Checkpoint 3: Shared-key hardening and docs

Deliverables:

- tighten behavior for shared `mcp_*` config keys now that at least two wrappers exist
- verify observability actions continue to work when multiple MCP wrapper families are installed but only one may be active per agent
- improve tests and docs around:
  - wrapper-specific config parsing over shared `mcp_*` keys
  - startup failure policy
  - runtime reuse
  - disabled server behavior

#### Checkpoint 4: Gemini

Deliverables:

- `plugins/gemini-tools/src/gemini_tools/mcp_tool.py`
- Gemini MCP registration in `plugins/gemini-tools/agent_plugin.json`

Gemini wrapper behavior:

- model-visible naming: `server__tool`
- Gemini-style schema handling and tool exposure
- Gemini-style MCP content/result formatting
- same shared `mcp_*` config keys parsed by the Gemini wrapper and normalized into canonical runtime config

If Gemini parity requires new core/provider-native tool-result interop support for richer multimodal tool outputs, that extension should be scoped into this slice rather than pushed down into `mcp-shared`.

### 9. Testing plan

#### Shared runtime package

- unit tests for runtime config normalization helpers
- unit tests for transport selection and spec normalization
- unit tests for tool discovery data models
- unit tests for runtime fingerprint / reuse keys
- unit tests for failure-state reporting
- integration test using a small stdio MCP fixture server

#### Conflict validation

- config/application-layer tests proving that two plugins with the same conflict key fail early with a clear message
- tests proving that non-conflicting plugin combinations still work

#### Codex wrapper

- naming tests for sanitization, collision disambiguation, and raw-name preservation
- schema tests for Codex wrapper-specific shaping
- result-format tests for Codex/OpenAI Responses-style payloads
- integration test proving discovered MCP tools appear in the tool catalog and execute end-to-end
- integration test proving the shared runtime can drive a real MCP server process via the official Python MCP SDK

#### Observability app plugin

- action discovery tests
- action execution tests for show-status / reconnect / clear-runtime
- action `display` payload shape tests
- default-config integration test coverage so the app plugin is present in normal shipped configuration

#### Default-config real e2e coverage

- add a default-config integration test that loads credentials from the repo-root `.env`
- use the shipped default config and a real session
- discover MCP-related config controls through session UI schema
- set overrides through the same session-override path used by real clients
- send a real request against `gpt-5.4-nano`
- verify that a real MCP server is launched from config and that the model actually uses an MCP-backed tool call

#### Kimi wrapper

- bare-name exposure tests
- collision-policy tests
- result-format tests for Kimi output structure

#### Gemini wrapper

- `server__tool` naming tests
- schema/result formatting tests for Gemini wrapper behavior
- integration tests for text-first MCP results and, if implemented, multimodal result interop

### 10. Known follow-up work after this task

This task still excludes:

- MCP prompts
- MCP resources
- OAuth/browser login UX
- approval/confirmation flows for MCP tools
- dynamic tool-list change notifications

If runtime observability proves useful, a later task may extend the application plugin with richer status-bar or session-list UI, but that is not required for the first implementation slices.

## Completion Notes

Added during task completion:

- clarified that `mcp-shared` must remain vendor-neutral and receive only canonical runtime config
- revised config direction to use shared `mcp_*` keys without Codex/Kimi/Gemini prefixes
- added a concrete proposal for single-wrapper conflict validation so shared config keys remain safe
- refined UI scope to a single global toggle plus per-server toggles
- moved the MCP observability application plugin into slice 1 as requested
- revised checkpoint order so observability ships with the first usable Codex MCP slice and single-wrapper safety lands with the second real wrapper
- implemented Checkpoint 1:
  - added `plugins/mcp-shared/` with vendor-neutral runtime config/models/manager
  - added Codex MCP wrapper tool in `plugins/codex-tools`
  - added `plugins/mcp-runtime-app/` application plugin with status/reconnect/clear actions
  - added application-owned runtime cleanup support
  - added focused unit tests for the shared package, Codex wrapper, app plugin, and runtime-store cleanup
- verification note for Checkpoint 1:
  - targeted tests passed locally, including:
    - shared runtime unit tests
    - shared runtime real filesystem MCP server integration test
    - Codex MCP wrapper unit tests
    - MCP runtime app plugin unit tests
    - application runtime-store cleanup tests
    - default-config real API + real MCP e2e test using `gpt-5.4-nano`
- new follow-up for Checkpoint 1 after user review:
  - completed:
    - installed the official Python MCP SDK locally
    - verified a real MCP filesystem server process with the shared runtime
    - wired MCP into the shipped default config in disabled-by-default form
    - added a realistic default-config real API + real MCP e2e test driven through UI-schema discovery, plugin discovery, and normal session-override updates
    - ran the targeted MCP-related verification suite after implementation
- implementation update after the async-host refactor:
  - replaced the old namespace-based tool runtime holder with a generic `RuntimeStore`
  - added an application-owned persistent async host
  - exposed `runtime_store` in plugin context while keeping `tool_runtime` as a compatibility alias
  - updated sync tool execution so async-only tool hooks run automatically through the shared application host
  - added `MCPRegistry` in `plugins/mcp-shared` and stored it flatly in `runtime_store` as `mcp_registry`
  - moved Codex MCP runtime reuse and `mcp-runtime-app` observability onto that registry
  - restored long-lived MCP runtime reuse across tool loops in one `AgentApplication`
- targeted verification completed after the refactor:
  - `pytest core/python/tests/test_tool_adapter.py core/python/tests/test_tool_preparation.py core/python/tests/test_application_runtime_env.py -q`
  - `pytest plugins/mcp-shared/tests/test_runtime.py plugins/mcp-runtime-app/tests/test_mcp_runtime_app.py plugins/codex-tools/tests/test_mcp_tool.py -q`
  - `pytest application/python/tests/test_terminal_default_config_codex_mcp_real_api.py -q`
- follow-up completion after packaging/default-config review:
  - simplified `plugins/codex-tools/setup.py` so sibling shared-package dependencies use the same direct `file://...` pattern as the other tool bundles
  - factored the repeated disabled-by-default Codex MCP config into a `codex_mcp_defaults` mixin in the shipped default config
  - added a frontend-SDK real MCP integration test in `packages/frontend-sdk` that:
    - discovers session plugin toggles through `RestAgentBackend`
    - discovers MCP config toggles through session UI schema
    - discovers the MCP observability action through session application UI schema
    - executes a real OpenRouter request that uses the filesystem MCP server
  - kept the heavy shipped-default-config coverage in the Python/server integration test, while using a focused real backend config for the SDK integration test so the SDK suite remains practical to run
  - additional verification completed:
    - `npm run integration:backend:openrouter:mcp` from `packages/frontend-sdk`
