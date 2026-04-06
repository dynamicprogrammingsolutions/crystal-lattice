# Tool Gating, Available Tools API, and Web Fetch Internal Tool Disable

Add first-class tool catalog and request-time tool gating support so plugin-contributed UI can expose per-request tool controls, and use that mechanism for the Gemini `web_fetch` internal fallback summarization call to disable all tools.

## Requirements checklist

- [x] Add a core-level `get_available_tools(config)` API that returns normalized tool descriptors, not only raw schemas.
- [x] Extend plugin-contributed UI schema generation so plugins can inspect the available tool catalog when building UI elements.
- [x] Add a request-time `prepare_tools(...)` hook that can filter or transform the available tool catalog before provider tool extensions inject tools into the request payload.
- [x] Implement a simple generic feature plugin that supports a config key such as `disable_all_tools`.
- [x] Use that feature for the first concrete rollout in Gemini `web_fetch`, so its internal fallback summarization request sends no tools even if the outer agent config normally has tools enabled.
- [x] Add tests covering the new core/tool-gating flow and the Gemini `web_fetch` integration path.

## Goal

The system currently resolves enabled tool plugins, gathers schemas, and injects them into provider payloads before the request is sent. That works for normal tool use, but it makes "no tools for this internal call" clumsy and provider-specific. The near-term need is the Gemini `web_fetch` fallback summarization request, which should not expose any tools at all. The longer-term need is a generic feature that lets plugin-contributed UI expose tool toggles and lets request execution honor the resulting config.

This task should add a single canonical flow:

1. `get_available_tools(config)` returns the full tool catalog for the resolved config.
2. `get_ui_schema(config)` passes that catalog into plugin `get_ui_elements(...)` context.
3. Frontends render plugin-contributed UI and write user choices back into config.
4. Request execution calls `prepare_tools(...)` with the resolved config.
5. Provider tool extensions serialize only the prepared tools into the outbound payload.

## Current state and findings

### Tool injection happens before feature `initialize_request`

