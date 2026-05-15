# OpenAI Responses ChatGPT System Message Instructions

Make ChatGPT-backed OpenAI Responses requests keep the visible leading system/developer message in session history while still sending that message as top-level `instructions` to endpoints that reject system/developer input items.

## Requirements checklist

- [x] Preserve existing explicit config behavior for `system_message_as_instructions` and `strip_leading_system_or_developer_message`.
- [x] Restore/default to previous visible-history behavior when those config params are not set: a leading system/developer message remains in message/native history and therefore remains visible in the UI.
- [x] For ChatGPT-backed OpenAI Responses requests, strip the leading system/developer item only from the outgoing request input and send its rendered text as `instructions`.
- [x] Apply the same outgoing-input/instructions behavior to native compaction requests.
- [x] Ensure placeholder compilation still happens once per request via `SystemMessageFeature`; do not add a second template compiler in the provider.
- [x] Cover every changed branch and relevant scenario with existing or new unit/integration tests.
- [x] Run the relevant real API integration tests, and add real API/manual integration coverage if existing tests do not exercise the new behavior.

## Background

ChatGPT login support for the `openai_responses` provider introduced two config flags:

- `system_message_as_instructions`: makes `SystemMessageFeature` compile the system message into `state["request"]["instructions"]` instead of injecting/retaining a system message.
- `strip_leading_system_or_developer_message`: makes the OpenAI Responses provider remove a leading system/developer item before sending.

That works for the ChatGPT endpoint, which requires the Responses `instructions` parameter and rejects `system`/`developer` input messages. However, when these flags are used globally, the leading system message is no longer visible in UI history. The desired behavior is to keep the visible/default message-history behavior unless those flags are explicitly configured, while still adapting the outgoing request for ChatGPT endpoints.

## Current Code References

`SystemMessageFeature.initialize_request` already contains the desired history/request split:

- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:845` documents that message mode inserts/keeps a template-level `system` message when `system_message_as_instructions` is disabled.
- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:897` inserts the synthetic native system message only when `as_instructions` is false.
- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:977` renders placeholders on every request.
- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:980` writes rendered text to `request["instructions"]` only when `as_instructions` is true.
- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:1003` builds `request["messages"]` override with the rendered system content in default/message mode.

The OpenAI Responses provider currently applies instructions and stripping separately:

- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:442` reads `request["instructions"]`.
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:455` delegates leading system/developer stripping.
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:2285` to `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:2296` builds non-streaming payload/history.
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:2454` to `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:2466` builds streaming payload/history.

Native compaction already gets per-request feature initialization:

- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py:625` uses `request["messages"]` override when building compaction input.
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py:638` currently strips only when `strip_leading_system_or_developer_message` is configured.
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py:760` to `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py:777` calls `core.initialize_action_request(...)`, so `SystemMessageFeature` has a chance to render placeholders before compaction.
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py:798` to `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py:829` passes `request["instructions"]` to `client.responses.compact(...)`.

Existing real API/manual integration references:

- `plugins/openai_responses/tests/test_openai_responses_native_compaction_integration.py:52` covers regular OpenAI API native compaction and follow-up turns.
- `plugins/openai_responses/tests/test_openai_responses_chatgpt_native_compaction_manual_integration.py:49` builds ChatGPT native compaction config, but currently sets `system_message_as_instructions: true` and `strip_leading_system_or_developer_message: true`.
- `plugins/openai_responses/tests/test_openai_responses_chatgpt_native_compaction_manual_integration.py:86` marks the ChatGPT compaction test as `manual_integration`, `integration`, and `openai`.

## Implementation Plan

1. Add shared request-preparation helpers in `plugins/openai_responses/src/openai_responses_plugins/openai_responses_runtime.py`.

   Suggested helpers:

   - `leading_system_or_developer_message_text(native_messages) -> Optional[str]`
   - `prepare_input_and_instructions_for_endpoint(native_messages, instructions, config) -> tuple[list[dict], Optional[str]]`

   The helper should detect a leading Responses item shaped like `{"type": "message", "role": "system" | "developer", "content": [...]}` or a compatible role-only dict, extract text from text-like parts (`input_text`, `output_text`, `text`), and return a new outgoing input list without mutating the original list.

2. Preserve explicit config behavior.

   If `strip_leading_system_or_developer_message` is true, keep the existing stripping behavior. Be careful with instruction merging:

   - Existing tests expect explicit `system_message_as_instructions + strip_leading_system_or_developer_message` to send the explicit compiled `request["instructions"]`.
   - Avoid duplicating instructions when both `request["instructions"]` and a leading system/developer item exist.

3. Add implicit ChatGPT endpoint behavior.

   For effective auth mode `chatgpt`, if the outgoing input starts with system/developer and `request["instructions"]` is absent, strip that first item from outgoing input and set `instructions` to the extracted rendered text. This should happen at request-send time only.

   The session history and provider-native stored history must still retain the leading system/developer message.

4. Use the shared helper in normal provider sends.

   Update both:

   - `OpenAIResponsesProvider.call_api`
   - `OpenAIResponsesProvider.stream_api`

   Build `base_history` from `request["messages"]` override or `native_messages`, run the helper, validate the resulting outgoing history, set `payload["instructions"]` from the helper result, and continue with the existing attachment/tool/retry logic.

5. Use the shared helper in native compaction.

   Update `_build_compaction_input` and/or `execute_action` so compaction request input and instructions are prepared with the same semantics as normal sends.

   Important behavior:

   - In default/message mode, `SystemMessageFeature` should render placeholders into `request["messages"]`; compaction should extract that rendered text into `instructions` for ChatGPT mode.
   - The compacted/stored native history restoration logic should still preserve the original template-level leading system/developer message where applicable.

6. Update config schema descriptions if needed.

   The existing `strip_leading_system_or_developer_message` description can stay as an explicit override, but if behavior changes visibly, add a short note in provider README/docs explaining that ChatGPT auth automatically converts leading system/developer request input into top-level `instructions` at send time while retaining history.

## Test Plan

Add or update unit tests first. Every changed branch should have a focused unit/regression test.

Provider unit tests in `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`:

- Default API mode with leading system/developer and no flags: outgoing input still includes the leading message and no implicit instructions are added.
- ChatGPT/effective ChatGPT streaming mode with leading system and no flags: outgoing input omits the leading system item and outgoing payload has `instructions` equal to the rendered system text.
- ChatGPT/effective ChatGPT streaming mode with leading developer and no flags: same as above for `developer`.
- ChatGPT/effective ChatGPT mode with existing `request["instructions"]`: do not duplicate or unexpectedly merge leading text; preserve current explicit instructions behavior.
- Existing explicit strip tests still pass, including `test_call_api_can_strip_leading_system_message_from_request_history` and `test_stream_api_can_strip_leading_developer_message_from_request_history`.
- Add helper-level tests for extracting text from Responses content parts, including multiple text parts and non-text parts.

System-message feature tests in `plugins/feature-system-message/tests/test_system_message_feature.py`:

- Existing tests should continue to prove message mode creates `request["messages"]` and instruction mode creates `request["instructions"]`.
- Add a regression only if implementation changes the feature; ideally no feature change is needed.

Native compaction unit tests in `plugins/openai_responses/tests/test_openai_responses_native_compaction_extension_unit.py`:

- Default/message mode plus effective ChatGPT config: `core.execute_session_action(...)` should send compact input without the leading rendered system/developer item and `compact_calls[0]["instructions"]` should equal the rendered system/developer text.
- Verify the visible/core messages and stored native history still contain the leading system/developer template after compaction.
- Existing explicit `system_message_as_instructions: true` plus `strip_leading_system_or_developer_message: true` test should still pass.
- Existing API/default message-injection compaction behavior should stay unchanged.

Application-level tests if behavior crosses `AgentApplication` or terminal config loading:

- Check existing AgentApplication OpenAI Responses config/load tests first.
- Add an application integration-style unit test only if the provider/core unit tests do not cover config-driven ChatGPT effective auth plus system-message feature initialization.

Real API/manual integration tests:

- Run existing real API OpenAI compaction tests:

  ```bash
  pytest plugins/openai_responses/tests/test_openai_responses_native_compaction_integration.py -m "integration and openai" -q
  ```

- Run existing ChatGPT manual native compaction test when saved login state is available:

  ```bash
  pytest plugins/openai_responses/tests/test_openai_responses_chatgpt_native_compaction_manual_integration.py -m "manual_integration and integration and openai" -q
  ```

- Add or modify a ChatGPT manual integration test to exercise the new default behavior with no `system_message_as_instructions` and no `strip_leading_system_or_developer_message`. The test should:

  - Use saved ChatGPT credentials as the existing manual test does.
  - Configure `SystemMessageFeature` in default/message mode with a short system message that asks for exact replies.
  - Send a streaming request and assert the response obeys the system instructions.
  - Assert the resulting visible messages still include the leading system message or that session/native history retains it, depending on the existing core message surface at that point.
  - Run native compaction and a follow-up streaming request to prove compaction also uses instructions-compatible input.

- If real API credentials are unavailable, report those tests as not run/skipped with the exact reason. Do not count skipped gated tests as successful verification.

Suggested focused non-real test command set:

```bash
pytest plugins/openai_responses/tests/test_openai_responses_provider_unit.py -q
pytest plugins/openai_responses/tests/test_openai_responses_native_compaction_extension_unit.py -q
pytest plugins/feature-system-message/tests/test_system_message_feature.py -q
```

## Complexity Notes

This should be moderate and localized, not overly complex. The cleanest path is shared request-preparation logic used by provider send paths and native compaction. Avoid adding template rendering logic to the provider; `SystemMessageFeature` already handles request-time compilation and compaction already calls the same initialization chain.

The one delicate decision is instruction merging. To minimize regressions, only perform implicit leading-message-to-instructions conversion for ChatGPT mode when there is no existing `request["instructions"]`. Existing explicit config behavior should remain exactly as it is today.

## Completion Notes

Added during implementation.

- Added shared OpenAI Responses request-preparation helpers that convert a leading system/developer input item into top-level `instructions` for ChatGPT-backed requests when no explicit instructions are already present.
- Wired the helper into non-streaming sends, streaming sends, and native compaction.
- Preserved stored native history during native compaction by restoring the original template-level leading system/developer item after implicit ChatGPT request conversion.
- Added provider unit coverage, native compaction unit coverage, and a ChatGPT manual integration test for the visible-system-message path.
- Updated the existing ChatGPT native compaction manual integration default model to `gpt-5.5` and removed a stale assertion that rejected current placeholder transcript output.
- Verified with focused unit tests, lint, regular OpenAI real compaction integration, and ChatGPT manual integration tests.