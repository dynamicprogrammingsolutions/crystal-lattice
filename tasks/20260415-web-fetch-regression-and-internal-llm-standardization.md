# Web Fetch Regression Recovery And Internal LLM Standardization
Create a regression test from the pre-refactor Gemini behavior, restore that behavior while still using the shared web-fetch library, and define a reusable standard for plugins that launch internal LLM requests from actions or helper flows.

## Requirements checklist

- [x] Add a regression test on top of the earlier-good behavior from commit `c7f9f48d535def66991f1bf122d37b340aac71f6`, not against the current shared implementation.
- [x] Build that regression test using a dummy provider and the real tool-gating flow; do not mock `AgentCore` or lock the test to a specific internal call shape.
- [x] Author the regression test on a side branch from the earlier commit, then bring it forward to the later code by cherry-pick or merge so it fails before the fix and passes after the fix.
- [x] Restore the original Gemini fallback behavior while continuing to use the shared library for the execution mechanics.
- [x] Keep prompt wording and response wording owned by the caller plugin; the shared library must expose only higher-level execution features.
- [x] Identify other plugins that make internal LLM calls inside actions or similar internal flows, and plan a standard process for them, with special attention to disabling tools for internal requests.

## Background

The original Gemini fallback flow at `c7f9f48d535def66991f1bf122d37b340aac71f6` used Gemini-owned prompt wording and an internal one-shot summarization request that explicitly disabled tools for that internal turn. Later, the shared refactor in `aa2d80ea95658e4533556e58701af616fcc470d2` moved more behavior into `plugins/web-fetch-shared`, which changed both the ownership boundary and the behavior.

Current shared implementation references:

- `plugins/web-fetch-shared/src/web_fetch_shared/web_fetch_engine.py:766`
  The shared library currently constructs a concrete summarization prompt itself.
- `plugins/web-fetch-shared/src/web_fetch_shared/web_fetch_engine.py:807`
  The fallback-agent branch discards the returned `fallback_session`.
- `plugins/web-fetch-shared/src/web_fetch_shared/web_fetch_engine.py:817`
  The fallback-agent branch streams with `fallback_config` directly.
- `plugins/web-fetch-shared/src/web_fetch_shared/web_fetch_engine.py:844`
  The same-agent branch streams with `config` directly.
- `plugins/gemini-tools/src/gemini_tools/gemini_web_fetch_tool.py:721`
  Gemini now delegates fallback summarization to `summarize_content_sync(...)`, so the shared library currently owns behavior that used to be Gemini-specific.

Historical reference for the intended behavior:

- `c7f9f48d535def66991f1bf122d37b340aac71f6:plugins/gemini-tools/src/gemini_tools/gemini_web_fetch_tool.py`
  The earlier implementation owned the fallback prompt text inside the Gemini plugin and forced internal summarization requests to disable all tools.

## Internal LLM Call Sites To Standardize

Primary targets already identified in production plugin code:

- `plugins/web-fetch-shared/src/web_fetch_shared/web_fetch_engine.py:722`
  Shared summarization helper used by Gemini and Qwen web fetch.
- `plugins/summarize-range-app/src/summarize_range_app/__init__.py:443`
  Summarize-range action prepares tools and then issues an internal `core.send_request(...)`.
- `plugins/generate-title-app/src/generate_title_app/__init__.py:482`
  Title-generation action issues an internal `app.send_request(...)`.
- `plugins/gemini-compaction-app/src/gemini_compaction_app/__init__.py:729`
  Compaction action issues an internal compaction request.
- `plugins/gemini-compaction-app/src/gemini_compaction_app/__init__.py:769`
  Optional verification pass issues a second internal request.
- `plugins/gemini-compaction-feature/src/gemini_compaction_feature/__init__.py:685`
  Feature-level compaction flow issues an internal compaction request.
- `plugins/gemini-compaction-feature/src/gemini_compaction_feature/__init__.py:714`
  Feature-level verification pass issues another internal request.

Notes for scope control:

- `plugins/tool-compat-shared/src/tool_compat_shared/web_search_engine.py:351`
  This makes a direct provider SDK call, but it is not an application/plugin action flow in the same shape as the summarization, compaction, and title-generation paths above. Treat it as adjacent context, not the primary standardization target for this task unless follow-up analysis shows the same abstraction should apply there.

## Expected Direction

The restored design should separate concerns like this:

- Caller plugin owns prompt wording, any provider- or feature-specific instructions, and the policy decision about whether tools must be disabled.
- Shared helper owns generic internal-request execution mechanics such as:
  - applying internal request safeguards like `disable_all_tools`
  - preserving and merging request overrides safely
  - supporting agent switching
  - using the returned switched session correctly
  - collecting final assistant output in a provider-agnostic way

