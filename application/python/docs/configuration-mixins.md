# Configuration mixins

Mixins are named reusable configuration fragments for providers, agents, and
other mixins.

## Basic use

```json
{
  "mixins": {
    "portable-system-message": {
      "system_message": {
        "variables": {
          "AGENTS": {
            "text": "${file:${env:WORKING_DIR}/AGENTS.md}"
          }
        }
      }
    },
    "openai-base": {
      "mixin_refs": ["portable-system-message"],
      "provider": "openai_compatible",
      "model": "gpt-5-mini"
    }
  },
  "providers": {
    "openai": {
      "mixin_refs": ["openai-base"],
      "api_key": "${env:OPENAI_API_KEY}"
    }
  },
  "agents": {
    "default": {
      "provider": "openai",
      "system_message": {
        "template": "{{AGENTS}}"
      }
    }
  }
}
```

## Keys

Top-level keys:

- `mixins`: mapping of mixin ID to config fragment;
- `mixin_policy.default_merge`: `shallow` by default or `deep`;
- `mixin_policy.max_depth`: positive recursion limit, default `16`.

Provider, agent, and mixin mappings may use:

- `mixin_refs`: ordered list of mixin IDs;
- `mixin_merge`: compatibility spelling for a root `shallow` or `deep` merge;
- `$merge`: recursive merge policy.

## Precedence

1. Referenced mixins are resolved recursively.
2. References are applied in `mixin_refs` order.
3. Later references override earlier references.
4. Local mixin/provider/agent values override referenced values.
5. Agent configuration overlays provider configuration.

Missing references, cycles, invalid merge policies, and excessive recursion
are startup errors.

## Merge modes

Shallow merge replaces a colliding direct value. If both mappings contain
`request_options`, the overlay's complete `request_options` value replaces the
base value.

Deep merge recursively merges colliding mappings. Arrays and scalar values
still replace.

String form:

```json
{
  "$merge": "deep",
  "request_options": {
    "temperature": 0.2
  }
}
```

Parent-scoped object form:

```json
{
  "$merge": {
    "default": "deep",
    "shallow": ["request_options"],
    "deep": ["headers"]
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
```

The lists name direct sibling keys:

- `request_options` uses shallow merge and replaces the complete colliding
  value;
- `headers` uses deep merge;
- other keys use `default`.

Nested mappings can define another policy for their children:

```json
{
  "$merge": "deep",
  "request_options": {
    "$merge": {
      "default": "deep",
      "shallow": ["thinking"]
    },
    "thinking": {
      "type": "adaptive",
      "display": "summarized"
    },
    "output_config": {
      "effort": "high"
    }
  }
}
```

Key lists use direct names, not dotted paths. One key cannot appear under both
`shallow` and `deep`.

## Compatibility

Existing configurations can continue using:

```json
{
  "mixin_merge": "deep"
}
```

At a provider, agent, or mixin root this is equivalent to:

```json
{
  "$merge": "deep"
}
```

If both forms are present, they must specify the same string mode.

## Arrays

Arrays replace in shallow and deep modes. They are not recursively interpreted
for mixins, variants, or merge controls.