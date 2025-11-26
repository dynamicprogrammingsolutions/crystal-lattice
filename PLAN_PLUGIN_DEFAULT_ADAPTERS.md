# Plan: Plugin Optional Methods via Default Adapters

## 1. Goals

- Make plugin protocol methods *effectively optional* by providing robust default implementations.
- Move all defaulting / shape-normalization logic into dedicated adapter classes, not into core or wrappers.
- Fix incorrect default behaviors (notably `FeaturePlugin.to_native_messages` / `ProviderExtensionPlugin.to_native_messages`).
- Keep the existing processing pipeline and public API of `AgentCore` intact.
- Ensure existing real plugins under `core/python/plugins` remain correct and simpler (only non-trivial logic stays in plugins).
- Cover the new behavior with unit and integration tests.


## 2. Current State & Issues (short)

- Protocols live in `core/python/agent_core/types.py` (`ProviderPlugin`, `ProviderExtensionPlugin`, `FeaturePlugin`, `ToolPlugin`).
- Wrappers in `core/python/agent_core/plugin/` (`provider.py`, `extension.py`, `feature.py`, `tool.py`) duck-type plugin instances and:
  - Repeatedly check `hasattr` for optional methods.
  - Implement ad-hoc default behaviors.
- Core (`core/python/agent_core/core.py`) further compensates for plugin diversity via:
  - `_coerce_models_result` and `_coerce_tags_result` to normalize return types.
  - Knowledge of some wrapper defaults.
- Known correctness issue: in `FeatureWrapper` and `ExtensionWrapper`:
  - `to_native_messages(messages, native_messages)` currently falls back to **`messages`**, but the pipeline expects provider-native `native_messages`.
  - This is inconsistent with `_pre_request` where provider, then extensions, then features transform **provider-native history**.


## 3. Design: Default Adapter Layer

### 3.1 New adapter classes

Add a new module `core/python/agent_core/plugin/adapters.py` containing four adapters:

- `ProviderDefaultsAdapter`  – wraps a provider implementation and guarantees the full `ProviderPlugin` interface plus sane defaults.
- `ProviderExtensionDefaultsAdapter` – wraps provider extensions and provides identity-style defaults for optional hooks.
- `FeatureDefaultsAdapter` – wraps feature plugins, fixing default stateless transforms and lifecycle hooks.
- `ToolDefaultsAdapter` – wraps tool plugins and centralizes default tags, schemas, and result formatting.

Each adapter:

- Stores the underlying implementation (e.g., `self.impl`).
- Normalizes identity (`name`, `version`) from `impl` or its class.
- Implements **all** protocol methods.
- Delegates to the underlying implementation when present, otherwise uses a default behavior.
- Normalizes return types (lists/dicts/strings) so that core and wrappers can assume correct shapes.

Wrappers will construct adapters internally and then call only adapter methods (no `hasattr` / special casing).


### 3.2 Methods with default implementations (with concrete behavior)

Below are the methods that will receive default implementations in adapters (non-exhaustive code sketches; final code will live in `adapters.py`).

#### 3.2.1 Shared BasePlugin defaults

These apply to providers, extensions, features, and tools via a small mixin used by all adapters:

```python
class _BasePluginDefaults:
    def _identity(self, value):
        return value

    def _safe_dict(self, value: Any) -> Dict[str, Any]:
        return value if isinstance(value, dict) else {}

    def _safe_list(self, value: Any) -> List[Any]:
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        try:
            return list(value)  # may still raise; caught by caller
        except Exception:
            return []

    def get_config_schema(self) -> Dict[str, Any]:
        fn = getattr(self.impl, "get_config_schema", None)
        if callable(fn):
            return self._safe_dict(fn())
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        fn = getattr(self.impl, "get_ui_elements", None)
        if callable(fn):
            return self._safe_list(fn())
        return []
```

This replaces all wrapper-level `hasattr(..., "get_config_schema")` / `get_ui_elements` checks.

