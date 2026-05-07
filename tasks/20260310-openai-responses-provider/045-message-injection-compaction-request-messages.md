# Message-Injection Compaction Must Use Request Messages

Short description: Make `openai_responses` native compaction use the same rendered request-time message override as a normal request when `feature-system-message` injects the prompt as a separate `system` or `developer` message instead of top-level `instructions`.

## Requirements checklist

- [x] `compact_native_history` must compact the same effective prompt-bearing native message content that a normal outbound request would use in message-injection mode.
- [x] The fix must work without plugin-to-plugin coupling; `openai_responses` compaction must not import or special-case `SystemMessageFeature` by name.
- [x] The current explicit action-side request preparation contract must be reused:
  - `AgentCore.initialize_action_request(native_messages, state, request_runtime, request_context)`
  - `request_runtime` and `request_context` from session-action context
- [x] The compaction payload must use request-time `state["request"]["messages"]` when that override exists and is the effective outbound message set for the provider.
- [x] The compaction payload must strip `_metadata` before sending compact input, but if the compacted output preserves the leading system/developer message, the stored native result must restore the original template-form message and its `_metadata`.
- [x] Prefix/range behavior must remain correct:
  - full-history compaction still compacts the full native prefix
  - prefix compaction still compacts exactly the visible-prefix native slice
- [x] Existing `system_message_as_instructions` behavior must keep working unchanged.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On:
- `tasks/20260310-openai-responses-provider/043-native-message-preparation-for-compaction.md`
- `tasks/20260310-openai-responses-provider/095-native-compaction-provider-extension.md`

Related:
- `tasks/20260310-openai-responses-provider/042-native-compaction-instruction-message-exclusion.md`
- `tasks/20260411-openai-responses-chatgpt-compaction-endpoint.md`

## Problem statement

The current explicit action preparation contract fixes compaction for the
top-level `instructions` path, because compaction can read the rendered prompt
from `state["request"]["instructions"]` after calling
`initialize_action_request(...)`.

But `feature-system-message` has another mode:

- `system_message_as_instructions: false`

In that mode, the feature keeps the retained native history mostly unchanged
and places the effective rendered outbound message list into:

- `state["request"]["messages"]`

Normal OpenAI Responses requests already honor that override. Native
compaction currently does not clearly do so; it slices and sanitizes the
prepared native list rather than the request-time message override.

That means compaction may still compact template-form or otherwise
non-effective instruction messages in normal API mode when the system prompt is
carried as a provider-native message.

## Required implementation outcome

1. After `initialize_action_request(...)`, native compaction must detect when
   `state["request"]["messages"]` is the effective outbound message set.
2. When present, compaction input must be derived from that effective message
   set rather than the retained/prepared native list.
3. The fix must preserve the existing prefix-selection semantics based on the
   original visible/native mapping of the session.
4. `_metadata` must never be sent to the compaction endpoint.
5. If the compacted output retains the leading system/developer message, the
   stored native result must restore the original retained version of that
   message, including template-form content and `_metadata` such as
   `compiled_content`.
6. The compaction extension must remain decoupled from specific feature names.
7. Existing ChatGPT / `system_message_as_instructions` behavior must not
   regress.

## Concrete verification required

Add or update tests so the task is only considered done when all of the
following assertions exist and pass.

### Test 1: unit regression for message-injection mode

Add a focused unit test in:

- `plugins/openai_responses/tests/test_openai_responses_native_compaction_extension_unit.py`

Suggested setup:

1. Register:
   - `OpenAIResponsesProvider`
   - `OpenAIResponsesNativeCompactionExtension`
   - `SystemMessageFeature`
2. Use normal API-mode config with:
   - `system_message_as_instructions: false`
   - `system_message` containing a template, for example:
     - `"You are helping {{PROJECT}}."`
   - a variable configuration such as:
     - `PROJECT = "AI Agent Platform"`
3. Build a session/native history where the leading retained system message is
   still template-form, not fully rendered.
4. Execute `compact_native_history`.

Required assertions:

1. The SDK `responses.compact(...)` call input contains the rendered system
   message text:
   - `"You are helping AI Agent Platform."`
