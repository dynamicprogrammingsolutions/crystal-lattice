# UI elements (`get_ui_elements`)

Plugins can optionally expose UI metadata via `get_ui_elements(config, tags, models) -> list[dict]`.

The core treats UI element dictionaries as **opaque** and flattens them via `AgentCore.get_ui_schema(config)`.

## Signature variations

### Core plugins (Provider, Extension, Feature, Tool)

```python
def get_ui_elements(
    self,
    config: Dict[str, Any],
    tags: List[str],
    models: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    ...
```

The core passes:
- `config`: effective configuration for the current agent/request
- `tags`: capability tags computed for this config (provider + enabled plugins)
- `models`: model descriptors computed for this config

### Application plugins

```python
def get_ui_elements(
    self,
    state: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
    models: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    ...
```

Application plugins receive `state` first (their internal state), followed by optional context parameters. When called via session-scoped endpoints, `config` contains the session's effective configuration, enabling config-aware UI filtering.

For backward compatibility, plugin adapters will also accept a legacy `get_ui_elements()` implementation with no arguments, but new plugins should prefer the context-aware signature.

Runtime references:
- Core plugins: `core/python/agent_core/types.py` (`BasePlugin.get_ui_elements`)
- Application plugins: `core/python/agent_app/app_plugins.py` (`ApplicationPlugin.get_ui_elements`)
- UI schema aggregation: `core/python/agent_core/core.py` (`AgentCore.get_ui_schema`)

---

## UI element aggregation

When `AgentCore.get_ui_schema()` is called, the core:

1. Resolves enabled plugins for the given config
2. Calls `get_ui_elements()` on each plugin (provider, extensions, features, tools)
3. Normalizes each element:
   - Sets `ui_type` to `"config"` if missing or falsy
   - Adds `plugin` field with the contributing plugin name
   - For `session_action`/`message_action` elements from extensions/features, sets `action_owner` field automatically
4. **Deduplicates config elements**: Elements with `ui_type == "config"` are collected by `key` and only the last definition for each key is kept
5. Appends deduplicated config elements at the end

This deduplication means later plugins can override earlier config elements with the same key.

### Automatic `action_owner` assignment

For `session_action` and `message_action` elements, the core automatically sets `action_owner`:

| Plugin type | `action_owner` value |
|-------------|---------------------|
| Provider extension | `"provider_extension"` |
| Feature plugin | `"feature"` |
| Application plugin | Not set (defaults to `"application"`) |

This allows frontends to route actions to the correct handler.

---

## UI element types (`ui_type`)

The `ui_type` field determines how frontends interpret and render the element. When `ui_type` is missing or falsy, the element is treated as `"config"`.

### Configuration elements (`ui_type == "config"` or omitted)

Used for configuration inputs in settings UIs. Frontends typically render these as text fields, checkboxes, or dropdowns.

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

#### Common fields

| Field | Type | Description |
|-------|------|-------------|
| `key` | string | Configuration key (required) |
| `type` | string | Input type: `text`, `checkbox`, `select`, `dropdown`, `multiline`, `number` |
| `label` | string | Human-readable label |
| `description` | string | Optional help text |
| `options` | array | For `select`/`dropdown`: `["value", ...]` or `[{"value": "...", "label": "..."}, ...]` |
| `default` | any | Default value shown when no override or config value exists |
| `required` | boolean | Whether the field is required |
| `placeholder` | string | Placeholder text for text inputs |
| `config_path` | string | Dotted path to nested config value (e.g., `"provider.api_key"`) |
| `condition` | object | Optional visibility condition (see below) |

#### Effective value resolution

Frontends resolve the effective value for a config element using this priority:

1. **Session override**: `session.metadata.overrides[key]` (highest priority)
2. **Base config value**: `base_config[key]`
3. **Nested config path**: `base_config` resolved via `config_path` (e.g., `"provider.api_key"` → `base_config.provider.api_key`)
4. **UI element default**: `element.default`
5. **Schema default**: `config_schema[key].default` (lowest priority)

The frontend SDK tags each setting with a source indicator:
- `"override"`: Value comes from session overrides
- `"config"`: Value comes from base config
- `"ui_default"`: Value comes from element's `default` field
- `"schema_default"`: Value comes from config schema default
- `"none"`: No value found

#### Input types

| Type | Description |
|------|-------------|
| `text` | Single-line text input |
| `multiline` | Multi-line text area |
| `checkbox` | Boolean toggle |
| `select` | Chip-style selection (all options visible) |
| `dropdown` | Dropdown menu (collapsed until clicked) |
| `number` | Numeric input |

