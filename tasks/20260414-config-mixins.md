# Config Mixins For Application Configuration

Investigate and implement support for reusable recursive mixins in the application configuration manager, with clear precedence and configurable shallow/deep merge behavior.

## Requirements checklist

- [x] Add a top-level `mixins` registry to the application config protocol.
- [x] Support referencing mixins from config nodes via an ordered array of string ids.
- [x] Support recursive mixins with circular-reference safety and a max-depth limit.
- [x] Define deterministic precedence so local keys override mixins and later mixins override earlier mixins.
- [x] Define configurable merge behavior with a default and per-node override.
- [x] Keep the design compatible with the current provider/agent config pipeline and plugin package resolution.
- [x] Add tests and docs covering the new behavior.

## Summary

The current application config flow is centralized and makes this feature feasible without changing `AgentCore` or the plugin protocols. Placeholder resolution happens first in `core/python/agent_app/config.py`, then `AgentApplication` consumes the resolved config and computes plugin catalogs and per-agent base configs. The only built-in structural merge today is shallow `provider defaults + agent overrides`, so mixins fit naturally as a new normalization step inserted after placeholder resolution and before plugin extraction / agent base-config caching.

## Current State

- Placeholder resolution is implemented in `core/python/agent_app/config.py`:
  - `resolve_placeholders(...)` at `core/python/agent_app/config.py:150`
  - recursive tree walk at `core/python/agent_app/config.py:135`
- Provider/agent flattening is currently shallow and lives in:
  - `build_agent_config(...)` at `core/python/agent_app/config.py:166`
  - current merge is `{**provider_defaults, **agent_cfg}` at `core/python/agent_app/config.py:188`
- Per-request config overrides are also shallow:
  - `resolve_request_config(...)` at `core/python/agent_app/config.py:199`
- `AgentApplication` currently loads and consumes resolved config here:
  - raw config load at `core/python/agent_app/application_future.py:128`
  - placeholder resolution at `core/python/agent_app/application_future.py:134`
  - plugin extraction begins immediately after at `core/python/agent_app/application_future.py:148`
  - per-agent base configs are cached at `core/python/agent_app/application_future.py:296`
  - `build_agent_config(...)` is called while caching at `core/python/agent_app/application_future.py:302`
- Existing docs describe config-layer plugin behavior and merge order:
  - `docs/plugins/application-config.md:52`
  - plugin catalog merge order at `docs/plugins/application-config.md:151`
- Existing tests cover placeholder resolution and basic provider/agent merge behavior:
  - `core/python/tests/test_application_layer_config.py:15`
  - `core/python/tests/test_application_layer_config.py:38`

## Feasibility Assessment

- Feasible without `AgentCore` changes.
- Feasible without changing the cross-language plugin protocols in `TYPES_AND_PROTOCOLS.md`.
- Best fit is a new config-normalization phase in `core/python/agent_app/config.py` that expands mixins before `AgentApplication` reads providers/agents/plugins.
- Mixins can affect normal runtime keys and config-owned plugin fields like `plugins`, `disabled_plugins`, and `enabled_plugins` if expansion happens before current plugin extraction logic.

## Recommended Protocol Draft

Recommended top-level keys:

- `mixins`: mapping of mixin id -> config fragment
- `mixin_policy`: optional global policy block

Recommended per-node keys on providers, agents, and mixin definitions:

- `mixin_refs`: ordered list of mixin ids
- `mixin_merge`: optional merge mode override, one of `"shallow"` or `"deep"`

Recommended initial scope:

- Support mixins on `providers.<id>` and `agents.<id>` in v1.
- Allow mixins themselves to reference other mixins recursively.
- Do not attempt fully generic “mixins anywhere in the config tree” in v1 unless product direction explicitly requires it.

Example draft config:

```json
{
  "mixin_policy": {
    "default_merge": "shallow",
    "max_depth": 16,
    "allowed_scopes": ["providers", "agents"]
  },
  "mixins": {
    "portable-paths": {
      "mixin_merge": "deep",
      "system_message": {
        "variables": {
          "AGENTS": {
            "text": "${file:${env:WORKING_DIR}/AGENTS.md}"
          }
        }
      }
    },
    "openai-base": {
      "mixin_refs": ["portable-paths"],
      "model": "gpt-5-mini"
    }
  },
  "providers": {
    "openai": {
      "mixin_refs": ["openai-base"],
      "provider": "openai_compatible",
      "api_key": "${env:OPENAI_API_KEY}"
    }
  },
  "agents": {
    "default": {
      "mixin_refs": ["portable-paths"],
      "provider": "openai",
      "system_message": {
        "template": "..."
      }
    }
  }
}
```

## Proposed Precedence Rules

Within a single resolved node:

