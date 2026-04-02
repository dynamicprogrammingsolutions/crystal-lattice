# 106 - Shell Tool Selection

Short description: Implement plugin enablement system with `is_enabled`, `forbidden_tags`, and config-driven shell tool selection.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/100-shell-tools.md`

Depends On: `tasks/20260315-gemini-qwen-grok-tool-packages/104-codex-v2-tool.md`

## Requirements checklist

- [x] Core: Add `forbidden_tags()` method to plugin protocols
- [x] Core: Add `is_enabled()` method to plugin protocols
- [x] Core: Add default implementations in adapters
- [x] Core: Add wrapper methods in extension/feature/tool wrappers
- [x] Core: Modify `_resolve_plugins_for_config` to use new methods
- [x] Core: Add `default_enabled` attribute support in core layer
- [x] Core: Add `enabled_plugins` config key support in core layer
- [x] App: Add `default_enabled` attribute support in application layer
- [x] App: Add `enabled_plugins` config key
- [x] App: Pass `force_enabled_plugins` to runtime config
- [x] Shell Tools: Add `is_enabled` implementation with `shell_tool_mode` config
- [x] Shell Tools: Add `get_tags` for mutual awareness
- [x] Shell Tools: Set `default_enabled = False` on legacy tool
- [x] Feature: Add CodexVariantFeature for codex-variant tag emission
- [x] Docs: Update plugin development docs
- [x] Docs: Update application config docs
- [x] Tests: Unit tests for new core methods
- [x] Tests: Integration tests for shell tool selection scenarios

## Goal

Implement a flexible plugin enablement system that allows:

1. **Plugins to be disabled by default** via `default_enabled = False` class attribute
2. **Config-level enablement** via `enabled_plugins` key to re-enable disabled-by-default plugins
3. **Tag-based selection** via `forbidden_tags()` method (negative constraint)
4. **Complex enablement logic** via `is_enabled()` method receiving full context
5. **Force enable override** via `force_enabled_plugins` config to bypass tag-based rules

Apply this system to shell tool selection:
- `shell` (array-based) enabled for non-Codex models
- `shell_command` (string-based) enabled for Codex models
- `shell_legacy` disabled by default, opt-in via `enabled_plugins`

## Core Layer Changes

### 1. Add `forbidden_tags()` to plugin protocols

**File**: `core/python/agent_core/types.py`

Add to `ProviderExtensionPlugin`, `FeaturePlugin`, `ToolPlugin`:

```python
def forbidden_tags(self) -> List[str]:
    """Tags that must NOT be present for this plugin to be enabled.
    
    If any of these tags are in the available tag set, the plugin is disabled.
    """
    return []
```

### 2. Add `is_enabled()` to plugin protocols

**File**: `core/python/agent_core/types.py`

```python
def is_enabled(
    self,
    config: Dict[str, Any],
    tags: List[str],
    models: List[Dict[str, Any]],
    context: Dict[str, Any],
) -> Optional[bool]:
    """Return whether this plugin should be enabled given the current context.
    
    Returns:
        True: plugin is enabled (bypass required_tags/forbidden_tags)
        False: plugin is disabled
        None: fall back to required_tags/forbidden_tags check
    
    The context dict includes:
        - "enabled_plugin_ids": dict mapping kind to list of currently enabled plugin ids
        - "disabled_plugins": config-level disabled list
        - "force_enabled_plugins": config-level force list
    """
    return None  # Default: fall back to tag-based check
```

### 3. Add default implementations in adapters

**File**: `core/python/agent_core/plugin/adapters.py`

Add to each adapter (`ExtensionDefaultsAdapter`, `FeatureDefaultsAdapter`, `ToolDefaultsAdapter`):

```python
def forbidden_tags(self) -> List[str]:
    fn = getattr(self.impl, "forbidden_tags", None)
    raw = fn() if callable(fn) else []
    return [str(t) for t in self._safe_list(raw)]

def is_enabled(
    self,
    config: Dict[str, Any],
    tags: List[str],
    models: List[Dict[str, Any]],
    context: Dict[str, Any],
) -> Optional[bool]:
    fn = getattr(self.impl, "is_enabled", None)
    if callable(fn):
        return fn(config, tags, models, context)
    return None  # Fall back to tag-based
```

### 4. Add wrapper methods

**Files**: `core/python/agent_core/plugin/extension.py`, `feature.py`, `tool.py`

```python
def forbidden_tags(self) -> List[str]:
    return self.plugin.forbidden_tags()

def is_enabled(
    self,
    config: Dict[str, Any],
    tags: List[str],
    models: List[Dict[str, Any]],
    context: Dict[str, Any],
) -> Optional[bool]:
    return self.plugin.is_enabled(config, tags, models, context)
