# Model Discovery, Provider UI, And Docs Follow-Up

Short description: Replace the `openai_responses` provider's placeholder `get_models()` implementation with real OpenAI model discovery, add provider-owned model-selection UI matching the established OpenRouter pattern, and update bundle docs/config examples to reflect the new behavior.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On:
- `tasks/20260310-openai-responses-provider/030-provider-core-conversion-and-nonstreaming-sdk.md`
- `tasks/20260310-openai-responses-provider/100-docs-readme-and-config-examples.md`

## Scope

1. Keep this subtask provider-focused.
- implement real model discovery for `OpenAIResponsesProvider`
- add provider-owned UI elements for model selection
- update `openai_responses` docs/config examples to describe the new model list behavior

2. Treat "config/UI similar to OpenRouter" as model-selection parity only.
- mirror the OpenRouter provider pattern for `model` config UI and `model_picker`
- do not add unrelated OpenRouter-specific config like `site_url` or `app_name`

3. Preserve architecture boundaries from the parent task.
- provider remains transport/native-history focused
- no new tools, reasoning, usage, or verbosity business logic in this task
- do not move extension-owned behavior into the provider while adding model discovery or UI

## Context From Investigation

1. `openai_responses` still has placeholder provider discovery/UI behavior.
- [plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:34](plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:34) exposes only `model`, `api_key`, `base_url`, and `timeout`
- [plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:54](plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:54) returns no provider UI elements
- [plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:62](plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:62) returns only the configured model instead of calling a real endpoint

2. The earlier provider-core subtask explicitly left room for this follow-up.
- [tasks/20260310-openai-responses-provider/030-provider-core-conversion-and-nonstreaming-sdk.md:11](tasks/20260310-openai-responses-provider/030-provider-core-conversion-and-nonstreaming-sdk.md:11) lists "optional model discovery using SDK where feasible" under provider implementation scope

3. OpenRouter is the reference shape for model-selection UI.
- [plugins/openrouter/src/openrouter_plugins/openrouter_provider.py:46](plugins/openrouter/src/openrouter_plugins/openrouter_provider.py:46) builds a dropdown-or-text `model` config element from discovered models
- [plugins/openrouter/src/openrouter_plugins/openrouter_provider.py:69](plugins/openrouter/src/openrouter_plugins/openrouter_provider.py:69) adds a `model_picker`
- [plugins/openrouter/src/openrouter_plugins/openrouter_provider.py:77](plugins/openrouter/src/openrouter_plugins/openrouter_provider.py:77) also exposes an image composer attachment, which is relevant because `openai_responses` already supports image input in provider-native conversion

4. Investigation note about OpenRouter Responses.
- the working assumption going in was that only the original OpenRouter provider implemented a real models endpoint
- investigation showed `openrouter_responses` also already does real model discovery in [plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py:119](plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py:119)
- for this follow-up, the original OpenRouter provider remains the best UI/config parity reference because its implementation is the simpler baseline

5. Existing provider tests currently validate the placeholder behavior.
- [plugins/openai_responses/tests/test_openai_responses_provider_unit.py:145](plugins/openai_responses/tests/test_openai_responses_provider_unit.py:145) checks current tags/schema behavior, but there is no provider test yet for real model discovery or provider-owned UI elements

## Chosen Solution Direction

1. Implement model discovery using the OpenAI SDK rather than a raw ad hoc HTTP request.
- use the same SDK family already adopted by the bundle
- normalize list results into the repo's expected model descriptor shape, at minimum `id` and optionally `name`
- keep failure handling soft: log and return `[]` instead of breaking config/UI generation

2. Add provider UI elements modeled after the OpenRouter provider.
- `model` should render as a dropdown when discovered models are available, and fall back to plain text when they are not
- include a `model_picker` entry for the same model list
- include an image `composer_attachment` consistent with the provider's existing image-input support

