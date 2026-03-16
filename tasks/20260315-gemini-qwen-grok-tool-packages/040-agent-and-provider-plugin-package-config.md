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

## Approved Documentation Plan Added After Planning

Added on 2026-03-16 after review of existing user-facing plugin and config docs.

This subtask should explicitly update `docs/plugins/application-config.md` so the new configuration model is discoverable without reading implementation code.

The docs update should include:

1. A clear explanation that `plugins` has different semantics by layer:
- top-level `plugins`: global plugin package specs
- provider-level `plugins`: provider-specific plugin package specs
- agent-level `plugins`: agent-specific plugin package specs
- session metadata `plugins`: explicit enabled plugin ids controlled by the existing session-level UI/API flow
2. A section for `disabled_plugins` explaining that it is a config-level shorthand for "everything from the merged catalog except these ids".
3. At least one complete example config showing:
- global `plugins`
- provider-level `plugins`
- agent-level `plugins`
- `disabled_plugins`
4. A precedence explanation covering:
- merged package loading order
- how `disabled_plugins` affects the default enabled set
- how session metadata `plugins` overrides the default enabled set when present
5. A migration note stating that old configs using agent-level `plugins` as enabled ids are not kept backward-compatible.
6. Any necessary cross-links to:
- `plugins/docs/plugin-packaging-and-loading.md`
- package README quickstarts for `gemini-tools`, `qwen-tools`, and `grok-tools`

## Approved Implementation Plan Added During Completion

Added on 2026-03-16 after user approval.

Implementation scope for this subtask:

1. Refactor `core/python/agent_app/application_future.py` so plugin package specs can be declared at three config layers:
- top-level `plugins`
- provider-level `plugins`
- agent-level `plugins`

2. Resolve plugin specs once per unique spec at app startup, cache those results in memory, and build:
- an application-wide plugin catalog for discovery/listing
- an agent-scoped effective plugin catalog used when creating/loading sessions

3. Change agent-level `plugins` semantics from enabled plugin ids to plugin package specs, and add config-level `disabled_plugins` support at:
- top level
- provider level
- agent level

4. Use this merge model:
- plugin package loading order: global -> provider -> agent
- duplicate plugin ids: first registration wins
- default enabled ids: all plugin ids from the resolved agent catalog minus the merged `disabled_plugins` union
- session metadata `plugins`: remains the explicit enabled-id override

5. Make session/plugin listing agent-aware so sessions only expose the resolved catalog for their own agent/provider stack, updating the terminal/server code paths as needed.

6. Update `docs/plugins/application-config.md` to document:
- the different `plugins` semantics by config layer
- `disabled_plugins`
- precedence and duplicate-id behavior
- the migration note that old agent-level enabled-id semantics are no longer supported

7. Add tests in the same change:
- core application-layer tests for global/provider/agent merging, `disabled_plugins`, session overrides, and duplicate precedence
- fixture-based OpenRouter application integration coverage using actual config files rather than inline JSON

8. Add two application-level OpenRouter integration tests using four agents with separate tool families:
- `codex-agent` using `plugins/codex-tools`
- `gemini-agent` using `plugins/gemini-tools`
- `qwen-agent` using `plugins/qwen-tools`
- `grok-agent` using `plugins/grok-tools`

9. Split the end-to-end integration coverage across two config fixtures and two tests:
- one fixture/test where the vendor tool package specs are declared on provider configs
- one fixture/test where the vendor tool package specs are declared on agent configs

10. In both end-to-end tests, assert that the effective behavior is the same:
- each agent resolves only its intended tool family
- unrelated tool families are absent from that agent's resolved catalog
- requests complete successfully against cheap OpenRouter models and exercise the corresponding tool surface

## Completion Notes Added During Completion

Added on 2026-03-16 after implementation and verification.

What changed:

1. Application-layer plugin package loading now supports `plugins` at three config layers:
- top-level global config
- provider config
- agent config

2. Agent/provider `plugins` now mean plugin package specs rather than enabled plugin ids.

3. Config-level `disabled_plugins` is now supported at the top level, provider level, and agent level.

4. Session metadata `plugins` still behaves as the explicit enabled-plugin-id override and was not repurposed for package specs.

5. Effective plugin catalogs are now resolved per agent with deterministic merge rules:
- package load order: global -> provider -> agent
- duplicate plugin ids: first registration wins
- default enabled ids: merged catalog minus merged `disabled_plugins`

6. Terminal/server session plugin listing now uses the resolved agent-specific catalog instead of the app-wide plugin union.

7. Runtime base configs no longer leak config-only `plugins` or `disabled_plugins` keys into provider/tool runtime config.

8. Documentation was updated in `docs/plugins/application-config.md` to explain the new config model, precedence, migration note, and related references.

9. Added unit coverage for:
- provider-level additive package loading
- agent-level additive package loading
- `disabled_plugins`
- session-level plugin-id overrides
- duplicate plugin-id precedence

10. Added two fixture-based OpenRouter application integration tests using actual config files:
- provider-level package specs fixture
- agent-level package specs fixture

11. The end-to-end integration tests cover four agents with distinct tool families:
- `codex-agent`
- `gemini-agent`
- `qwen-agent`
- `grok-agent`

Files touched:

- `core/python/agent_app/application_future.py`
- `core/python/agent_app/config.py`
- `application/python/agent_terminal_app/terminal_app.py`
- `application/python/agent_terminal_app/server.py`
- `core/python/tests/test_application_layer_plugins.py`
- `core/python/tests/dummy_tool_same_id.py`
- `core/python/tests/test_application_layer_openrouter_multi_agent_tool_packages.py`
- `core/python/tests/fixtures/configs/openrouter_multi_agent_provider_plugins.json`
- `core/python/tests/fixtures/configs/openrouter_multi_agent_agent_plugins.json`
- `docs/plugins/application-config.md`

Tests run:

- `python -m pytest core/python/tests/test_application_layer_plugins.py -q`
- `python -m pytest core/python/tests/test_application_layer_openrouter_multi_agent_tool_packages.py -q -m 'integration and openrouter'`
- `python -m pytest application/python/tests/test_terminal_application.py -q -k 'list_plugins_for_session_implicit_defaults or set_session_plugins_persists_and_reloads_core or clear_session_plugins_reverts_to_implicit_defaults'`
- `python -m pytest application/python/tests/test_agent_terminal_app_server.py -q -k 'session_plugins_endpoints_roundtrip'`

Outcomes:

- All listed tests passed.
- The two new OpenRouter application-level tests passed against real models and validated both provider-level and agent-level plugin package declarations.

Open issues / notes:

- App-wide `list_plugins()` now reflects the deduplicated union of all configured plugin packages, while session/agent views use agent-scoped catalogs. This matches the new layering model but means duplicate ids across different tool families only appear once in the global list.