```

### 5. Modify `_resolve_plugins_for_config` in core

**File**: `core/python/agent_core/core.py`

Update the resolution loop to:

1. Check `force_enabled_plugins` from config first (always enabled)
2. Call `is_enabled()` for each plugin
3. If `is_enabled()` returns `None`, fall back to `required_tags`/`forbidden_tags` check
4. Loop until stable

```python
def _resolve_plugins_for_config(self, config: Dict[str, Any]) -> Tuple[...]:
    # ... existing setup ...
    
    force_enabled = set(config.get("force_enabled_plugins") or [])
    
    while True:
        # ... compute tags ...
        
        def _filter_plugins(plugins):
            result = []
            for p in plugins:
                # Check force_enabled first
                if p.name in force_enabled:
                    result.append(p)
                    continue
                
                # Check is_enabled
                is_enabled_result = p.is_enabled(config, list(available_tags), models, {
                    "enabled_plugin_ids": {
                        "extensions": [e.name for e in enabled_extensions],
                        "features": [f.name for f in enabled_features],
                        "tools": [t.name for t in enabled_tools],
                    },
                    "disabled_plugins": config.get("disabled_plugins", []),
                    "force_enabled_plugins": list(force_enabled),
                })
                
                if is_enabled_result is True:
                    result.append(p)
                elif is_enabled_result is False:
                    continue
                else:
                    # Fall back to tag-based check
                    if not set(p.required_tags()).issubset(available_tags):
                        continue
                    if set(p.forbidden_tags()).intersection(available_tags):
                        continue
                    result.append(p)
            
            return result
        
        # ... apply filter and check for stability ...
```

## Application Layer Changes

### 1. Add `default_enabled` attribute support

**File**: `core/python/agent_app/application_future.py`

When computing `default_enabled_ids`, check plugin classes for `default_enabled` attribute:

```python
# Get plugins with default_enabled=False
plugins_disabled_by_default = set()
for kind in ("providers", "extensions", "features", "tools"):
    for plugin_cls in deduped_classes.get(kind) or []:
        plugin_id = self._plugin_id_for_class(plugin_cls)
        default_enabled = getattr(plugin_cls, "default_enabled", True)
        if default_enabled is False:
            plugins_disabled_by_default.add(plugin_id)
```

### 2. Add `enabled_plugins` config key

**File**: `core/python/agent_app/application_future.py`

Add config key to re-enable plugins that are disabled by default:

```python
# Get enabled_plugins from config (re-enable disabled-by-default plugins)
agent_enabled_plugins = set(
    self._coerce_plugin_ids(
        agent_cfg.get("enabled_plugins"),
        f"agents.{agent_id}.enabled_plugins",
        self._config_errors,
    )
)

# Compute final disabled set
disabled_set = set(global_disabled_plugins)
disabled_set.update(provider_disabled)
disabled_set.update(agent_disabled_plugins.get(agent_id, []))
disabled_set.update(plugins_disabled_by_default - agent_enabled_plugins)  # Re-enable if in enabled_plugins
```

### 3. Pass `force_enabled_plugins` to runtime config

**File**: `core/python/agent_app/config.py`

Include `force_enabled_plugins` from agent config in the runtime config passed to core.

## Shell Tool Configuration

### Plugin Declarations

**File**: `plugins/codex-tools/src/codex_tools/shell_tool.py` (legacy)

```python
class ShellTool:
    name = "shell_legacy"  # Rename to avoid conflict
    default_enabled = False  # Opt-in only
```

**File**: `plugins/codex-tools/src/codex_tools/shell_array_tool.py`

```python
class ShellArrayTool:
    name = "shell"
    default_enabled = True
    
    def get_tags(self, config, models):
        return ["shell:array"]  # Advertise presence
    
    def is_enabled(self, config, tags, models, context):
        mode = config.get("shell_tool_mode", "auto")
        
        if mode == "shell":
            return True  # Force enabled
        if mode == "shell_command":
            return False  # Force disabled
        # mode == "auto"
        return "codex-variant" not in tags
```

**File**: `plugins/codex-tools/src/codex_tools/shell_command_tool.py`

```python
class ShellCommandTool:
    name = "shell_command"
    default_enabled = True
    
    def get_tags(self, config, models):
        return ["shell:command"]  # Advertise presence
    
    def is_enabled(self, config, tags, models, context):
        mode = config.get("shell_tool_mode", "auto")
        
        if mode == "shell":
            return False  # Force disabled
        if mode == "shell_command":
            return True  # Force enabled
        # mode == "auto"
        return "codex-variant" in tags
