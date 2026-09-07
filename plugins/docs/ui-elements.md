# UI elements (`get_ui_elements`)

Plugins can optionally expose UI metadata via `get_ui_elements(...) -> list[dict]`.

The core treats UI element dictionaries as **opaque** and flattens them via `AgentCore.get_ui_schema(config)`.

## Signature variations

### Core plugins (Provider, Extension, Feature, Tool)

```python
def get_ui_elements(
    self,
    config: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    ...
```

The core passes:
- `config`: effective configuration for the current agent/request
- `context["tags"]`: capability tags computed for this config (provider + enabled plugins)
- `context["models"]`: model descriptors computed for this config

### Application plugins

```python
def get_ui_elements(
    self,
    state: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    ...
```

Application plugins receive `state` first (their internal state), followed by
optional `config` and `context` parameters. When called via session-scoped
endpoints, `config` contains the session's effective configuration, enabling
config-aware UI filtering. Current application-owned server settings are
supplied in `context["server_settings"]` on every application UI-schema
surface. When called for server settings, `config` remains configuration rather
than being replaced by those live values.

For backward compatibility, plugin adapters also accept legacy application
plugin signatures such as `get_ui_elements()`, `get_ui_elements(state)`,
`get_ui_elements(state, config)`, and
`get_ui_elements(state, config, tags, models)`, but new plugins should prefer
the context-aware signature.

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
| `scope` | string | Optional setting scope; application plugins use `"server"` for server-scoped settings |
| `options` | array | For `select`/`dropdown`: `["value", ...]` or `[{"value": "...", "label": "..."}, ...]` |
| `default` | any | Default value shown when no override or config value exists |
| `required` | boolean | Whether the field is required |
| `placeholder` | string | Placeholder text for text inputs and searchable dropdowns |
| `config_path` | string | Dotted path to nested config value (e.g., `"provider.api_key"`) |
| `condition` | object | Optional visibility condition (see below) |
| `custom_value` | object | Optional searchable-dropdown custom entry with `enabled`, `pattern`, and `option_label` |
| `rich_ui` | object | Optional self-contained compact presentation in chat |

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

#### Server-scoped configuration elements

Application plugins can expose server-scoped settings by returning config-like
elements with `scope: "server"` from `get_ui_elements(...)`.

```python
def get_ui_elements(self, state, config=None, context=None):
    settings = (context or {}).get("server_settings") or {}
    elements = [
        {
            "ui_type": "config",
            "scope": "server",
            "key": "show_advanced",
            "type": "checkbox",
            "label": "Show advanced settings",
            "default": False,
        }
    ]
    if settings.get("show_advanced"):
        elements.append(
            {
                "ui_type": "config",
                "scope": "server",
                "key": "keep_awake_enabled",
                "type": "checkbox",
                "label": "Keep server awake",
                "default": False,
            }
        )
    return elements
```

Frontends retrieve these elements from `GET /server/settings/ui-schema` and
filter to config-like elements whose `scope` is `"server"`. Current values are
loaded from `GET /server/settings`; mutations use `PATCH /server/settings` and
`DELETE /server/settings/{key}`.

Dynamic server settings UI should be plugin-side: the application passes current
server settings in `context["server_settings"]`, and the plugin returns the
controls that should be visible for that state. Do not use the session/agent
`config` argument to carry server settings.

Server-scoped settings are application-owned state. Plugins can react to
`server_settings_changed`, but should not store a second authoritative copy of
the same user-editable values.

The same context mapping is available while generating ordinary application
UI declarations. This allows a live server setting to include or omit a
session-list field without copying that setting into plugin state.

<!-- Keep a minimal static example for readers who do not need dynamic UI. -->

```python
def get_ui_elements(self, state, config=None, context=None):
    return [
        {
            "ui_type": "config",
            "scope": "server",
            "key": "keep_awake_enabled",
            "type": "checkbox",
            "label": "Keep server awake",
            "default": False,
        }
    ]
```

#### Input types

