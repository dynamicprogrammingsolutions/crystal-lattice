# Plan: Model- and Tag-Based Plugin Dependency Resolution

## Goal

- Replace the unused, provider-local `detect_capabilities(config)` with a cross-plugin, model- and tag-based dependency system.
- Allow Core to automatically enable/disable plugins per-request based on provider, selected model(s), and configuration.
- Introduce three new methods:
  - `get_models(config)`
  - `get_tags(config, models)`
  - `required_tags()`
- Support provider extensions, features, and tools participating in model discovery and dependency tagging.
- Make dependency checks deterministic, pure (config + model list only), and cached so they are not recomputed when inputs are unchanged.

## High-Level Design

### New concepts

- **ModelDescriptor** (language-neutral type):
  - Represents a model available for a given provider/config.
  - Minimal contract:
    - `id: string` — model identifier (e.g., `"gpt-4o"`, `"llama3:8b"`).
    - `data: dict (optional)` — arbitrary provider/plugin-specific metadata (capabilities, context window, pricing, etc.).

- **Tags**:
  - String identifiers that describe available capabilities or environment conditions for the current `(provider, config, model list)`.
  - Examples:
    - `"supports_tools"`, `"supports_thinking"`, `"supports_streaming"`
    - `"http_outbound_allowed"`, `"filesystem_read_allowed"`
    - `"ext:openai_tools"`, `"feature:web_search"`

- **Required tags**:
  - String identifiers a plugin needs to be present in the global tag set for it to be enabled in the pipeline.
  - A plugin is **enabled** only if all of its `required_tags()` are present in the final tag set.

### Method semantics

- `get_models(config) -> list[ModelDescriptor]`
  - Entry point for model discovery for the current provider and configuration.
  - Primary implementation is expected on the **provider plugin**.
  - Other plugin types may:
    - **Modify** the discovered list (filter, annotate, reorder).
    - **Provide** models when the provider does not implement `get_models`.
  - Core orchestrates this as a pure function of `config` and the registered plugins (no request/session state).
  - Result is cached by Core per `(provider, normalized_config)`.

- `get_tags(config, models) -> list[string]`
  - Pure function implemented by **all plugin types, including the provider and tool plugins**.
  - Input:
    - `config`: final resolved flat config passed to Core.
    - `models`: list of `ModelDescriptor` produced by `get_models` for this `(provider, config)`.
  - Output:
    - Tags contributed by this plugin (zero or more). Must be deterministic given `(config, models)`.
  - Core will cache each plugin's `get_tags` result per `(plugin, provider, normalized_config, normalized_models)`.

- `required_tags() -> list[string]`
  - Implemented by **all plugin types except the provider plugin**.
  - Returns a static list of tags that **must** be present in the final tag set for the plugin to be enabled.
  - Does **not** take `config` or `models`; if a plugin wishes to become a no-op based on config, it should still handle that internally.

### Core dependency resolution algorithm

1. **Select provider**:
   - From `config["provider"]`, select the provider plugin/wrapper.
   - If none, raise the existing provider selection error.

2. **Compute model list** via `get_models(config)`:
   - See "Model discovery pipeline" below.

3. **Compute global tags** for the current `(config, models)` and current set of **candidate plugins**:
   - Candidate plugins include:
     - The selected provider plugin (always considered enabled by config, no `required_tags`).
      - All registered provider extensions registered with the provider (selection is controlled via tags).

     - All registered feature plugins.
     - All registered tool plugins.
   - For each **currently enabled** plugin (including provider) call `get_tags(config, models)` and union the results into a global `available_tags` set.

4. **Eliminate plugins with unsatisfied requirements**:
   - For each non-provider plugin, check `required_tags()` against `available_tags`.
   - If any `required_tag` is missing from `available_tags`, mark the plugin as **disabled**.

