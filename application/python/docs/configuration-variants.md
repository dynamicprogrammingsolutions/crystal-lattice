# Configuration variants

Variants apply model- or config-selected settings without duplicating complete
provider or agent definitions.

## Basic use

```json
{
  "$variants": [
    {
      "$when": {
        "model": "example-model-5"
      },
      "request_options": {
        "thinking": {
          "type": "adaptive"
        }
      }
    }
  ]
}
```

Each entry contains:

- `$when`: required condition mapping;
- optional `$merge`: merge policy for the entry's ordinary sibling keys;
- ordinary keys that form the selected overlay.

Matching variants apply in declaration order.

## Exact conditions

A scalar value uses exact equality:

```json
{
  "$when": {
    "model": "claude-sonnet-5"
  }
}
```

Multiple condition fields use logical AND.

## Regular-expression conditions

Use `$matches` for string regular expressions:

```json
{
  "$when": {
    "model": {
      "$matches": "^claude-sonnet-5(?:$|-)"
    }
  }
}
```

Invalid expressions are startup errors. Conditions initially inspect
top-level effective-config fields.

## Effective-config ordering

Variant selection uses an immutable preview of:

```text
base agent config + explicit session/request overrides
```

The resolver then:

1. Starts again from the unchanged base config.
2. Applies matching variants in order.
3. Applies explicit session/request overrides last.

An earlier variant cannot make a later condition start matching. Changing the
session model reevaluates the variants from the clean base, so settings from
the previous model do not remain.

## Merge behavior

Variants default to deep merge. They support the same `$merge` language as
[configuration mixins](configuration-mixins.md).

Example:

```json
{
  "$variants": [
    {
      "$when": {
        "model": {
          "$matches": "^example-model-5(?:$|-)"
        }
      },
      "$merge": {
        "default": "deep",
        "shallow": ["request_options"]
      },
      "request_options": {
        "thinking": {
          "type": "adaptive"
        }
      },
      "headers": {
        "x-feature": "enabled"
      }
    }
  ]
}
```

Here `request_options` replaces a colliding base value, while `headers` merges
recursively.

## Nested variants

`$variants` may appear in mixins, providers, agents, selected overlays, and
nested mappings:

```json
{
  "request_options": {
    "temperature": 0.2,
    "$variants": [
      {
        "$when": {
          "model": {
            "$matches": "^claude-haiku-4-5(?:$|-)"
          }
        },
        "thinking": {
          "type": "enabled",
          "budget_tokens": 1024
        }
      }
    ]
  }
}
```

Mappings inside arrays are treated as data and are not traversed for variants.

## Protected keys

Root variants cannot change application/plugin topology after startup:

- `provider`;
- `plugins`;
- `disabled_plugins`;
- `enabled_plugins`;
- `force_enabled_plugins`;
- `mixin_refs`;
- `mixin_merge`;
- `mixin_policy`.

Provider request bodies may still contain similarly named nested fields. For
example, `request_options.provider` is not the application provider selector.

## Claude model example

One direct Anthropic agent can select manual thinking for Haiku 4.5 and
adaptive thinking for Sonnet 5:

```json
{
  "mixins": {
    "claude-model-variants": {
      "$variants": [
        {
          "$when": {
            "model": {
              "$matches": "^claude-haiku-4-5(?:$|-\\d{8}$)"
            }
          },
          "anthropic_reasoning_mode": "manual",
          "anthropic_reasoning_budget_tokens": 1024
        },
        {
          "$when": {
            "model": {
              "$matches": "^claude-sonnet-5$"
            }
          },
          "betas": [
            "context-management-2025-06-27"
          ],
          "anthropic_reasoning_mode": "adaptive",
          "anthropic_reasoning_display": "summarized",
          "anthropic_reasoning_effort": "high"
        }
      ]
    }
  },
  "agents": {
    "claude-anthropic": {
      "mixin_refs": ["claude-model-variants"],
      "provider": "anthropic",
      "model": "claude-sonnet-5"
    }
  }
}
```

The Anthropic reasoning-controls extension derives available settings from
official model capabilities and known model fallbacks. These variants select
defaults. Unknown models receive no inferred defaults unless another variant
matches. Raw request options remain available.

## Diagnostics

Malformed variant collections, missing or invalid `$when`, unknown condition
operators, invalid regular expressions, protected keys, invalid merge policy,
and excessive nesting prevent application startup with a path-specific
configuration error.