# Request options UI product specification

## Purpose

Provider-compatible APIs frequently accept useful request-body options that do
not justify a dedicated provider extension. The `feature-request-options`
plugin lets configuration authors pass those options through while optionally
exposing selected values as ordinary session settings.

`request_options_ui` must preserve a concise shorthand for common settings and
support nested native request shapes. Configuration authors also need a small
opt-in for promoting a fixed-choice request option, such as
`reasoning_effort`, to the standard rich UI around the message composer.

## Users

### Configuration authors

Configuration authors need to:

- declare ordinary controls without reproducing complete UI-schema elements;
- keep provider-native request options nested in their wire-format shape;
- select only a few important options for compact composer placement;
- use the same configuration with official and compatible provider endpoints;
- avoid provider-specific frontend contracts or duplicate mutation paths.

### Plugin and frontend consumers

The request-options plugin generates ordinary config UI elements. Frontends
consume those elements through the shared config and rich-UI contracts and do
not need request-options-specific rendering or mutation behavior.

## Existing shorthand contract

`request_options_ui` is a nested mapping. Existing leaf shorthand remains:

| Declaration | Generated ordinary control |
|---|---|
| `["low", "high"]` | Fixed-choice `select` with string options |
| `"string"` | Text input |
| `"number"` | Number input |
| `"boolean"` or `"checkbox"` | Boolean checkbox |

An object without a recognized leaf descriptor is a nested request-options
subtree:

```json
{
  "request_options": {
    "thinking": {
      "type": "enabled",
      "clear_thinking": false
    }
  },
  "request_options_ui": {
    "thinking": {
      "type": ["disabled", "enabled"],
      "clear_thinking": "boolean"
    }
  }
}
```

The generated keys are flat session-override identities:

```text
request_options__thinking__type
request_options__thinking__clear_thinking
```

Each element retains its nested source through `config_path`, such as
`request_options.thinking.type`, and copies the current nested
`request_options` value into `default` when present. During plugin
initialization, flat overrides are inflated and deep-merged into
`request_options` without discarding sibling request fields.

Unknown leaf forms, empty option arrays, invalid array members, and invalid
nested subtrees are ignored without preventing valid sibling controls from
being generated.

## Rich fixed-choice descriptor

A fixed-choice leaf may use an explicit descriptor:

```json
{
  "request_options_ui": {
    "reasoning_effort": {
      "type": "select",
      "options": ["high", "max"],
      "rich_ui": true
    }
  }
}
```

The `type` field distinguishes a leaf descriptor from a nested request-options
subtree. The initial descriptor contract supports:

| Field | Required | Meaning |
|---|---|---|
| `type` | yes | Must be `"select"` |
| `options` | yes | Non-empty array of string values |
| `rich_ui` | no | `true` opts the control into the standard composer presentation |

Malformed descriptors are ignored as invalid leaves without preventing valid
sibling declarations from generating controls. Unsupported descriptor types
do not change the meaning of ordinary nested mappings.

Without `rich_ui: true`, the descriptor is equivalent to the existing option
array shorthand. With `rich_ui: true`, the plugin generates the same ordinary
fixed-choice control and adds a self-contained rich dropdown:

- the flat override key and `config_path` remain unchanged;
- the ordinary element has the generated label, a static `sliders` fallback
  icon, options, and nested default;
- the rich element repeats the generated label and options;
- `placements` is `["composer"]`;
- `default_pinned` is `true`;
- `show_label` and `show_icon` are `false`, making the pinned presentation
  text-only;
- custom values are not enabled, because request-option choices remain
  fixed-choice;
- option labels equal their configured string values and do not add
  state-dependent colors or icons.

For example, the descriptor above generates a rich control equivalent to:

```json
{
  "kind": "dropdown",
  "label": "Reasoning Effort",
  "show_label": false,
  "show_icon": false,
  "options": [
    {"value": "high", "label": "high"},
    {"value": "max", "label": "max"}
  ],
  "placements": ["composer"],
  "default_pinned": true
}
```

The descriptor may appear at any supported nesting depth. For example:

```json
{
  "request_options_ui": {
    "thinking": {
      "effort": {
        "type": "select",
        "options": ["low", "medium", "high"],
        "rich_ui": true
      }
    }
  }
}
```

This produces the ordinary flat key
`request_options__thinking__effort` and writes overrides back to
`request_options.thinking.effort`.

## Compatibility

Existing shorthand configuration remains valid and keeps its existing output.
The descriptor is additive and uses the same flat-key, default-resolution,
deep-merge, and request-injection paths.

The generated rich metadata uses the platform's existing config rich-UI
contract. The request-options plugin does not add a frontend renderer, action
endpoint, provider-specific setting, or second persistence format.

## Non-goals

- Rich numeric, text, or boolean request-option controls in the initial
  descriptor contract.
- Arbitrary rich labels, icons, tones, placements, or pinning configuration.
- Custom values for descriptor-generated fixed-choice controls.
- Provider-specific validation of request-option names or values.
- Model discovery or provider-owned model selector generation.
- Moving reasoning response parsing or preservation into the request-options
  plugin.
- Editing a user's home configuration as part of the package implementation.