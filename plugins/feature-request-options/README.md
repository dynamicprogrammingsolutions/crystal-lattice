# Feature Request Options

Feature plugin that merges `request_options` from config into the provider payload, with support for declarative UI configuration using flat keys.

## Overview

This plugin allows you to inject arbitrary request parameters into the provider's API call. It's useful for setting parameters like `temperature`, `max_tokens`, `top_p`, etc.

The plugin supports two configuration patterns:
1. Direct `request_options` for simple cases
2. `request_options_ui` for UI-driven configuration with flat keys like `request_options__temperature`

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

Declarative UI element definitions for `request_options` keys. This generates **flat config keys** with the prefix `request_options__`.

| Config Value | UI Element Type | Generated Config Key |
|--------------|-----------------|-------------------|
| `["opt1", "opt2"]` | `select` dropdown | `request_options__{key}` (string enum) |
| `"string"` | text input | `request_options__{key}` (string) |
| `"number"` | number input | `request_options__{key}` (number) |

Keys are automatically converted to labels (e.g., `max_tokens` → "Max Tokens").

## How Flat Keys Work

When you define `request_options_ui`, the plugin:

1. **Generates UI elements** with flat keys like `request_options__temperature`
2. **Generates config schema** entries for these flat keys
3. **Merges flat keys into `request_options`** during `init()`, then removes them from config

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

## Benefits

- **Zero code required** - Define UI elements declaratively with `request_options_ui`
- **Flat config keys** - UI-friendly key names like `request_options__temperature`
- **Auto-merge** - Flat keys automatically merge into nested `request_options`
- **Provider agnostic** - Works with any OpenAI-compatible provider
- **Clean state** - Flat keys are removed from config after merging
- **Auto-generated labels** - Clean UI labels from your config keys