### Message footers (`ui_type == "message_footer"`)

Per-message footer fields rendered under each message bubble. Frontends extract the specified data path from each message's metadata.

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

| Field | Type | Description |
|-------|------|-------------|
| `data` | string | Dotted JSON path into the message object (e.g., `"metadata.total_cost"`) |
| `template` | string | Optional template string; `{{data}}` is replaced with the resolved value |
| `condition` | object | Optional visibility condition (see below) |

### Status bar fields (`ui_type == "status_bar"`)

Persistent fields displayed in the status bar, typically derived from the last assistant message.

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

Fields are the same as `message_footer`.

### Session actions (`ui_type == "session_action"`)

Session-scoped actions displayed in session menus or toolbars. Used by application plugins to expose actions like "Compact range", "Export session", etc.

```python
def get_ui_elements(self, state, config, tags, models):
    # Config-aware filtering
    if config is not None and not self._is_enabled(config):
        return []
    
    return [
        {
            "ui_type": "session_action",
            "id": "compact_range",
            "label": "Compact range",
            "icon": "archive",
            "order": 45,
            "action_id": "compact_range",
            "fixed_params": {},
            "param_map": {
                "session_id": "$session.session_id",
                "start": "$dialog.start",
                "end": "$dialog.end",
            },
            "dialog": {
                "kind": "form",
                "title": "Compact range",
                "message": "Select a range of messages to compact.",
                "inputs": [
                    {"name": "start", "type": "integer", "label": "Start"},
                    {"name": "end", "type": "integer", "label": "End"},
                ],
            },
        }
    ]
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique element identifier |
| `label` | string | Human-readable label |
| `icon` | string | Optional icon name (frontend-specific) |
| `order` | number | Sort order (lower appears first) |
| `action_id` | string | Action to execute (from `get_actions`) |
| `action_owner` | string | Action handler: `"application"` (default), `"feature"`, or `"provider_extension"`; automatically set by core for extension/feature plugins |
| `fixed_params` | object | Parameters passed verbatim |
| `param_map` | object | Parameter mappings from context (see below) |
| `dialog` | object | Dialog configuration (see below) |
| `condition` | object | Optional visibility condition (see below) |

#### Parameter mappings (`param_map`)

Maps action parameters to context values using `$` prefixes:

| Expression | Source |
|------------|--------|
| `$session.session_id` | Current session ID |
| `$session.agent_id` | Current agent ID |
| `$message.index` | Message index (for message actions) |
| `$dialog.start` | User input from dialog |
| `$dialog.instructions` | User input from dialog |

#### Dialog configuration

```python
"dialog": {
    "kind": "form",  # Currently only "form" is supported
    "title": "Compact range",
    "message": "Optional description shown in dialog.",
    "inputs": [
        {
            "name": "start",           # Parameter name
            "type": "integer",         # Input type
            "label": "Start index",   # Label
            "required": False,
            "placeholder": "e.g. 0 or -10",
        },
    ],
}
```

### Message actions (`ui_type == "message_action"`)

Message-scoped actions displayed on individual message bubbles. Similar to `session_action` but with additional `$message.*` parameter mappings.

```python
{
    "ui_type": "message_action",
    "id": "compact_up_to_here",
    "label": "Compact up to here",
    "icon": "archive",
    "order": 25,
    "action_id": "compact_range",
    "fixed_params": {"start": 0, "end_inclusive": True},
    "param_map": {
        "session_id": "$session.session_id",
        "end": "$message.index",
    },
    "dialog": {...},
}
```

### Session list fields (`ui_type == "session_list_field"`)

Fields displayed in session list views. Extracted from session metadata for summary display.

```python
{
    "ui_type": "session_list_field",
    "key": "message_count",
    "label": "Messages",
    "data": "metadata.message_count",
    "template": "{{data}} messages",
    "order": 10,
}
```

### Composer attachments (`ui_type == "composer_attachment"`)

Attachment UI hints for the message composer. Frontends use these to display attachment options.

```python
{
    "ui_type": "composer_attachment",
    "key": "myprovider:attachment:image",
    "attachment_type": "image",
    "supports_url": True,
    "supported_file_types": ["png", "jpg", "gif"],
    "label": "Image",
}
```

### Model picker (`ui_type == "model_picker"`)

Model selection UI for providers that support model switching.

```python
{
    "ui_type": "model_picker",
    "key": "model",
    "label": "Select Model",
    "order": 10,
}
```

---

## Conditional visibility (`condition`)

UI elements can include a `condition` field that determines visibility based on session or message state.

```python
{
    "type": "checkbox",
    "key": "enable_reasoning",
    "label": "Enable reasoning",
    "condition": {
        "all": [
            {"path": "metadata.supports_reasoning", "eq": True},
        ],
    },
}
```

### Condition operators

| Operator | Description |
|----------|-------------|
| `all` | All child conditions must be true |
| `any` | Any child condition must be true |
| `not` | Negate child condition |
| `path` | JSON path to evaluate |
| `eq` | Equality check |
| `exists` | Path exists |
| `empty` | Path is empty or missing |

Example combining operators:

```python
"condition": {
    "all": [
        {"path": "metadata.reasoning_available", "eq": True},
        {"not": {"path": "metadata.reasoning_disabled", "exists": True}},
    ],
}
```

---

## Config-aware filtering

Plugins can filter UI elements based on configuration. This is especially useful for application plugins that may need to hide actions when features are disabled.

```python
def get_ui_elements(self, state, config, tags, models):
    # When config is None (global endpoint), return all elements
    if config is None:
        return self._get_all_ui_elements()
    
    # When config is provided (session-scoped), filter based on enablement
    if not self._is_enabled(config):
        return []
    
    return self._get_enabled_ui_elements(config)