| Type | Description |
|------|-------------|
| `text` | Single-line text input |
| `multiline` | Multi-line text area |
| `checkbox` | Boolean toggle |
| `select` | Chip-style selection (all options visible) |
| `dropdown` | Dropdown menu (collapsed until clicked) |
| `number` | Numeric input |

#### Compact rich configuration

An ordinary session configuration element may include `rich_ui` to make the
same setting available as a compact control in chat. This does not define an
action and does not require an application plugin. The containing config
element remains the setting binding: its `key`, optional `config_path`,
effective value, session override, schema/default source, disabled state, and
reset behavior are authoritative.

The compact presentation is self-contained for its compact label, options,
custom-entry text, pinning, and placements. The containing config element
still owns the ordinary/fallback `label` and `icon`. Frontends that do not
support rich UI can therefore render the setting without interpreting
`rich_ui`, and the ordinary action menu uses those outer fields for its left
side.

The supported rich config kinds are `dropdown` and `toggle`.

```python
model_options = [
    {"value": model["id"], "label": model.get("name") or model["id"]}
    for model in models
]

{
    "ui_type": "config",
    "type": "dropdown",
    "key": "model",
    "label": "Model",
    "icon": "cpu",
    "options": model_options,
    "placeholder": "Search models or enter a model ID",
    "custom_value": {
        "enabled": True,
        "pattern": r"^[^\s]+$",
        "option_label": "Use '{value}' as a custom model ID",
    },
    "rich_ui": {
        "kind": "dropdown",
        "label": "Model",
        "show_label": False,
        "options": model_options,
        "placeholder": "Search models or enter a model ID",
        "custom_value": {
            "enabled": True,
            "pattern": r"^[^\s]+$",
            "option_label": "Use '{value}' as a custom model ID",
        },
        "placements": ["composer"],
        "default_pinned": True,
    },
}
```

`rich_ui.kind` identifies the compact renderer rather than merely identifying
the element as a setting. Future kinds can define different validated shapes,
such as `select`, `toggle`, or `text`.

The rich dropdown fields are:

| Field | Type | Description |
| --- | --- | --- |
| `kind` | string | Must be `dropdown` for this presentation |
| `label` | string | Compact-surface label; required |
| `options` | array | Self-contained string value/label options; may be empty only when `custom_value.enabled` is true |
| `placeholder` | string | Text for the one field used to filter options or enter a custom value |
| `custom_value` | object | Nested custom-entry declaration; repeat it on the containing config element |
| `description` | string | Optional compact help text |
| `show_label` | boolean | Whether the compact control visually shows `label:`; accessibility always retains the label |
| `show_icon` | boolean | Whether the compact control shows an icon; defaults to true |
| `placements` | array | Ordered compact locations; initially `session_header` and `composer` |
| `default_pinned` | boolean | Initial pin preference when the connection has no stored choice |

`custom_value.enabled` enables custom values. `custom_value.pattern` is an
optional ECMAScript regular expression applied as a full-value match.
`custom_value.option_label` contains `{value}`, for example
`"Use '{value}' as a custom model ID"`.

The dropdown uses one field for both search and custom entry. A non-empty
query filters labels and values case-insensitively. When the trimmed query does
not exactly equal a declared value and satisfies the custom pattern, the list
appends a synthetic custom option after the declared matches. Invalid custom
configuration disables only the synthetic option; declared values remain
usable.

Options may add a theme-aware semantic tone and icon:

```python
{"value": "high", "label": "High", "icon": "chevron-up", "tone": "highlight"}
```

Supported tones are `primary`, `highlight`, `warning`, `success`, `danger`,
and `muted`. A selected option icon overrides the containing config element's
ordinary icon for compact presentation. Otherwise the compact control uses
the outer icon unless `show_icon` is false. The selected option controls the
compact tone. Frontends may apply a shorter host-specific visual character
limit while preserving the full accessibility label and stored value.

