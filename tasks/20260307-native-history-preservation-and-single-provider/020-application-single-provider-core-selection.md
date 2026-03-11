# Ensure application-built cores use exactly one provider when config already selects one

Short description: Change the application layer so the `AgentCore` instances used for session/message operations contain only the provider selected by the effective application config, instead of carrying multiple registered providers when that is unnecessary.

Parent Task: tasks/20260307-native-history-preservation-and-single-provider/000-main.md
Depends On: none

## Problem statement

A major contributor to the stripping/failure behavior is that the application currently constructs session-specific cores with all enabled provider plugins, even when the agent/request config already selects a single concrete provider.

That matters because several message operations assume a single provider context for safe native-history preservation. In the reproduced case, having two providers registered caused:

- `len(self._providers) != 1` in `AgentCore.slice_session()`
- immediate fallback to `_slice_session_core_only()` under the old behavior
- native history being stripped during delete

Even after subtask 010 changes the core behavior to “preserve or fail”, this application-layer issue should still be fixed because the effective provider is already explicit in app config.

## Current code path

### Core construction in the application
`AgentApplication._build_core_with_enabled_ids()` registers every enabled provider, not just the one selected by config.

Relevant code:
- `core/python/agent_app/application_future.py:258-300`

Important lines:
- provider filtering by enabled plugin ids: `application_future.py:279-287`
- registration of all enabled providers: `application_future.py:293-294`

### Session loading
`AgentApplication.load_session()` builds a fresh core from enabled plugin ids, but does not narrow providers using the agent/session/request provider setting.

Relevant code:
- `core/python/agent_app/application_future.py:924-955`

Important lines:
- base config resolution: `application_future.py:945`
- plugin ids from session metadata or agent config: `application_future.py:947-951`
- current core build call: `application_future.py:953-954`

### User-facing operations that consume this core
These paths call `load_session()` and then invoke core mutators such as `slice_session()`, `modify_message()`, or `fork_session()`:

- Terminal delete/modify/fork in `application/python/agent_terminal_app/terminal_app.py:317-610`
- HTTP modify/delete/fork in `application/python/agent_terminal_app/server.py:1562-1902`, `2280-2350`
- Session-actions app delete/fork/copy in `plugins/session-actions-app/src/session_actions_app/__init__.py:330-625`

## Why this should be solvable in the app layer

The application config model already carries explicit provider selection information:

- agent base config is resolved by `build_agent_config(...)`
- request-time overrides are merged by `resolve_request_config(...)`
- downstream operations already compute configs that include provider selection before calling the core

The core already has provider-selection logic for config values:
- `_select_provider_for_config()` in `core/python/agent_core/core.py:1208-1282`

The application should therefore avoid constructing a multi-provider core when the effective config unambiguously selects one provider.

## Investigation / implementation directions

At minimum, investigate where provider narrowing should happen. Possible approaches:

### Option A: Narrow providers in `load_session()`
Build the session core with only the provider selected by the base agent config.

Pros:
- Centralized fix for many message operations.
- Keeps downstream code simple.

Cons / questions:
- Need to ensure the selected provider can be identified from the config before request-specific overrides are applied.
- Need to define what happens if later request overrides switch providers.

### Option B: Add a new application helper for operation-specific cores
For mutating message operations, construct a fresh core using the fully resolved request config (base config + session overrides) and register only the selected provider.

Pros:
- Uses the exact config that the operation will pass into the core.
- Avoids mismatch between core provider set and resolved request config.

Cons:
- Slightly more plumbing at each call site.
- May coexist awkwardly with current `load_session()` API shape.

### Option C: Extend `_build_core_with_enabled_ids()` to accept a selected provider
Example shape:
- `_build_core_with_enabled_ids(enabled_ids, selected_provider=...)`

Then call it from `load_session()` or a new helper after resolving the selected provider id/alias.

## Important constraints / questions to resolve

1. **Mapping provider config values to plugin classes**
   The app config may use provider aliases such as those under `providers:` and agents reference those aliases. Determine the correct mapping path from:
   - agent/request config provider value
   - to plugin id / class used by `_plugins_by_kind_and_id`
   - to a single registered provider in the built core

2. **Session plugin filtering vs provider narrowing**
   Sessions/agents may still enable multiple plugins overall. The requirement is not “one plugin total”; it is “one provider in the built core for message operations”. Keep features/tools/extensions behavior intact.

3. **Compatibility with request-time overrides**
   Some operations resolve `config = resolve_request_config(base_config, overrides)` immediately before calling the core. Prefer a design where the core provider set matches that resolved config, not just the base config.

4. **Error behavior when the selected provider cannot be resolved uniquely**
   If the application cannot map the effective config to exactly one provider plugin, it should fail explicitly rather than silently building a multi-provider core.

## Recommended implementation direction

Recommended path to investigate first:

1. Introduce an application helper that resolves the **effective request config** for a session operation.
2. From that resolved config, determine the single concrete provider plugin/class that should be registered.
3. Build an operation-specific core containing:
   - exactly one provider
   - the enabled extensions
   - the enabled features/tools as before
4. Use that narrowed core for message mutators (`delete`, `modify`, `fork`, and any similar app/plugin actions).

This keeps the core state aligned with the config actually passed to the operation.

## Test work expected

Add or update tests proving that application-built cores no longer carry multiple providers when a single provider is explicitly selected.

Suggested coverage:

1. **Session loading / core build tests**
   - verify the built core has one provider when the effective config selects one
   - verify failure if the provider cannot be resolved uniquely

2. **Regression tests for message operations**
   - delete/modify/fork through terminal app, HTTP server, and session-actions app should no longer hit the old multi-provider constraint in normal cases
   - use a config fixture with multiple installed provider plugins but one explicit provider selection

3. **Preservation behavior integration tests**
   - with valid native history and a multi-provider plugin environment, normal delete should preserve native history once the application builds a single-provider core

## Acceptance criteria

- Application-level session/message operations call into a core that has exactly one provider whenever the effective config already selects one.
- Multi-provider installation in the app environment no longer forces message-edit operations into failure or fallback when the selected provider is unambiguous.
- Features, tools, and extensions remain enabled according to existing agent/session plugin rules.
- Tests cover the provider-narrowing behavior and the resulting end-to-end regression case.

## Completion notes (added during completion as a prerequisite for `tasks/20260310-openai-responses-provider/090-integration-native-retention-and-regression-tests.md`)

1. Implemented provider narrowing in `core/python/agent_app/application_future.py`.
- `_build_core_with_enabled_ids(...)` now accepts an effective provider config and resolves exactly one enabled provider class for the built core
- `load_session(...)` now resolves the effective config from stored overrides plus optional request overrides before building the per-session core
- `create_session_ephemeral(...)` and `update_agent(...)` now build a core aligned with the selected provider

2. Updated request/session callers that needed the effective config.
- `application/python/agent_terminal_app/server.py` now passes request overrides into the session-context helper used by send flows
- `application/python/agent_terminal_app/terminal_app.py` refreshes the active core after override updates so the terminal state stays aligned with the selected provider

3. Added regression coverage.
- `core/python/tests/test_application_single_provider_selection.py`
- `application/python/tests/test_agent_terminal_app_server.py` multi-provider server regression
- existing app/plugin tests were also rerun to verify delete/fork/override paths remain healthy

4. Outcome.
- application-built cores now use exactly one provider when the effective config selects one, which removes the old multi-provider `slice_session()` fallback in the covered app/server flows
