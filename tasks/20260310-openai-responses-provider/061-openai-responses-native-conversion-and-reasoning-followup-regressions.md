# OpenAI Responses Native Conversion And Reasoning Follow-up Regressions

Short description: Fix `openai_responses` native-history to core-message conversion so one Responses response segment becomes one canonical assistant core message, stop stale tool-call reexecution after rebuild/follow-up flows, and add real-world OpenAI GPT-5 Mini reasoning tests at both core and application level, including a follow-up turn.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On:
- `tasks/20260310-openai-responses-provider/050-tools-extension-responses-api.md`
- `tasks/20260310-openai-responses-provider/060-reasoning-extension-responses-api.md`
- `tasks/20260310-openai-responses-provider/090-integration-native-retention-and-regression-tests.md`

## Problem summary

Two related regressions are showing up when using the new OpenAI Responses provider with real retained native history.

1. A single Responses response segment can currently rebuild into multiple assistant core messages.
2. Old tool calls can later be treated as pending and reexecuted after rebuild/follow-up flows.

The concrete symptom observed in `.crystal/sessions/f0d3ae28-03a8-42ac-bd20-6fdca69dd655.json` is that the same response segment is represented by:

- one assistant commentary message with native index `57`
- one assistant reasoning/final-answer message with native indices `[56, 57, 58]`

This is exactly the shape that makes extension-owned metadata attachment and later pending-tool heuristics unreliable.

## What the current code is doing

### Provider conversion problem

`OpenAIResponsesProvider.from_native_messages()` currently emits one core message per native `message` item, then later merges full segment ownership onto only one chosen output.

Relevant code:

- [plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:383](plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:383)
- [plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:452](plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:452)
- [plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:503](plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:503)

Important behavior in the current implementation:

- every native `type == "message"` becomes its own assistant core message
- response-segment native indices are tracked separately by `response_id`
- later, one candidate assistant message is assigned the full segment `native_indices`
- earlier assistant messages from the same response segment are left intact

This is why a `commentary` message and an empty `final_answer` message can both survive as separate core assistants.

### Extension interaction problem

Both reasoning and tools are then attached by extensions based on `native_indices` and `response_id`.

Relevant code:

- [plugins/openai_responses/src/openai_responses_plugins/openai_responses_tools_extension.py:227](plugins/openai_responses/src/openai_responses_plugins/openai_responses_tools_extension.py:227)
- [plugins/openai_responses/src/openai_responses_plugins/openai_responses_reasoning_extension.py:292](plugins/openai_responses/src/openai_responses_plugins/openai_responses_reasoning_extension.py:292)

Because the provider already produced multiple assistant messages for one response segment, the extensions may:

- decorate the wrong assistant message
- decorate multiple assistant messages from the same segment
- leave behind an old assistant-with-tool-calls shape that is later treated as unresolved

### Pending tool-call replay problem

The application-level tool loop treats the last assistant message with `tool_calls` as pending unless there is a later `tool` message.

Relevant code:

- [core/python/agent_app/tool_loop.py:51](core/python/agent_app/tool_loop.py:51)
- [core/python/agent_app/tool_loop.py:494](core/python/agent_app/tool_loop.py:494)

Current heuristic:

- scan for the last assistant with `metadata.tool_calls`
- if any later `tool` message exists, consider it handled
- otherwise auto-execute those tool calls before the next LLM phase

That heuristic is too weak for rebuilt/reconverted Responses histories. It does not check whether a later user turn or later assistant reply already superseded that assistant-with-tools message.

## Desired behavior

For Responses-native history, conversion should work turn-by-turn, not item-by-item.

The target invariant is:

1. One contiguous response segment for a single `response_id` should rebuild into one canonical assistant core message.
2. That one canonical assistant message should own the full segment `native_indices`.
3. That one canonical assistant message should be the single anchor for extension-added reasoning, usage, citations, and tool calls.
4. Tool outputs should remain separate core `tool` messages.
5. Follow-up turns and rebuilt histories must not cause already-executed tool calls to be replayed.

