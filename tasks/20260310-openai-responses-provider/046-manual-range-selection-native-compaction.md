# Manual Range Selection For Native Compaction

Short description: Add user-facing manual range selection for `openai_responses` native compaction in the same general interaction style as `summarize_range`, while also adding a simple `compact up to here` UI path and real integration coverage to verify whether non-prefix compaction is truly supported by the provider.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On:
- `tasks/20260310-openai-responses-provider/043-native-message-preparation-for-compaction.md`
- `tasks/20260310-openai-responses-provider/044-visible-rebuild-from-compacted-native-output.md`
- `tasks/20260310-openai-responses-provider/095-native-compaction-provider-extension.md`

Related:
- `tasks/20260310-openai-responses-provider/042-native-compaction-instruction-message-exclusion.md`

## Goal

Let users trigger native compaction for a selected visible range in a workflow similar to the existing summarize-range experience.

Assume for this task that non-prefix compaction may be supported by the underlying provider. The implementation should therefore aim to support arbitrary visible ranges, not prematurely constrain the feature to prefixes only.

At the same time, add a convenient `compact up to here` message action because that prefix workflow remains useful even if arbitrary ranges work.

## Problem statement

Today, native compaction is exposed primarily as a session action that accepts an optional end index representing a prefix slice.

That leaves two gaps:

1. users do not have a summarize-range-style way to select an arbitrary visible range for compaction
2. the product currently assumes prefix compaction operationally, but we do not yet have a real integration test proving whether the OpenAI compact API actually forbids non-prefix ranges or can support them if we shape native input/output correctly

We should not encode a prefix-only product assumption unless the real provider behavior proves that limitation.

## Required outcome

1. Add a range-selection UX for native compaction using the same general interaction style as `summarize_range`.
2. Add a `compact up to here` message action as a convenience path for prefix compaction.
3. Extend the compaction action contract so a caller can request at least `start_index` and `end_index` over visible messages, or another equivalent explicit range shape.
4. Translate the selected visible range into the appropriate provider-native compaction request.
5. Add real OpenAI integration coverage that attempts non-prefix compaction and records the actual provider behavior.
6. If the provider rejects non-prefix compaction, keep that limitation explicit in validation and docs rather than silently degrading behavior.

## Scope notes

1. This task is about manual user-triggered compaction selection only.
2. The pre-action native-message preparation path belongs to `043` and should be reused here.
3. Visible transcript rebuilding after compaction belongs to `044` and should be preserved here.
4. Auto-compaction belongs to `047` and is out of scope for this task.

## Suggested implementation direction

1. Extend the `openai_responses` native compaction action to accept an explicit visible range rather than only a prefix end.
2. Add UI schema and backend wiring so the user can choose a range in the same overall style as `summarize_range`.
3. Also add a message action that maps naturally to `compact up to here` for the common prefix case.
4. Resolve the selected visible range to the corresponding provider-native range.
5. If the compact API can compact arbitrary subranges, keep the returned mixed native history coherent and rebuild visible messages normally.
6. If the compact API only supports prefixes, detect that through integration behavior and make the restriction explicit in the action validation and user-facing messaging.

## Open questions to resolve during implementation

1. What exact action param shape is best for manual compaction: `start_index` + `end_index`, a summarize-range string, or another explicit range object?
2. If non-prefix compaction works, should the resulting compacted native output replace only the selected native span while preserving both prefix and suffix around it?
3. If non-prefix compaction fails at the provider layer, should the summarize-range-style UI still be shown with clear rejection for unsupported shapes, or should the UI be narrowed after confirmation?

## Test plan

### Test group A: manual range selection UX

Add UI/action tests proving that:

1. a user can invoke native compaction with an explicit visible range using the same general interaction style as `summarize_range`
2. a `compact up to here` message action is exposed and routes to the same underlying compaction action

### Test group B: visible-range to native-range mapping

Add unit coverage proving that:

1. the selected visible range is translated into the intended native range
2. mixed message/native index ownership still resolves correctly when the chosen range cuts across rebuilt message boundaries

### Test group C: real provider behavior for non-prefix compaction

Add an OpenAI integration test that:

1. creates a session with enough history for a middle-range compaction attempt
2. requests compaction for a non-prefix visible range
3. records whether the request succeeds or fails with a provider limitation
4. if it fails, keeps that failure visible in the task outcome and converts it into explicit product validation rather than assuming support silently

### Test group D: prefix convenience path

Add tests proving that:

1. `compact up to here` works for a prefix selection
2. the resulting session remains valid for a follow-up turn

## Likely files to touch

1. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py`
2. provider-extension UI schema wiring and any relevant frontend/backend action routing
3. `plugins/openai_responses/tests/test_openai_responses_native_compaction_extension_unit.py`
4. `plugins/openai_responses/tests/test_openai_responses_native_compaction_integration.py`
5. potentially app/server endpoint tests covering session and message actions

## Definition of done

1. Users can trigger native compaction for a selected visible range manually.
2. A `compact up to here` action is available.
3. Real integration coverage makes non-prefix support or limitation explicit.
4. Any provider limitation discovered by integration tests is reflected clearly in validation and behavior.