5. **Iterate to a fixpoint**:
   - Because tags can change when plugins are disabled (their `get_tags` contributions are removed), we run the above steps until no further plugins are disabled:
     - Start with `enabled_plugins = all_candidates`.
     - Loop:
       - Compute `available_tags` from `get_tags` across `enabled_plugins`.
       - Compute `next_enabled_plugins` by applying `required_tags` filtering.
       - If `next_enabled_plugins == enabled_plugins`, stop.
       - Otherwise assign `enabled_plugins = next_enabled_plugins` and repeat.

6. **Use final `enabled_plugins` for this request**:
   - Core uses this filtered set for:
     - Provider extensions in the hot/cold paths.
     - Features in the cold path transforms.
     - Tools surfaced via `get_tool_schemas`.

7. **Caching**:
   - Dependency resolution is associated with a specific **provider**, **config**, and **model list**:
     - A stable cache key is derived from `(provider_name, normalized_config, normalized_models)`.
     - If this key matches a previous resolution result, Core returns the cached `enabled_plugins` and `available_tags` without recomputing `get_tags`/`required_tags`.
   - Normalization will be defined per language; for Python this can be implemented via deterministic JSON dumps or a frozen-structure representation.


## Model Discovery Pipeline (`get_models`)

### Provider responsibility

- Provider plugins gain an optional instance method:

  ```python
  class ProviderPlugin(BasePlugin, Protocol):
      def get_models(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:  # optional
          """Return a list of ModelDescriptor-like dicts for this provider.

          Each entry MUST include an `"id"` key (str). Additional keys are
          provider-defined; a conventional `"data"` dict may hold capabilities,
          context window, pricing, etc.
          """
  ```

- If implemented, this is the **authoritative source** of the initial model list for a provider.
- Providers are free to:
  - Return a static list.
  - Call a remote API to enumerate models.
  - Infer supported models from config.

### Other plugins participating

- Provider extensions, features, and tools may declare an optional method to **transform** or **provide** models:

  ```python
  class ProviderExtensionPlugin(BasePlugin, Protocol):
      # existing methods...

      def get_models(
          self,
          config: Dict[str, Any],
          models: List[Dict[str, Any]],
      ) -> List[Dict[str, Any]]:  # optional
          """Statelessly transform or provide ModelDescriptors.

          - `models` is the current list (possibly empty).
          - Return a new list; do not mutate `models` in-place.
          """

  class FeaturePlugin(BasePlugin, Protocol):
      # existing methods...

      def get_models(
          self,
          config: Dict[str, Any],
          models: List[Dict[str, Any]],
      ) -> List[Dict[str, Any]]:  # optional
          ...

  class ToolPlugin(BasePlugin, Protocol):
      # existing methods...

      def get_models(
          self,
          config: Dict[str, Any],
          models: List[Dict[str, Any]],
      ) -> List[Dict[str, Any]]:  # optional
          ...
  ```

- Semantics:
  - All `get_models` methods are **pure** and depend only on `config` (and upstream `models`).
  - Extensions and features **must not** perform network I/O or rely on shared provider state inside `get_models`.
  - A plugin may **supply** models when `models` is empty (e.g., a global registry plugin for a given provider family).

### Core orchestration for `get_models`

- New internal method on `AgentCore` (Python example):

  ```python
  class AgentCore:
      def _get_models_for_config(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
          """Return cached or freshly-computed ModelDescriptors for this config."""
  ```

- Algorithm:
  1. Derive `provider_name` from `config["provider"]` and select the corresponding provider wrapper.
  2. Build a cache key `(provider_name, normalized_config)`.
  3. If present in `self._models_cache`, return cached models.
  4. Else:
     - Initialize `models: List[Dict[str, Any]] = []`.
     - If provider implements `get_models(config)`, call it and assign the result to `models`.
     - For each registered plugin in deterministic order:
       - Provider extensions for this provider.
       - Feature plugins.
       - Tool plugins.
       - If the plugin implements `get_models(config, models)`, call it and assign its return as the new `models`.
     - Validate that each entry has a string `"id"`.
     - Store models into `self._models_cache[key]` and return.

- This method is used as the single source of `models` for:
  - Dependency resolution (`get_tags` / `required_tags`).
  - Any future `AgentCore.get_models(config)` public API.


