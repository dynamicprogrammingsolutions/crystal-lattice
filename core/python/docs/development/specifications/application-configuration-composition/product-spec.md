# Application configuration composition product specification

## Purpose

Application configurations need reusable static fragments and model-specific
settings without duplicating complete provider or agent definitions.

Mixins already provide static reuse. The target adds conditional variants and
one consistent recursive merge language so a configuration can select
request options, UI, beta features, and other already-loaded provider settings
from the effective model.

## Users

Application users need to:

- reuse provider and agent settings through named mixins;
- choose models at runtime without maintaining one agent per model family;
- define exact or regular-expression model conditions;
- preserve common nested settings while replacing selected subtrees;
- understand deterministic precedence among providers, mixins, variants, and
  explicit session overrides;
- receive actionable configuration diagnostics.

Application maintainers need:

- one merge implementation for mixins, provider-to-agent composition, and
  variants;
- isolated condition operators that can be extended without changing provider
  or plugin code;
- compatibility with existing mixin configurations;
- bounded recursion and immutable input mappings.

## Target experience

Static configuration reuse remains available:

```json
{
  "mixins": {
    "provider-defaults": {
      "timeout": 300,
      "request_options": {
        "temperature": 0.2
      }
    }
  },
  "providers": {
    "example": {
      "mixin_refs": ["provider-defaults"],
      "provider": "example_provider"
    }
  }
}
```

Model-specific behavior uses variants:

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
        "reasoning": {
          "type": "adaptive"
        }
      }
    }
  ]
}
```

The application reevaluates the variants when the effective model changes.
Explicit session overrides remain authoritative.

## Goals

- Preserve current mixin behavior.
- Share one recursive shallow/deep merge implementation.
- Support `$variants`, `$when`, and `$matches`.
- Permit `$variants` and `$merge` in nested mappings.
- Allow a deep default with shallow behavior for selected sibling keys.
- Keep configuration-language controls out of runtime provider config.
- Prevent variants from changing provider/plugin topology after startup.
- Support focused consumer documentation for mixins and variants.

## Non-goals

- Arbitrary Python, JavaScript, or expression evaluation.
- Conditional plugin installation or provider-class loading.
- Conditions over provider-discovered capability objects in the initial
  implementation.
- Dotted-path condition lookup in the initial implementation.
- Interpreting variants inside arrays.
- Array append, prepend, or de-duplication operations in the initial
  implementation.
- Moving provider-specific wire-format behavior into the application config
  resolver.