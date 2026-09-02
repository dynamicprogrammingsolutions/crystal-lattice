# Anthropic reasoning controls

`AnthropicReasoningExtension` interprets and preserves thinking returned by any
supported Anthropic-compatible endpoint.

`AnthropicReasoningControlsExtension` is a separate optional extension for
official-style Anthropic reasoning controls. It uses the selected model's
discovered capability descriptor, explicit capability details, or built-in
Claude model regex fallbacks.

## Settings

The extension contributes:

- `anthropic_reasoning_mode`: `disabled`, `manual`, or `adaptive`;
- `anthropic_reasoning_effort`: model-supported effort level;
- `anthropic_reasoning_budget_tokens`: manual-thinking budget;
- `anthropic_reasoning_display`: `summarized` or `omitted`.

The request mapping is:

| Setting | Anthropic request |
|---|---|
| `disabled` | `thinking.type=disabled` |
| `manual` | `thinking.type=enabled` plus `budget_tokens` |
| `adaptive` | `thinking.type=adaptive` |
| effort | `output_config.effort` |
| display | `thinking.display` |

Raw `request_options` is applied after the controls extension and wins when
both configure the same request field.

## Capability enablement

Official configuration can enable the extension explicitly:

```json
{
  "capabilities": {
    "anthropic_reasoning_controls": true
  }
}
```

When explicit enablement is absent, an authoritative selected-model descriptor
can enable the extension automatically. Explicit false disables it.

Compatible endpoints without official capability data continue using
`AnthropicReasoningExtension` and raw `request_options`. They may opt in with
the capability plus explicit details:

```json
{
  "capabilities": {
    "anthropic_reasoning_controls": true
  },
  "anthropic_reasoning_capabilities": {
    "thinking_types": ["enabled"],
    "effort_levels": [],
    "adaptive_interleaving": false
  }
}
```

## Copyable regex fallback

The extension contains fallback rules for known Claude model IDs when the
Models API does not return capability details. The equivalent configuration
below can be copied into an application config and edited when an endpoint,
alias, or future model needs different behavior.

Explicit `anthropic_reasoning_capabilities` selected by these variants
overrides both discovered and built-in fallback details.

```json
{
  "mixins": {
    "anthropic_reasoning_capability_overrides": {
      "$variants": [
        {
          "$when": {
            "model": {
              "$matches": "^claude-(?:haiku|sonnet|opus)-4-5(?:$|-\\d{8}$)"
            }
          },
          "anthropic_reasoning_capabilities": {
            "thinking_types": ["enabled"]
          }
        },
        {
          "$when": {
            "model": {
              "$matches": "^claude-(?:sonnet|opus)-4-5(?:$|-\\d{8}$)"
            }
          },
          "anthropic_reasoning_capabilities": {
            "manual_interleaving_beta": "interleaved-thinking-2025-05-14"
          }
        },
        {
          "$when": {
            "model": {
              "$matches": "^claude-opus-4-5(?:$|-\\d{8}$)"
            }
          },
          "anthropic_reasoning_capabilities": {
            "effort_levels": ["low", "medium", "high"]
          }
        },
        {
          "$when": {
            "model": {
              "$matches": "^claude-(?:sonnet|opus)-4-6$"
            }
          },
          "anthropic_reasoning_capabilities": {
            "thinking_types": ["enabled", "adaptive"],
            "effort_levels": ["low", "medium", "high", "max"],
            "adaptive_interleaving": true,
            "manual_interleaving_beta": "interleaved-thinking-2025-05-14"
          }
        },
        {
          "$when": {
            "model": {
              "$matches": "^claude-(?:sonnet-5|opus-4-(?:7|8)|opus-5|fable-5|mythos-5)$"
            }
          },
          "anthropic_reasoning_capabilities": {
            "thinking_types": ["adaptive"],
            "effort_levels": ["low", "medium", "high", "xhigh", "max"],
            "adaptive_interleaving": true
          }
        },
        {
          "$when": {
            "model": "claude-mythos-preview"
          },
          "anthropic_reasoning_capabilities": {
            "thinking_types": ["adaptive"],
            "effort_levels": ["low", "medium", "high", "max"],
            "adaptive_interleaving": true
          }
        }
      ]
    }
  },
  "providers": {
    "anthropic": {
      "capabilities": {
        "anthropic_reasoning_controls": true
      }
    }
  },
  "agents": {
    "claude-anthropic": {
      "mixin_refs": [
        "anthropic_reasoning_capability_overrides"
      ]
    }
  }
}
```

The built-in fallback and this snippet deliberately do not add provider
`betas` or `beta_headers`. Manual interleaving beta selection remains explicit
provider configuration.

## Default-setting variants

Capability details determine available controls. Defaults remain ordinary
configuration and can use separate variants:

```json
{
  "$variants": [
    {
      "$when": {
        "model": {
          "$matches": "^claude-(?:haiku|sonnet|opus)-4-5(?:$|-\\d{8}$)"
        }
      },
      "anthropic_reasoning_mode": "manual",
      "anthropic_reasoning_budget_tokens": 1024
    },
    {
      "$when": {
        "model": {
          "$matches": "^claude-opus-4-5(?:$|-\\d{8}$)"
        }
      },
      "anthropic_reasoning_effort": "high"
    },
    {
      "$when": {
        "model": {
          "$matches": "^claude-(?:(?:sonnet|opus)-4-6|sonnet-5|opus-4-(?:7|8)|opus-5|(?:fable|mythos)-5|mythos-preview)$"
        }
      },
      "anthropic_reasoning_mode": "adaptive",
      "anthropic_reasoning_effort": "high",
      "anthropic_reasoning_display": "summarized"
    }
  ]
}
```

Context-management edits and provider beta configuration remain independent
raw configuration.