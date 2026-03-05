# UI elements (`get_ui_elements`) and `ui_type`

Plugins can optionally expose UI metadata via `get_ui_elements(config, tags, models) -> list[dict]`.

The core treats UI element dictionaries as **opaque** and flattens them via `AgentCore.get_ui_schema(config)`.

The core passes additional context:

- `config`: effective configuration for the current agent/request
- `tags`: capability tags computed for this config (provider + enabled plugins)
- `models`: model descriptors computed for this config

For backward compatibility, plugin adapters will also accept a legacy `get_ui_elements()` implementation
with no arguments, but new plugins should prefer the context-aware signature.

Runtime reference: `core/python/agent_core/types.py` (`BasePlugin.get_ui_elements`).

Related runtime behavior:

- UI schema aggregation and plugin selection: `core/python/agent_core/core.py` (`AgentCore.get_ui_schema`, `_resolve_plugins_for_config`)
- Backward-compatible defaults: `core/python/agent_core/plugin/adapters.py`

## Configuration elements (default)

If `ui_type` is missing or falsy, the element is treated as a config element.

Example:

```python
def get_ui_elements(self, config, tags, models):
    return [
        {"type": "text", "key": "model", "label": "Model"},
        {"type": "checkbox", "key": "debug_stream", "label": "Debug stream"},
        {
            "type": "select",
            "key": "reasoning_effort",
            "label": "Reasoning effort",
            "options": ["low", "medium", "high"],
        },
    ]
```

### Option formats

Applications may accept multiple option formats.

The built-in terminal UI accepts both:

- `options: ["low", "medium", "high"]`
- `options: [{"value": "low", "label": "Low"}, ...]`

When you have model metadata, the `{value,label}` form is usually nicer.

## Model-driven inputs (using `models`)

The `models` argument is a list of model descriptors computed for the effective config.

- The core requires each descriptor to include an `"id": str`.
- Additional keys are provider-defined (for example `"name"` or provider-specific capability metadata).

Common pattern: render a dropdown when `models` contains multiple options, otherwise fall back to a text input.

```python
from __future__ import annotations

from typing import Any


def get_ui_elements(
    self,
    config: dict[str, Any],
    tags: list[str],
    models: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    options: list[dict[str, str]] = []
    for m in models:
        model_id = m.get("id")
        if not isinstance(model_id, str) or not model_id:
            continue
        label = m.get("name")
        label = label if isinstance(label, str) and label else model_id
        options.append({"value": model_id, "label": label})

    if options:
        return [
            {
                "type": "select",
                "key": "model",
                "label": "Model",
                "options": options,
            }
        ]

    return [{"type": "text", "key": "model", "label": "Model id"}]
```

## Capability-aware UI (using `tags`)

The `tags` argument contains capability/environment tags computed for the effective config.
Plugins typically use tags to:

- gate whether an entire plugin is enabled (`required_tags()`), and
- hide optional UI elements when a capability is missing.

Example: only show a reasoning knob when the provider advertises a reasoning capability.

```python
from __future__ import annotations

from typing import Any


def get_ui_elements(
    self,
    config: dict[str, Any],
    tags: list[str],
    models: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if "supports_reasoning" not in tags:
        return []

    return [
        {
            "type": "checkbox",
            "key": "enable_reasoning",
            "label": "Enable reasoning",
        }
    ]
```

## Message footers (`ui_type == "message_footer"`)

Used by some apps to render a compact footer under each message.

```python
def get_ui_elements(self, config, tags, models):
    return [
        {
            "ui_type": "message_footer",
            "data": "metadata.total_cost",
            "template": "Cost: {{data}}",
        }
    ]
```

## Status bar fields (`ui_type == "status_bar"`)

Similar to message footers, but persistent.

```python
def get_ui_elements(self, config, tags, models):
    return [
        {
            "ui_type": "status_bar",
            "data": "metadata.cached_tokens",
            "template": "Cached: {{data}}",
        }
    ]
```

## Custom UI types

Applications may support additional `ui_type` values.

If an application does not recognize a `ui_type`, it should ignore the element.

Example (attachment UI hint; application-specific):

```python
def get_ui_elements(self, config, tags, models):
    return [
        {
            "ui_type": "composer_attachment",
            "key": "myprovider:attachment:image",
            "attachment_type": "image",
            "supports_url": True,
            "supported_file_types": ["png", "jpg"],
            "label": "Image",
        }
    ]
```
