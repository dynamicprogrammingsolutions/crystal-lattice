# OpenAI Flex Processing Extension And Provider Retries

Short description: Add OpenAI flex processing support to the `openai_responses` bundle with a dedicated extension for UI/config and provider-owned application of `service_tier`, increased timeout, and retry policy.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On: `tasks/20260310-openai-responses-provider/040-provider-streaming-event-normalization-and-finalization.md`

## Why this follow-up exists

The current `openai_responses` provider bundle supports core Responses chat, streaming, tools, reasoning, usage, verbosity, native compaction, prompt caching, and attachment follow-ups, but it does not yet expose OpenAI flex processing.

Flex processing has a few requirements that do not fit cleanly into a single layer:

1. users need explicit UI controls to enable flex mode and tune the higher timeout / retry behavior
2. the provider must remain the only place that actually applies request execution behavior to the OpenAI SDK
3. the extension should own the actual chosen flex values so those settings can evolve independently from the provider

This task captures that split so implementation stays consistent with the extension-centric architecture already used in `openai_responses`.

## Architecture boundary that must hold

Keep the same boundary used by the rest of the bundle:

### Extension-owned

1. Config schema for flex enablement and related controls.
2. UI controls for:
- enabling flex processing
- setting the increased timeout with a recommended default
- enabling automatic retries
- setting max retries with a default
3. Validation and normalization of flex config values.
4. Writing provider-consumable request override state so the provider can apply the settings.

### Provider-owned

1. Applying the actual Responses request option `service_tier="flex"`.
2. Applying the effective timeout to the SDK call path.
3. Applying the effective retry count to the SDK call path.
4. Doing the same thing for both `call_api()` and `stream_api()`.

Do not move SDK execution logic into the extension, and do not make the provider own UI policy defaults beyond a small fallback that preserves backward compatibility.

## Current repo state relevant to this task

### Provider currently supports timeout but not explicit retry control

The provider today exposes only `timeout` as a provider config value and uses it to construct the OpenAI SDK client and request execution path.

Relevant references:

1. [plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py](plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py):36
2. [plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py](plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py):164
3. [plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py](plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py):222
4. [plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py](plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py):845
5. [plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py](plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py):900

Implication: implementation needs a provider-owned way to honor per-request `max_retries` in addition to the existing timeout path.

### OpenAI SDK in this repo supports request-scoped timeout and retry overrides

Research against the installed SDK in this environment showed:

1. `OpenAI(...)` accepts `max_retries`
2. client instances support `with_options(timeout=..., max_retries=...)`
3. `responses.create(...)` accepts `service_tier`

This makes request-scoped provider application straightforward and avoids mutating global SDK state.

### Existing extensions already show the preferred patterns

Two current extensions are especially relevant:

1. [plugins/openai_responses/src/openai_responses_plugins/openai_responses_reasoning_extension.py](plugins/openai_responses/src/openai_responses_plugins/openai_responses_reasoning_extension.py):31
- uses extension-owned config/UI normalization and writes request-related data before the provider request is finalized

2. [plugins/openai_responses/src/openai_responses_plugins/openai_responses_prompt_caching_extension.py](plugins/openai_responses/src/openai_responses_plugins/openai_responses_prompt_caching_extension.py):21
- mutates provider request state directly for provider-owned OpenAI request fields

Implication: flex should follow the prompt-caching style more than the reasoning style, because timeout/retry execution behavior belongs to the provider request layer rather than generic `request_options`.

### The bundle manifest has no flex extension entry yet

Current bundle registration does not include a flex extension.

Relevant reference:

1. [plugins/openai_responses/agent_plugin.json](plugins/openai_responses/agent_plugin.json):1

### App-layer UI tests already cover provider-extension settings patterns

Prompt-caching endpoint tests already verify that provider-extension UI schema entries appear in the session settings API and session actions are tagged correctly.

Relevant reference:

1. [application/python/tests/test_openai_responses_prompt_caching_endpoints.py](application/python/tests/test_openai_responses_prompt_caching_endpoints.py):99

