# Provider Streaming Event Normalization And Finalization

Short description: Implement OpenAI SDK streaming handling in provider, including event normalization and finalize behavior, without moving tools/reasoning/usage/verbosity domain logic into provider.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On: `tasks/20260310-openai-responses-provider/030-provider-core-conversion-and-nonstreaming-sdk.md`

## Implementation

1. Implement `stream_api` with OpenAI SDK streaming API.
2. Normalize SDK events into provider-native chunk dicts suitable for extension processing.
3. Implement provider `process_chunk` and `finalize` for generic text/lifecycle handling.
4. Ensure full native history invariants are preserved in streaming path.
5. Do not implement extension-owned logic (tool/reasoning/usage/verbosity) here.

## Tests (required in this step)

1. Unit tests for streaming event normalization from mocked SDK stream events.
2. Unit tests for partial emission + finalize semantics.
3. Unit tests ensuring no raw chunk artifacts pollute native history.
4. Regression tests for provider wrapper compatibility (`send_request_stream` behavior).

## References

- `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py`
- `core/python/agent_core/plugin/provider.py`
- `plugins/docs/provider-plugins.md`

## Completion notes (added during completion)

### Changes made

1. Implemented streaming transport + normalization in `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`:
- added `stream_api` using OpenAI SDK `client.responses.create(..., stream=True)`
- reused request/input validation and internal `_metadata` stripping before send
- normalized streamed SDK events into plain provider-native chunk dicts via `model_dump(mode="python")`
- added stream error wrapping (`OpenAI Responses stream failed: ...`)

2. Implemented streaming chunk reduction semantics in provider:
- `process_chunk` now emits partials only for `response.output_text.delta`
- `process_chunk` now emits final native items only on `response.completed`
- final native items are derived from `response.output`, annotated with existing response metadata helper (`response_id` and selected `usage`)
- no raw streaming event artifacts are appended to native history
- no `response.done` handling/fallback path is used

3. Implemented finalize semantics for streaming path:
- `finalize` remains an intentional no-op (`[], native_messages, state`), because final native items are emitted at `response.completed`

4. Added deterministic streaming fixture support:
- new script: `plugins/openai_responses/tests/scripts/generate_streaming_fixture.py`
- generated fixture: `plugins/openai_responses/tests/fixtures/openai_responses_gpt5mini_streaming_events.json`

5. Expanded unit coverage in `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`:
- stream event normalization from mocked SDK stream events (object+dict mix)
- stream error wrapping
- partial emission + `response.completed` finalization behavior
- malformed `response.completed` negative path
- finalize no-op assertion
- wrapper regression test using `AgentCore.send_request_stream` with fixture-backed streaming client
- native history invariant checks ensuring no `response.*` chunk artifacts are persisted

6. Added real streaming integration test in `plugins/openai_responses/tests/test_openai_responses_provider_integration.py`:
- new `gpt-5-mini` streaming test via `AgentCore.send_request_stream`
- asserts partials are emitted, final response is present, and native history is clean

### Tests run

1. `pytest plugins/openai_responses/tests/test_openai_responses_provider_unit.py -q`
- result: `16 passed`

2. `pytest plugins/openai_responses/tests/test_openai_responses_provider_integration.py -q`
- result: `2 passed`

3. `pytest plugins/openai_responses/tests -q`
- result: `23 passed`

### Open issues

1. None blocking for subtask 040.
2. Extension-owned streaming behaviors (tools/reasoning/usage/verbosity extraction/shaping) remain intentionally deferred to subtasks 050-080.

## Review notes (added after completion review)

1. Remaining issue: streaming terminal lifecycle handling is incomplete.
- provider `process_chunk` finalizes only on `response.completed`
- provider `finalize` is a no-op
- if stream ends without `response.completed` (for example a terminal failure event payload instead of transport exception), request flow can complete with no assistant finals and no explicit error

2. Remaining test gap: no explicit coverage for terminal failure stream events.
- current unit/integration tests cover normalization, partials, completed-event finalize, malformed completed payload, and transport exception wrapping
- add a fixture-driven unit test for failure terminal event behavior (for example `response.failed`) and assert deterministic error/behavior instead of silent empty final output

3. Resolved in current uncommitted corrections: provider-side usage shaping was removed, so usage ownership remains in the usage extension scope.

## Post-review corrections (added after review notes)

### Corrections implemented

1. Added explicit terminal failure handling in provider streaming reduction.
- `process_chunk` now detects terminal failure events and raises deterministic errors for:
  - `response.failed`
  - `response.incomplete`
  - `error`
- failure messages include event-type context and, when available, response id / error code / reason.

2. Added stream lifecycle guard in provider `finalize`.
- `process_chunk` now marks stream lifecycle in state:
  - `_openai_responses_stream_started`
  - `_openai_responses_stream_completed`
- `finalize` now raises if a streaming request started but no `response.completed` terminal event was observed.
- successful streaming path remains unchanged: final native messages come only from `response.completed`.

3. Added fixture-driven unit coverage for terminal failure behavior.
- new fixture: `plugins/openai_responses/tests/fixtures/openai_responses_gpt5mini_streaming_failed_events.json`
- new unit tests cover:
  - `response.failed` terminal event raises deterministic error
  - `response.incomplete` terminal event raises deterministic error
  - finalize raises on started-without-completed stream
  - wrapper-level `send_request_stream` raises on failed terminal stream

### Post-review tests run

1. `pytest plugins/openai_responses/tests/test_openai_responses_provider_unit.py -q`
- result: `22 passed`

2. `pytest plugins/openai_responses/tests/test_openai_responses_provider_integration.py -q`
- result: `2 passed`

3. `pytest plugins/openai_responses/tests -q`
- result: `29 passed`