For the web-fetch regression specifically:

- Gemini should again own the fallback summarization prompt text.
- The shared layer should help execute that internal request without embedding Gemini-specific prompt wording.
- The regression test should assert externally observable behavior through a dummy provider:
  - the internal request omits tools
  - fallback settings overrides still apply
  - the Gemini-owned prompt semantics match the earlier branch behavior

## Execution plan

This plan was added while preparing the task file.

1. Create a side branch from `c7f9f48d535def66991f1bf122d37b340aac71f6` and add a regression test in the Gemini tool test suite using a dummy provider plus the real tool-gating feature.
2. Make the regression test assert behavior semantically, not structurally: verify provider-observed payload/tool availability, effective model overrides, and the original Gemini fallback prompt wording rather than asserting on a mocked core method call.
3. Cherry-pick or merge that regression test onto the later branch so the test demonstrates the refactor regression before any production fix is applied.
4. Refactor `plugins/web-fetch-shared` so its summarization helper accepts caller-supplied prompt text and performs only abstract execution tasks such as config merging, tool disabling, optional agent switching, and final assistant-text collection.
5. Update the Gemini web-fetch tool to reconstruct the original fallback prompt in the plugin itself and call the shared execution helper with that prompt plus the existing fallback settings overrides.
6. Fix the shared execution flow to use the switched session returned by `app.update_agent(...)` and to apply internal-request safeguards consistently in both same-agent and switched-agent branches.
7. Audit the other internal LLM action flows in `summarize-range-app`, `generate-title-app`, `gemini-compaction-app`, and `gemini-compaction-feature`, and classify each path by whether it should default to `disable_all_tools`.
8. Standardize the other internal LLM action flows by behavior and structure, not by forcing them onto one shared runtime helper; use the same policy baseline for tool disabling, override merging, and agent-switch handling unless a plugin has a documented reason to differ.
9. Add or plan focused regression coverage for at least one non-web-fetch action plugin so the standardization effort does not remain web-fetch-only.
10. Run the relevant targeted tests on the earlier branch, on the regressed later branch, and after the fix on the working branch.

## Open Questions

- Decide whether the long-term guidance for internal LLM requests should remain a documented pattern/checklist only, or whether a very small optional utility is still worthwhile for narrow cases. For this task, the action plugins should remain independent rather than being rewritten onto a single shared call path.
- Confirm whether every title-generation path should always disable tools, or whether some deployments intentionally want tools available during title generation. The likely safe default is “disable tools unless explicitly enabled.”
- Confirm whether the feature-level compaction plugin should follow the same behavioral policy as application plugins while keeping its own native-history-specific implementation.

## Detailed implementation plan

This detailed plan was added after the initial task file creation to spell out test setup, assertions, and code-structure changes.

### 1. Regression test strategy for web fetch

Add the canonical regression test to the Gemini tool test suite on a side branch from `c7f9f48d535def66991f1bf122d37b340aac71f6`, then bring that test forward unchanged or minimally adjusted into the later branch.

Why the Gemini suite:

- The regression is about preserving Gemini-owned behavior while using a shared execution helper.
- The test should pin caller-visible behavior, not shared-helper internals.
- The earlier branch already contains Gemini-specific fallback behavior and is the authoritative baseline.

Recommended location:

- `plugins/gemini-tools/tests/test_gemini_web_fetch_tool.py`

### 2. Dummy provider design for the regression test

Use a real provider plugin rather than mocking `AgentCore`.

Model the provider after `RecordingOpenAIProvider` in `core/python/tests/test_tool_gating_feature.py`, because that pattern already verifies tool gating through the actual request preparation pipeline and `OpenAIToolsExtension`.

Recommended provider shape:

- Provider class name: `RecordingOpenAIProvider` or Gemini-test-local equivalent.
- Base protocol: `ProviderPlugin`
- Tags:
  - `provider:openai_compatible`
  - `supports_tools`
- Extensions:
  - register with `OpenAIToolsExtension`

Provider responsibilities:

- `init(config)` stores the config.
- `to_native_messages(...)` and `from_native_messages(...)` can pass messages through unchanged.
- `initialize_request(...)` starts a payload with at least:
  - `model`
  - optionally a copy of selected config fields that are useful to assert later
- `call_api(...)` returns a deterministic assistant message and includes provider-observed request details in `assistant.metadata`, for example:
  - `payload`
  - `last_user_message`
  - `message_count`

Important detail:

