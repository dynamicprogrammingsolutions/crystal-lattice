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