## Tag Computation (`get_tags`) and Requirements (`required_tags`)

### Protocol additions

- All plugin protocols gain:

  ```python
  class ProviderPlugin(BasePlugin, Protocol):
      # existing methods...

      def get_tags(
          self,
          config: Dict[str, Any],
          models: List[Dict[str, Any]],
      ) -> List[str]:
          """Return capability/environment tags for this provider.

          Pure function; must not depend on mutable shared state.
          """

  class ProviderExtensionPlugin(BasePlugin, Protocol):
      # existing methods...

      def get_tags(
          self,
          config: Dict[str, Any],
          models: List[Dict[str, Any]],
      ) -> List[str]:
          ...

      def required_tags(self) -> List[str]:
          """Tags that must be present for this extension to be enabled."""

  class FeaturePlugin(BasePlugin, Protocol):
      # existing methods...

      def get_tags(
          self,
          config: Dict[str, Any],
          models: List[Dict[str, Any]],
      ) -> List[str]:
          ...

      def required_tags(self) -> List[str]:
          ...

  class ToolPlugin(BasePlugin, Protocol):
      # existing methods...

      def get_tags(
          self,
          config: Dict[str, Any],
          models: List[Dict[str, Any]],
      ) -> List[str]:
          ...

      def required_tags(self) -> List[str]:
          ...
  ```

- Provider plugins **do not** implement `required_tags()` (they are selected directly by config), but they do implement `get_tags`.
- All plugins must keep `get_tags` **pure**: no I/O, no shared-state access, deterministic for given `(config, models)`.

### Core orchestration for tags and dependencies

- New internal method in AgentCore for dependency resolution (Python example):

  ```python
  class AgentCore:
      def _resolve_plugins_for_config(
          self,
          config: Dict[str, Any],
      ) -> Tuple[
          ProviderWrapper,
          List[ProviderExtensionWrapper],
          List[FeatureWrapper],
          List[ToolWrapper],
          List[str],  # final tag set
      ]:
          """Return enabled plugins and tags for a given config.

          Uses cached results when (provider, config, models) are unchanged.
          """
  ```

- Algorithm sketch:

  1. Compute `models = _get_models_for_config(config)`.
  2. Build `dep_key = (provider_name, normalized_config, normalized_models)`.
  3. If `dep_key` exists in `self._dependency_cache`, return cached enabled plugin lists and tag set.
  4. Else:
     - Build `candidate_extensions`, `candidate_features`, `candidate_tools` as all registered for this provider.
     - Set `enabled_extensions = candidate_extensions`, etc.
     - Loop until fixpoint:
       - Compute `available_tags`:
         - Start with empty set.
         - For provider and each currently enabled extension/feature/tool:
           - Use a per-plugin `tags_cache[(plugin_id, dep_key)]` if present.
           - Else call `plugin.get_tags(config, models)` and cache the result.
           - Add returned tags into `available_tags`.
       - Derive `next_enabled_*` by keeping only plugins whose `set(plugin.required_tags()).issubset(available_tags)`.
       - If `next_enabled_*` collections are identical to `enabled_*`, stop.
       - Otherwise assign and repeat.
     - Store final enabled plugin lists and `available_tags` into `self._dependency_cache[dep_key]` and return.

- This method is used at the beginning of:
  - `send_request` / `send_request_stream` / `send_request_stream_async` to decide which provider extensions and features participate.
  - `get_tool_schemas(config)` to decide which tools are exposed for the current agent.


## Removal/Replacement of `detect_capabilities`

### Protocol change

- `ProviderPlugin.detect_capabilities(config: Dict[str, Any]) -> List[str]` is currently defined but unused.
- Plan:
  - **Mark as deprecated in `TYPES_AND_PROTOCOLS.md`** and the Python protocol.
  - Remove any references from docs and code in the same change that introduces `get_models`/`get_tags`/`required_tags`.
  - Migrate any hypothetical future uses to the tag-based system instead of capability strings.

### Mapping from old idea to new system