Implication: flex should add at least one similar app-layer regression test for surfaced UI controls.

## Recommended config and UI shape

Use flat config keys so they work naturally with the current session settings UI:

1. `enable_flex_processing`: boolean, default `false`
2. `flex_timeout_seconds`: number, default `300`
3. `enable_flex_retries`: boolean, default `true`
4. `flex_max_retries`: integer, default `2`

Recommended UI controls:

1. checkbox: `Enable flex processing`
2. text or numeric input: `Flex timeout (seconds)`
3. checkbox: `Enable flex retries`
4. text or numeric input: `Flex max retries`

The extension should no-op when flex is disabled.

## Request/state design recommendation

Prefer a dedicated provider-owned override container on `state["request"]`, for example:

```python
request = {
    ...,
    "payload": {...},
    "timeout": 60.0,
    "provider_options": {
        "max_retries": 2,
    },
}
```

or an equivalent explicit shape such as:

```python
request = {
    ...,
    "payload": {..., "service_tier": "flex"},
    "timeout": 300.0,
    "max_retries": 2,
}
```

Either is acceptable as long as:

1. the extension writes the desired values into request state
2. the provider is the layer that actually applies them to the SDK client or request call
3. both streaming and non-streaming execution paths use the same effective values

The second shape is probably the smallest change because the provider already reads `request["timeout"]` directly.

## Tests required in this step

### Extension unit tests

1. Config schema exposes all four flex keys.
2. UI elements are present when the extension is enabled for `openai_responses`.
3. `init()` / `initialize_request()` no-op when flex is disabled.
4. Invalid timeout / retry values are ignored or rejected consistently.
5. Enabled flex injects:
- `service_tier: "flex"`
- increased request timeout
- request retry count only when retry toggle is enabled

### Provider unit tests

1. Provider applies request timeout override in `call_api()`.
2. Provider applies request timeout override in `stream_api()`.
3. Provider applies request retry override in `call_api()`.
4. Provider applies request retry override in `stream_api()`.
5. Existing non-flex behavior remains unchanged when no flex override is present.

These tests can use the same fake client patterns already present in:

1. [plugins/openai_responses/tests/test_openai_responses_provider_unit.py](plugins/openai_responses/tests/test_openai_responses_provider_unit.py):178

### App-layer / config-load coverage

1. Add config-load coverage so the new extension appears in the loaded provider bundle ordering.
2. Add at least one endpoint/UI schema regression test showing the flex settings in session UI output.

Useful reference:

1. [plugins/openai_responses/tests/test_agent_application_openai_responses_config_loads.py](plugins/openai_responses/tests/test_agent_application_openai_responses_config_loads.py):12

### Optional live integration coverage

Live OpenAI flex integration should be treated as optional, not mandatory, because flex availability may vary by account or entitlement.

If added, it must:

1. use `OPENAI_API_KEY` from repo root `.env`
2. skip cleanly when flex is unavailable
3. avoid asserting on account-specific latency/cost behavior

## Suggested execution plan for the implementing agent

1. Create `OpenAIResponsesFlexProcessingExtension` and register it in the plugin manifest.
2. Add flat config schema and UI controls with the recommended defaults above.
3. Normalize flex values in the extension and write explicit request overrides into `state["request"]`.
4. Extend the provider request execution path to honor request-scoped `max_retries` in both non-streaming and streaming calls.
5. Ensure the provider adds `service_tier="flex"` only when flex is enabled.
6. Add unit tests for extension behavior and provider SDK-application behavior.
7. Add app-layer config/UI regression coverage.
8. Update `README.md` and any relevant config examples.

## Assumptions approved during planning

1. Flex controls should be shown for all `openai_responses` models for now because current model discovery does not expose a reliable flex-capability signal.
2. The provider remains responsible for actual request execution behavior, even though the extension chooses the effective timeout and retry values.
3. A dedicated extension should own user-facing defaults so those values can evolve without pushing UI policy into the provider.

