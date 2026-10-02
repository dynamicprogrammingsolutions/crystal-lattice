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
    "model": "example-model-5"
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
      "$matches": "^example-model-5(?:$|-)"
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
            "$matches": "^example-small(?:$|-)"
          }
        },
        "reasoning": {
          "enabled": true,
          "effort": "low"
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

## Complete composition example

This fictional configuration demonstrates a complete mixin, provider, and
agent composition without prescribing settings for a real provider:

```json
{
  "mixins": {
    "example-provider-defaults": {
      "timeout": 120,
      "request_options": {
        "temperature": 0.2
      }
    },
    "example-model-profiles": {
      "$variants": [
        {
          "$when": {
            "model": {
              "$matches": "^example-pro(?:$|-)"
            }
          },
          "service_tier": "standard",
          "request_options": {
            "reasoning": {
              "enabled": true
            }
          }
        },
        {
          "$when": {
            "model": "example-pro-preview"
          },
          "service_tier": "priority",
          "request_options": {
            "reasoning": {
              "effort": "high"
            }
          }
        },
        {
          "$when": {
            "model": {
              "$matches": "^example-pro(?:$|-)"
            },
            "region": "eu"
          },
          "headers": {
            "x-example-region": "eu"
          }
        }
      ]
    }
  },
  "providers": {
    "example": {
      "mixin_refs": [
        "example-provider-defaults",
        "example-model-profiles"
      ],
      "provider": "example-provider"
    }
  },
  "agents": {
    "example-agent": {
      "provider": "example",
      "model": "example-pro-preview",
      "region": "eu"
    }
  }
}
```

All three variants match. The first and second variants deep-merge their
`request_options.reasoning` mappings. Both write `service_tier`, so the later
exact-match variant wins that scalar conflict. The third variant demonstrates
logical AND across `model` and `region`.

The resolved agent configuration is:

```json
{
  "provider": "example-provider",
  "model": "example-pro-preview",
  "region": "eu",
  "timeout": 120,
  "service_tier": "priority",
  "headers": {
    "x-example-region": "eu"
  },
  "request_options": {
    "temperature": 0.2,
    "reasoning": {
      "enabled": true,
      "effort": "high"
    }
  }
}
```

This example is intentionally provider-neutral. Real provider defaults belong
in the maintained configuration and package documentation, not in this
configuration-language guide.

## Diagnostics

Malformed variant collections, missing or invalid `$when`, unknown condition
operators, invalid regular expressions, protected keys, invalid merge policy,
and excessive nesting prevent application startup with a path-specific
configuration error.