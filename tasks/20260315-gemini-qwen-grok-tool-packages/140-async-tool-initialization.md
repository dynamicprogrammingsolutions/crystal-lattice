# 140 — Async Tool Initialization Protocol Extension

Short description: Add explicit tool preparation hooks (`prepare` / `prepare_async`) plus optional async execution hooks, so long-running setup can stay separate from cheap sync discovery APIs while feeding them JSON-like prepared data.

## Requirements checklist

- [x] Define explicit `prepare` / `prepare_async` semantics for long-running tool setup without making existing cheap tool-discovery APIs async
- [x] Keep cheap tool hooks pure/fast by feeding them JSON-like prepared data instead of live runtime handles
- [x] Wire tool preparation into `AgentApplication` request flow without implicitly turning `get_available_tools()` or similar calls into long-running operations
- [x] Define optional async execution hooks as plugin-author convenience without requiring async core tool APIs in this task
- [x] Document how optional app-owned runtime services support MCP-style long-lived resources while remaining isolated from cheap hooks

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

## Execution plan

Added during completion planning after review of the current tool protocol, wrapper/adapter behavior, application request flow, and the latest plugin docs under `plugins/docs`.

### 1. Reframe the task around explicit preparation, not async discovery APIs

The current task text assumes that async initialization may need to push core discovery APIs such as `get_available_tools()` toward async. The approved direction is the opposite:

1. Keep existing cheap core APIs such as `get_available_tools()`, `get_tool_schemas()`, preview helpers, and current sync tool-loop entry points blocking and fast.
2. Introduce a separate explicit long-running preparation phase via `prepare(...)` and `prepare_async(...)`.
3. Treat preparation as opt-in and application-driven, similar in spirit to provider `get_models()` being a separate stage that feeds later pure logic.

This preserves a clean distinction between:

1. cheap/pure hooks that should remain easy to unit test
2. long-running hooks that may do I/O, subprocess startup, MCP discovery, auth handshakes, or cache hydration

### 2. Proposed protocol semantics

Add explicit preparation hooks to `ToolPlugin`:

```python
def prepare(
    self,
    config: Dict[str, Any],
    state: Dict[str, Any],
    *,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Optional blocking preparation hook.

    Performs long-running setup and returns JSON-like prepared data.
    The returned mapping must be serializable / JSON-like so it can feed
    cheap hooks without leaking live runtime objects into them.
    """
    return {}


async def prepare_async(
    self,
    config: Dict[str, Any],
    state: Dict[str, Any],
    *,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Optional async preparation hook returning the same prepared-data shape."""
    return self.prepare(config, state, context=context)
```

Key semantic rules:

1. `init(config)` remains cheap and synchronous. It should construct only base state.
2. `prepare(...)` and `prepare_async(...)` are alternative entry points for the same long-running preparation phase.
3. Preparation returns **prepared data**, not mutated live state and not runtime objects.
4. Prepared data must be JSON-like / serializable so that later cheap hooks remain pure and easy to test.
5. If a tool is never prepared, it may legitimately expose an empty or degraded schema set rather than forcing long-running work into a cheap hook.

### 3. Feed prepared data into cheap hooks instead of live runtime

The approved refinement is that cheap functions should consume prepared JSON-like data similarly to how provider model descriptors feed later pure logic.

Recommended interface evolution:

```python
def get_tool_schemas(
    self,
    state: Dict[str, Any],
    *,
    prepared: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Fast schema generation from cheap base state + optional prepared data."""
```

Potentially the same optional `prepared=` keyword can be added to other cheap hooks when needed:

1. `can_handle_tool_call(...)`
2. `format_tool_call_preview(...)`
3. other purely local routing/introspection helpers if this task touches them

Important rule:

1. Cheap hooks receive base `state` plus optional JSON-like `prepared` data.
2. Cheap hooks do **not** receive live runtime handles and should not depend on them.

