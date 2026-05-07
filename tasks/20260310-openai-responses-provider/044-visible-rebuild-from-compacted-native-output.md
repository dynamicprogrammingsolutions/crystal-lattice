# Visible Rebuild From Compacted Native Output

Short description: Update `openai_responses` native compaction so the compact API's returned native messages are rebuilt into visible core messages directly, instead of being hidden behind a single placeholder message that owns the whole compacted native range.

## Requirements checklist

- [x] Native compaction keeps the compact API output as retained native history.
- [x] The visible transcript after compaction is rebuilt from that native output through the normal conversion pipeline.
- [x] The compacted transcript is no longer hidden behind a single placeholder message by default.
- [x] Follow-up requests still work after both full and partial compaction.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On:
- `tasks/20260310-openai-responses-provider/095-native-compaction-provider-extension.md`

## Goal

After native compaction finishes, the returned native message list should remain the retained native history and should also drive the visible transcript through normal native-to-core rebuild.

The user should see the rebuilt messages that come from the compact API output, rather than a synthetic placeholder assistant message that hides the compacted content.

## Problem statement

The current compaction flow already stores the compact API output as retained native history, but the extension then hides that output from the user by collapsing the affected native segment into one placeholder core message.

That placeholder message also owns the entire compacted native range through explicit `native_indices`, which means:

1. the returned native transcript is not shown to the user even though it could be rebuilt normally
2. native ownership becomes artificial rather than reflecting the rebuilt message structure
3. follow-up work that wants the compacted result visible has to undo extension-specific hiding behavior

The preferred direction is simpler:

1. keep the returned native messages as native history
2. run the normal `from_native_messages(...)` rebuild path on them
3. let the resulting core messages be visible as-is unless a narrow, justified adjustment is still needed

## Current behavior

### Core already rebuilds visible messages from returned native history

Relevant code:

- `core/python/agent_core/core.py:2331`
- `core/python/agent_core/core.py:2342`

Important behavior:

1. a session action returns full replacement `native_messages`
2. `_apply_session_action_result(...)` already calls `_rebuild_core_from_native(new_native_messages, config)`
3. so the basic rebuild machinery already exists and does not need a compaction-specific session model

### The compaction extension overrides that rebuild with a placeholder policy

Relevant code:

- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py:166`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py:190`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py:205`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py:242`

Important behavior:

1. the extension builds placeholder metadata that stores the hidden native segment
2. `from_native_messages(...)` scans for `compaction` items and replaces the covered native span with one synthetic assistant placeholder
3. `to_native_messages(...)` later expands that placeholder back into the stored native segment

This means the returned native messages are retained but intentionally hidden from the visible transcript.

### Current tests lock in the placeholder transcript

Relevant tests:

- `plugins/openai_responses/tests/test_openai_responses_native_compaction_extension_unit.py:160`
- `plugins/openai_responses/tests/test_openai_responses_native_compaction_extension_unit.py:221`
- `plugins/openai_responses/tests/test_openai_responses_native_compaction_extension_unit.py:252`
- `plugins/openai_responses/tests/test_openai_responses_native_compaction_extension_unit.py:324`

Important behavior:

1. the tests explicitly expect `Earlier conversation compacted to reduce context size.` as the visible transcript after compaction
2. they also expect the placeholder message to own the compacted native indices
3. follow-up request tests verify that the hidden placeholder is expanded back to native compaction items on the next request

Those tests should be replaced with expectations that match direct rebuild from the returned native messages.

## Desired behavior

1. `execute_action(...)` continues returning the compact API output as full replacement `native_messages`
2. core rebuilds visible messages from that native list through the normal provider and extension `from_native_messages(...)` chain
3. the compaction extension does not collapse the compacted region into a single placeholder by default
4. rebuilt core messages carry natural `native_indices` derived from the normal conversion pipeline, instead of one synthetic message owning the whole compacted span
5. follow-up requests continue to work using the retained compacted native history without any placeholder round-trip requirement

## Suggested implementation direction

1. Remove or substantially narrow the placeholder-specific `from_native_messages(...)` and `to_native_messages(...)` behavior in `OpenAIResponsesNativeCompactionExtension`.
2. Let the provider's normal `from_native_messages(...)` handling rebuild visible messages from the compact API output.
3. Keep extension-layer transformation only if there is a concrete native item type from compact output that still needs a small readability adjustment.
4. Update any docs/tests that currently present the placeholder transcript as intentional product behavior.

## Open questions

1. If the compact API returns preserved instruction messages such as `system` or `developer`, how should they appear in visible core history with the current core role model?
2. Are there compact API native item shapes that the provider currently does not surface well enough without one narrow extension-layer assist?
3. Should a placeholder remain available as an optional UX mode later, or should direct visible rebuild become the only behavior?

## Test plan

Add or update tests before implementation so the new visible behavior is explicit.

### Test group A: direct visible rebuild after compaction

Update the main compaction unit test so that after compaction:

1. visible messages match the compact API output after normal native-to-core conversion
2. no synthetic placeholder message is inserted by default
3. retained native history still contains the returned compacted native items

### Test group B: natural native index ownership

Add assertions showing that:

1. rebuilt visible messages each own their normal `native_indices`
2. there is no single synthetic message with `native_indices` spanning the whole compacted region

### Test group C: follow-up request continuity without placeholder round-trip

Update follow-up request tests so they verify:

1. a post-compaction request still succeeds
2. the next request uses retained compacted native items directly
3. the request path no longer depends on placeholder expansion back into native history

### Test group D: partial/prefix compaction

For prefix-slice compaction, verify that:

1. the compacted prefix rebuilds visibly from returned native output
2. the uncompacted suffix remains visible as normal messages
3. follow-up requests continue to work with the mixed compacted + uncompacted native history

## Likely files to touch

1. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py`
2. `plugins/openai_responses/tests/test_openai_responses_native_compaction_extension_unit.py`
3. Potentially `plugins/openai_responses/tests/test_openai_responses_native_compaction_integration.py` if integration expectations currently assume placeholder behavior
4. Potentially `plugins/openai_responses/README.md` if the docs currently describe the placeholder transcript as intended behavior

## Definition of done

1. Native compaction keeps the compact API output as retained native history.
2. The visible transcript after compaction is rebuilt from that native output through the normal conversion pipeline.
3. The compacted transcript is no longer hidden behind a single placeholder message by default.
4. Follow-up requests still work after both full and partial compaction.

## Completion Notes

Added during completion:

1. Removed the placeholder-focused `from_native_messages(...)` / `to_native_messages(...)` behavior from `OpenAIResponsesNativeCompactionExtension`.
2. Native compaction now returns retained compacted native history directly and lets the normal provider rebuild path surface visible messages from that native output.
3. Updated the compaction unit tests so visible results are asserted against rebuilt native output rather than the old placeholder transcript.
4. Updated integration expectations to verify retained native compaction artifacts and follow-up request continuity without placeholder round-trip behavior.
5. Updated `plugins/openai_responses/README.md` so the docs match the new direct visible rebuild behavior.

Verification run during completion:

- `python -m pytest plugins/openai_responses/tests/test_openai_responses_native_compaction_extension_unit.py -q`
- `python -m pytest plugins/openai_responses/tests/test_openai_responses_imports.py -q`
- `python -m pytest plugins/openai_responses/tests/test_openai_responses_native_compaction_integration.py --collect-only -q`

Notes:

- The real OpenAI integration compaction tests were updated to the new expectations, but only collected in this completion step rather than executed live.