- The provider should not assert anything internally.
- It should only record what the real pipeline handed it.
- The test should make assertions on those recorded outputs.

Suggested recorded fields:

- `metadata.payload`: the final request payload after tool preparation and extensions
- `metadata.last_user_message`: the actual summarization prompt seen by the provider
- `metadata.model`: optional, if not already present in payload

Suggested assistant content:

- Return a fixed string such as `"recorded-summary"` so the tool result can be asserted without relying on provider behavior beyond recording.

### 3. Regression test setup for the earlier-good branch

The test should drive the real fallback path of `GeminiWebFetchTool`, but with HTTP fetch mocked and the summarization turn routed through the dummy provider.

Setup steps:

1. Build an `AgentCore`.
2. Register:
   - the recording provider with `OpenAIToolsExtension`
   - `GeminiWebFetchTool`
   - at least one extra tool, for example `DummyCalculator`, so tool gating has something real to suppress
   - `ToolGatingFeature`
3. Build config with:
   - `model: "test-model"`
   - provider selection for the recording provider
   - `web_fetch_use_gemini_api: false` or trigger private-URL fallback
   - optional `web_fetch_fallback_settings_overrides`, for example `{ "model": "fallback-model", "temperature": 0.2 }`
4. Patch `fetch_url(...)` to return a successful `FetchResult` with deterministic plain text content.
5. If needed, patch `is_private_url(...)` to force the fallback route for a normal URL.
6. Execute the tool through the real tool path, ideally via `core.execute_tool_calls(...)` or the registered tool wrapper path, so the tool receives realistic context including `core` and config.

Preferred execution shape:

- Use `core.execute_tool_calls(...)` when possible, because it exercises the tool through the normal tool runtime path.
- If direct tool execution is required to provide context, pass a real context object containing the live `core` and config rather than a fake core.

### 4. What the regression test will assert

The regression test should make only behavioral assertions that matter across refactors.

Primary assertions:

- The fallback summarization succeeds and returns the provider’s deterministic assistant text.
- The internal summarization request had tools disabled:
  - `metadata.payload` does not contain `tools`
  - `metadata.payload` does not contain `tool_choice`
  - or, if provider conventions require it, tools are otherwise absent from the effective payload
- The prompt seen by the provider is Gemini-owned and matches the earlier branch semantics:
  - includes the original user prompt
  - includes the fetched content block
  - includes the explicit “do not attempt to access the URL again” wording or the exact earlier wording from the baseline branch
- Fallback settings overrides propagate:
  - `metadata.payload["model"] == "fallback-model"` when a model override is configured
  - non-model request options remain preserved where supported by the provider payload shape

Secondary assertions:

- The presence of a registered extra tool does not leak into the internal summarization request.
- The normal tool catalog still exists outside that internal request, meaning this is request-time gating, not global tool removal.

### 5. Bringing the regression test forward

After the earlier-branch test is green:

1. Cherry-pick or merge the test commit onto the later branch.
2. Run the same test before any production change.
3. Confirm it fails specifically because:
   - the later code moved prompt construction into the shared helper
   - the later code no longer disables tools for the internal summarization request
4. Preserve the test intent while making only mechanical adjustments needed for changed imports or helper names.

### 6. Production fix for web fetch

Refactor the shared helper boundary so the shared package owns execution mechanics, while Gemini owns wording.

#### Shared helper changes

Target file:

- `plugins/web-fetch-shared/src/web_fetch_shared/web_fetch_engine.py`

Replace the current “prompt-owning summarizer” API with an execution-oriented API.

Recommended direction:

- Introduce a helper such as `run_internal_summary_request(...)` or similarly named generic helper.
- Inputs should include:
  - `prompt_text`
  - `context`
  - optional `fallback_agent_id`
  - optional `fallback_model`
  - optional `settings_overrides`
  - optional `disable_all_tools` flag defaulting to `True`
- Outputs should be:
  - event stream or sync `(success, text)` result, depending on the final API shape

Shared helper responsibilities:

- create the temporary session
- add the caller-supplied prompt text
- switch agents when configured
- use the returned switched session from `app.update_agent(...)`
- merge config and request overrides safely
- set `disable_all_tools = True` by default for internal summarization-like requests
- preserve existing request options while merging
- collect final assistant text
- fall back to raw content on request failure where that is part of the existing contract

Shared helper must not:

- generate provider-specific or plugin-specific prompt text
- hardcode Gemini wording
- hardcode response text conventions beyond generic assistant-text collection

#### Gemini caller changes

Target file:

- `plugins/gemini-tools/src/gemini_tools/gemini_web_fetch_tool.py`