This keeps the “fast path” unit-testable:

1. construct `state` with `init(...)`
2. pass in a handcrafted `prepared` dict
3. assert pure behavior without needing network, subprocesses, or app runtime

### 4. Optional async execution hooks remain convenience-only in this task

Add canonical async execution hooks to the protocol:

```python
async def execute_tool_async(... ) -> Dict[str, Any]: ...
async def stream_tool_async(... ) -> AsyncIterator[Dict[str, Any]]: ...
```

But the agreed semantics are:

1. these hooks are an optional convenience for plugin authors
2. they do **not** require `AgentCore` sync execution APIs to become async in this task
3. the main sync core tool path remains blocking for now

Compatibility direction:

1. wrappers/adapters should support the new canonical async hook names
2. wrappers should continue tolerating existing in-repo tools that currently implement `async def execute_tool(...)` under the sync name
3. docs should make `execute_tool_async` / `stream_tool_async` the preferred forward-looking shape while acknowledging the compatibility shim

### 5. AgentCore preparation API and cache shape

Add explicit core entry points:

```python
def prepare_tools(
    self,
    config: Dict[str, Any],
    *,
    context: Optional[Dict[str, Any]] = None,
) -> None: ...


async def prepare_tools_async(
    self,
    config: Dict[str, Any],
    *,
    context: Optional[Dict[str, Any]] = None,
) -> None: ...
```

Preparation behavior:

1. resolve the enabled tools for the effective config
2. build base tool state with `init(...)`
3. prepare each tool exactly once for the current config
4. cache the returned prepared data on the `AgentCore` instance for later cheap-hook reuse

Per-tool hook selection:

1. `prepare_tools(...)` prefers `prepare(...)`
2. if only `prepare_async(...)` is implemented, `prepare_tools(...)` may block on it
3. `prepare_tools_async(...)` prefers `prepare_async(...)`
4. if only `prepare(...)` is implemented, `prepare_tools_async(...)` just calls it directly
5. if both are implemented, they are alternative entry points, not two separate stages

Prepared-data cache semantics:

1. cache base state from `init(...)`
2. cache prepared data separately from base state
3. key by tool identity + effective tool-init config fingerprint
4. later sync fast APIs reuse cached prepared data when available
5. existing sync fast APIs do **not** implicitly trigger preparation in this task

### 6. AgentApplication wiring

Tool preparation should be wired at the application layer, not hidden inside fast core discovery helpers.

Primary automatic wiring point:

1. `AgentApplication.send_request(...)`
2. after `run_session_lifecycle("request_prepare", ...)`
3. after effective config resolution for the final post-lifecycle session/runtime
4. before the tool loop/provider request begins

This is the right ownership boundary because:

1. `request_prepare` is already the documented long-running application-owned preparation point
2. lifecycle actions may mutate the session/config and even cause runtime rebuilding
3. preparation must run against the final effective runtime rather than an earlier stale core

Recommended application behavior:

1. automatically call `core.prepare_tools(...)` in the sync request path
2. add `prepare_tools_for_session(...)` / `prepare_tools_for_session_async(...)` helpers for explicit non-request callers
3. do not auto-run preparation from read-style APIs like “list available tools”

### 7. Optional app-owned runtime service for long-lived resources

The earlier `tool_runtime` idea remains useful, but only for long-running hooks and execution hooks.

Approved refinement:

1. cheap hooks consume only JSON-like prepared data
2. live runtime services are exposed only to long-running functions such as `prepare`, `prepare_async`, `execute_tool`, `execute_tool_async`, `stream_tool`, and `stream_tool_async`

Reserved context key:

1. `tool_runtime`

Intended role:

1. app-owned registry for long-lived runtime resources such as MCP client managers
2. lets fresh `AgentCore` instances reuse the same live resource through `AgentApplication`
3. keeps live objects out of cheap hooks and out of the prepared-data contract