#### 3.2.2 ProviderDefaultsAdapter

Key defaults (inspired by `OpenAICompatibleProvider` and `EchoOpenAILikeProvider`):

```python
class ProviderDefaultsAdapter(_BasePluginDefaults, ProviderPlugin):
    def __init__(self, impl: Any):
        self.impl = impl
        self.name = getattr(impl, "name", impl.__class__.__name__)
        self.version = getattr(impl, "version", "unknown")

    # state lifecycle
    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        fn = getattr(self.impl, "init", None)
        if callable(fn):
            state = fn(config)
            return state if isinstance(state, dict) else {"config": dict(config)}
        # default: config-only state, matching existing providers
        return {"config": dict(config)}

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        fn = getattr(self.impl, "initialize_request", None)
        if callable(fn):
            new_state = fn(native_messages, state)
            return new_state if isinstance(new_state, dict) else state
        return state

    # message conversion
    def to_native_messages(
        self, messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        fn = getattr(self.impl, "to_native_messages", None)
        if callable(fn):
            out = fn(messages, state)
            return self._safe_list(out)
        # Default: OpenAI-style mapping from core messages
        return [
            {"role": m.get("role", "user"), "content": m.get("content", "")}
            for m in messages
        ]

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        fn = getattr(self.impl, "from_native_messages", None)
        if callable(fn):
            out = fn(native_messages, state)
            return self._safe_list(out)
        # Default: inspired by OpenAICompatibleProvider.from_native_messages
        finals: List[Dict[str, Any]] = []
        for m in native_messages:
            if not isinstance(m, dict):
                continue
            if not ("role" in m or "content" in m or "reasoning" in m):
                continue
            msg: Dict[str, Any] = {
                "role": m.get("role", "assistant"),
                "content": m.get("content", ""),
            }
            if "reasoning" in m:
                msg["reasoning"] = m.get("reasoning")
            finals.append({**msg, "metadata": {}})
        return finals

    # models / tags
    def get_models(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        fn = getattr(self.impl, "get_models", None)
        if callable(fn):
            out = fn(config)
            models = [m for m in self._safe_list(out) if isinstance(m, dict)]
        else:
            # Default: if config["model"] is present, expose it as a single model descriptor
            model = config.get("model")
            models = [{"id": model}] if isinstance(model, str) and model else []
        return models

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        fn = getattr(self.impl, "get_tags", None)
        if callable(fn):
            raw = fn(config, models)
        else:
            raw = []
        return [str(t) for t in self._safe_list(raw)]

    def to_display_format(
        self, message: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        fn = getattr(self.impl, "to_display_format", None)
        if callable(fn):
            out = fn(message, state)
            return out if isinstance(out, dict) else message
        return message

    # NOTE: `call_api`, `stream_api`, `process_chunk`, `finalize` remain required
    # provider responsibilities; adapters will only wrap/normalize results,
    # not invent generic I/O behavior.
```

For I/O methods (`call_api`, `stream_api`, `process_chunk`, `finalize`) the adapter will simply delegate and lightly validate types; they are considered **required** for a provider.

#### 3.2.3 ProviderExtensionDefaultsAdapter

Key defaults (fixing `to_native_messages` and `from_native_messages`):

