# Configuration schema (`get_config_schema`)

Plugins can declare their configuration keys via `get_config_schema()`.

This schema is used for **discovery and documentation** (for example, the terminal app’s `/help config` output and HTTP endpoints that expose schema), not for runtime validation.

Runtime reference:

- Flattening/aggregation: `core/python/agent_core/core.py` (`AgentCore.get_config_schema`)
- Terminal rendering: `application/python/agent_terminal_app/terminal.py` (`/help config`)

## What plugins return

`get_config_schema()` returns a **dict mapping top-level config keys → entry metadata**.

Minimal example:

```python
from typing import Any


def get_config_schema(self) -> dict[str, Any]:
    return {
        "model": {"type": "string", "required": True, "description": "Model id"},
        "timeout": {"type": "number", "default": 60, "description": "Request timeout (seconds)"},
    }
```

Each value must be a dict. The core does not enforce a strict schema; it simply preserves the entry dicts.

## What the core exposes

`AgentCore.get_config_schema()` returns a **flattened list** combining every registered provider, provider extension, feature, and tool.

For each entry, the core adds:

- `key`: the config key (from the returned dict’s key)
- `plugin`: the contributing plugin id/name (provider/extension/feature/tool)

All other fields are passed through unchanged.

Because the result is flattened, multiple plugins may contribute entries for the same `key` (they are returned as separate list elements).

## Fields used by built-in apps

The terminal app’s `/help config` currently displays:

- `key` (from the core)
- `plugin` (from the core)
- `type` (string; if missing prints `?`)
- `default` (if present)
- `description` (if present)

Everything else is treated as metadata for other clients.

## Recommended entry fields

Even though the core does not validate these, using a consistent, JSON-schema-like shape makes schemas easier to understand and consume.

Common fields:

- `type`: recommended values are `string`, `number`, `integer`, `boolean`, `object`, `array`
- `required`: boolean
- `default`: JSON-serializable default value
- `description`: human-readable text used by `/help config`

Notes:

- The core and terminal treat `type` as **display metadata** (a string); it is not validated.
- Some built-in schemas use informal values like `int` / `bool`. Prefer JSON-schema-like names for consistency, but clients should not rely on a closed set.

Optional fields (passed through; may be consumed by other UIs):

- `enum`: list of allowed values
- `items`: schema dict for array items
- `properties`: schema dict for object properties

Example with `enum`:

```python
def get_config_schema(self) -> dict[str, Any]:
    return {
        "reasoning_effort": {
            "type": "string",
            "enum": ["low", "medium", "high"],
            "description": "Control reasoning depth (model-specific)",
        }
    }
```

Example with `items`:

```python
def get_config_schema(self) -> dict[str, Any]:
    return {
        "allowed_paths": {
            "type": "array",
            "items": {"type": "string"},
            "default": ["."],
            "description": "Allowlist of base paths",
        }
    }
```

## Relation to UI schema (`get_ui_elements`)

`get_config_schema()` describes what keys exist and their defaults.

Interactive configuration in the terminal (via `/set`) is driven by `get_ui_elements(config, tags, models)` (see `plugins/docs/ui-elements.md`). It’s common to keep `get_config_schema()` and `get_ui_elements()` aligned (same keys, same defaults), but they are independent.

Because `get_ui_elements` receives `tags` and `models`, the set of UI-exposed keys may vary by provider capabilities and the selected model. This is useful for hiding knobs that do not apply, but it also means:

- `/help config` may list keys that do not appear in `/set` for a given session, and
- keys may appear/disappear when you change the session’s effective config.

## Application-level schema (terminal app)

The terminal app also exposes and renders a separate schema for keys under `config["application"]` (settings consumed by the terminal app itself, not by plugins). See `application/python/agent_terminal_app/terminal_app.py` (`TerminalApplication.get_application_config_schema`).