The simplest conversion model is the one suggested during investigation:

1. Sequentially scan native messages.
2. Start a new response accumulator whenever a new `response_id` begins.
3. Aggregate into one assistant result for that response segment:
   - reasoning items
   - assistant message text and/or commentary
   - tool calls
4. Flush tool outputs as separate `tool` messages.

## Recommended implementation plan

### 1. Refactor `openai_responses` provider conversion

Refactor [plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py](plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py) so `from_native_messages()` becomes a sequential reducer over native history.

Recommended structure:

1. Track a current response-segment accumulator keyed by contiguous `response_id`.
2. Aggregate within the segment:
   - all native indices in the segment
   - assistant text candidates
   - assistant phase records if present
   - any multipart content extracted from assistant `message` items
3. Emit exactly one assistant core message for the segment.
4. Preserve separate `tool` core messages for `function_call_output` items.
5. Leave non-response items without `response_id` on the simple item-by-item path.

Canonical assistant message selection rules:

1. Prefer the last non-empty assistant text in the segment.
2. If `final_answer` is empty but `commentary` has text, use the commentary text as the canonical assistant content.
3. Preserve phase detail in metadata, for example under a new key such as `phase_messages`, rather than by emitting multiple assistant core messages.
4. Always assign the full segment `native_indices` to the canonical assistant message.

### 2. Keep extension behavior aligned with the new invariant

After the provider emits one assistant message per response segment, the existing extension logic in:

- [plugins/openai_responses/src/openai_responses_plugins/openai_responses_tools_extension.py](plugins/openai_responses/src/openai_responses_plugins/openai_responses_tools_extension.py)
- [plugins/openai_responses/src/openai_responses_plugins/openai_responses_reasoning_extension.py](plugins/openai_responses/src/openai_responses_plugins/openai_responses_reasoning_extension.py)

should naturally become more reliable because both extensions already key off `native_indices` and `response_id`.

Check whether either extension needs a small adjustment for any new metadata field such as `phase_messages`, but avoid moving segment-grouping logic into the extensions. The grouping belongs in the provider.

### 3. Tighten pending-tool detection in the tool loop

Update [core/python/agent_app/tool_loop.py](core/python/agent_app/tool_loop.py) so `_extract_pending_tool_calls_from_session()` only returns pending calls when that assistant-with-tools is still the active unresolved tail of the conversation.

Recommended rule:

1. Find the last assistant message with `tool_calls`.
2. If any later `tool` message exists, treat those calls as handled.
3. If any later `user` message exists, also treat those calls as no longer pending.
4. If any later assistant message exists, also treat those calls as no longer pending.

This keeps the auto-resume behavior for truly interrupted tool loops while preventing replay after follow-up turns or rebuild flows.

### 4. OpenRouter parity

If the same multiple-assistant-per-response-segment issue is still present in [plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py](plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py), apply the same conversion fix there too so both Responses providers share the same invariant.

This is secondary to the OpenAI fix, but it should not be left divergent if the bug is confirmed in both providers.

## Tests to add

### Provider and regression tests for `openai_responses`

1. Add a provider unit test in `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`:
- response segment with `reasoning + commentary + empty final_answer`
- assert exactly one assistant core message is produced
- assert it owns the full segment `native_indices`
- assert the assistant content comes from the non-empty assistant text

2. Add a provider unit test in `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`:
- response segment with `reasoning + function_call`
- assert one assistant core message is produced
- later tools extension attaches the tool call to that one assistant message
- assert `native_indices` covers the full response segment

3. Add a provider unit test in `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`:
- response segment with `reasoning + commentary + final_answer + function_call`
- assert one assistant core message is produced
- assert phase detail is preserved in metadata if we add a `phase_messages` field

4. Extend `plugins/openai_responses/tests/test_openai_responses_native_history_regressions.py`:
- rebuild from synthetic/native retained history that includes reasoning and tool calls
- send a follow-up
- assert already-executed tool call ids are not replayed