```python
class ProviderExtensionDefaultsAdapter(_BasePluginDefaults, ProviderExtensionPlugin):
    def __init__(self, impl: Any):
        self.impl = impl
        self.name = getattr(impl, "name", impl.__class__.__name__)
        self.version = getattr(impl, "version", "unknown")

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        fn = getattr(self.impl, "init", None)
        if callable(fn):
            new_state = fn(config, state)
            return new_state if isinstance(new_state, dict) else state
        return state

    def get_models(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        fn = getattr(self.impl, "get_models", None)
        if callable(fn):
            out = fn(config, models)
            return [m for m in self._safe_list(out) if isinstance(m, dict)] or list(models)
        return list(models)

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        fn = getattr(self.impl, "get_tags", None)
        raw = fn(config, models) if callable(fn) else []
        return [str(t) for t in self._safe_list(raw)]

    def required_tags(self) -> List[str]:
        fn = getattr(self.impl, "required_tags", None)
        raw = fn() if callable(fn) else []
        return [str(t) for t in self._safe_list(raw)]

    # FIXED default stateless transforms
    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        fn = getattr(self.impl, "to_native_messages", None)
        if callable(fn):
            out = fn(messages, native_messages)
            return self._safe_list(out)
        # Correct default: identity over provider-native history
        return list(native_messages)

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        fn = getattr(self.impl, "from_native_messages", None)
        if callable(fn):
            out = fn(native_messages, messages)
            return self._safe_list(out)
        return list(messages)

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        fn = getattr(self.impl, "initialize_request", None)
        if callable(fn):
            new_state = fn(native_messages, state)
            return new_state if isinstance(new_state, dict) else state
        return state

    def process_chunk(...):
        # delegate if present, else identity over messages/state
        fn = getattr(self.impl, "process_chunk", None)
        if callable(fn):
            return fn(native_chunk, state, partial_messages, final_messages, native_messages)
        return partial_messages, final_messages, native_messages, state

    def finalize(...):
        fn = getattr(self.impl, "finalize", None)
        if callable(fn):
            return fn(final_messages, native_messages, state)
        return final_messages, native_messages, state
```

#### 3.2.4 FeatureDefaultsAdapter

Very similar to `ProviderExtensionDefaultsAdapter`, but without `process_chunk` and with feature-specific tags:

```python
class FeatureDefaultsAdapter(_BasePluginDefaults, FeaturePlugin):
    def __init__(self, impl: Any):
        self.impl = impl
        self.name = getattr(impl, "name", impl.__class__.__name__)
        self.version = getattr(impl, "version", "unknown")

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        fn = getattr(self.impl, "init", None)
        if callable(fn):
            new_state = fn(config, state)
            return new_state if isinstance(new_state, dict) else state
        return state

    def get_models(...):  # same pattern as extension
        ...

    def get_tags(...):
        ...

    def required_tags(...):
        ...

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        fn = getattr(self.impl, "to_native_messages", None)
        if callable(fn):
            out = fn(messages, native_messages)
            return self._safe_list(out)
        # Correct default: identity on provider-native history
        return list(native_messages)

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        fn = getattr(self.impl, "from_native_messages", None)
        if callable(fn):
            out = fn(native_messages, messages)
            return self._safe_list(out)
        return list(messages)

    def initialize_request(...):  # same as extension
        ...

    def finalize(...):  # same as extension
        ...
```

#### 3.2.5 ToolDefaultsAdapter

Defaults guided by `FileReaderTool` and `FileWriterTool`:

```python
class ToolDefaultsAdapter(_BasePluginDefaults, ToolPlugin):
    def __init__(self, impl: Any):
        self.impl = impl
        self.name = getattr(impl, "name", impl.__class__.__name__)
        self.version = getattr(impl, "version", "unknown")

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        fn = getattr(self.impl, "init", None)
        if callable(fn):
            state = fn(config)
            return state if isinstance(state, dict) else {"config": dict(config)}
        return {"config": dict(config)}

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        fn = getattr(self.impl, "get_tags", None)
        raw = fn(config, models) if callable(fn) else []
        return [str(t) for t in self._safe_list(raw)]

    def required_tags(self) -> List[str]:
        fn = getattr(self.impl, "required_tags", None)
        raw = fn() if callable(fn) else []
        return [str(t) for t in self._safe_list(raw)]

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        fn = getattr(self.impl, "get_tool_schemas", None)
        if callable(fn):
            out = fn(state)
            return [s for s in self._safe_list(out) if isinstance(s, dict)]
        return []

    def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        fn = getattr(self.impl, "execute_tool", None)
        if callable(fn):
            out = fn(tool_name, arguments, state)
            return out if isinstance(out, dict) else {"success": False, "error": "invalid tool result"}
        return {"success": False, "error": f"Unknown tool: {tool_name}"}

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        fn = getattr(self.impl, "format_tool_result", None)
        if callable(fn):
            out = fn(result, state)
            return str(out)
        # Default mirrors ToolWrapper today
        if result.get("success"):
            return f"Result: {result.get('result')}"
        return f"Error: {result.get('error')}"
```


