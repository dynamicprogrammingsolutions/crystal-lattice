# UI elements (`get_ui_elements`) and `ui_type`

Plugins can optionally expose UI metadata via `get_ui_elements() -> list[dict]`.

The core treats UI element dictionaries as **opaque** and flattens them via `AgentCore.get_ui_schema()`.

Runtime reference: `core/python/agent_core/types.py` (`BasePlugin.get_ui_elements`).

## Configuration elements (default)

If `ui_type` is missing or falsy, the element is treated as a config element.

Example:

```python
def get_ui_elements(self):
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

## Message footers (`ui_type == "message_footer"`)

Used by some apps to render a compact footer under each message.

```python
def get_ui_elements(self):
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
def get_ui_elements(self):
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

Example (attachment UI hint; application-specific):

```python
def get_ui_elements(self):
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