```

For session-scoped endpoints, `config` contains the session's effective configuration (base config merged with session overrides), enabling per-session UI customization.

---

## Model-driven inputs

The `models` argument is a list of model descriptors computed for the effective config. Use this to build model selection UIs.

```python
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

Each model descriptor must include `"id": str`. Additional keys like `"name"` or capability metadata are provider-defined.

---

## Capability-aware UI

The `tags` argument contains capability/environment tags computed for the effective config. Use tags to gate elements based on provider capabilities.

```python
def get_ui_elements(
    self,
    config: dict[str, Any],
    tags: list[str],
    models: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    # Only show reasoning control if provider supports it
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

---

## Frontend type reference

Frontends consume UI elements via TypeScript types defined in the frontend SDK:

```typescript
// packages/frontend-sdk/src/types/uiSchema.ts
interface UiSchemaElement {
  ui_type?: string;
  key?: string;
  type?: string;
  label?: string;
  description?: string;
  options?: any;
  data?: string;
  template?: string;
  metadata?: Record<string, any>;
  condition?: unknown;
  plugin?: string;
  [k: string]: any;
}

// packages/frontend-sdk/src/types/plugins.ts
interface ActionUiElement {
  ui_type: string;
  plugin: string;
  id: string;
  label: string;
  icon?: string;
  order?: number;
  action_id: string;
  action_owner?: string;  // "application" | "feature" | "provider_extension"
  fixed_params?: Record<string, any>;
  param_map?: Record<string, string>;
  dialog?: any;
  metadata?: Record<string, any>;
}

interface SessionListFieldElement {
  ui_type: string;
  plugin: string;
  key?: string;
  label?: string;
  data: string;
  template?: string;
  order?: number;
}

// Union type for all application-level UI elements
type ApplicationUiElement = ActionUiElement | SessionListFieldElement | Record<string, any>;
```

---

## Custom UI types

Applications may support additional `ui_type` values not documented here. If an application does not recognize a `ui_type`, it should ignore the element.

Example (hypothetical custom type):

```python
def get_ui_elements(self, config, tags, models):
    return [
        {
            "ui_type": "custom_widget",
            "key": "my_widget",
            "custom_field": "value",
            "label": "Custom Widget",
        }
    ]
```

Frontends should gracefully handle unknown `ui_type` values by either ignoring them or passing them through for application-specific rendering.

---

## HTTP endpoints

Frontends retrieve UI schemas via HTTP endpoints:

### Core plugin UI schema

```
GET /sessions/{session_id}/ui-schema
```

Returns UI elements from core plugins (provider, extensions, features, tools). Filters by `ui_type` for different use cases:
- `ui_type == "config"` or omitted: Configuration inputs
- `ui_type == "message_footer"`: Message footer fields
- `ui_type == "status_bar"`: Status bar fields

### Application plugin UI schema

```
GET /sessions/{session_id}/application/ui-schema
```

Returns UI elements from application plugins. Used for:
- `ui_type == "session_action"`: Session-scoped actions
- `ui_type == "message_action"`: Message-scoped actions
- `ui_type == "session_list_field"`: Session list fields

Optional query parameter `?plugin=name` filters elements by plugin.

---

## See also

- [Provider plugins](provider-plugins.md) - Provider implementation guide
- [Application plugins](application-plugins.md) - Application plugin guide
- [Feature plugins](feature-plugins.md) - Feature plugin guide
- [Plugin actions](actions.md) - Action definitions and lifecycle