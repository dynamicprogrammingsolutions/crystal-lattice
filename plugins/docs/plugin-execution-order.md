# Execution order (providers, extensions, features, tools)

This page documents the runtime ordering of provider/plugins during a request.

It is shared across plugin kinds and matches the implementation in:

- `core/python/agent_core/core.py` (`_pre_request`, `send_request`, `send_request_stream`)
- `core/python/agent_core/plugin/provider.py` (`ProviderWrapper`)

## Dependency resolution (models + tags)

Before running a request, the core resolves which provider extensions, features, and tools are enabled for the **effective config**.

This same resolution is also used when computing UI schema (`AgentCore.get_ui_schema`) and tool schemas (`AgentCore.get_tool_schemas`).

High-level flow:

1) Select provider for `config`.
2) Compute `models` for the config.
3) Compute `tags` from the provider and enabled plugins.
4) Filter extensions/features/tools using `is_enabled()`, `required_tags()`, and `forbidden_tags()`.
5) Apply `force_enabled_plugins` config override.
6) Repeat steps (3–5) until the enabled set stops changing.

### Plugin enablement methods

Plugins can control their enablement through several mechanisms:

- **`required_tags()`**: Tags that must ALL be present for the plugin to be enabled.
- **`forbidden_tags()`**: Tags that must NOT be present for the plugin to be enabled.
- **`is_enabled(config, tags, models, context)`**: Custom method returning `True`/`False`/`None`.
  - Returns `True`: plugin is enabled (bypasses tag checks)
  - Returns `False`: plugin is disabled
  - Returns `None`: fall back to `required_tags()`/`forbidden_tags()` check

- **`force_enabled_plugins` config**: List of plugin IDs to always enable, overriding `is_enabled()` results.
- **`default_enabled` attribute**: Class attribute (`True`/`False`) for opt-in plugins. Set to `False` for plugins that require explicit enablement via `enabled_plugins` config.

Pseudocode (simplified):

```python
provider = select_provider(config)

models = provider.get_models(config)
for ext in provider.extensions:
    models = ext.get_models(config, models)
for feat in features:
    models = feat.get_models(config, models)

enabled_exts = list(provider.extensions)
enabled_feats = list(features)
enabled_tools = list(tools)

force_enabled = set(config.get("force_enabled_plugins", []))

def check_plugin_enabled(plugin, tags, models, context):
    # force_enabled_plugins overrides everything
    if plugin.name in force_enabled:
        return True
    
    # Check is_enabled method
    result = plugin.is_enabled(config, tags, models, context)
    if result is True:
        return True
    if result is False:
        return False
    
    # Fall back to tag-based check
    if not set(plugin.required_tags()).issubset(tags):
        return False
    if set(plugin.forbidden_tags()).intersection(tags):
        return False
    return True

while True:
    tags = set()
    tags |= set(provider.get_tags(config, models))
    tags |= set().union(*(ext.get_tags(config, models) for ext in enabled_exts))
    tags |= set().union(*(feat.get_tags(config, models) for feat in enabled_feats))
    tags |= set().union(*(tool.get_tags(config, models) for tool in enabled_tools))

    context = {
        "enabled_plugin_ids": {
            "extensions": [e.name for e in enabled_exts],
            "features": [f.name for f in enabled_feats],
            "tools": [t.name for t in enabled_tools],
        },
        "disabled_plugins": config.get("disabled_plugins", []),
        "force_enabled_plugins": list(force_enabled),
    }

    next_exts = [ext for ext in enabled_exts if check_plugin_enabled(ext, tags, models, context)]
    next_feats = [feat for feat in enabled_feats if check_plugin_enabled(feat, tags, models, context)]
    next_tools = [tool for tool in enabled_tools if check_plugin_enabled(tool, tags, models, context)]

    if next_exts == enabled_exts and next_feats == enabled_feats and next_tools == enabled_tools:
        break
    enabled_exts, enabled_feats, enabled_tools = next_exts, next_feats, next_tools
```

Runtime references:

- model caching + validation: `core/python/agent_core/core.py` (`_get_models_for_config`)
- tag-based dependency loop: `core/python/agent_core/core.py` (`_resolve_plugins_for_config`)

## Request-time ordering (high level)

For a request, the core runs:

1) **Tool schema injection**
2) **Init chain** (shared provider state)
3) **Stateless transforms** (core ↔ native)
4) **Stateful per-turn initialization** (`initialize_request` chain)
5) **I/O** (`call_api` or streaming)
6) **Finalize chain**
7) **Convert finals back to core**

## Concrete order (non-streaming)

Pseudocode:

```python
# tools
tool_states = [tool.init(config) for tool in tools]
tool_schemas = sum([tool.get_tool_schemas(st) for tool, st in zip(tools, tool_states)], [])
provider_config = {**config, "tools": tool_schemas}

# init chain (shared state)
state = provider.init(provider_config)
state = ext1.init(provider_config, state)
state = ext2.init(provider_config, state)
state = feat1.init(provider_config, state)

# core -> native
native = provider.to_native_messages(core_messages, state)
native = ext1.to_native_messages(core_messages, native)
native = feat1.to_native_messages(core_messages, native)

# stateful per-turn setup
native, state = provider.initialize_request(native, state)
native, state = ext1.initialize_request(native, state)
native, state = feat1.initialize_request(native, state)

# I/O
partials, finals_1, native, state = provider.call_api(native, state)

# finalize chain (provider then extensions then features)
finals_2, native, state = provider.finalize(native, state)
finals = finals_1 + finals_2
finals, native, state = ext1.finalize(finals, native, state)
finals, native, state = feat1.finalize(finals, native, state)

# native -> core
core_finals = provider.from_native_messages(finals, state)
core_finals = ext1.from_native_messages(finals, core_finals)
core_finals = feat1.from_native_messages(finals, core_finals)
```

Notes:

- Provider extensions run next to the provider on the hot path.
- Features do **not** run per-chunk; they only run on the cold path.

## Concrete order (streaming)

Differences:

- Provider does `stream_api` and yields raw chunks.
- For each chunk, provider runs `process_chunk` then extensions run `process_chunk`.
- Final message is typically emitted in `finalize` from accumulated state.

Pseudocode for the streaming part:

```python
for chunk in provider.stream_api(native, state):
    partials, finals, native, state = provider.process_chunk(chunk, native, state)
    partials, finals, native, state = ext1.process_chunk(chunk, partials, finals, native, state)
    # core converts partials to core messages for UI streaming

finals, native, state = provider.finalize(native, state)
finals, native, state = ext1.finalize(finals, native, state)
finals, native, state = feat1.finalize(finals, native, state)
```