- Old concept: `detect_capabilities(config) -> ["tools", "citations", ...]`.
- New concept: provider `get_tags(config, models)` returning tags like:
  - `"supports_tools"`, `"supports_citations"`, `"supports_reasoning"`.
- Plugins that need those capabilities declare `required_tags()` accordingly:
  - Example: `openai_tools_extension.required_tags() -> ["supports_tools"]`.


## File-Level Changes (Python Core)

1. `core/python/agent_core/types.py`
   - Add `ModelDescriptor` description to docstring in `TYPES_AND_PROTOCOLS.md` and mirror here as "dict with at least `id: str`".
   - Extend `ProviderPlugin`, `ProviderExtensionPlugin`, `FeaturePlugin`, and `ToolPlugin` protocols with `get_models` / `get_tags` / `required_tags` as per above.
   - Deprecate and then remove `ProviderPlugin.detect_capabilities`.

2. `core/python/agent_core/core.py`
   - Add internal caches to `AgentCore` (immutable dicts replaced on update):
     - `_models_cache: Dict[Tuple[str, Any], List[Dict[str, Any]]]`.
     - `_dependency_cache: Dict[Tuple[str, Any, Any], Tuple[...enabled plugins..., List[str]]]`.
     - `_tags_cache: Dict[Tuple[str, Any], List[str]]` keyed by `(plugin_id, dep_key)`.
   - Implement `_normalize_config(config)` and `_normalize_models(models)` utility functions (pure; no I/O) for cache keys.
   - Implement `_get_models_for_config(config)` and `_resolve_plugins_for_config(config)` as described.
   - Update:
     - `send_request` / `send_request_stream` / `send_request_stream_async` to use the resolved plugin lists instead of all registered plugins.
     - `get_tool_schemas(config)` to only include schemas from enabled tools.

3. `core/python/agent_core/plugin/*.py` (wrappers)
   - Provider wrapper:
     - Expose `get_models(config)` and `get_tags(config, models)` that delegate to the underlying plugin instance if implemented, else return reasonable defaults (empty list / empty tags).
   - Extension/feature/tool wrappers:
     - Mirror `get_models`, `get_tags`, `required_tags` on wrappers, delegating to plugin instances when implemented; fall back to sensible defaults:
       - `get_models(config, models)` default: return `models` unchanged.
       - `get_tags(config, models)` default: `[]`.
       - `required_tags()` default: `[]`.


## Built-in Plugin Updates (Python)

1. `core/python/plugins/openai_provider.py`
   - Implement `get_models(config)` with a simple initial strategy (static list or call OpenAI/Ollama as appropriate).
   - Implement `get_tags(config, models)` to emit tags like:
     - `"supports_streaming"` if streaming APIs are available.
     - `"supports_tools"` if the selected/default model supports tool calling.
     - `"supports_thinking"` for models with reasoning capabilities (e.g., via metadata in `data`).

2. `core/python/plugins/openai_tools_extension.py`
   - Implement `required_tags() -> ["supports_tools"]`.
   - Implement `get_tags(config, models)` to emit an identifying tag such as `"ext:openai_tools"`.

3. `core/python/plugins/ollama_thinking_extension.py`
   - Implement `required_tags()` to require `"supports_thinking"` or a provider/model-specific tag.
   - Implement `get_tags` for identification and potential downstream dependency.

4. `core/python/plugins/request_options_feature.py`, `system_message_feature.py`
   - Implement `get_tags` (even if just identification tags).
   - Use `required_tags` only if these features depend on, e.g., `"filesystem_read_allowed"` or similar future tags.

5. Dummy plugins used in tests (`core/python/tests/dummy_*.py`)
   - Implement minimal versions of `get_tags` / `required_tags` needed for tests.
   - Optionally implement `get_models` to support unit tests for the model pipeline.


## Testing

1. **New tests for dependency resolution** (e.g., `core/python/tests/test_plugin_dependency_tags.py`):
   - Create dummy provider, extensions, features, and tools with:
     - Predictable `get_models` output.
     - Well-defined `get_tags` and `required_tags` relationships.
   - Scenarios:
     - A feature requires a tag that only a specific extension provides; disabling that extension disables the feature as well.
     - Circular-ish dependencies resolved by fixpoint iteration (ensure termination and expected final enabled set).
     - Provider-only tags enabling/disabling features/tools.