Gemini should:

- rebuild the original fallback summarization prompt in the plugin
- pass that prompt into the shared execution helper
- continue to pass fallback settings overrides and fallback agent selection

This restores the earlier caller-owned wording while retaining the shared execution path.

### 7. Additional web fetch behavior correction

Also correct the agent-switching regression in the shared helper:

- use `fallback_session` returned by `app.update_agent(...)`
- do not continue streaming against the pre-switch temp session

This is not the main reported regression, but it is a concrete behavior difference introduced by the refactor and should be fixed while touching the same execution helper.

### 8. Standardization plan for other internal LLM callers

Audit and standardize the following production call sites:

- `plugins/summarize-range-app/src/summarize_range_app/__init__.py`
- `plugins/generate-title-app/src/generate_title_app/__init__.py`
- `plugins/gemini-compaction-app/src/gemini_compaction_app/__init__.py`
- `plugins/gemini-compaction-feature/src/gemini_compaction_feature/__init__.py`

For each site, classify:

- whether the internal request should default to `disable_all_tools`
- whether it needs optional agent switching
- whether it needs request override merging
- whether it requires `app.send_request(...)`, `core.send_request(...)`, or a lower-level helper

Initial policy recommendation:

- `web_fetch` summarization: disable all tools by default
- `summarize_range` action: disable all tools by default
- `generate_title` action: disable all tools by default
- `gemini_compaction_app` compaction request: disable all tools by default
- `gemini_compaction_app` verification pass: disable all tools by default
- `gemini_compaction_feature` compaction request: disable all tools by default
- `gemini_compaction_feature` verification pass: disable all tools by default

Reasoning:

- These are all “internal transformation” or “internal summarization” requests.
- Allowing tools there creates a high risk of re-entering unrelated tools, causing recursion, side effects, or prompt drift.
- These flows operate on already-available conversation or fetched content, so tool access is usually unnecessary.

Standardization here means “same policy, same quality bar, similar structure,” not “rewrite them to use one shared runtime helper.”

For this task, keep these plugins independent:

- `generate-title-app`
- `summarize-range-app`
- `gemini-compaction-app`
- `gemini-compaction-feature`

What should be standardized across them:

- internal requests default to `disable_all_tools=True` unless the plugin explicitly documents a reason not to
- request-option merging preserves existing settings rather than replacing them accidentally
- agent-switching paths use the returned switched session consistently
- prompt text remains plugin-owned
- tests verify behavior through real request preparation and a recording provider, not through mocked `AgentCore` internals

What should remain plugin-specific:

- prompt wording
- session slicing / message selection
- whether the plugin uses `core.send_request(...)` or `app.send_request(...)`
- output parsing rules
- failure handling and user-facing error messages

Implementation approach for each plugin:

1. Audit the current internal request path.
2. Identify where overrides are merged and where tool-gating should be applied.
3. Add or adjust local code in that plugin only.
4. Add a focused test that verifies the plugin’s internal request suppresses tools and still preserves its current prompt/result semantics.

### 9. Standardization tests beyond web fetch

Add at least one additional focused regression test for another internal LLM action plugin to make the standardization real.

Best first candidate:

- `generate-title-app`

Why:

- it already has application-level tests
- it uses `app.send_request(...)`, which is a useful second shape to cover
- title generation is a strong candidate for default tool disabling

Suggested title-generation test:

- configure the same recording provider plus a real tool and `ToolGatingFeature`
- execute the title-generation action
- assert the provider-observed payload for the internal request contains no tools
- assert title prompt text remains caller-owned by the title plugin

Possible second candidate:

- `summarize-range-app`

Suggested assertions:

- internal summarization request disables tools
- configured prompt override still determines the last-user-message text

### 10. Per-plugin change outline

#### `generate-title-app`

Files:

- `plugins/generate-title-app/src/generate_title_app/__init__.py`
- relevant tests under `plugins/generate-title-app/tests/`

Planned changes:

- keep the existing `app.send_request(...)` shape
- ensure the internal request overrides include `disable_all_tools=True` by default
- preserve any existing caller/config overrides when adding that flag
- add a recording-provider-based test that checks the internal request payload omits tools

#### `summarize-range-app`

Files:

- `plugins/summarize-range-app/src/summarize_range_app/__init__.py`
- relevant tests under `plugins/summarize-range-app/tests/`

Planned changes:

- keep the existing `prepare_tools_for_session(...)` plus `core.send_request(...)` flow
- ensure the request config used for the internal summarization turn sets `disable_all_tools=True`
- preserve prompt override behavior and existing result extraction
- add a recording-provider-based test that confirms tools are suppressed and prompt override still works