## 4. Wrapper and Core Changes

### 4.1 Wrappers use adapters, no `hasattr` / manual defaults

- `FeatureWrapper` (`core/python/agent_core/plugin/feature.py`):
  - In `__init__`, wrap the plugin: `self.plugin = FeatureDefaultsAdapter(plugin_class())`.
  - All methods become thin pass-throughs to adapter methods (no attribute checks, no manual defaults):
    - `init`, `get_config_schema`, `get_ui_elements`, `get_models`, `get_tags`, `required_tags`,
      `to_native_messages`, `from_native_messages`, `initialize_request`, `finalize`.
- `ExtensionWrapper` (`extension.py`):
  - Same pattern with `ProviderExtensionDefaultsAdapter`.
- `ProviderWrapper` (`provider.py`):
  - Construct `self.plugin = ProviderDefaultsAdapter(plugin_class())`.
  - Remove `hasattr` checks in `get_config_schema`, `get_ui_elements`, `get_models`, `get_tags`, `from_native_messages`, `to_display_format`.
  - Keep state management, streaming helpers, and `_merge_history` unchanged.
- `ToolWrapper` (`tool.py`):
  - Wrap plugin via `ToolDefaultsAdapter` and drop `hasattr` / default logic from wrapper methods.

### 4.2 Core simplification (`AgentCore`)

- Remove `_coerce_models_result` and `_coerce_tags_result` from `core/python/agent_core/core.py`; use adapter-normalized outputs instead.
- `_get_models_for_config`:
  - Directly do:
    - `models = provider.get_models(config)`.
    - For each extension: `models = ext.get_models(config, models)`.
    - For each feature: `models = feat.get_models(config, models)`.
  - Keep final validation that each model is a dict with non-empty `id` string.
- `_resolve_plugins_for_config`:
  - Assume `get_tags` always returns `List[str]`; remove calls to `_coerce_tags_result`.
  - `required_tags` likewise returns `List[str]` from adapters.
- No changes to the high-level request/streaming pipeline besides relying on adapters.


## 5. Plugin Implementations to Update

Real plugin modules under `core/python/plugins` (primary focus for defaults and cleanup):

- Providers:
  - `core/python/plugins/openai_provider.py` (OpenAICompatibleProvider)
  - `core/python/plugins/echo_openai_like_provider.py` (EchoOpenAILikeProvider)
- Provider extensions:
  - `core/python/plugins/ollama_thinking_extension.py` (OllamaThinkingExtension)
  - `core/python/plugins/openai_tools_extension.py` (OpenAIToolsExtension)
- Features:
  - `core/python/plugins/request_options_feature.py` (RequestOptionsFeature)
  - `core/python/plugins/system_message_feature.py` (SystemMessageFeature)
- Tools:
  - `core/python/plugins/file_reader_tool.py` (FileReaderTool)
  - `core/python/plugins/file_writer_tool.py` (FileWriterTool)

Additional plugin-like classes used only for tests (must be kept in sync with adapter behavior):

- `core/python/tests/dummy_provider.py`
- `core/python/tests/dummy_extension.py`
- `core/python/tests/dummy_feature.py`
- `core/python/tests/dummy_transform_feature.py`
- `core/python/tests/dummy_tool.py`

Implementation guidelines:

