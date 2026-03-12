# Prompt Caching Session-Key Extension

Short description: Add prompt-caching controls for `openai_responses`, including a session-owned prompt cache key that is auto-created for new sessions, preserved on fork, visible/editable in session settings, and regeneratable by action. Keep request shaping in an extension and depend on a separate generic prerequisite task for non-application-plugin session-settings lifecycle writes.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On:
- `tasks/20260312-provider-extension-session-settings-lifecycle/010-provider-extension-session-settings-lifecycle.md`
- `tasks/20260310-openai-responses-provider/095-native-compaction-provider-extension.md`

## Goal

Implement a first-class prompt-caching capability for `openai_responses` that feels native to session settings and session actions rather than a raw request-options escape hatch.

## Why this is a late-stage subtask

This feature now depends on a generic platform capability outside the original provider task tree:

1. the prompt cache key is session-owned
2. it must be auto-created for new sessions
3. it must be repairable on first request for older sessions
4. it must remain visible/editable in normal session settings UI
5. it must support an explicit regenerate action

Those requirements are broader than simple request shaping, so the shared prerequisite is intentionally split into its own task directory.

## Feature requirements

1. Add prompt-caching controls as an `openai_responses` extension.
2. Add a session-owned prompt cache key setting.
3. Auto-create the prompt cache key when creating a new session.
4. If an older session reaches send-time without a key but key support is enabled, create one through the lifecycle fallback path.
5. Fork must preserve the existing prompt cache key and must not generate a new one.
6. Users must be able to view and edit the key through a normal config UI element.
7. Users must be able to regenerate the key through a separate session action.
8. Request shaping must stay extension-owned rather than moving into the provider.

## Configuration / UI intent

The extension should expose user-visible settings along these lines:

1. `enable_prompt_cache_key: boolean`
2. `prompt_cache_key: string`
3. `enable_prompt_cache_retention_24h: boolean`

UI expectations:

1. `prompt_cache_key` is shown as a normal string config UI element so users can view or manually replace it.
2. Regeneration is a separate session action and is not coupled to config editing.
3. Extended retention is represented as a boolean UX toggle. When false, the request should omit retention entirely.

## Request-shaping requirements

The extension should inject Responses request options as follows:

1. inject `prompt_cache_key` only when key support is enabled and the effective session-owned value is non-empty
2. inject `prompt_cache_retention: "24h"` only when the extended-retention toggle is enabled
3. leave `prompt_cache_retention` unset by default

The extension should not own cached-token display logic; cached-token observability should remain in the usage extension.

## Architectural boundaries

1. Provider remains transport/native-history focused.
2. Prompt-caching request shaping belongs in an `openai_responses` extension.
3. Session key lifecycle depends on the generic prerequisite task and must not be hardcoded as OpenAI-specific application behavior.
4. The regenerate operation should use the existing provider-extension session-action pattern rather than an application plugin.

## Acceptance criteria

1. `openai_responses` exposes prompt-caching controls via extension-owned config/UI.
2. A new session receives a prompt cache key automatically when key support is enabled.
3. A legacy session missing a key can receive one through the lifecycle fallback path.
4. Fork preserves the existing key.
5. Users can view/edit the key as a normal session setting.
6. Users can regenerate the key through a separate session action.
7. The extension injects `prompt_cache_key` correctly.
8. The extension injects `prompt_cache_retention: "24h"` only when the 24-hour toggle is enabled.
9. No prompt-caching request shaping is added to the provider itself.

## Test expectations

1. Unit tests for config validation and request payload mutation.
2. Tests for new-session auto-assignment behavior.
3. Tests for first-send fallback assignment on legacy sessions missing the key.
4. Regression tests that fork preserves the existing key.
5. Tests for manual setting edits and regenerate action behavior.
6. OpenAI integration smoke coverage that requests succeed with:
- generated key enabled
- manually supplied key
- 24-hour retention enabled

## Documentation / follow-up expectations

1. Update `openai_responses` docs/examples to include the new prompt-caching settings and regenerate action.
2. Document any product caveats relevant to the 24-hour retention mode.
3. Keep cached-token UI/usage ownership clearly separated from this extension.

## References

- `tasks/20260312-provider-extension-session-settings-lifecycle/000-main.md`
- `tasks/20260312-provider-extension-session-settings-lifecycle/010-provider-extension-session-settings-lifecycle.md`
- `tasks/20260310-openai-responses-provider/095-native-compaction-provider-extension.md`
- `plugins/feature-request-options/src/feature_request_options/request_options_feature.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_usage_extension.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_verbosity_extension.py`
- `plugins/openai_responses/README.md`

## Approved plan (added during completion)

1. Add a dedicated `openai_responses` prompt-caching extension.
- own config schema and UI for:
  - `enable_prompt_cache_key`
  - `prompt_cache_key`
  - `enable_prompt_cache_retention_24h`