3. Leave capability tags heuristic and provider-local.
- keep the current tag approach based on the configured model id unless a clearly reliable capability field is available from OpenAI model metadata
- do not turn this task into a broader capability-detection redesign

4. Update the plugin README/config examples in the same change.
- explain that model selection now uses real OpenAI model discovery when credentials/network access are available
- mention that UI gracefully falls back to manual model entry when discovery is unavailable
- keep doc updates narrow and aligned with the provider-only scope of this task

## Acceptance Criteria

1. `OpenAIResponsesProvider.get_models(config)` no longer echoes `config["model"]` as a synthetic one-item list.

2. Model discovery uses a real OpenAI model list endpoint through the OpenAI SDK.
- credential resolution for discovery should be consistent with provider initialization, including `OPENAI_API_KEY` fallback from the environment
- discovery should honor `base_url` where applicable so alternate compatible endpoints continue to work

3. Discovery failure is non-fatal.
- missing credentials, transport errors, or malformed responses should return `[]`
- failures should be logged at warning level rather than raising during UI/schema generation

4. Provider UI now supports model selection.
- `model` config element uses dropdown when models are present and text otherwise
- `model_picker` is present
- image `composer_attachment` is present

5. The task does not expand provider scope beyond model discovery and provider-owned UI.
- no new tools/reasoning/usage/verbosity behavior is added here
- provider tags remain conservative and do not promise unsupported capabilities based solely on speculative model metadata

6. `plugins/openai_responses/README.md` and any relevant config examples are updated to match the implemented behavior.

## Test Expectations

1. Add provider unit coverage for model discovery.
- success path with mocked SDK list results
- failure path returns `[]`
- env-based API key fallback for discovery path
- normalization of SDK model objects into model descriptors

2. Add provider unit coverage for UI behavior.
- dropdown `model` element when models are supplied
- text fallback when no models are supplied
- `model_picker` presence and option wiring
- image composer attachment presence

3. Add a live integration test guarded by `OPENAI_API_KEY`.
- mirror the existing OpenRouter models API integration style
- assert that real model discovery returns a non-empty list with string `id` fields
- avoid brittle assertions about the exact catalog contents

4. Keep existing provider/application config-load tests green.
- update any tests that currently encode the placeholder `get_models()` assumption
- verify UI schema generation remains stable with the full `openai_responses` bundle loaded

## Risks And Non-Goals

1. OpenAI may return a broad catalog that includes models not ideal for the Responses UI.
- do not overfit the first implementation with aggressive filtering unless a concrete product rule is agreed later

2. Capability metadata may be incomplete or unstable.
- this task should not attempt to replicate OpenRouter's `supported_parameters`-driven tagging unless OpenAI exposes a stable equivalent already proven in practice

3. Do not reopen completed extension work.
- if model discovery reveals future opportunities for reasoning/verbosity/tool-specific UI refinement, capture those separately rather than extending this subtask's scope

## Approved plan (added during completion)

1. Update `OpenAIResponsesProvider` model discovery to use the OpenAI Python SDK.
- add a provider-local helper that resolves `api_key`, `base_url`, and timeout consistently with `init()`, including `OPENAI_API_KEY` fallback
- call the SDK models endpoint, normalize results into model descriptors with `id` and optional `name`, and return `[]` on missing credentials or API/shape failures
- keep discovery failures non-fatal by logging warnings instead of raising during model/UI generation

2. Add provider-owned UI elements for model selection.
- mirror the OpenRouter/OpenRouter Responses pattern for the `model` config element: dropdown when discovered models exist and text otherwise
- add a `model_picker` entry wired to the same model options
- add an image `composer_attachment` consistent with the provider's existing image-input support

3. Expand provider tests in the same change.
- add unit coverage for successful model discovery, normalization, env-based API key fallback, and failure returning `[]`
- add unit coverage for provider UI behavior: dropdown vs text fallback, `model_picker`, and image attachment presence
- add a live integration test guarded by `OPENAI_API_KEY` that asserts real discovery returns a non-empty list of string ids without brittle catalog assertions