- Remove methods from plugins where the body becomes identical to adapter defaults (e.g., trivial `get_models` that just `return list(models)`).
- Keep methods that encode real behavior (e.g., tags, config schema, request shaping, thinking/tool logic).
- Ensure provider plugins still implement the core I/O methods (`call_api`, `stream_api`, `process_chunk`, `finalize`).


## 6. Testing Strategy (high level)

### 6.1 New unit tests for adapters

- Add tests for `ProviderDefaultsAdapter`, `ProviderExtensionDefaultsAdapter`, `FeatureDefaultsAdapter`, `ToolDefaultsAdapter` (e.g., in `core/python/tests/test_plugin_default_adapters.py`):
  - Minimal plugin classes implementing only one or two methods; verify all other methods behave according to defaults.
  - Verify `FeatureDefaultsAdapter.to_native_messages` and `ProviderExtensionDefaultsAdapter.to_native_messages` return `native_messages` when underlying plugin omits the method.
  - Check list/dict normalization for `get_models`/`get_tags`/`required_tags` when underlying plugins return `None`, tuples, sets, or non-iterables.
  - Confirm `ToolDefaultsAdapter.execute_tool` and `format_tool_result` behavior matches existing wrappers for success/failure cases.

### 6.2 Regression tests on existing behavior

- Reuse and extend existing tests to ensure no behavior change except the intended `to_native_messages` default fix:
  - Provider and extension tests:
    - `core/python/tests/test_openai_compat_ollama.py`
    - `core/python/tests/test_openai_tools_with_ollama.py`
    - `core/python/tests/test_ollama_thinking_qwen3.py`
    - `core/python/tests/test_ollama_thinking_qwen3_stream.py`
    - `core/python/tests/test_openai_tools_extension_unit.py`
  - Feature tests:
    - `core/python/tests/test_system_message_feature.py`
    - `core/python/tests/test_system_message_integration_with_echo.py`
    - `core/python/tests/test_request_options_feature.py`
    - `core/python/tests/test_feature_transform.py`
  - Tool tests:
    - `core/python/tests/test_tool_adapter.py` (extend or duplicate patterns for new adapter layer)
    - Example-based tests under `core/python/examples/tests/test_example11_openai_tools_file_reader.py`.

Key verifications:

- `AgentCore.get_config_schema` and `AgentCore.get_ui_schema` aggregate schemas/UI for providers, extensions, features, and tools unchanged.
- Model discovery and tag-based dependency resolution (`_get_models_for_config`, `_resolve_plugins_for_config`) still produce the same enabled plugins/tags for existing configs.
- Request/response behavior is identical for:
  - Basic non-streaming flows (`test_core.py`, example tests).
  - Streaming flows using OpenAI-compatible provider plus thinking/tools extensions.
- New default for feature/extension `to_native_messages` does not break any existing tests, and any change in behavior is explicitly asserted where appropriate.

### 6.3 Discover-and-register behavior

- Extend `core/python/tests/test_plugin_dependency_tags.py` or add a focused test to cover `AgentCore.discover_and_register` with classes missing some optional methods:
  - Ensure type classification (provider/extension/feature/tool) continues to rely only on the presence of core I/O methods, not adapter internals.
  - Verify discovered plugins still work end-to-end through adapters.


## 7. Implementation Order

1. Introduce `adapters.py` with the four adapters and shared helpers (no wrapper changes yet); add unit tests exercising adapters directly.
2. Update wrappers to use adapters, remove `hasattr` and manual default logic; adjust any failing tests.
3. Remove `_coerce_models_result` and `_coerce_tags_result` from `AgentCore`, updating `_get_models_for_config` and `_resolve_plugins_for_config` to rely on adapters.
4. Simplify real plugins under `core/python/plugins` to remove now-redundant identity methods.
5. Update dummy/test plugins only as necessary to align with the new default behaviors.
6. Run and fix any remaining test regressions, especially around streaming providers and feature/extension transforms.