## Approved execution plan (added during completion)

1. Inspect the current `openai_responses` provider execution path and nearby extensions to pin down the smallest provider-owned request override shape for `service_tier`, `timeout`, and `max_retries`.
2. Add a new `OpenAIResponsesFlexProcessingExtension` under `plugins/openai_responses/src/openai_responses_plugins/` with flat config keys: `enable_flex_processing`, `flex_timeout_seconds`, `enable_flex_retries`, and `flex_max_retries`. It will own UI schema, value normalization, and request-state injection only.
3. Register that extension in `plugins/openai_responses/agent_plugin.json` and update config-load coverage so bundle ordering includes it.
4. Extend the provider so `call_api()` and `stream_api()` honor per-request timeout and retry overrides using the OpenAI SDK request/client options, while only adding `service_tier="flex"` when the extension enabled flex.
5. Add extension unit tests for schema/UI exposure, disabled no-op behavior, normalization rules, and request injection semantics.
6. Add provider unit tests proving timeout and retry overrides are applied in both non-streaming and streaming paths, plus unchanged behavior without flex overrides.
7. Add app-layer regression coverage showing the flex settings appear in session UI output for the `openai_responses` bundle.
8. Update the `openai_responses` README/config example just enough to document flex processing without expanding scope beyond this subtask.
9. Run the relevant targeted test files in the worktree and report results, then append completion notes to the subtask file and stop there.
## Completion notes (added during completion)

### Changes made

1. Added `OpenAIResponsesFlexProcessingExtension` in `plugins/openai_responses/src/openai_responses_plugins/openai_responses_flex_processing_extension.py`.
2. Registered and exported the new extension in `plugins/openai_responses/agent_plugin.json` and `plugins/openai_responses/src/openai_responses_plugins/__init__.py`.
3. Extended `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py` so `call_api()` and `stream_api()` honor request-scoped `max_retries` through SDK `with_options(...)`, while continuing to honor per-request timeout overrides and preserving unchanged behavior when no retry override is present.
4. Added flex extension unit coverage in `plugins/openai_responses/tests/test_openai_responses_flex_processing_extension_unit.py`.
5. Added provider regression coverage in `plugins/openai_responses/tests/test_openai_responses_provider_unit.py` for timeout and retry application in both streaming and non-streaming paths.
6. Added config-load and import coverage in `plugins/openai_responses/tests/test_agent_application_openai_responses_config_loads.py` and `plugins/openai_responses/tests/test_openai_responses_imports.py`.
7. Added app-layer UI schema coverage in `application/python/tests/test_openai_responses_flex_processing_endpoints.py`.
8. Updated `plugins/openai_responses/README.md` with flex-processing config/examples.

### Tests run

1. `pytest plugins/openai_responses/tests/test_openai_responses_flex_processing_extension_unit.py plugins/openai_responses/tests/test_openai_responses_provider_unit.py plugins/openai_responses/tests/test_openai_responses_imports.py plugins/openai_responses/tests/test_agent_application_openai_responses_config_loads.py application/python/tests/test_openai_responses_flex_processing_endpoints.py -q`
- result: `60 passed`
- notes: FastAPI emitted existing deprecation warnings about `.on_event`; no flex-specific failures.

### Open issues

1. A broad `pytest plugins/openai_responses/tests -q` run exceeded the time budget in this environment, so verification is limited to the targeted subtask-related suites above.

## Post-completion follow-up (added after flex verification discussion)

1. Provider now preserves returned `response.service_tier` in private native metadata as `_openai_responses_service_tier`.
2. `OpenAIResponsesFlexProcessingExtension` now surfaces that value on assistant message metadata as `openai_service_tier` and `flex_processing_applied`.
3. Added live integration coverage in `plugins/openai_responses/tests/test_openai_responses_flex_processing_integration.py`.
4. Test outcome in this environment: `pytest plugins/openai_responses/tests/test_openai_responses_flex_processing_integration.py -q` -> `1 passed`.