For manual testing without changing a production provider, load the
[dummy rich configuration UI plugin](../dummy-rich-config-ui/README.md) and
enable `dummy_rich_config_ui` for an agent. The plugin exposes all semantic
option tones, distinct icons, a rich toggle, both chat placements, and a
disabled-state example.

Boolean checkbox settings may expose a compact toggle:

```python
{
    "type": "checkbox",
    "key": "enable_web_search",
    "label": "Enable web search",
    "icon": "globe",
    "rich_ui": {
        "kind": "toggle",
        "label": "Web search",
        "show_label": False,
        "placements": ["composer"],
        "default_pinned": True,
        "options": [
            {
                "value": False,
                "label": "Off",
                "icon": "globe",
                "tone": "primary",
            },
            {
                "value": True,
                "label": "On",
                "icon": "globe",
                "tone": "success",
            },
        ],
    },
}
```

A rich config toggle has exactly one `false` and one `true` option. Disabled
controls are muted; absent option tones default to primary for false and
success for true. Selecting the compact control patches the ordinary Boolean
session override.

Rich placement is additive. The complete setting remains available in Session
Settings. Selecting a declared or custom value patches the ordinary session
override; reset deletes that override. A custom value remains visible even
when it is absent from a later discovery response.

Unknown future rich kinds remain transportable. Frontends without a renderer
ignore the compact presentation and retain the ordinary setting, including
its outer label and icon.

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
| `rich_ui` | object | Optional compact toggle/list presentation and placement |

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

Frontends combine plugin-provided actions with their native actions by
ascending finite `order`. Missing orders sort after ordered actions. Equal
orders preserve the original frontend/plugin declaration order, so plugin
authors can choose broad ordering bands without relying on plugin load order.

For example, a frontend-native Reload action at order `0`, a plugin Copy
session action at `10`, and a frontend Settings action at `90` appear in that
sequence in the same menu.

#### Rich session actions in chat

