# 040 - Agent and Provider Plugin Package Config

Short description: Extend application configuration so plugin packages can be declared not only globally but also on agent configs and provider configs using the `plugins` key, while keeping session metadata plugin selection as the existing enabled-plugin-id/class-name style override and adding config-level `disabled_plugins`.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On: None

## Goal

Allow users to configure plugin packages at more than one config layer.

Requested behavior:

1. Keep the existing top-level global `plugins` config.
2. At the agent and provider config levels, use `plugins` to declare plugin package specs.
3. Effective plugin classes for a session should be the union of:
- globally configured plugin packages
- agent-specific additional plugin packages
- provider-specific additional plugin packages, if supported by the final design
4. Keep session metadata `plugins` behavior as-is conceptually.
- Session metadata should still select enabled plugins by plugin id/class-style identity.
- Session metadata should not become a place where raw plugin package specs are stored.
5. Add config-level `disabled_plugins` so users can say "load these packages, then disable these plugin ids by default" without having to list every enabled plugin id.

## Why this is needed

The new vendor-style tool bundles are naturally package-oriented.

Example desired usage:

1. Global config loads common providers/features used everywhere.
2. A Gemini-oriented agent adds `path:.../plugins/gemini-tools`.
3. A Qwen-oriented agent adds `path:.../plugins/qwen-tools`.
4. A Grok-oriented agent adds `path:.../plugins/grok-tools`.

Without agent/provider-level package loading, users would need to put every plugin package in the global set and then rely only on filtering, which is less ergonomic and makes package-level composition harder.

## Current behavior references

### Global plugin loading at app startup

- Global plugin specs are resolved from top-level `plugins` in:
  - `core/python/agent_app/application_future.py:82`
- Plugin manager resolution happens once during app init:
  - `core/python/agent_app/application_future.py:112`

### Agent-level plugin selection today

- Agent configs currently support `plugins`, but these are interpreted as enabled plugin ids, not plugin package specs:
  - `core/python/agent_app/application_future.py:208`
- Those ids are later used to filter already-loaded plugin classes:
  - `core/python/agent_app/application_future.py:285`

### Session-level plugin selection today

- Session metadata `plugins` overrides agent defaults with enabled ids:
  - `core/python/agent_app/application_future.py:437`
- Terminal app and server surface this as session plugin enablement, not plugin package loading:
  - `application/python/agent_terminal_app/terminal_app.py:1028`
  - `application/python/agent_terminal_app/server.py:880`

## Problem statement

Today the app has only one plugin-package loading phase, driven by top-level `plugins`.

That means:

1. package specs are global only
2. agent `plugins` currently means enabled ids, not package specs
3. there is no place to say "this agent brings in extra plugin packages"

We need to change the config-level meaning of agent/provider `plugins` while preserving the current meaning of session metadata `plugins`.

## Requirements

1. Global top-level `plugins` continues to work unchanged.
2. Agent configs can declare additional plugin package specs using `plugins`.
3. Provider configs can declare additional plugin package specs using `plugins`, or the task should clearly justify limiting support to agents only.
4. Effective loaded plugin class catalog for a session is the union of global plus additive config-layer package specs.
5. Session metadata `plugins` remains an enabled-plugin-id selector over the resolved catalog.
6. Add config-level `disabled_plugins` for concise default disabling by plugin id.
7. Config merge and conflict rules must be deterministic and documented.
8. No backward compatibility is required for the old agent-level meaning of `plugins`.

## Recommended design direction

Use different semantics at different config layers:

1. Top level `plugins` remains global plugin package specs.
2. Agent-level `plugins` becomes agent-specific plugin package specs.
3. Provider-level `plugins` becomes provider-specific plugin package specs if provider-level support is accepted.
4. Session metadata `plugins` remains the explicit enabled-plugin-id list.
5. Config-level `disabled_plugins` becomes the concise default filter for "all except these ids".

Reasoning:

1. This matches the user's preferred config shape.
2. No backward compatibility is required for the old agent-level meaning of `plugins`.
3. The explicit session-level UI-controlled `plugins` list still exists for fine-grained overrides.
4. `disabled_plugins` gives a concise config authoring path when the desired behavior is "enable almost everything from these packages except a few ids".

## Merge model to plan for

The likely effective resolution order should be:

1. Load global plugin package specs.
2. Load additional plugin package specs from the selected provider config, if supported.
3. Load additional plugin package specs from the selected agent config.
4. Build the unioned plugin-class catalog.
5. Determine default enabled ids from the merged catalog.
6. Apply config-level `disabled_plugins` from provider and agent layers according to the documented precedence rule.
7. Apply session metadata `plugins` if present as the explicit per-session enabled-id override.
8. If session metadata `plugins` is absent, use the config-derived default enabled set.

Questions to settle during implementation:

1. Whether provider-level additions should be applied before or after agent-level additions when duplicate plugin ids appear.
2. Whether first-registration-wins should remain the duplicate policy, or whether more local config layers should override more global ones.
3. Whether loading should still happen only once at app startup or whether per-agent/provider plugin-package resolution should be cached lazily.
4. How provider-level and agent-level `disabled_plugins` should merge when both are present.

## Likely implementation areas

1. `core/python/agent_app/application_future.py`
- startup config parsing
- plugin package resolution strategy
- per-agent and provider config bookkeeping
- runtime resolution of plugin ids vs loaded catalog
- config-level disabled-plugin filtering
2. `core/python/agent_app/config.py`
- if new config helpers or validation are needed
3. docs for application config and plugin loading behavior
- `docs/plugins/application-config.md`

## Design constraints

1. Avoid re-resolving and reinstalling the same plugin packages repeatedly if the configuration can be cached deterministically.
2. Preserve the current session-level UX and server endpoints around enabled plugins.
3. Keep plugin package specs out of session metadata unless there is an explicitly separate future feature for session-scoped package loading.
4. Preserve top-level config backward compatibility.
5. It is acceptable to break backward compatibility for the old agent-level meaning of `plugins`.

## Test expectations

1. Global-only config still works.
2. Agent-level `plugins` adds plugin package specs for that agent only.
3. Provider-level `plugins` adds plugin package specs for agents using that provider, if provider-level support is implemented.
4. Config-level `disabled_plugins` removes plugin ids from the default enabled set.
5. Session metadata `plugins` still works as explicit enabled-id filtering against the merged catalog.
6. Duplicate plugin ids across global and additive package specs follow the documented precedence rule.
7. Old configs using agent `plugins` as enabled ids are not required to remain compatible.

## Deliverables

1. Config contract for plugin package specs at global, provider, and agent levels.
2. Config contract for `disabled_plugins` at the config layers where it is supported.
3. Application-layer implementation of merged plugin package resolution.
4. Tests covering global + provider + agent + disabled + session-enabled-id interactions.
4. Docs updates explaining the distinction between:
- plugin package specs
- config-level `disabled_plugins`
- session-level enabled plugin ids