1. Resolve referenced mixins recursively.
2. Apply mixins in `mixin_refs` order.
3. Later mixins override earlier mixins.
4. Keys explicitly defined on the target node override all mixin-provided keys.

Across provider and agent layers:

1. Resolve provider config, including provider mixins.
2. Resolve agent config, including agent mixins.
3. Keep the current provider-then-agent merge model, so agent values still override provider defaults.

This preserves the current mental model:

- local beats mixin
- later mixin beats earlier mixin
- agent beats provider

## Proposed Merge Rules

Suggested v1 behavior:

- Global default from `mixin_policy.default_merge`, defaulting to `"shallow"` for backward compatibility.
- Optional per-node override via `mixin_merge`.
- `"shallow"`:
  - top-level key replacement only
- `"deep"`:
  - dict + dict => recursive merge
  - list/scalar/mismatched types => replace, do not concatenate

This keeps current semantics as the default while allowing deeper composition for nested structures like `system_message`.

## Validation / Error Handling Draft

Recommended fatal config errors:

- `mixins` is not a mapping
- mixin entry is not a mapping
- `mixin_refs` is not a list of non-empty strings
- `mixin_merge` is not `"shallow"` or `"deep"`
- unknown mixin reference
- cycle detected in mixin references
- max mixin recursion depth exceeded

Recommended behavior:

- Collect structured config errors in the same style as existing config errors.
- Treat mixin protocol errors as fatal during `AgentApplication` initialization, similar to plugin-resolution failures.

## Suggested Implementation Approach

Primary code changes:

- `core/python/agent_app/config.py`
  - add a config-normalization helper such as `resolve_config_mixins(...)`
  - add internal helpers for DFS expansion, cycle detection, merge-mode resolution, and deep/shallow merging
  - strip mixin control keys from resolved runtime configs before they are passed downstream
- `core/python/agent_app/application_future.py`
  - call mixin expansion after placeholder resolution and before plugin/provider/agent extraction
  - raise for fatal mixin-related config errors
- `core/python/tests/test_application_layer_config.py`
  - add unit coverage for precedence, deep/shallow merge, recursive expansion, cycles, and provider/agent composition
- `docs/plugins/application-config.md`
  - document protocol keys, precedence, merge rules, and examples

Likely no changes needed:

- `AgentCore`
- plugin type protocols in `TYPES_AND_PROTOCOLS.md`

## Open Decision

Before implementation, confirm the intended initial scope:

1. `providers` and `agents` only
2. any config mapping node

Recommendation: choose option 1 for v1 to keep validation and user expectations simpler while covering the main reuse cases.

## Execution plan

Added during completion after user approval.

1. Add a mixin-resolution phase in `core/python/agent_app/config.py` that runs after placeholder resolution and before any plugin/provider/agent extraction.
2. Validate `mixins`, `mixin_refs`, `mixin_merge`, and `mixin_policy`, and resolve recursive mixin references with cycle detection and max-depth protection.
3. Apply ordered mixins with deterministic precedence, supporting `shallow` and `deep` merge modes, and strip mixin control keys from resolved runtime-facing configs.
4. Wire the normalization into `core/python/agent_app/application_future.py` so later plugin/provider/agent logic sees already-expanded configs, and treat mixin protocol errors as fatal startup errors.
5. Keep v1 scope limited to `providers` and `agents`, while allowing mixins themselves to reference other mixins recursively.
6. Add tests in `core/python/tests/test_application_layer_config.py` for precedence, recursion, cycle detection, depth limits, shallow vs deep merge behavior, provider/agent composition, and plugin-related inherited fields.
7. Update `docs/plugins/application-config.md` to document the new keys, precedence rules, merge semantics, and examples.

## Completion Notes

Added during completion.

- Implemented recursive config mixin expansion in `core/python/agent_app/config.py` with:
  - top-level `mixins`
  - `mixin_policy.default_merge`
  - `mixin_policy.max_depth`
  - per-node `mixin_refs`
  - per-node `mixin_merge`
- Limited v1 scope to `providers` and `agents`, while allowing mixins to reference other mixins recursively.
- Enforced precedence:
  - later mixins override earlier mixins
  - local node keys override mixin-provided keys
  - agent still overrides provider after both sides are mixin-expanded
- Added fatal startup handling for mixin protocol errors in `AgentApplication`.
- Updated `build_agent_config(...)` so provider-to-agent flattening can also honor deep merge mode when configured.
- Added regression tests for recursion, cycles, depth limits, ordered precedence, shallow vs deep behavior, plugin-field inheritance, and invalid startup configs.
- Updated `docs/plugins/application-config.md` with the new config protocol and examples.
- Verification run:
  - `pytest core/python/tests/test_application_layer_config.py core/python/tests/test_application_config_errors.py -q`