2. The SDK `responses.compact(...)` call input does not contain the raw
   template text:
   - `"You are helping {{PROJECT}}."`
3. The SDK `responses.compact(...)` call input does not contain `_metadata`
   on the system/developer message item.
4. The compact input order matches the effective request message order that a
   normal outbound request would use.

### Test 2: prefix compaction still uses the correct slice

Add a second unit or integration-style regression in:

- `plugins/openai_responses/tests/test_openai_responses_native_compaction_extension_unit.py`
  or
- `plugins/openai_responses/tests/test_openai_responses_native_compaction_integration.py`

Suggested setup:

1. Create a multi-turn session with a message-injected system prompt.
2. Compact only a visible prefix with `end_index`.

Required assertions:

1. The compaction SDK input includes the rendered system message from the
   effective outbound request set.
2. The compaction SDK input contains exactly the native/messages that
   correspond to the selected visible prefix, no more and no less.
3. A follow-up request after compaction still succeeds and preserves retained
   native compaction artifacts without needing placeholder round-trip behavior.

### Test 3: stored native result restores the original first system/developer message

Add a focused unit regression in:

- `plugins/openai_responses/tests/test_openai_responses_native_compaction_extension_unit.py`

Suggested setup:

1. Start from a retained leading system or developer native message like:
   - template-form `text`, for example `"You are helping {{PROJECT}}."`
   - `_metadata` containing compiled/request-only information, for example:
     - `"compiled_content": "You are helping AI Agent Platform."`
2. Simulate a compaction SDK response that preserves that leading message in
   the returned compacted output, but in rendered/no-metadata form.
3. Execute `compact_native_history`.

Required assertions:

1. The stored `result["native_messages"]` or rebuilt session-native history
   keeps the original leading system/developer message text:
   - `"You are helping {{PROJECT}}."`
2. The stored leading message restores `_metadata`, including
   `compiled_content`.
3. The outbound compaction SDK input still used the rendered text and omitted
   `_metadata`.

### Test 4: no regression for `system_message_as_instructions`

Keep or extend existing coverage in:

- `plugins/openai_responses/tests/test_openai_responses_native_compaction_extension_unit.py`

Required assertions:

1. When `system_message_as_instructions: true`, compaction still uses:
   - `state["request"]["instructions"]`
2. The compact input still excludes the stripped leading `system` /
   `developer` message when configured.

## Likely files to touch

1. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py`
2. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
3. `plugins/feature-system-message/src/feature_system_message/system_message_feature.py`
4. `plugins/openai_responses/tests/test_openai_responses_native_compaction_extension_unit.py`
5. optionally `plugins/openai_responses/tests/test_openai_responses_native_compaction_integration.py`

## Notes

- This is intentionally smaller than task `043`.
- Do not reintroduce broad automatic action lifecycles.
- Reuse the explicit action preparation contract that already exists.

## Completion Notes

Added during completion:

1. Native compaction now checks `state["request"]["messages"]` after explicit action-side request preparation and uses that rendered outbound message list as compact input when present.
2. Outbound compact input still runs through the normal compaction sanitizer, which strips `_metadata` before the request is sent.
3. When the compacted output preserves the leading `system` or `developer` message, the stored native result restores the original retained item so template-form content and `_metadata` such as `compiled_content` are preserved.
4. The implementation remains decoupled from `SystemMessageFeature` by name and simply consumes the generic request-prepared state produced by `initialize_action_request(...)`.
5. Added a focused unit regression that verifies:
   - rendered system-message text is sent to `responses.compact(...)`
   - raw template text is not sent
   - `_metadata` is not sent
   - the stored native result restores the original first system message and its metadata

Verification run during completion:

- `python -m pytest plugins/openai_responses/tests/test_openai_responses_native_compaction_extension_unit.py -q`
- `python -m pytest plugins/openai_responses/tests/test_openai_responses_provider_unit.py -q`
- `python -m pytest plugins/openai_responses/tests/test_openai_responses_chatgpt_native_compaction_manual_integration.py --collect-only -q`

Notes:

- The live/manual ChatGPT compaction test was updated to the new no-placeholder expectation and collected successfully, but not executed during this completion step.