An ordinary `session_action` may use the same `rich_ui.kind: "toggle"` or
`rich_ui.kind: "list"` contract documented for
[session-list actions](#optional-rich-presentation-and-permanent-fallback).
The ordinary `action_id`, parameter mapping, and dialog remain the permanent
execution and fallback path.

Chat placements are declared inside `rich_ui.placements`:

- `session_header`: the session action area above the transcript;
- `composer`: the action area around the message composer.

When rich placement is omitted, a session action keeps its existing
`session_header` behavior. A supported rich toggle invokes the ordinary action
immediately. A supported rich list submits its selected option through
`$dialog.<input_name>`. Unknown or malformed rich presentation falls back to
the ordinary action dialog.

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

Action dialog inputs use the same input field model as configuration UI elements,
with `name` replacing configuration `key`. Shared fields include `type`, `label`,
`description`, `placeholder`, `default`, `required`, and, for `select`/`dropdown`,
`options`.

```python
"dialog": {
    "kind": "form",
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

Supported dialog kinds are:

- `none`: execute immediately without opening a dialog;
- `confirm`: show `title` / `message` and OK/Cancel controls, then submit no
  dialog values;
- `form`: show the declared named inputs and submit their values only after the
  user chooses OK.

Omitting `dialog` is equivalent to `{"kind": "none"}` for an ordinary
`session_list_action`. Unknown dialog kinds are invalid; they are not treated as
immediate actions.

For `select` and `dropdown`, use the same option model as config UI:

```python
{
    "name": "server_name",
    "type": "select",
    "label": "MCP server",
    "options": [
        {"value": "figma", "label": "Figma"},
        "linear",
    ],
    "required": True,
}
```

`select` is a single-choice control that frontends typically render with all
options visible, such as chips on mobile. `dropdown` uses the same option model
but allows frontends to render a collapsed menu. Submitted `select` and
`dropdown` values are strings.

An input may initialize itself from the current context:

```python
{
    "name": "status",
    "type": "select",
    "prefill_from": "$session.metadata.status",
    "default": "todo",
    "options": [
        {"value": "todo", "label": "To do"},
        {"value": "done", "label": "Done"},
    ],
}
```

When `prefill_from` resolves to a usable value, that value wins even when
`default` is non-empty. The default is used only when the path is missing or
resolves to `null` or an empty string. False and zero are usable prefill values.
Prefill initializes the control; the action still needs a corresponding
`param_map` entry such as `"status": "$dialog.status"` to submit it.

#### Action deep links

Mobile action callbacks use a session-scoped route so the frontend can route the
callback to the intended backend connection and session before invoking the
action:

```text
crystal-lattice://action/<connection-id>/<session-id>/<action-id>?result=approved&nonce=n-123
crystal-lattice://action/<connection-id>/<session-id>/<plugin-id>/<action-id>?result=approved&nonce=n-123
```

`connection-id` and `session-id` are always required. `plugin-id` is optional so
callbacks can be produced by one plugin and handled by another plugin exposing
the same action id. When omitted, the application layer resolves the action id
against the target session. If no action matches, execution fails with
`unknown_action`; if more than one action matches, execution fails with
`ambiguous_action` and candidate details.

Query parameters are submitted as action inputs. Frontends also add
`redirect_url` with the full original callback URL.

Plugins that generate external callback URLs can return those URLs in display
actions using the standard `copy_text` action shape:

```python
{
    "kind": "copy_text",
    "id": "copy-callback-link",
    "label": "Copy link",
    "text": "crystal-lattice://action/...",
    "copied_label": "Copied",
}
```

Because callback links require a frontend connection id, link-generating session
actions should request it through generic action context mapping, such as a
`param_map` entry from `$context.connectionId`. Completion callback links should
usually omit `plugin-id` when the callback should be handled by whichever plugin
currently exposes the action id.

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

### Session-list actions (`ui_type == "session_list_action"`)

Session-list actions are ordinary application actions attached to each session
summary. They use the same routing, fixed parameters, parameter mapping, and
dialog fields as other action UI elements:

```python
{
    "ui_type": "session_list_action",
    "id": "edit_status",
    "label": "Edit status",
    "icon": "circle",
    "order": 20,
    "action_id": "set_status",
    "fixed_params": {
        "source": "session_list",
    },
    "param_map": {
        "session_id": "$session.session_id",
        "status": "$dialog.status",
    },
    "dialog": {
        "kind": "form",
        "title": "Set status",
        "inputs": [
            {
                "name": "status",
                "type": "select",
                "prefill_from": "$session.metadata.status",
                "default": "todo",
                "options": [
                    {"value": "todo", "label": "To do"},
                    {"value": "done", "label": "Done"},
                ],
            }
        ],
    },
}
```

Parameter sources are evaluated against the selected shared session summary:

| Source | Meaning |
| --- | --- |
| `$session.session_id` | Opaque session ID |
| `$session.modified` | Store-supplied modification timestamp |
| `$session.preview` | First-user-message preview |
| `$session.metadata.*` | Projected session metadata |
| `$session.presentation.*` | Application-derived title, subtitle, or meta text |
| `$session.<contributed-field>` | A field produced by a `session_list` trigger |
| `$dialog.<input-name>` | Submitted form value |

`fixed_params` are applied first; a successfully resolved `param_map` value for
the same parameter replaces the fixed value. Mappings whose source is missing
do not submit that parameter. The backend action definition applies input
defaults and validation after mapping.

Action menus and pinned actions are presentation choices over the same element:

- an unpinned action remains available in the ordinary action menu;
- pinning is a frontend/user preference and does not change the action
  definition or execution parameters;
- selecting either representation invokes the same `action_id`;
- `dialog.kind` remains the permanent ordinary behavior.

#### Optional rich presentation and permanent fallback

A session-list action may include one optional `rich_ui` object. All
presentation-specific fields belong inside that object; rich behavior does not
use another action `ui_type`.

```python
{
    "ui_type": "session_list_action",
    "id": "example",
    "label": "Example",
    "action_id": "example_action",
    "param_map": {
        "session_id": "$session.session_id",
        "value": "$dialog.value",
    },
    "dialog": {
        "kind": "form",
        "inputs": [
            {
                "name": "value",
                "type": "string",
                "prefill_from": "$session.metadata.value",
            }
        ],
    },
    "rich_ui": {
        "kind": "future_kind",
    },
}
```

Fallback is part of the permanent contract:

1. A frontend that supports `rich_ui.kind` may use that presentation.
2. A frontend that does not support the kind ignores `rich_ui` and uses the
   ordinary `dialog`.
3. An unknown future kind is valid for transport and follows the same fallback.
4. Malformed `rich_ui` is reported and discarded without discarding the valid
   ordinary action.

The initial supported kinds are `toggle` and `list`. Both use:

```typescript
interface SessionListRichUiBase {
  kind: 'toggle' | 'list';
  value_path: string;
  missing_value?: unknown;
  default_pinned?: boolean;
  placements?: string[];
}
```

`value_path` resolves against the selected shared session summary. A missing
path uses `missing_value`; explicit `null`, `false`, zero, and empty strings
remain actual values. `default_pinned` is an initial frontend preference only:
it applies when no preference is stored for that connection, never overrides a
stored empty/custom choice, and does not change plugin action semantics.

`placements` is an ordered, optional list of display locations. The supported
locations are `actions_bar`, `header_leading`, and `header_trailing`.
`actions_bar` is the default when `placements` is absent. A plugin can select
only a header slot or list multiple locations without duplicating its ordinary
action declaration; for example, `["header_trailing", "actions_bar"]` renders
both where supported. Unknown future location strings are transportable and
ignored by frontends that do not support them. Duplicate and malformed entries
are discarded during normalization. A header slot displays at most one action:
the first action in declaration order wins, while the ordinary action menu
always retains every action and its fallback dialog.

#### `rich_ui.kind: "toggle"`

```python
"rich_ui": {
    "kind": "toggle",
    "value_path": "metadata.pinned",
    "missing_value": False,
    "active_value": True,
    "default_pinned": True,
    "placements": ["header_trailing", "actions_bar"],
    "appearance": {
        "active": {"tone": "highlight"},
        "inactive": {"tone": "muted"},
    },
}
```

`active_value` is a string, number, or Boolean and is compared with both type
and value. Pinned toggle controls use the top-level action icon and the active
or inactive semantic tone. Selecting a supported toggle immediately invokes
its ordinary action; it does not introduce a second mutation route.

#### `rich_ui.kind: "list"`

```python
"rich_ui": {
    "kind": "list",
    "value_path": "metadata.status",
    "missing_value": "todo",
    "input_name": "status",
    "default_pinned": False,
    "options": [
        {"value": "todo", "label": "To do", "tone": "muted"},
        {"value": "done", "label": "Done", "tone": "success"},
    ],
}
```

List option values are typed strings or Booleans, unique by type/value, and
use the same optional icon/tone vocabulary as session-list filter options.
Pinned lists show the current option compactly. Their selection view marks the
current value and has no OK/Cancel confirmation. Selecting another option
passes it as `$dialog.<input_name>` to the ordinary action; selecting the
current value simply closes the list without a mutation. The top-level form
dialog stays separate and is always the fallback.

Semantic tones are frontend-owned and theme-aware: `primary`, `highlight`,
`warning`, `success`, `danger`, and `muted`. `highlight` is the shared yellow
saved/pinned emphasis, distinct from the orange warning signal. Plugins
declare those names, not raw colors.
Plugins must always provide a valid ordinary dialog even when they also
provide rich configuration.

### Session list fields (`ui_type == "session_list_field"`)

Session-list fields derive the `presentation` included in every application
session summary. They can read base summary data or fields contributed by
`trigger: "session_list"` actions.

```python
{
    "ui_type": "session_list_field",
    "id": "session_title",
    "role": "title",
    "label": "Title",
    "data": "metadata.title",
    "template": "{{data}}",
    "order": 0,
}
```

Required interpreted fields:

| Field | Meaning |
| --- | --- |
| `id` | Stable non-empty element ID |
| `role` | `title`, `subtitle`, or `meta` |
| `data` | Dotted path into the shared session summary |
| `template` | Optional text template; defaults to `{{data}}` |
| `order` | Optional finite number; defaults to `0` |

Fields are evaluated in ascending `order`, preserving plugin/declaration order
for ties.

- `title`: the first field with a non-missing, non-null, non-empty value whose
  template renders non-empty text wins.
- `subtitle`: follows the same first-usable-candidate rule.
- `meta`: every usable field is rendered and the results are joined with
  ` · ` in order.
- If no title field produces text, `preview` is used.
- If preview is empty, the fallback title is `Session ` plus the first eight
  characters of `session_id`.
- Missing subtitle and meta values are returned as `null`.

For example, a status plugin can place a human-readable value after earlier
timestamp and message-count fields:

```python
{
    "ui_type": "session_list_field",
    "id": "session_status_meta",
    "label": "Status",
    "role": "meta",
    "data": "session_status_label",
    "template": "Status: {{data}}",
    "order": 100,
}
```

If earlier usable meta fields render Updated, Created, and message count, the
result is joined as:

```text
Updated: … · Created: … · 12 messages · Status: In progress
```

`{{data}}` and `{{ data }}` are supported placeholders. A field may set
`metadata.format: "datetime"` to format an epoch-second or ISO datetime value
as a UTC ISO timestamp before templating. Invalid datetime values are rendered
unchanged.

Presentation is application-owned. `GET /sessions` and
`GET /sessions/{session_id}/summary` already include:

```typescript
presentation: {
  title: string;
  subtitle: string | null;
  meta: string | null;
}
```

Frontends should consume this value rather than independently reinterpret field
declarations. A local evaluator may be retained only for compatibility with an
older server.

### Session-list filters (`ui_type == "session_list_filter"`)

Session-list filters are declarative, non-action elements. Filter-aware
runtimes normalize the same contract; invalid declarations are reported and
ignored without hiding valid filters.

```python
{
    "ui_type": "session_list_filter",
    "id": "session_search",
    "label": "Search",
    "icon": "search",
    "order": 0,
    "data": [
        "session_id",
        "preview",
        "first_user_message",
        "presentation.title",
        "presentation.subtitle",
        "presentation.meta",
    ],
    "type": "text",
    "match": "contains",
    "case_sensitive": False,
    "default": "",
    "main_search": True,
}
```

The normalized declaration surface is:

```typescript
interface SessionListFilter {
  ui_type: 'session_list_filter';
  id: string;
  label: string;
  icon?: string;
  order?: number;
  data: string | string[];
  type: 'text' | 'boolean' | 'select';
  match: 'contains' | 'equals' | 'one_of';
  multiple?: boolean;          // select only
  case_sensitive?: boolean;    // text only
  missing_value?: unknown;
  default?: string | boolean | null | Array<string | boolean>;
  options?: SessionListOption[];
  main_search?: boolean;       // text only
}
```

`data` is one dotted path or an ordered list of paths. A missing path resolves
to `missing_value` when that field is declared. `missing_value` does not replace
an explicit `null`, false, zero, or empty string.

Supported combinations are:

| Type | Runtime value | Match | Inactive value |
| --- | --- | --- | --- |
| `text` | string | `contains` or `equals` | `""` |
| `boolean` | `null`, `true`, or `false` | `equals` | `null` |
| single `select` | `null` or one declared option value | `equals` | `null` |
| multiple `select` | list of declared option values | `one_of` | `[]` |

Text matching is case-insensitive unless `case_sensitive` is true. Non-string
summary values do not match text operators. For a multiple select, the
resolved summary value is scalar and matches when it occurs among the selected
values.

Composition rules:

- paths inside one filter combine with OR;
- active filters combine with AND;
- inactive filters do not affect the result;
- filtering preserves the already plugin-ordered input;
- ordering occurs before filtering, and a query limit is applied last.

Options use:

```typescript
interface SessionListOption {
  value: string | boolean;
  label: string;
  icon?: string;
  tone?: 'primary' | 'highlight' | 'warning' | 'success' | 'danger' | 'muted';
}
```

The string option value `any` is reserved for the inactive terminal spelling
and is not a valid declared select option.

`default` initializes state and is restored by Reset. Show all uses the inactive
value from the table instead of restoring plugin defaults.

`main_search: true` is valid only on a text filter. Zero or one effective main
search is valid. Competing declarations are a schema error; a runtime must not
silently choose one. Duplicate filter IDs are also rejected as ambiguous rather
than resolved by plugin order. Invalid declarations and conflicts produce
structured diagnostics while unrelated valid filters remain usable.

Mobile and desktop always keep a search input. When exactly one valid main
search exists, its label, paths, operator, and case-sensitivity control that
input. When none can be selected—including a reported conflict—the clients use
a shared case-insensitive fallback over available ordinary summary text:
`session_id`, `preview`, and derived presentation title/subtitle/meta. The
fallback does not make a conflicting plugin declaration valid and the UI still
reports the schema warning.

Terminal free-text search remains plugin-driven. `/session <text>` requires one
valid main search, while an exact session ID remains directly accessible
regardless of filters. `--filter <id>=<value>` applies command-local non-main
overrides on top of defaults. Boolean and single-select filters use `any` for
their inactive value. Multiple selects use comma-separated option values with
CSV quoting inside the shell-quoted assignment when an option itself contains
a comma.

Plugins may pair a broad main search with focused non-main text filters. The
built-in search plugin also declares `session_title_search` over displayed
title/subtitle paths and `session_first_message_search` over a complete
`first_user_message` field contributed by a `session_list` trigger.

HTTP session listing remains unfiltered in this iteration. Mobile and desktop
apply declarations to the complete ordered collection locally. Terminal
filtering uses the in-process `AgentApplication` query service. Exact session
loading by ID is independent of filter state. Frontend state is scoped by the
active connection and normalized declaration identity; changing either restores
the current declarations' defaults and removes stale values.

Built-in pin, archive, and status plugins demonstrate metadata-backed filters
and rich ordinary actions. Their `rich_ui.value_path` and filters use the same
configured metadata key; mobile and desktop never depend on a feature-specific
top-level summary field. Pin is Any by default, archive defaults to false
(hiding archived sessions), and status defaults to Any.

```python
{
    "ui_type": "session_list_filter",
    "id": "pinned_state",
    "label": "Pinned",
    "icon": "star",
    "type": "boolean",
    "match": "equals",
    "data": "metadata.pinned",
    "missing_value": False,
    "default": None,
    "options": [
        {
            "value": False,
            "label": "Not pinned",
            "icon": "star",
            "tone": "muted",
        },
        {
            "value": True,
            "label": "Pinned",
            "icon": "star",
            "tone": "highlight",
        },
    ],
}
```

```python
{
    "ui_type": "session_list_filter",
    "id": "session_status",
    "label": "Status",
    "icon": "circle",
    "type": "select",
    "match": "one_of",
    "multiple": True,
    "data": "metadata.status",
    "missing_value": "todo",
    "default": [],
    "options": [
        {"value": "todo", "label": "To do", "tone": "muted"},
        {
            "value": "in_progress",
            "label": "In progress",
            "tone": "primary",
        },
        {"value": "blocked", "label": "Blocked", "tone": "danger"},
        {"value": "done", "label": "Done", "tone": "success"},
    ],
}
```

All three plugins derive `data` from their configured metadata key. Pin and
status inactive defaults preserve the full list; archive intentionally hides
archived sessions by default. Missing pin/archive state resolves to false and
missing status resolves to `todo`, allowing old sessions to participate
without a migration write.

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

    return [
        {
            "ui_type": "config",
            "type": "dropdown",
            "key": "model",
            "label": "Model",
            "icon": "cpu",
            "options": options,
            "placeholder": "Search models or enter a model ID",
            "custom_value": {
                "enabled": True,
                "pattern": r"^[^\s]+$",
                "option_label": "Use '{value}' as a custom model ID",
            },
            "rich_ui": {
                "kind": "dropdown",
                "label": "Model",
                "show_label": False,
                "options": options,
                "placeholder": "Search models or enter a model ID",
                "custom_value": {
                    "enabled": True,
                    "pattern": r"^[^\s]+$",
                    "option_label": "Use '{value}' as a custom model ID",
                },
                "placements": ["composer"],
                "default_pinned": True,
            },
        }
    ]
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
  icon?: string;
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
  dialog?: {
    kind: "none" | "confirm" | "form";
    title?: string;
    message?: string;
    inputs?: ActionDialogInput[];
  };
  rich_ui?: {
    kind: "toggle";
    value_path: string;
    missing_value?: unknown;
    default_pinned?: boolean;
    placements?: string[];
    active_value: string | number | boolean;
    appearance: {
      active: { tone: "primary" | "highlight" | "warning" | "success" | "danger" | "muted" };
      inactive: { tone: "primary" | "highlight" | "warning" | "success" | "danger" | "muted" };
    };
  } | {
    kind: "list";
    value_path: string;
    missing_value?: unknown;
    default_pinned?: boolean;
    placements?: string[];
    input_name: string;
    options: SessionListOption[];
  } | {
    // Unknown future kinds remain transportable and fall back to dialog.
    kind: string;
    [key: string]: unknown;
  };
  metadata?: Record<string, any>;
}

interface SessionListFieldElement {
  ui_type: string;
  plugin: string;
  id: string;
  label?: string;
  role: "title" | "subtitle" | "meta";
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
GET /application/ui-schema
```

Returns global UI elements from application plugins. Used for:
- global application actions or display elements that do not require a current
  session;
- `session_list_action` definitions;
- `session_list_field` presentation declarations;
- `session_list_filter` declarations.

```
GET /sessions/{session_id}/application/ui-schema
```

Returns session-contextual UI elements from application plugins. Used for:
- `ui_type == "session_action"`: Session-scoped actions
- `ui_type == "message_action"`: Message-scoped actions

Optional query parameter `?plugin=name` filters elements by plugin.

Session-list declarations come from the global application schema because they
must be interpreted once for the complete list rather than rediscovered per
session.

### Application actions

An element with `ui_type: "application_action"` is rendered once for the
connected application and does not require a selected session:

```json
{
  "ui_type": "application_action",
  "plugin": "application_config",
  "id": "reload_application",
  "label": "Reload application",
  "action_id": "reload_application",
  "dialog": {
    "kind": "confirm",
    "title": "Reload application"
  }
}
```

Action identity is the pair `(plugin, action_id)`, so different application
plugins may use the same local action id. `secret` and `password` dialog fields
are masked and never prefilled.

### Session summaries

```text
GET /sessions
GET /sessions/{session_id}/summary
```

The first endpoint returns the complete application-ordered summary list
(optionally truncated by its existing `limit` parameter). The second returns
the same summary contract for one exact ID without applying list filters.

### Server settings values

```
GET /server/settings/ui-schema
```

Returns server settings UI elements from application plugins. The application
passes current server settings in UI context so plugins can decide which
server-scoped controls to return.

```
GET /server/settings
PATCH /server/settings
DELETE /server/settings/{key}
```

These endpoints read and mutate application-owned server settings. They are the
value channel for application plugin config elements with `scope: "server"`.

---

## See also

- [Provider plugins](provider-plugins.md) - Provider implementation guide
- [Application plugins](application-plugins.md) - Application plugin guide
- [Feature plugins](feature-plugins.md) - Feature plugin guide
- [Plugin actions](actions.md) - Action definitions and lifecycle