- expose a separate `regenerate_prompt_cache_key` session action
- keep all request shaping inside the extension's `initialize_request(...)`

2. Use the shared lifecycle action system for session-owned key management.
- auto-generate a prompt cache key on `session_create` when key support is enabled
- repair legacy sessions on `request_prepare` when key support is enabled but no key exists
- rely on default fork metadata preservation so fork keeps the same key without generating a new one

3. Register the extension in the `openai_responses` bundle and document it.
- update bundle exports and plugin descriptor registration
- update `plugins/openai_responses/README.md` with settings, lifecycle behavior, and regenerate action usage

4. Add tests in the same change.
- unit tests for request mutation, lifecycle generation/repair, and regenerate action behavior
- app/server-oriented tests that session settings UI exposes the config keys and that the session action executes through existing action endpoints
- OpenAI integration smoke tests for generated key enabled, manual key supplied, and 24-hour retention enabled

5. Run focused tests and then append completion notes to this task file.
- report exact test commands and outcomes
- stop after this subtask only

## Completion notes (added during completion)

### What changed

1. Added a new `openai_responses` prompt-caching extension.
- new file: `plugins/openai_responses/src/openai_responses_plugins/openai_responses_prompt_caching_extension.py`
- owns:
  - config schema for `enable_prompt_cache_key`, `prompt_cache_key`, and `enable_prompt_cache_retention_24h`
  - config UI elements so the key is visible/editable in normal session settings
  - request shaping for `prompt_cache_key` and optional `prompt_cache_retention: "24h"`
  - a separate `regenerate_prompt_cache_key` provider-extension session action

2. Implemented session-owned key lifecycle through the shared lifecycle-action system.
- `ensure_prompt_cache_key` runs on `session_create` and `request_prepare`
- new sessions auto-generate a key when key support is enabled
- legacy sessions missing a key are repaired on first request
- fork preservation relies on the default metadata-preserving fork behavior, so no fork-specific regeneration path was added

3. Registered the extension in the `openai_responses` bundle.
- updated `plugins/openai_responses/src/openai_responses_plugins/__init__.py`
- updated `plugins/openai_responses/agent_plugin.json`
- updated import/descriptor coverage accordingly

4. Updated docs and examples for the new prompt-caching controls.
- `plugins/openai_responses/README.md` now documents:
  - the three prompt-caching settings
  - auto-generation and first-request repair behavior
  - manual key editing through session settings
  - the `regenerate_prompt_cache_key` session action

5. Added tests covering unit behavior, app/server flows, and live OpenAI smoke behavior.
- unit tests for request mutation and lifecycle/action behavior
- application/server tests for UI schema exposure, manual edit, regenerate action execution, request-time repair, and fork preservation
- integration tests for live OpenAI success with generated key enabled, manual key supplied, and 24-hour retention enabled

### Files touched

1. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_prompt_caching_extension.py`
2. `plugins/openai_responses/src/openai_responses_plugins/__init__.py`
3. `plugins/openai_responses/agent_plugin.json`
4. `plugins/openai_responses/README.md`
5. `plugins/openai_responses/tests/test_openai_responses_prompt_caching_extension_unit.py`
6. `plugins/openai_responses/tests/test_openai_responses_prompt_caching_integration.py`
7. `plugins/openai_responses/tests/test_agent_application_openai_responses_config_loads.py`
8. `plugins/openai_responses/tests/test_openai_responses_imports.py`
9. `application/python/tests/test_openai_responses_prompt_caching_endpoints.py`

### Tests run

1. `pytest plugins/openai_responses/tests/test_openai_responses_prompt_caching_extension_unit.py plugins/openai_responses/tests/test_agent_application_openai_responses_config_loads.py application/python/tests/test_openai_responses_prompt_caching_endpoints.py plugins/openai_responses/tests/test_openai_responses_imports.py -q`
- result: `11 passed`

2. `ruff check plugins/openai_responses/src/openai_responses_plugins/openai_responses_prompt_caching_extension.py plugins/openai_responses/tests/test_openai_responses_prompt_caching_extension_unit.py plugins/openai_responses/tests/test_agent_application_openai_responses_config_loads.py application/python/tests/test_openai_responses_prompt_caching_endpoints.py plugins/openai_responses/tests/test_openai_responses_imports.py`
- result: `All checks passed`

3. `pytest plugins/openai_responses/tests/test_openai_responses_prompt_caching_integration.py -q`
- result: `3 passed`

### Outcomes

1. Prompt-caching request shaping remains extension-owned; no prompt-caching request logic was added to the provider.
2. Session-owned prompt cache key creation, repair, editing, regeneration, and fork preservation now work end-to-end through the generic lifecycle/action/session-settings mechanisms.
3. Live OpenAI smoke coverage passed for the three required prompt-caching request modes.

### Open issues

1. Focused application tests still surface the pre-existing FastAPI `on_event` deprecation warnings from `application/python/agent_terminal_app/server.py`; those warnings were not changed in this subtask.