For MCP, the intended pattern is:

1. `prepare_async(...)` uses `context["tool_runtime"]` to look up or create an MCP manager
2. it performs discovery through that live manager
3. it returns only serializable prepared data such as sanitized schemas, tool index mappings, and possibly a stable `runtime_key`
4. `get_tool_schemas(..., prepared=...)` returns schemas from prepared data only
5. `execute_tool_async(...)` reacquires the live manager via `runtime_key` + `tool_runtime`

### 8. Out-of-process tool hosts (Node and Bash)

This task should not force a single cross-language MCP runtime story.

Current architecture:

1. Node-hosted tools are already Python proxy `ToolPlugin`s backed by an NDJSON host protocol
2. Bash-hosted tools are already Python proxy `ToolPlugin`s backed by subcommand invocation

Recommended scope for this task:

1. Python in-process tools get the new preparation hooks first
2. Node and bash proxy tools inherit default no-op preparation behavior unless explicitly extended later
3. no host-protocol change is required for this task

Implications:

1. Python MCP tools can use `tool_runtime` immediately
2. Node tools can continue working unchanged
3. if Node-hosted tools later need preparation parity, that should be a separate host-protocol extension adding optional `prepare` / `prepareAsync` RPC methods
4. bash tools likely remain preparation no-ops for now

### 9. Documentation and testing direction

Docs to update during implementation:

1. `plugins/docs/tool-plugins.md`
2. any protocol reference docs that mention `ToolPlugin`
3. host docs only as needed to clarify that Node/Bash do not yet expose preparation unless explicitly extended

Key documentation points:

1. `init()` must remain cheap
2. `prepare()` / `prepare_async()` are the only long-running preparation hooks
3. prepared data must be JSON-like and is intended to feed cheap hooks
4. cheap hooks do not receive live runtime handles
5. sync core discovery APIs remain sync and do not implicitly prepare tools

Tests to add later during implementation:

1. `prepare()` feeds cached prepared data into `get_available_tools()` / schema generation on the same core
2. `prepare_async()` does the same
3. fast core discovery APIs remain cheap and do not auto-trigger preparation
4. compatibility with tools that implement only existing sync hooks
5. compatibility with existing tools that currently expose an awaitable `execute_tool(...)`
6. application request flow invokes tool preparation after `request_prepare` and before the tool loop

## Completion Notes

Updated during implementation completion.

Completed work:

1. Added `prepare` / `prepare_async`, optional `prepared=...` hook plumbing, and canonical async execution/streaming hooks to the Python tool protocol and wrapper/adapter layer.
2. Added `AgentCore.prepare_tools(...)` / `prepare_tools_async(...)` plus per-core caching of prepared JSON-like tool data so explicit preparation feeds existing sync discovery, preview, and execution paths.
3. Wired `AgentApplication.send_request(...)` to prepare tools after `request_prepare` and before the tool loop, and added an app-owned `tool_runtime` store plus explicit `prepare_tools_for_session(...)` helpers.
4. Updated tool-plugin docs to describe the new split between cheap hooks and long-running preparation, and documented the current Node-host limitation.
5. Added regression coverage for prepared schema discovery, sync blocking over async-only preparation, async execution helper compatibility, and application-layer preparation context wiring.

Verification:

1. `pytest core/python/tests/test_tool_preparation.py core/python/tests/test_tool_adapter.py core/python/tests/test_core.py core/python/tests/test_application_layer_plugins.py -q`
2. `pytest core/python/tests/test_node_tool_plugins.py core/python/tests/test_bash_tool_plugins.py core/python/tests/test_tool_plugin_context.py -q`

Notes:

1. `pytest core/python/tests/test_plugin_default_adapters.py -q` still reports two pre-existing failures in `test_adapter_init_and_initialize_request_default_passthrough(...)` for provider-extension and feature adapters; this task did not modify those code paths.
- Choosing final method names (decided during implementation)
