# Subtask: Improve template provider tests (integration-ready scaffolding)

Parent Task: tasks/20260303-provider-plugin-docs/000-main.md

## Description

Expand the test suite shipped with `plugins/template-python-provider` so it provides:

1) **Unit tests** for provider/extension patterns (offline, deterministic)
2) **Integration-test scaffolding** that can be reused by most real providers with minimal changes
3) An **application-level end-to-end** test scaffold (AgentApplication tool loop)

The OpenRouter plugin repo contains a set of tests that demonstrate good patterns that can be generalized.
This subtask adapts those patterns into a provider template so provider authors can quickly validate:

- Basic non-streaming and streaming
- Reasoning support (via provider extension)
- Tool calling support (via provider extension)
- Combined tools + reasoning
- Optional usage/cost tracking (via provider extension)
- App-level request loop (AgentApplication)

## Key reference tests to study (OpenRouter)

These files contain setups/assertions that are broadly applicable:

- Basic provider streaming/non-streaming:
  - `plugins/openrouter/tests/test_openrouter_basic_integration.py`
- Reasoning integration:
  - `plugins/openrouter/tests/test_openrouter_reasoning_integration.py`
- Comprehensive tools:
  - `plugins/openrouter/tests/test_openrouter_tools_comprehensive.py`
- Tools + reasoning retention across tool loop:
  - `plugins/openrouter/tests/test_openrouter_tools_reasoning_integration.py`
- Usage extension integration (usage metadata + cumulative cost):
  - `plugins/openrouter/tests/test_openrouter_usage_extension_integration.py`
- Application-level end-to-end tool loop:
  - `plugins/openrouter/tests/test_agent_application_openrouter_puzzle.py`

Also useful unit tests for extension logic patterns:

- Provider unit tests:
  - `plugins/openrouter/tests/test_openrouter_provider_unit.py`
- Reasoning extension unit tests:
  - `plugins/openrouter/tests/test_openrouter_reasoning_extension_unit.py`
- Tools extension unit tests:
  - `plugins/openrouter/tests/test_openrouter_tools_extension_unit.py`
- Usage extension unit tests:
  - `plugins/openrouter/tests/test_openrouter_usage_extension_unit.py`

## Current template state (as of 2026-03-03)

Template tests currently:

- validate accumulator path via a test-only provider subclass
- validate custom streaming via a test-only provider
- validate native history retention using a native-only marker extension

Location:

- `plugins/template-python-provider/tests/`

These tests pass offline and should continue to do so.

## Goals

- Keep the template tests and scaffolding simple and broadly applicable; avoid adding lots of framework code that authors would immediately delete.
- Provide reusable, provider-agnostic test scaffolding that provider authors can run with minimal changes.
- Add explicit test coverage for reasoning + tools + usage patterns (even if real provider integration tests are optional/skipped by default).

## Proposed approach

This subtask has two tracks:

1) **Now (template-first):** add integration-test *templates* that developers can enable by editing a small constants file.
2) **Later (optional future direction):** refactor these templates into fully provider-agnostic tests driven by env vars.

### 1) Keep the existing offline tests (always run)

Continue shipping offline, deterministic tests that validate core invariants and the template patterns:

- accumulator mixin updates `state['partial']`
- finalize appends the final message to native history
- native history retention across `AgentCore` instances using a native-only marker extension

These tests should remain network-free and should continue to pass in any environment.

### 1.1) Add minimal unit tests (always run)

Add a small set of unit tests that help authors implement common provider/extension features without requiring network calls.

Keep these tests minimal; the goal is to provide quick feedback during development, not a full conformance suite.

Recommended unit tests to include in the template (copy/adapt from OpenRouter unit tests where helpful):

1) Provider identity + schema
- Provider has `name` and `version`
- `get_config_schema()` includes expected keys and defaults

Reference patterns:
- `plugins/openrouter/tests/test_openrouter_provider_unit.py`

2) Request initialization shape
- `initialize_request()` creates `state['request']` with `url/payload/headers/timeout` (or provider-specific equivalent)
- if missing required config, raises a clear error

Reference pattern:
- `plugins/openrouter/tests/test_openrouter_provider_unit.py::test_initialize_request_*`

3) Conversion tests
- `to_native_messages()` and `from_native_messages()` handle the minimal supported core message shape
- if multipart is supported by the provider, include one conversion unit test (image URL)

Reference patterns:
- `plugins/openrouter/tests/test_openrouter_provider_unit.py::test_to_native_messages`
- `plugins/openrouter/tests/test_openrouter_provider_multipart_conversion_unit.py`

4) Accumulator helper behavior
- Given a sequence of chunks, ensure the accumulator-based implementation produces expected partial fragments and final output.
- Ensure `finalize()` appends final messages to native history.

Reference pattern:
- (template’s existing accumulator smoke test)

5) Extension unit tests (minimal)
- A reasoning extension: verifies that `process_chunk` accumulates reasoning fragments into `state['partial']` and that `from_native_messages` surfaces reasoning into core metadata.
- A tools extension: verifies mapping of `tool_calls`/`tool_call_id` between core metadata and provider-native fields.
- A usage extension (optional): verifies that usage metadata in chunks is converted into formatted metadata fields.

Reference patterns:
- `plugins/openrouter/tests/test_openrouter_reasoning_extension_unit.py`
- `plugins/openrouter/tests/test_openrouter_tools_extension_unit.py`
- `plugins/openrouter/tests/test_openrouter_usage_extension_unit.py`

These extension unit tests should live in the template even if the template ships only placeholder extension implementations; the unit tests can define small test-only extensions (like the existing test-only providers) to demonstrate the required behaviors.