4. Update docs narrowly for this subtask.
- refresh `plugins/openai_responses/README.md` so it explains real OpenAI model discovery and the manual-entry fallback when discovery is unavailable
- keep the docs change provider-focused without moving extension-owned behavior into the provider story

5. Verify with focused test runs and then append completion notes.
- run the relevant provider unit tests and the new discovery integration test
- record files changed, tests run, outcomes, and any remaining caveats in this task file

## References

- [plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py](plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py)
- [plugins/openrouter/src/openrouter_plugins/openrouter_provider.py](plugins/openrouter/src/openrouter_plugins/openrouter_provider.py)
- [plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py](plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py)
- [plugins/openrouter/tests/test_openrouter_models_api_integration.py](plugins/openrouter/tests/test_openrouter_models_api_integration.py)
- [plugins/openrouter_responses/tests/test_openrouter_models_api_integration.py](plugins/openrouter_responses/tests/test_openrouter_models_api_integration.py)
- [plugins/openai_responses/tests/test_openai_responses_provider_unit.py](plugins/openai_responses/tests/test_openai_responses_provider_unit.py)
- [plugins/openai_responses/tests/test_agent_application_openai_responses_config_loads.py](plugins/openai_responses/tests/test_agent_application_openai_responses_config_loads.py)
- [plugins/openai_responses/README.md](plugins/openai_responses/README.md)

## Completion notes (added during completion)

### What changed

1. Replaced placeholder model discovery in `OpenAIResponsesProvider` with real SDK-backed discovery.
- `get_models(config)` now creates an OpenAI SDK client using the same credential/base URL/timeout resolution pattern as provider initialization
- discovery calls the SDK `models.list()` endpoint and normalizes results into repo-style descriptors with `id` and optional `name`
- failures during credential resolution, transport, or response normalization now log a warning and return `[]` instead of raising during UI generation

2. Added provider-owned model-selection UI elements.
- `get_ui_elements(...)` now exposes a `model` config element that renders as a dropdown when discovered models exist and falls back to text otherwise
- added a `model_picker` entry wired to the same model options
- added an image `composer_attachment` consistent with the provider's existing image-input support

3. Expanded provider test coverage.
- added unit tests for SDK-backed discovery success, descriptor normalization, env-based `OPENAI_API_KEY` fallback, and warning-backed failure handling
- added unit tests for provider UI behavior covering dropdown mode, text fallback, `model_picker`, and image attachment presence
- added a live integration test asserting that real OpenAI discovery returns a non-empty list of string model ids

4. Updated provider docs in `plugins/openai_responses/README.md`.
- documented that provider UIs now try to populate model selection from the live OpenAI catalog via the OpenAI Python SDK
- documented the fallback to manual model entry when discovery is unavailable

### Files touched

1. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
2. `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`
3. `plugins/openai_responses/tests/test_openai_responses_provider_integration.py`
4. `plugins/openai_responses/README.md`
5. `tasks/20260310-openai-responses-provider/120-model-discovery-provider-ui-and-doc-followup.md`

### Tests run

1. `pytest plugins/openai_responses/tests/test_openai_responses_provider_unit.py -q`
- result: `31 passed`

2. `pytest plugins/openai_responses/tests/test_agent_application_openai_responses_config_loads.py -q`
- result: `1 passed`

3. `pytest plugins/openai_responses/tests/test_openai_responses_provider_integration.py -q`
- result: `3 passed`

### Outcomes

1. `openai_responses` no longer synthesizes model discovery from `config["model"]`; it uses the real OpenAI models endpoint through the OpenAI Python SDK.
2. Provider UI now supports discovered-model dropdown selection, model picker wiring, and image composer attachments while preserving a manual-entry fallback.
3. Focused unit, app-config, and live integration coverage all passed for this subtask.

### Open issues

1. None identified within this subtask's approved scope.