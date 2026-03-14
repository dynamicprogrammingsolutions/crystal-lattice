# Auto-Compaction After Request Complete

Short description: Add an automatic native-compaction path that runs only after a request has fully completed and the resulting session has already been saved, using a dedicated post-request lifecycle/action flow rather than folding compaction into the request execution path itself.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On:
- `tasks/20260310-openai-responses-provider/043-native-message-preparation-for-compaction.md`
- `tasks/20260310-openai-responses-provider/044-visible-rebuild-from-compacted-native-output.md`
- `tasks/20260310-openai-responses-provider/070-usage-extension-responses-api.md`
- `tasks/20260310-openai-responses-provider/095-native-compaction-provider-extension.md`

Related:
- `tasks/20260310-openai-responses-provider/042-native-compaction-instruction-message-exclusion.md`

## Goal

Provide an automatic compaction mechanism that can run after a successful request is fully finished and the updated session has already been persisted.

The compaction logic should still execute through a separate action-like path rather than being embedded directly in the request flow. The new lifecycle should therefore act as a trigger for a normal compaction action consumer, not as a custom one-off compaction implementation.

## Problem statement

Native compaction currently exists only as a manual action.

That is useful, but it leaves no framework-supported way to compact automatically after a request when history or token usage grows past a configured threshold.

This automation should not happen in the middle of the live request flow because:

1. request execution should finish and save normally first
2. post-request compaction is a second concern and should be observable as a separate action/lifecycle step
3. future consumers may also want post-save session actions that act on the completed request result rather than the in-flight request state

## Required outcome

1. Add a dedicated lifecycle or dispatch point that runs only after a successful request has completed and the session has already been saved.
2. That lifecycle must be action-oriented: it should be able to trigger a separate compaction action consumer rather than embedding compaction logic directly into request completion.
3. `openai_responses` native compaction must be invokable through that lifecycle using normal action semantics.
4. Auto-compaction decisions should be configurable and should be able to use request usage/history information.
5. The post-request auto-compaction path must preserve follow-up request validity and visible transcript rebuild behavior.

## Scope notes

1. Manual compaction UX belongs to `046` and is out of scope here.
2. Pre-action native-message preparation belongs to `043` and should be reused if the compaction action needs it.
3. Visible transcript rebuild after compaction belongs to `044` and should be preserved here.
4. The new lifecycle should occur after persistence, not merely after model response generation.

## Suggested implementation direction

1. Add a post-request-saved lifecycle owned by `AgentApplication`.
2. Pass serializable context describing the completed request, saved session id, and relevant usage/history metadata.
3. Let plugins opt into that lifecycle and return an instruction to run a session action, or otherwise route through the same generic action execution path rather than hardcoding compaction in the request flow.
4. Implement `openai_responses` auto-compaction as the first consumer of that lifecycle.
5. Persist any resulting compacted session as a second, explicit mutation after the normal request save.

## Policy questions to resolve during implementation

1. What config shape should control auto-compaction: usage threshold, message-count threshold, explicit enable flag, or a combination?
2. Should auto-compaction run synchronously in the request path after save, or as a clearly sequenced second synchronous step before the request API returns?
3. What should happen if auto-compaction fails after the request itself already succeeded and was saved?
4. Should the lifecycle be named specifically for post-save request completion, or should it be a more general post-persist action hook that future features can reuse?

## Test plan

### Test group A: lifecycle timing

Add application-level tests proving that:

1. the new lifecycle runs only after the successful request result has been saved
2. the lifecycle is not fired before persistence
3. the lifecycle can trigger a separate session action rather than directly mutating request execution state

### Test group B: threshold behavior

Add tests proving that:

1. below-threshold requests do not compact automatically
2. above-threshold requests trigger auto-compaction
3. the threshold decision can use the intended usage/history metadata

### Test group C: request continuity after auto-compaction

Add unit and/or integration coverage proving that:

1. the request succeeds normally
2. the subsequent auto-compaction step also succeeds when enabled
3. a later follow-up request still works on the compacted session

### Test group D: failure handling

Add tests proving the intended failure policy if auto-compaction fails after request save, for example:

1. the completed request remains saved and visible
2. the compaction failure is surfaced in a controlled way
3. session integrity is not corrupted by a partially applied post-save action

## Likely files to touch

1. `core/python/agent_app/application_future.py`
2. potentially `core/python/agent_core/core.py` and `core/python/agent_core/types.py` if new lifecycle/action plumbing is needed
3. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py`
4. app-layer tests under `application/python/tests/` or `core/python/tests/`
5. `plugins/openai_responses/tests/test_openai_responses_native_compaction_integration.py` or a dedicated auto-compaction test file

## Definition of done

1. A successful saved request can trigger a separate auto-compaction action path afterwards.
2. Auto-compaction is configurable and threshold-driven.
3. The request result and the compaction step remain distinct in behavior and error handling.
4. Follow-up requests still work after auto-compaction.