2. **Caching behavior tests**:
   - Verify that repeated calls to `send_request` with the same `config` and model list do **not** recompute `get_models` / `get_tags` (use counters in dummy plugins).
   - Verify that changing `config` (e.g., selected model id) invalidates the relevant entries and recomputes.

3. **Integration tests**:
   - Extend or add tests in `core/python/tests/test_integration.py` (or new file) to:
     - Register a tool that requires a tag only provided for a given model; changing the model in config should automatically hide the tool schemas.
     - Use streaming and non-streaming paths to ensure the same dependency resolution is applied consistently.


## Documentation Updates

1. `TYPES_AND_PROTOCOLS.md`
   - Add `ModelDescriptor` type definition.
   - Update plugin protocols to include `get_models`, `get_tags`, and `required_tags` as described.
   - Mark `detect_capabilities` as deprecated/removed and describe the tag-based replacement.

2. `ARCHITECTURE.md`
   - Add a short subsection under Configuration or Plugin Architecture describing:
     - Model discovery.
     - Tag computation.
     - Automatic plugin enable/disable via `required_tags`.

3. `docs/api/core-sdk.md`
   - If a public `AgentCore.get_models(config)` API is added, document it.
   - Document that `get_tool_schemas(config)` respects the tag-based dependency system and only returns schemas from enabled tools.

4. `PROJECT_PLAN.md`
   - Link this plan as the concrete implementation of the Stage 2 "Provider capability detection" item.
   - Optionally adjust wording there from "Provider capability detection" to "Model- and tag-based plugin capability detection".


## Open Questions / Follow-Ups

- **Model selection vs. model enumeration**:
  - For now, `get_models(config)` is designed for enumeration; Core does not pick a model automatically. Model choice continues to be driven by `config["model"]`.
- **Cross-language parity**:
  - This plan describes Python changes; a follow-up plan/doc may be needed to mirror the same design in the JavaScript core once it exists.
- **UI integration**:
  - Later, the Application / Frontend layers can expose `get_models` and the tag set to drive provider/model pickers and show which plugins will be active.


## Implementation Status (Python core, 2025-11)

The Python core largely implements this plan. This section summarizes
where the implementation intentionally deviates from the original design
and which follow-up items remain.

### Deviations from original plan

- Tool plugins do **not** implement `get_models(config, models)` and do
  **not** participate in model enumeration. Only providers,
  provider extensions, and features contribute to the model list. Tools
  still implement `get_tags(config, models)` / `required_tags()` and are
  enabled/disabled via the tag-based fixpoint.
- The Python `AgentCore` now supports multiple registered providers. When
  more than one provider is registered, it selects the provider from
  `config["provider"]` (by short name or fully-qualified class path) for
  each request. When exactly one provider is registered, `config["provider"]`
  remains optional for backward compatibility.
- Provider extensions are registered explicitly with the provider via
  `register_provider(..., extensions=[...])` instead of being matched by
  a `target_provider` attribute. Tag-based enablement still controls
  whether a registered extension is active for a given request.

### Testing and documentation status

- Tag-based dependency resolution and caching are exercised indirectly by
  existing tests (OpenAI-compatible provider, `OpenAIToolsExtension`,
  `OllamaThinkingExtension`, `RequestOptionsFeature`,
  `SystemMessageFeature`, and the dummy plugins). A dedicated
  `test_plugin_dependency_tags.py` file, as sketched in this plan, has
  not been added yet.
- `TYPES_AND_PROTOCOLS.md` has been updated with `ModelDescriptor` and
  the tag-based plugin protocols. `ARCHITECTURE.md`,
  `docs/api/core-sdk.md`, and `PROJECT_PLAN.md` have not yet been
  updated to reference this plan explicitly or to describe the
  tag-based dependency system in detail.