- Provider tool extensions inject payload tools from `config["tools"]`.
- The relevant code today:
  - [core.py](/Users/ferenci84/Dev/Mine/ai-agent-platform/core/python/agent_core/core.py#L1569) builds `provider_config` and populates `config["tools"]` from enabled tool plugins inside `_init_provider_and_features_for_config(...)`.
  - [openai_tools_extension.py](/Users/ferenci84/Dev/Mine/ai-agent-platform/core/python/plugins/openai_tools_extension.py#L142) injects `tools` and `tool_choice` into the request payload during provider-extension request init.
  - [openrouter_responses_tools_extension.py](/Users/ferenci84/Dev/Mine/ai-agent-platform/plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_tools_extension.py#L87) does the same for the OpenRouter Responses stack.
- In the request flow, provider `initialize_request(...)` runs before feature `initialize_request(...)` in [_pre_request](/Users/ferenci84/Dev/Mine/ai-agent-platform/core/python/agent_core/core.py#L1763).

Consequence:
- A feature hook that runs only at `initialize_request(...)` is too late to prevent tool schemas from appearing in the payload.
- Tool gating must run before provider tool extensions serialize tools into the request.

### Existing core/tool seams already help

- Core already exposes [get_tool_schemas(config)](/Users/ferenci84/Dev/Mine/ai-agent-platform/core/python/agent_core/core.py#L2989), but it returns only raw schemas.
- UI schema generation already passes `config`, `tags`, and `models` into plugin UI hooks in [core.py](/Users/ferenci84/Dev/Mine/ai-agent-platform/core/python/agent_core/core.py#L2335).
- Tool enablement already participates in plugin dependency resolution, and tools can be enabled/disabled at the plugin level through the normal config-driven resolver in [core.py](/Users/ferenci84/Dev/Mine/ai-agent-platform/core/python/agent_core/core.py#L1390).

What is missing:
- A normalized "available tools" catalog with stable names and provenance.
- A pre-serialization hook to filter that catalog per request.
- A way to pass the available tool catalog into plugin-contributed UI schema hooks.

### Gemini `web_fetch` first-use case

- The Gemini `web_fetch` tool has an internal fallback summarization call in [gemini_web_fetch_tool.py](/Users/ferenci84/Dev/Mine/ai-agent-platform/plugins/gemini-tools/src/gemini_tools/gemini_web_fetch_tool.py#L577).
- The current local fix already forces `request_options["tool_choice"] = "none"` in that internal call in [gemini_web_fetch_tool.py](/Users/ferenci84/Dev/Mine/ai-agent-platform/plugins/gemini-tools/src/gemini_tools/gemini_web_fetch_tool.py#L586).
- That is better than nothing, but it still relies on provider semantics and does not guarantee that tools are absent from the payload.

The first concrete usage of the new feature should replace that provider-facing workaround with config-driven tool suppression for the internal summarization call.

## Agreed design direction

### 1. Add `get_available_tools(config)`

Use the earlier agreed name: `get_available_tools`.

This should return normalized tool descriptors rather than just raw schemas. Suggested shape:

```python
@dataclass(frozen=True)
class ToolDescriptor:
    plugin_name: str
    tool_name: str
    schema: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
```

Why this matters:
- UI needs stable tool names and plugin provenance.
- Request-time policy may want to filter by tool name or plugin.
- Future policy can attach metadata such as `dangerous`, `read_only`, `category`, or `internal_only`.

`get_tool_schemas(config)` should remain for backward compatibility and can become a thin wrapper over `get_available_tools(config)`.

### 2. Extend plugin UI hooks with context

The current UI flow is plugin-contributed, which is good. Keep that model and extend it.

Add an optional `context` argument to plugin `get_ui_elements(...)` calls, passed by adapters for backward compatibility. Suggested shape:

```python
get_ui_elements(config, tags, models, context=None)
```

UI context should include at least:

```python
{
    "available_tools": [...],   # full tool catalog before request-time filtering
    "enabled_plugins": {
        "providers": [...],
        "extensions": [...],
        "features": [...],
        "tools": [...],
    },
    "provider": "...",
}
```

Important:
- UI should see the full available catalog, not only the currently effective tool set.
- Otherwise a disabled tool can disappear from the UI, making it impossible to re-enable.

### 3. Add request-time `prepare_tools(...)`

Add a hook that runs after plugin resolution and `init(...)`, but before provider tool extensions serialize tools into the payload.

Suggested hook:

```python
prepare_tools(tools, context) -> list[ToolDescriptor]
```

Recommended first placement:
- Add it to `FeaturePlugin` first.

Why start with features:
- The immediate use case is generic cross-provider policy, not provider-specific tool shaping.
- Provider tool extensions should remain focused on payload serialization.

Context should include both `config` and `state`:

```python
{
    "config": resolved_config,
    "state": provider_state_after_init,
    "tags": tags,
    "models": models,
    "provider": provider_name,
    "request_id": request_id,
}
```

Design note:
- Do not choose between `config` and `state`.
- `config` is the explicit source of truth, including UI selections.
- `state` is useful for runtime-aware policy and should reflect provider/extensions/features after `init(...)`, but before `initialize_request(...)`.

### 4. First generic implementation: simple `disable_all_tools` feature

Add a small feature plugin that:
- contributes a config schema key such as `disable_all_tools`
- optionally contributes plugin UI elements using `available_tools` context
- implements `prepare_tools(...)`

Behavior:
- when `disable_all_tools` is false or absent, return the tool catalog unchanged
- when `disable_all_tools` is true, return an empty list

This should be intentionally simple as the first rollout. Later expansion can add:
- `disabled_tools`
- `enabled_tools`
- `disabled_tool_plugins`

### 5. First concrete usage in Gemini `web_fetch`

Use the new generic feature for the internal fallback summarization request in `gemini_web_fetch_tool`.

Acceptable first rollout options:

- Preferred:
  - Add the simple feature to the default plugin set and make the internal fallback request pass `disable_all_tools: true`.
- Acceptable alternative:
  - Require that users add the feature plugin to config for this to work, and document that the internal `web_fetch` fallback call sets `disable_all_tools: true` only when the feature is present.

The task request explicitly allows either option. The preferred one gives better out-of-the-box behavior.

## Implementation sketch

### Core

Refactor the current tool assembly flow around [_init_provider_and_features_for_config(...)](/Users/ferenci84/Dev/Mine/ai-agent-platform/core/python/agent_core/core.py#L1569):

1. Resolve provider, extensions, features, tools, tags, and models.
2. Build `available_tools` from enabled tool plugins.
3. Initialize provider/features state with `init(...)`.
4. Run feature `prepare_tools(...)` hooks on the catalog with `{config, state, tags, models, provider, request_id}` context.
5. Convert the resulting prepared descriptors into `config["tools"]`.
6. Continue into provider `initialize_request(...)`.

Concrete additions:
- add `ToolDescriptor` type in a core types module
- add `AgentCore.get_available_tools(config)`
- keep `AgentCore.get_tool_schemas(config)` delegating to available/prepared tool APIs as appropriate
- thread `available_tools` into `get_ui_schema(...)`
- update plugin adapters so `get_ui_elements(..., context=...)` and `prepare_tools(...)` remain backward compatible

Open design choice:
- `get_available_tools(config)` should return the catalog before request-time filtering.
- Request execution should use prepared/effective tools.
- If needed, add a small internal helper like `_prepare_tools_for_request(...)` rather than exposing that publicly right away.

### Generic feature plugin

Implement a small feature plugin, for example under `core/python/plugins/` or as a small built-in feature package, that:
- exposes `disable_all_tools` in config schema/UI
- optionally emits a simple checkbox UI element
- implements `prepare_tools(...)`

Suggested behavior:

```python
if config.get("disable_all_tools"):
    return []
return tools
```

### Gemini `web_fetch`

Update the internal fallback summarization config merge in [gemini_web_fetch_tool.py](/Users/ferenci84/Dev/Mine/ai-agent-platform/plugins/gemini-tools/src/gemini_tools/gemini_web_fetch_tool.py#L577) so the internal call sets:

```python
disable_all_tools = True
```

Keep `tool_choice: "none"` only if it remains useful as a defensive provider hint. The main guarantee should come from the new tool-gating flow, not the provider payload option alone.

## Testing expectations

Add tests for each layer changed.

### Core/unit tests

- `get_available_tools(config)` returns normalized descriptors including tool names and plugin names.
- `get_ui_schema(config)` passes `available_tools` into plugin `get_ui_elements(...)` context.
- `prepare_tools(...)` runs before provider tool extensions inject payload tools.
- `disable_all_tools=true` results in no tools being serialized into request payloads.

### Integration tests

- OpenAI-compatible stack: tools feature enabled, `disable_all_tools=true`, confirm outbound request payload has no `tools`.
- OpenRouter Responses stack: same assertion.
- Gemini `web_fetch` integration test:
  - real app-level flow using the path-loaded Gemini tools package
  - internal fallback summarization path enabled
  - confirm the fallback succeeds without exposing tools
  - confirm the request no longer relies only on `tool_choice: none`

## Execution plan

Added during completion:

1. Add the core `ToolDescriptor` type plus `FeaturePlugin.prepare_tools(...)`, and update adapters/wrappers so legacy plugins still work.
2. Refactor `AgentCore` tool assembly into "available tools" and "prepared tools", use prepared tools during requests, and pass `available_tools` into plugin UI context.
3. Add a minimal built-in feature plugin for `disable_all_tools`, then use it from Gemini `web_fetch` internal fallback requests.
4. Add focused core tests for available tools, UI context, and request-time tool suppression, then update Gemini tests to cover the new internal no-tools behavior.

## Notes for the implementing agent

- Preserve backward compatibility for existing plugins that define `get_ui_elements(self, config, tags, models)` with no `context`.
- Keep provider tool extensions serialization-only if possible; avoid duplicating policy logic per provider.
- Do not make UI depend on request-time prepared tools. UI should use the full available catalog so disabled tools remain visible.
- The first feature is intentionally minimal. It is acceptable to stop at `disable_all_tools` for the first pass as long as the architecture clearly leaves room for per-tool gating later.

## Completion Notes

Added during task creation:
- Captured the agreed naming (`get_available_tools`) and the desired high-level flow: available tool catalog -> plugin-contributed UI -> resolved config -> request-time `prepare_tools(...)`.
- Recorded the current architectural constraint that feature `initialize_request(...)` is too late for tool suppression because payload tools are injected earlier.
- Included the first concrete rollout requirement for Gemini `web_fetch`: use a simple generic `disable_all_tools` feature to suppress tools for its internal summarization request.

Added during completion:
- Implemented `ToolDescriptor`, `AgentCore.get_available_tools(...)`, request-time feature `prepare_tools(...)`, and UI-context propagation of both `available_tools` and effective `tools`.
- Refined the final architecture so `prepare_tools(...)` runs before provider/extension init, with the prepared schemas written into `config["tools"]` as the core-owned compatibility shim for older implementations.
- Updated the plugin API direction so canonical UI hooks are `get_ui_elements(config, context=None)`, while adapters still accept legacy `get_ui_elements(self)`, `get_ui_elements(self, config)`, and `get_ui_elements(self, config, tags, models)` implementations.
- Added optional `context` support to provider/extension/feature `initialize_request(...)` so new implementations can inspect `tools` and `available_tools` without reading them from `state["config"]`.
- Added a built-in `ToolGatingFeature` with `disable_all_tools` and registered it in the portable default terminal app config.
- Updated Gemini `web_fetch` fallback summarization to set `disable_all_tools=True` for its internal request while keeping `tool_choice: "none"` as a provider hint.
- Kept provider tool extensions serialization-only in the final version by removing the temporary `state["config"]` fallback and relying on the pre-init `config["tools"]` shim instead.
- Added focused core tests for available tools, UI context, effective tool filtering, and payload suppression, plus a Gemini unit regression for the internal fallback config and updated real app integration coverage.