#### `gemini-compaction-app`

Files:

- `plugins/gemini-compaction-app/src/gemini_compaction_app/__init__.py`
- relevant tests under `plugins/gemini-compaction-app/tests/`

Planned changes:

- keep the current local compaction and verification request flow
- ensure both compaction and verification requests set `disable_all_tools=True`
- preserve existing compaction prompt and verification prompt ownership
- confirm switched-agent flows continue to use `session_for_compact`
- add at least one focused test around internal tool suppression if coverage is missing

#### `gemini-compaction-feature`

Files:

- `plugins/gemini-compaction-feature/src/gemini_compaction_feature/__init__.py`
- relevant tests for the feature package

Planned changes:

- keep the current feature-local request logic
- ensure both compaction and verification requests disable tools by default
- preserve native-history-specific behavior and output parsing
- add or plan a focused test for internal tool suppression if the package currently lacks one

### 11. Verification sequence

Run tests in this order:

1. Earlier branch:
   - new Gemini regression test passes
2. Later branch before fix:
   - same regression test fails
3. Later branch after fix:
   - Gemini regression test passes
   - shared web-fetch tests pass
   - any newly added title-generation or summarize-range standardization tests pass

Targeted test commands to plan for:

- `pytest plugins/gemini-tools/tests/test_gemini_web_fetch_tool.py -q`
- `pytest plugins/web-fetch-shared/tests/test_web_fetch_engine.py -q`
- `pytest plugins/generate-title-app/tests/test_generate_title_app_plugin_unit.py -q`
- `pytest plugins/summarize-range-app/tests/test_summarize_range_app_plugin_unit.py -q`
- `pytest plugins/gemini-compaction-app/tests/test_gemini_compaction_app_via_agent_application.py -q`

## Completion Notes

These notes were added during completion.

- Added the Gemini web-fetch regression test first on a side branch from `c7f9f48d535def66991f1bf122d37b340aac71f6`, committed it there, then cherry-picked it onto `develop`.
- The regression test now verifies the behavior semantically through a recording provider and real tool gating:
  - internal fallback summarization uses the caller-owned Gemini prompt wording
  - the internal request omits tool schemas
  - the internal request sets `tool_choice` to `none`
  - fallback settings overrides still propagate
- Refactored `plugins/web-fetch-shared` so it no longer owns concrete summarization prompts.
- Restored Gemini prompt ownership in `plugins/gemini-tools` and moved Qwen prompt ownership into `plugins/qwen-tools`.
- The shared internal request helper now:
  - runs a one-shot non-streaming internal request
  - merges request options safely
  - defaults to `disable_all_tools=True`
  - uses the switched session returned by `app.update_agent(...)`
- Standardized local internal-request defaults in:
  - `generate-title-app`
  - `summarize-range-app`
  - `gemini-compaction-app`
  - `gemini-compaction-feature`
- Added focused recording-provider tests for:
  - `generate-title-app`
  - `summarize-range-app`
- Verified passing targeted tests for:
  - `plugins/gemini-tools/tests/test_gemini_web_fetch_tool.py`
  - `plugins/web-fetch-shared/tests/test_web_fetch_engine.py`
  - `plugins/qwen-tools/tests/test_qwen_web_fetch_tool.py`
  - `plugins/generate-title-app/tests/test_generate_title_app_plugin_unit.py`
  - `plugins/summarize-range-app/tests/test_summarize_range_app_plugin_unit.py`
  - `plugins/gemini-compaction-app/tests/test_gemini_compaction_app_unit.py`
  - `plugins/gemini-compaction-app/tests/test_gemini_compaction_app_via_agent_application.py`
  - `plugins/gemini-compaction-feature/tests/test_gemini_compaction_feature_unit.py`
- Follow-up test cleanup:
  - removed remaining monkeypatch-based `generate-title-app` and `summarize-range-app` tests
  - added an importable controllable provider at `plugins.controllable_openai_test_provider`
  - converted those suites to drive real `AgentApplication` flows with provider-configured responses, request recording, and deterministic blocking for concurrency coverage
- Follow-up runtime standardization:
  - switched all identified internal plugin LLM calls from `core.send_request(...)` to `core.send_request_stream(...)`
  - updated internal request tests/providers so they now exercise streaming-only provider behavior as well
- Residual risk:
  - a real-model OpenRouter integration test in `plugins/gemini-compaction-app/tests/test_gemini_compaction_app_system_message.py` remained unstable in this environment even after loading `ToolGatingFeature` in the custom test config. The main regression fix and all local/unit-level standardization checks are passing.