5. Add a tool-loop regression test at the app layer or unit layer:
- session contains an assistant-with-tool-calls followed by a later user message
- `_extract_pending_tool_calls_from_session()` should return `[]`

### Real-world reasoning tests requested by user

The user asked for two new live OpenAI GPT-5 Mini reasoning suites, both guarded by `OPENAI_API_KEY` from the repo root `.env`, both using high reasoning effort, and both including a follow-up-turn variation.

#### A. Copy/adapt the existing OpenRouter reasoning integration test for OpenAI

Reference source to adapt:

- [plugins/openrouter_responses/tests/test_openrouter_reasoning_integration.py:1](plugins/openrouter_responses/tests/test_openrouter_reasoning_integration.py:1)

Create an OpenAI-focused counterpart under `plugins/openai_responses/tests/`, likely:

- `plugins/openai_responses/tests/test_openai_responses_reasoning_integration.py`

Scope:

1. OpenAI Responses provider only.
2. GPT-5 Mini only.
3. `reasoning_effort = "high"`.
4. Use the existing reasoning scenario style rather than the small metadata-only smoke tests in:
- [plugins/openai_responses/tests/test_openai_responses_reasoning_extension_integration.py](plugins/openai_responses/tests/test_openai_responses_reasoning_extension_integration.py)

Add two cases:

1. Initial reasoning/tool-call scenario.
2. Same scenario plus a follow-up user prompt that requires another fresh reasoning + tool-call + final response cycle.

The follow-up can reuse the same base puzzle/question with a different seed or parameter so the model should reason again instead of reusing the previous literal answer.

#### B. Add an application-level end-to-end reasoning test for OpenAI

The user also wants a real-world application-level test, structurally similar to the OpenRouter reasoning integration test but executed through `AgentApplication`.

Reference for existing application-level OpenRouter style:

- [plugins/openrouter_responses/tests/test_agent_application_openrouter_responses_puzzle.py:1](plugins/openrouter_responses/tests/test_agent_application_openrouter_responses_puzzle.py:1)

Create a new OpenAI application-level test file under `plugins/openai_responses/tests/`, likely:

- `plugins/openai_responses/tests/test_agent_application_openai_responses_reasoning.py`

Requirements:

1. Provider is `openai_responses` only.
2. Model is `gpt-5-mini` only.
3. `reasoning_effort = "high"`.
4. Drive the request through `AgentApplication`, not direct `AgentCore` usage.
5. Assertions should be similar in spirit to the OpenRouter reasoning integration:
- reasoning/tool execution actually happens
- final answer is correct for the scenario
- follow-up turn also succeeds and triggers a fresh reasoning/tool cycle

Add two cases:

1. Single-turn end-to-end reasoning scenario.
2. Same scenario followed by a second user message that causes another reasoning/tool call/final answer cycle.

## Suggested file additions

1. `plugins/openai_responses/tests/test_openai_responses_reasoning_integration.py`
2. `plugins/openai_responses/tests/test_agent_application_openai_responses_reasoning.py`

Possible touched existing files:

1. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
2. `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`
3. `plugins/openai_responses/tests/test_openai_responses_native_history_regressions.py`
4. `core/python/agent_app/tool_loop.py`
5. Optionally `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py`
6. Optionally `plugins/openrouter_responses/tests/test_openrouter_responses_provider_unit.py`

## Test execution targets

Unit/regression:

1. `pytest plugins/openai_responses/tests/test_openai_responses_provider_unit.py -q`
2. `pytest plugins/openai_responses/tests/test_openai_responses_native_history_regressions.py -q`
3. `pytest -q core/python/tests -k pending_tool_calls`

Live OpenAI integration:

1. `pytest plugins/openai_responses/tests/test_openai_responses_reasoning_integration.py -q -m openai`
2. `pytest plugins/openai_responses/tests/test_agent_application_openai_responses_reasoning.py -q -m openai`

If OpenRouter parity is also changed:

