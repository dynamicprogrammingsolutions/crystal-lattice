# Fix `/responses` `native_indices` Mapping + Add Delete/Slice Integration Tests

Short description: Fix `OpenRouterResponsesProvider.from_native_messages()` so core `metadata.native_indices` correctly covers *all* provider-native items that belong to a single response/turn (reasoning items, assistant message items, and tool-call items). Add integration tests that exercise `AgentCore.slice_session()` for both delete and fork/slice scenarios on a multi-turn reasoning+tool-call session, and verify a follow-up request succeeds.

Parent Task: `tasks/20260309-openrouter-responses-provider/000-main.md`

## Problem

The framework’s history editing operations (`slice_session`, `fork_session`, modify/delete flows) rely on core message `metadata.native_indices` to decide which provider-native items are owned by which core messages.

For `/responses`, one assistant “turn” can produce multiple provider-native items (e.g. `reasoning`, phased `message` items, `function_call` items). If a core assistant message’s `native_indices` only points at a single output item, slicing/deleting that turn can:

- Leave behind orphan provider-native items (e.g. reasoning or tool call items) that still get replayed in subsequent requests.
- Produce inconsistent native history reconstruction, or fail with integrity/normalization errors.

## Target behavior

- For a response/turn that yields multiple native items, core message(s) representing that turn must include `metadata.native_indices` that cover *all relevant native indices*.
- In particular, when a response contains reasoning + assistant output + tool calls, the `native_indices` for the canonical assistant result message (or tool-call message that triggers the tool loop) must include indices for:
  - `type:"reasoning"` output items
  - assistant `type:"message"` output items (including phased messages)
  - `type:"function_call"` output items

## Implementation approach

1. Use `response_id` (persisted into provider-native items under `"_metadata"`) to group provider-native items by response segment.
2. In `OpenRouterResponsesProvider.from_native_messages()`:
   - When converting native items into core messages, compute the full set of native indices belonging to a response segment.
   - Attach `metadata.native_indices` for the segment onto the primary assistant core message for that response.
     - Prefer the assistant message with `phase == "final_answer"` when present.
     - Otherwise use the last assistant content message, or the tool-call assistant message if the response ended in tool calls.
3. Ensure the mapping remains compatible with `AgentCore.slice_session()`:
   - Every core message included in the rebuilt session must have valid `native_indices`.
   - The slice/delete operations should remove the intended provider-native items with no leftovers.

## Integration tests to add

Add a new integration test file under `plugins/openrouter_responses/tests/` that uses the existing `reasoning_test/` fixture and runs a tool loop (reasoning + file tool call) for two turns.

### Test 1: Delete first turn

Setup:
- Run two user→assistant turns where the first turn includes reasoning + at least one tool call + tool output.

Action:
- Remove the *entire first turn* from the session using `AgentCore.slice_session(...)` (delete semantics), ensuring tool-result messages are removed as well.

Assertions:
- The resulting session’s `metadata["native_messages"]` contains no native items from the first response segment.
- The resulting session’s core messages are the expected shape (roles ordered sensibly; no dangling tool outputs without corresponding tool calls).
- Sending a new user message on the resulting session succeeds (no provider error).

### Test 2: Slice/fork first turn

Setup:
- Same initial two-turn session.

Action:
- Keep only the first turn (slice/fork semantics), dropping the second turn.

Assertions:
- The resulting session’s `metadata["native_messages"]` contains only native items for the first response segment.
- Core messages and native history remain consistent (native integrity passes).
- Sending a new user message on the forked session succeeds.

## Test commands

- `pytest plugins/openrouter_responses/tests/<new_test_file>.py -q`

## Acceptance criteria

- A core assistant message corresponding to a `/responses` turn that includes reasoning + tool calls has a `metadata.native_indices` list whose length is > 1 and includes indices for the relevant native output items.
- Both integration tests described above pass reliably against OpenRouter.
- A follow-up request after delete/slice succeeds.

## Execution Plan (added during completion)

1. Update `OpenRouterResponsesProvider.from_native_messages()` to compute per-`response_id` native index sets and assign segment-wide `metadata.native_indices` to the selected canonical assistant message for that response segment.
2. Extend canonical-assistant selection so that priority is:
   - assistant with `phase == "final_answer"`, otherwise
   - tool-call assistant (when the response contains `function_call` items), otherwise
   - last assistant with non-empty content, otherwise
   - last assistant candidate.
3. Keep existing response-level metadata derivation (`reasoning` summary and `url_citations`) and apply it to the same chosen canonical assistant message, together with segment-wide `native_indices`.
4. Add provider unit tests validating that a reasoning+message+function_call response segment maps to assistant metadata whose `native_indices` covers all segment item indices.
5. Add OpenRouter integration tests that:
   - build a two-turn session using `reasoning_test/` with a real tool loop,
   - validate delete slicing removes all first-turn response native items,
   - validate fork slicing keeps only first-turn response native items,
   - verify follow-up requests succeed after each slice operation.
6. Run targeted provider unit tests and the new integration file.

## Completion Notes (added during completion)

- Updated `OpenRouterResponsesProvider.from_native_messages()` to track response-segment item indices by `response_id` and assign segment-wide `metadata.native_indices` onto a canonical assistant message per response segment.
- Added canonical assistant selection helper with priority:
  - `phase == "final_answer"`
  - assistant carrying `tool_calls` when response output includes `function_call` items
  - last assistant with non-empty content
  - final assistant fallback
- Kept existing response-level metadata derivation (`reasoning`, `url_citations`) and now applied it together with segment-wide `native_indices` on the chosen assistant message.
- Added provider unit tests:
  - `test_from_native_messages_assigns_segment_native_indices_to_final_answer_assistant`
  - `test_from_native_messages_assigns_segment_native_indices_to_tool_call_assistant`
- Added new integration file:
  - `plugins/openrouter_responses/tests/test_openrouter_responses_slice_integration.py`
  - Covers delete-first-turn and fork-first-turn slicing flows, validates response-id segment removal/retention in native history, checks for no dangling tool outputs, and verifies follow-up requests succeed.

### Verification run

- `pytest -q plugins/openrouter_responses/tests/test_openrouter_provider_unit.py -k "segment_native_indices or aggregates_function_calls"`
- `pytest -q plugins/openrouter_responses/tests/test_openrouter_responses_provider_unit.py`
- `pytest -q plugins/openrouter_responses/tests/test_openrouter_responses_slice_integration.py -q`