### 2) Add integration test templates (copied patterns from OpenRouter; xfail by default)

Add integration test modules under `plugins/template-python-provider/tests/` that:

- are very close in setup/assertions to the OpenRouter integration tests
- are intended to run for **most real providers** when a model supports the capability being tested
- are marked as `xfail` in the template by default (so the template test suite stays green)

The expectation is:

- developers implement their provider + extensions
- set constants for provider class/model/API key
- remove `xfail` (or flip a constant/marker) to enforce the test

Important: tests must not error at import time.

### 3) Provider-under-test constants (shared file)

Add a small shared file like:

- `plugins/template-python-provider/tests/provider_under_test.py`

It should contain constants used by the integration templates, for example:

```python
PROVIDER_CLASS = "template_python_provider.provider.TemplateProvider"  # update me
PROVIDER_MODEL = ""  # update me
PROVIDER_API_KEY_ENV = ""  # e.g. "OPENROUTER_API_KEY" or "OPENAI_API_KEY"
PROVIDER_BASE_URL = ""  # optional

REASONING_EXTENSION_CLASS = ""  # dotted path
TOOLS_EXTENSION_CLASS = ""      # dotted path
USAGE_EXTENSION_CLASS = ""      # dotted path
```

The integration tests read these constants and dynamic-import the classes.

### 4) Provide reusable helper utilities in the template test suite

Add `plugins/template-python-provider/tests/_helpers.py` with functions:

- `import_symbol(dotted: str) -> object`
- `get_provider_and_extensions_from_env() -> (provider_cls, extension_classes)`
- `build_core(provider_cls, extensions, features, tools) -> AgentCore`
- `run_non_streaming(core, session, config) -> (session, finals)`
- `run_streaming(core, session, config) -> (session, finals, partial_text)`
- `run_tool_loop(core, session, config, max_iters=...) -> (session, finals)`
  - detect `metadata.tool_calls`
  - execute via `core.execute_tool_calls(tool_calls, config)`
  - append tool messages via `core.add_message(..., config=config)`

This mirrors patterns used in OpenRouter tools tests.

### 4.1) Revise existing template tests to follow the new patterns

The existing template tests should be refactored to align with the new approach:

- Add a shared constants module (`provider_under_test.py`) for provider-under-test configuration.
- Keep offline tests deterministic and passing.
- Add integration templates as separate files and mark them `xfail` by default.

Concretely:

- Update `test_accumulator_path_smoke.py` and `test_custom_streaming_path_smoke.py` to:
  - use shared helper functions where appropriate
  - keep assertions minimal and stable
  - avoid printing unless needed for debugging

- Keep `test_native_history_retention_pattern.py`, but consider moving common “native-only marker” helpers into `_helpers.py`.

### 5) Add integration-ready test modules (template)

Add test modules inspired by OpenRouter tests but kept close to their setups/assertions:

1) `test_provider_basic_integration_template.py`
   - based on `test_openrouter_basic_integration.py`
   - non-streaming + streaming
   - assertions: assistant final exists, content non-empty; streaming partials observed
   - marked `xfail` by default

2) `test_provider_reasoning_integration_template.py`
   - based on `test_openrouter_reasoning_integration.py`
   - registers provider + reasoning extension
   - assertions: reasoning metadata non-empty for reasoning-capable models
   - marked `xfail` by default

3) `test_provider_tools_integration_template.py`
   - based on `test_openrouter_tools_comprehensive.py` (single-tool call scenario)
   - registers provider + tools extension + basic tools (MathTools, FileReaderTool)
   - drives a tool loop and asserts at least one tool call exists
   - marked `xfail` by default

4) `test_provider_tools_reasoning_integration_template.py`
   - based on `test_openrouter_tools_reasoning_integration.py`
   - registers provider + reasoning + tools extensions
   - runs multi-iteration tool loop and asserts the expected final answer
   - marked `xfail` by default

5) `test_provider_usage_extension_integration_template.py`
   - based on `test_openrouter_usage_extension_integration.py`
   - provider + usage extension
   - send two turns; assert usage fields exist and cumulative cost is present
   - marked `xfail` by default

### 6) Application-level end-to-end scaffold (AgentApplication)

Add a template E2E test inspired by the OpenRouter puzzle test:

`test_agent_application_provider_tools_e2e_template.py`
  - based on `plugins/openrouter/tests/test_agent_application_openrouter_puzzle.py`
  - writes a temp config JSON for AgentApplication
  - uses provider-under-test constants (dotted class paths) for provider + tool extension + tools
  - runs `app.send_request(..., stream=False)` and asserts a `final` event exists
  - marked `xfail` by default

This test should be marked integration and skipped unless configuration is present.

## Success criteria

- Offline template tests continue to pass:

```bash
PYTHONPATH=plugins/template-python-provider/src:core/python \
  pytest plugins/template-python-provider/tests -q
```

-- Integration templates are present, `xfail` by default, and do not break collection.
-- Developers can enable them by setting constants and removing `xfail` markers.

## Optional future direction (mention only)

Once the template integration tests stabilize, consider making them fully provider-agnostic by:

- driving provider + extension class selection via environment variables
- selecting model/capability matrix via env or config

This would allow the same test suite to validate multiple providers without copying files.

## Notes / pitfalls (based on OpenRouter tests)

- Tool calling tests should be conservative about model compliance; offer strictness env flags.
- Reasoning may be absent or encrypted; tests should be tolerant unless strict mode is enabled.
- Usage metadata is provider-specific; treat it as optional but recommended.
- For some providers/models, you may need request options/features to force provider routing; keep the test harness flexible.