1. `pytest plugins/openrouter_responses/tests/test_openrouter_responses_provider_unit.py -q`

## Notes for the implementing agent

1. `openai_responses` streaming finalization already looks correct and should not be broadened unnecessarily:
- [plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:835](plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:835)
- [plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:899](plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:899)

2. The main bug is not premature final emission in `openai_responses`; it is the provider's native-to-core grouping invariant.

3. Keep provider vs extension boundaries intact:
- provider owns native history grouping and canonical core message construction
- tools extension owns tool-call extraction/attachment
- reasoning extension owns reasoning metadata extraction/attachment

4. Use `OPENAI_API_KEY` from the repo root `.env` for live tests and skip cleanly when missing.

---

## Execution plan appended during task completion

Approved execution plan for this task:

1. Refactor `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py` so `from_native_messages()` reduces contiguous Responses segments by `response_id` into exactly one canonical assistant core message per segment while still emitting `function_call_output` items as separate `tool` messages.
2. Keep segment-grouping logic in the provider and make only minimal extension adjustments in the OpenAI tools/reasoning extensions if the new single-assistant invariant requires it.
3. Tighten `core/python/agent_app/tool_loop.py` so `_extract_pending_tool_calls_from_session()` only resumes calls when the assistant-with-tool-calls is still the unresolved tail; later `tool`, `user`, or `assistant` messages should suppress replay.
4. Add provider and native-history regression tests for the canonical assistant invariant and the stale-tool-call replay bug.
5. Add an application/tool-loop regression test for the updated pending-tool heuristic.
6. Add two live OpenAI GPT-5 Mini reasoning suites guarded by `OPENAI_API_KEY`: one provider-level integration suite and one `AgentApplication` end-to-end reasoning suite, both with follow-up-turn coverage and `reasoning_effort = "high"`.
7. Check OpenRouter Responses parity and only apply the same conversion invariant there if the same bug is confirmed.

---

## Completion notes appended during task completion

Implemented:

1. Refactored `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py` so `from_native_messages()` reduces contiguous `response_id` segments into one canonical assistant message with full segment `native_indices`, preserved `phase_messages`, and separate `tool` messages for `function_call_output` items.
2. Tightened `core/python/agent_app/tool_loop.py` pending-tool detection so any later `tool`, `user`, or `assistant` message suppresses stale auto-replay.
3. Added OpenAI provider/native-history regression coverage in:
   - `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`
   - `plugins/openai_responses/tests/test_openai_responses_native_history_regressions.py`
   - `core/python/tests/test_application_layer_tools.py`
4. Confirmed the same multi-assistant segment issue existed in OpenRouter Responses and aligned `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py` with the same single-assistant-per-segment invariant, updating `plugins/openrouter_responses/tests/test_openrouter_provider_unit.py` accordingly.
5. Added live OpenAI GPT-5 Mini reasoning suites with follow-up coverage in:
   - `plugins/openai_responses/tests/test_openai_responses_reasoning_integration.py`
   - `plugins/openai_responses/tests/test_agent_application_openai_responses_reasoning.py`

Verification run during completion:

1. `pytest plugins/openai_responses/tests/test_openai_responses_provider_unit.py -q`
2. `pytest plugins/openai_responses/tests/test_openai_responses_native_history_regressions.py -q`
3. `pytest core/python/tests/test_application_layer_tools.py -q`
4. `pytest plugins/openrouter_responses/tests/test_openrouter_provider_unit.py -q`
5. `pytest plugins/openai_responses/tests/test_openai_responses_reasoning_integration.py -q -m openai`
6. `pytest plugins/openai_responses/tests/test_agent_application_openai_responses_reasoning.py -q -m openai`

Notable finding:

1. Some real OpenAI follow-up turns return reasoning only in native history items rather than on the final assistant metadata. The new live tests account for this by asserting fresh reasoning/tool activity via native response segments in follow-up cases instead of assuming `metadata["reasoning"]` is always present on the last assistant message.