```

### Selection Table

| `shell_tool_mode` | `codex-variant` tag | `shell` result | `shell_command` result | Active Tool |
|-------------------|---------------------|----------------|------------------------|-------------|
| auto | No | True | False | shell |
| auto | Yes | False | True | shell_command |
| shell | Any | True | False | shell |
| shell_command | Any | False | True | shell_command |

## Configuration Examples

### Scenario 1: Default auto-selection

```json
{
  "plugins": ["path:${env:BUILTIN_PLUGINS}/codex-tools"],
  "agents": {
    "codex-agent": {
      "provider": "openrouter",
      "model": "openai/gpt-5.2-codex"
    }
  }
}
```
- Feature plugin adds `codex-variant` tag → `shell_command` enabled

### Scenario 2: Force shell_command

```json
{
  "agents": {
    "my-agent": {
      "provider": "openrouter",
      "model": "openai/gpt-5",
      "shell_tool_mode": "shell_command"
    }
  }
}
```
- `shell_command` forced on, `shell` forced off

### Scenario 3: Force shell

```json
{
  "agents": {
    "my-agent": {
      "provider": "openrouter",
      "model": "openai/gpt-5.2-codex",
      "shell_tool_mode": "shell"
    }
  }
}
```
- `shell` forced on, `shell_command` forced off

### Scenario 4: Enable legacy tool

```json
{
  "agents": {
    "legacy-agent": {
      "provider": "openrouter",
      "model": "openai/gpt-4",
      "enabled_plugins": ["shell_legacy"],
      "disabled_plugins": ["shell", "shell_command"]
    }
  }
}
```

### Scenario 5: Force enable both (override)

```json
{
  "agents": {
    "forced-agent": {
      "shell_tool_mode": "shell_command",
      "force_enabled_plugins": ["shell"]
    }
  }
}
```
- Both tools enabled despite mode setting

## Out of Scope

- Dynamic tool switching mid-session
- Per-request tool selection overrides
- Tool schema merging or aliasing

## Completion Notes

### Core Layer Changes

Added new methods to plugin protocols and their implementations:

1. **`forbidden_tags()`** - Returns list of tags that disable the plugin if present
2. **`is_enabled(config, tags, models, context)`** - Custom enablement logic returning `True`/`False`/`None`

Updated `_resolve_plugins_for_config` in `core.py` to:
- Check `default_enabled` attribute when building initial candidate set
- Support `enabled_plugins` config to re-enable disabled-by-default plugins
- Support `force_enabled_plugins` config to force-enable plugins (also works for default_enabled=False)
- Check `force_enabled_plugins` config first in resolution loop
- Call `is_enabled()` for each plugin
- Fall back to `required_tags()`/`forbidden_tags()` check

### Application Layer Changes

Added support for:
- **`default_enabled`** class attribute on plugins (default: `True`, set to `False` for opt-in)
- **`enabled_plugins`** config key to re-enable disabled-by-default plugins
- **`force_enabled_plugins`** passed through to runtime config

### Shell Tools Updated

1. **`ShellArrayTool`** (`shell`):
   - Added `is_enabled()` with `shell_tool_mode` logic
   - Added `get_tags()` returning `["shell:array"]`

2. **`ShellCommandTool`** (`shell_command`):
   - Added `is_enabled()` with `shell_tool_mode` logic
   - Added `get_tags()` returning `["shell:command"]`

3. **`ShellTool`** (renamed to `shell_legacy`):
   - Renamed tool name from `shell` to `shell_legacy`
   - Added `default_enabled = False` for opt-in only
   - Updated function name in schema

### Documentation Updated

- `docs/plugins/application-config.md`: Added `enabled_plugins`, `force_enabled_plugins`, and plugin enablement flow
- `plugins/docs/plugin-execution-order.md`: Updated dependency resolution flow with new methods
- `plugins/codex-tools/src/codex_tools/__init__.py`: Updated docstring with shell tool selection info

### Tests Added

1. **`core/python/tests/test_plugin_is_enabled.py`** - 9 tests covering:
   - `is_enabled` overriding `required_tags`
   - `is_enabled` returning `False` disabling tool
   - `is_enabled` returning `None` falling back to tags
   - `forbidden_tags` disabling tool
   - `force_enabled_plugins` overriding `is_enabled` and `forbidden_tags`
   - Wrapper methods existence
   - Default adapter implementations

2. **`plugins/codex-tools/tests/test_shell_tool_selection.py`** - 24 tests covering:
   - Tool name verification
   - Auto mode selection based on `codex-variant` tag
   - Shell mode forcing shell tool
   - Shell_command mode forcing shell_command tool
   - `force_enabled_plugins` override
   - Legacy tool disabled by default
   - `enabled_plugins` enabling legacy tool
   - Tag contributions from shell tools
   - Direct `is_enabled` method testing
   - All tools registered together scenarios

3. **`plugins/codex-tools/tests/test_shell_tool_openrouter_integration.py`** - 16 tests covering:
   - Real OpenRouter provider integration
   - CodexVariantFeature tag emission
   - Shell tool selection with various models (codex vs non-codex)
   - `shell_tool_mode` config override
   - `force_enabled_plugins` with real provider

### CodexVariantFeature Added

**File**: `plugins/codex-tools/src/codex_tools/codex_variant_feature.py`

A feature plugin that emits the `codex-variant` tag when the model name ends with `-codex`:
- `openai/gpt-5.2-codex` → emits `codex-variant` tag
- `openai/gpt-5` → no tag emitted

This enables automatic shell tool selection based on model name.

All 111 codex-tools tests pass.