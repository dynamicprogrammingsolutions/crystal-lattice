# Feature Request Options

Feature plugin that merges `request_options` from config into the provider payload, with support for declarative UI configuration using flat override keys.

## Overview

This plugin allows you to inject arbitrary request parameters into the provider's API call. It's useful for setting parameters like `temperature`, `max_tokens`, `top_p`, etc.

The plugin supports two configuration patterns:
1. Direct `request_options` for simple cases and defaults
2. `request_options_ui` for UI-driven configuration with flat override keys like `request_options__temperature`

## Configuration

### `request_options`

A dictionary of options to merge into the request payload. These override any existing values.

```json
{
  "request_options": {
    "temperature": 0.7,
    "max_tokens": 2048,
    "top_p": 0.9
  }
}
```

### `request_options_ui`

Declarative UI element definitions for `request_options` keys. This generates **flat override keys** with the prefix `request_options__`, while still resolving defaults from the nested `request_options` object.

| Config Value | UI Element Type | Generated Override Key |
|--------------|-----------------|-------------------|
| `["opt1", "opt2"]` | `select` dropdown | `request_options__{path}` |
| `"string"` | text input | `request_options__{path}` |
| `"number"` | number input | `request_options__{path}` |
| `"boolean"` / `"checkbox"` | checkbox | `request_options__{path}` |
| `{"type": "select", "options": [...], "rich_ui": true}` | fixed-choice select plus a pinned composer dropdown | `request_options__{path}` |
| nested object | recursive subtree | `request_options__{parent}__{child}` |

Keys are automatically converted to labels (for example, `max_tokens` → "Max Tokens", `thinking.type` → "Thinking Type").

Generated UI elements also include:

- `config_path`: nested source path such as `request_options.thinking.type`
- `default`: nested default copied from `request_options` when present in config

### Composer controls

Use an explicit select descriptor to make one fixed-choice request option
available as a text-only rich control around the message composer:

```json
{
  "request_options": {
    "reasoning_effort": "max"
  },
  "request_options_ui": {
    "reasoning_effort": {
      "type": "select",
      "options": ["high", "max"],
      "rich_ui": true
    }
  }
}
```

The descriptor keeps the ordinary Session Settings control and its flat
`request_options__reasoning_effort` override key. `rich_ui: true` adds the
same setting around the composer with the generated label and options,
composer placement, default pinning, and no custom values, colors, or
per-option icons.

Without `rich_ui: true`, a select descriptor is equivalent to the existing
array shorthand. Descriptors may appear inside nested `request_options_ui`
subtrees and retain the same nested `config_path`, default lookup, deep merge,
and request-payload behavior.

## How Flat Keys Work

When you define `request_options_ui`, the plugin:

1. **Generates UI elements** with flat keys like `request_options__temperature`
2. **Keeps nested source metadata** via `config_path` and `default`
3. **Merges flat override keys into `request_options`** during `init()`, then removes them from config

### Example Flow

**Config input:**
```json
{
  "request_options": {
    "temperature": 0.7
  },
  "request_options_ui": {
    "temperature": ["0.0", "0.5", "0.7", "1.0"],
    "max_tokens": ["512", "1024", "2048"]
  },
  "request_options__temperature": "0.9"
}
```

**After `init()`:**
```json
{
  "request_options": {
    "temperature": "0.9"
  },
  "request_options_ui": { ... }
}
```

The flat key `request_options__temperature` is merged into `request_options.temperature` and then removed.

### Nested Example

You can also define nested provider-specific controls:

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

This generates UI elements with keys:

- `request_options__thinking__type`
- `request_options__thinking__clear_thinking`

and nested source metadata:

- `config_path: request_options.thinking.type`
- `config_path: request_options.thinking.clear_thinking`

If the UI overrides only `request_options__thinking__clear_thinking`, the plugin deep-merges it back into `request_options.thinking` so sibling keys like `type` are preserved.

## Complete Examples

### Basic Usage (No UI)

```json
{
  "agents": {
    "default": {
      "provider": "openai",
      "model": "gpt-4o",
      "request_options": {
        "temperature": 0.7,
        "max_tokens": 2048
      }
    }
  }
}
```

### With UI Configuration

```json
{
  "agents": {
    "creative_writer": {
      "provider": "openai",
      "model": "gpt-4o",
      "request_options": {
        "temperature": 0.9,
        "max_tokens": 4096
      },
      "request_options_ui": {
        "temperature": ["0.0", "0.5", "0.7", "0.9", "1.0"],
        "max_tokens": ["1024", "2048", "4096", "8192"],
        "frequency_penalty": "number"
      }
    }
  }
}
```

This generates:
- A **select dropdown** with key `request_options__temperature`
- A **select dropdown** with key `request_options__max_tokens`
- A **number input** with key `request_options__frequency_penalty`

### Provider-Specific Nested UI Example

```json
{
  "agents": {
    "zai": {
      "provider": "zai",
      "model": "glm-4.5-air",
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
  }
}
```

This lets the UI expose nested request settings while keeping the persisted defaults in the natural nested `request_options` structure.

### Flat Override With Nested Defaults Example

```json
{
  "agents": {
    "fireworks": {
      "provider": "fireworks",
      "model": "fireworks/qwen3-8b",
      "request_options": {
        "reasoning_history": "preserved"
      },
      "request_options_ui": {
        "reasoning_history": ["disabled", "interleaved", "preserved"]
      }
    }
  }
}
```

The UI element still uses the flat override key `request_options__reasoning_history`, but its default/current value is resolved from `request_options.reasoning_history`.

### Runtime Override Example

When the UI sets a value, it updates the flat key which gets merged:

```json
{
  "request_options": {
    "temperature": 0.5,
    "max_tokens": 2048
  },
  "request_options_ui": {
    "temperature": ["0.0", "0.5", "0.7", "0.9"]
  },
  // UI sets this, overriding request_options.temperature
  "request_options__temperature": "0.9"
}
```

Result after `init()`: `request_options.temperature` becomes `0.9`

For nested keys, the merge is deep. For example, overriding only `request_options__thinking__clear_thinking` updates `request_options.thinking.clear_thinking` without discarding `request_options.thinking.type`.

## Benefits

- **Zero code required** - Define UI elements declaratively with `request_options_ui`
- **Flat override keys** - UI-friendly session override keys like `request_options__temperature`
- **Nested defaults** - Base config can stay in natural nested `request_options` objects
- **Auto-merge** - Flat override keys automatically deep-merge into nested `request_options`
- **Provider agnostic** - Works with any OpenAI-compatible provider
- **Clean state** - Flat keys are removed from config after merging
- **Auto-generated labels** - Clean UI labels from your config keys and nested paths

## License

Copyright 2026 Dynamic Programming Solutions Kft.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

<http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
