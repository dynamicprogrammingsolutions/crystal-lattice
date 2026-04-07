# 140 — Async Tool Initialization Protocol Extension

Short description: Extend the ToolPlugin protocol to support async initialization for long-running setup operations (such as MCP server discovery), with layered context and optional cache support. Also add async variants for existing execution methods to support tools that use async internally.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On: None (prerequisite for 150-mcp-tools)

## Goal

Add async initialization support to the ToolPlugin protocol so that tools requiring long-running setup operations (connecting to external services, discovering tool schemas from MCP servers, downloading dependencies) can perform this work without blocking the main request flow.

Additionally, provide async variants for existing execution methods (`execute_tool`, `stream_tool`) so that tools using async internally can implement them without blocking the event loop.

## Background

Current ToolPlugin protocol has:

```python
def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous initialization. Returns state dict."""
```

This is insufficient for tools that need to:
1. Start external processes (MCP stdio servers)
2. Wait for network connections
3. Discover schemas from remote sources
4. Cache expensive computation results

Additionally, some existing tools use `asyncio` internally (e.g., shell tools with async subprocess, web fetch with aiohttp) but must bridge back to sync for `execute_tool`. Providing native async variants avoids this bridging overhead.

The existing `execute_tool` already supports an optional `context` parameter via inspection (added for tools needing LLM access). This pattern should be extended to initialization and async execution.

## Requirements

### Protocol Changes

1. **Add async initialization method to ToolPlugin protocol**.

Note: The method name shown below is an **example only**. The actual naming will be decided during implementation. Options include:
- `initialize` (shown below)
- `async_init`
- `init_async`
- `prepare` / `prepare_async`
- Overloading `init` with inspection-based sync/async detection

```python
async def initialize(  # EXAMPLE NAME - actual naming TBD during implementation
    self,
    config: Dict[str, Any],
    state: Dict[str, Any],
    *,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Async initialization with context.
    
    Called after init(). Use for long-running setup operations.
    
    Args:
        config: Plugin configuration.
        state: State dict from init().
        context: Layered context with runtime capabilities.
            Layer 1 (Core): "core", "config", "cache" (optional)
            Layer 2 (Application): "app", "base_config", "session_asset_store"
    
    Returns:
        Updated state dict.
    """
    return state
```

2. **Add async execution methods to ToolPlugin protocol**:

Note: Method names are examples. Actual naming TBD during implementation.

```python
async def execute_tool_async(
    self,
    tool_name: Optional[str],
    payload: Any,
    state: Dict[str, Any],
    *,
    payload_kind: Optional[str] = None,
    payload_format: Optional[str] = None,
    payload_metadata: Optional[Dict[str, Any]] = None,
    tool_call: Optional[Dict[str, Any]] = None,
    cancellation: Any | None = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Async variant of execute_tool.
    
    Tools that use asyncio internally (shell execution, HTTP requests, etc.)
    should implement this method instead of execute_tool to avoid sync bridging.
    
    Default implementation calls execute_tool synchronously.
    """
    return self.execute_tool(
        tool_name, payload, state,
        payload_kind=payload_kind,
        payload_format=payload_format,
        payload_metadata=payload_metadata,
        tool_call=tool_call,
        cancellation=cancellation,
        context=context,
    )


async def stream_tool_async(
    self,
    tool_name: Optional[str],
    payload: Any,
    state: Dict[str, Any],
    *,
    payload_kind: Optional[str] = None,
    payload_format: Optional[str] = None,
    payload_metadata: Optional[Dict[str, Any]] = None,
    tool_call: Optional[Dict[str, Any]] = None,
    cancellation: Any | None = None,
    context: Optional[Dict[str, Any]] = None,
) -> AsyncIterator[Dict[str, Any]]:
    """Async variant of stream_tool.
    
    Tools that stream results asynchronously (shell output, HTTP streaming, etc.)
    should implement this method instead of stream_tool.
    
    Default implementation wraps stream_tool in an async generator.
    """
    for chunk in self.stream_tool(
        tool_name, payload, state,
        payload_kind=payload_kind,
        payload_format=payload_format,
        payload_metadata=payload_metadata,
        tool_call=tool_call,
        cancellation=cancellation,
        context=context,
    ):
        yield chunk
```

3. **Add cache interface to context**:

```python
class ToolCache(Protocol):
    """Optional cache interface for tool initialization."""
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached value by key. Returns None if not found or expired."""
        ...
    
    def set(self, key: str, value: Dict[str, Any], ttl_seconds: Optional[float] = None) -> None:
        """Store value in cache with optional TTL."""
        ...
    
    def delete(self, key: str) -> None:
        """Remove cached value."""
        ...
```

4. **Context structure for async initialize**:

```python
# Layer 1 (Core - always present when called from AgentCore)
context = {
    "core": AgentCore,
    "config": Dict[str, Any],
    "cache": Optional[ToolCache],  # Application-provided cache
    "trigger_source": "core",
}

# Layer 2 (Application - when called from AgentApplication)
context = {
    **layer1_context,
    "app": AgentApplication,
    "application": AgentApplication,  # Alias
    "base_config": Dict[str, Any],
    "session_asset_store": SessionAssetStore,
    "trigger_source": "application",
}
```

### Core Changes

1. **Add async tool initialization method to AgentCore**:

```python
async def initialize_tools_async(
    self,
    config: Dict[str, Any],
    *,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """Run async initialize() on all registered tools.
    
    Called by application after plugin loading but before first request.
    Tools without async initialize() are skipped.
    """
```

2. **Add async tool execution support to AgentCore**:

```python
async def execute_tool_call_async(
    self,
    tool_call: Dict[str, Any],
    state: Dict[str, Any],
    *,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute a single tool call using async variant if available."""


async def iter_tool_messages_async(
    self,
    tool_calls: List[Dict[str, Any]],
    config: Dict[str, Any],
    *,
    context: Optional[Dict[str, Any]] = None,
) -> AsyncIterator[Dict[str, Any]]:
    """Iterate tool messages using async streaming if available."""
```

3. **Update ToolWrapper to support async methods**:

```python
async def initialize(
    self,
    config: Dict[str, Any],
    state: Dict[str, Any],
    *,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Async initialization via adapter."""
    return await self.plugin.initialize(config, state, context=context)


async def execute_tool_async(
    self,
    tool_name: Optional[str],
    payload: Any,
    state: Dict[str, Any],
    *,
    context: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Async execution via adapter."""
    return await self.plugin.execute_tool_async(
        tool_name, payload, state, context=context, **kwargs
    )


async def stream_tool_async(
    self,
    tool_name: Optional[str],
    payload: Any,
    state: Dict[str, Any],
    *,
    context: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> AsyncIterator[Dict[str, Any]]:
    """Async streaming via adapter."""
    async for chunk in self.plugin.stream_tool_async(
        tool_name, payload, state, context=context, **kwargs
    ):
        yield chunk
```

4. **Update ToolDefaultsAdapter with default async implementations**:

```python
async def initialize(
    self,
    config: Dict[str, Any],
    state: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Default: return state unchanged."""
    return state


async def execute_tool_async(
    self,
    tool_name: Optional[str],
    payload: Any,
    state: Dict[str, Any],
    **kwargs,
) -> Dict[str, Any]:
    """Default: delegate to sync execute_tool."""
    return self.execute_tool(tool_name, payload, state, **kwargs)


async def stream_tool_async(
    self,
    tool_name: Optional[str],
    payload: Any,
    state: Dict[str, Any],
    **kwargs,
) -> AsyncIterator[Dict[str, Any]]:
    """Default: wrap sync stream_tool in async generator."""
    for chunk in self.stream_tool(tool_name, payload, state, **kwargs):
        yield chunk
```

### Application Changes

1. **Add cache provider to AgentApplication**:

```python
class AgentApplication:
    def __init__(self, ...):
        ...
        self._tool_cache: Optional[ToolCache] = None
    
    def set_tool_cache(self, cache: ToolCache) -> None:
        """Set the cache for tool initialization."""
        self._tool_cache = cache
```

2. **Call async initialization during startup**:

```python
async def _ensure_tools_initialized(self) -> None:
    """Initialize tools before first request."""
    if self._tools_initialized:
        return
    
    context = self._build_tool_context()
    await self._core.initialize_tools_async(self._config, context=context)
    self._tools_initialized = True
```

3. **Use async execution in tool loop**:

```python
async def run_tool_loop_async(self, ...):
    """Tool loop using async execution primitives."""
```

### Backward Compatibility

1. **Existing sync methods remain unchanged**. All existing tools continue to work.
2. **Async methods are optional**. Tools that don't implement them use default sync fallbacks.
3. **Detection via inspection**: ToolWrapper checks if the underlying plugin implements async methods as coroutine functions.

### Detection Pattern (from existing context support)

```python
import inspect

def _supports_async_initialize(self) -> bool:
    """Check if plugin implements async initialize."""
    method = getattr(self.plugin, "initialize", None)
    if method is None:
        return False
    return inspect.iscoroutinefunction(method)


def _supports_async_execute(self) -> bool:
    """Check if plugin implements async execute_tool_async."""
    method = getattr(self.plugin, "execute_tool_async", None)
    if method is None:
        return False
    return inspect.iscoroutinefunction(method)


def _supports_async_stream(self) -> bool:
    """Check if plugin implements async stream_tool_async."""
    method = getattr(self.plugin, "stream_tool_async", None)
    if method is None:
        return False
    return inspect.isasyncgenfunction(method)
```

## Source References

### Current protocol

- ToolPlugin protocol: `core/python/agent_core/types.py:1163-1320`
- ToolWrapper: `core/python/agent_core/plugin/tool.py:1-289`
- ToolDefaultsAdapter: `core/python/agent_core/plugin/adapters.py`

### Context pattern (existing)

- FeaturePlugin context in `execute_action`: `core/python/agent_core/types.py:1100-1180`
- ToolPlugin context in `execute_tool`: `plugins/docs/tool-plugins.md` (Tool execution context section)
- Inspection-based parameter detection: `core/python/agent_core/plugin/adapters.py` (context parameter handling)

### Async initialization precedent

- FeaturePlugin `initialize_request` already has context parameter: `core/python/agent_core/types.py:1000-1020`
- FeatureWrapper passes context: `core/python/agent_core/plugin/feature.py:72-85`

### Async tools (existing)

- Shell tools using asyncio: `plugins/codex-tools/src/codex_tools/base_shell_tool.py`
- Web fetch tools with aiohttp: `plugins/web-fetch-shared/`
- Context support added for async tools: `plugins/codex-tools/src/codex_tools/apply_patch_tool.py`

## Deliverables

1. ToolPlugin protocol extension with async initialize method (naming TBD)
2. ToolPlugin protocol extension with `execute_tool_async` and `stream_tool_async` (naming TBD)
3. ToolCache protocol definition
4. ToolWrapper async method support
5. ToolDefaultsAdapter default async implementations
6. AgentCore async tool methods
7. AgentApplication cache provider and async initialization flow
8. Updated `plugins/docs/tool-plugins.md` with async method documentation
9. Unit tests for:
   - Async method detection
   - Context passing
   - Cache interface
   - Backward compatibility (tools without async methods)
   - Async execution vs sync fallback

## Out of Scope

- Implementation of specific cache backends (file, memory, Redis)
- MCP-specific implementation (that's task 150)
- Changing the synchronous `init()` / `execute_tool` / `stream_tool` methods
- Making `get_tool_schemas` async (deferred - requires deeper core changes)
- Choosing final method names (decided during implementation)
