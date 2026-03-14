# Native Message Preparation For Compaction

Short description: Add generic action lifecycles owned by `AgentApplication` that run automatically before and after actions, and use the pre-action lifecycle to prepare provider-native messages for `openai_responses` native compaction without mutating or persisting the session.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On:
- `tasks/20260310-openai-responses-provider/041-system-message-rendering-and-developer-role-followup.md`
- `tasks/20260310-openai-responses-provider/095-native-compaction-provider-extension.md`

Related:
- `tasks/20260310-openai-responses-provider/042-native-compaction-instruction-message-exclusion.md`

## Why this split exists

Task `042` captures a broader design discussion around a generic native-message preparation lifecycle.

For implementation, the approved scope is intentionally narrower:

1. solve the current compaction bug where retained native history may still contain unprepared instruction/template messages
2. keep the mechanism generic enough to avoid plugin-specific coupling
3. avoid turning this task into a larger framework redesign

## Goal

Make `compact_native_history` compact the same effective native instruction messages that a real outbound request would use, while keeping the solution generic and non-persisting.

The mechanism should not be a one-off helper called only by compaction. Instead, `AgentApplication` should provide generic action-scoped lifecycles that run automatically around actions so plugins can prepare action inputs before execution and react after completion.

The first motivating case is `feature-system-message`, where retained native history may store template-form instruction content such as `{{VARIABLES}}`, but request preparation renders concrete text only for the outbound request.

## Problem statement

Today, `AgentCore.execute_session_action(...)` resolves retained native history and passes it directly into the selected action.

That means `OpenAIResponsesNativeCompactionExtension.execute_action(...)` currently compacts raw retained native messages, not a prepared working set.

For `feature-system-message`, this can produce compact input based on:

1. templated instruction content rather than rendered content
2. instruction-role/native-request shaping that only happens during request preparation, not during session-action execution

## Required outcome

1. Add generic action lifecycles that `AgentApplication` executes automatically before and after actions.
2. The pre-action lifecycle must support non-persisting preparation of a working native message list plus serializable context for the selected action.
3. The post-action lifecycle must be available generically even if the first concrete motivating use is pre-action native preparation.
4. `openai_responses` native compaction must receive prepared native messages before slicing/sanitizing compact input.
5. `feature-system-message` must be able to participate through the generic mechanism so compaction sees rendered instruction messages.
6. The compaction extension must not import or special-case `SystemMessageFeature` by name.

## Approved scope

This task should include only the minimum framework surface needed to support native-message preparation for session-action purposes.

That means:

1. action lifecycles owned and triggered by `AgentApplication`
2. a pre-action path that can prepare native messages for a named action purpose without persisting session changes
3. a post-action lifecycle hook available for later consumers
4. compaction as the first pre-action consumer
5. regression coverage for the `feature-system-message` motivating case

## Explicitly out of scope

1. no new user-facing compaction UX or dialog redesign
2. no new message-action or range-selection workflow beyond what already exists
3. no auto-compaction on `request_complete`
4. no broad redesign of the full lifecycle/action framework unless the narrow helper proves impossible
5. no plugin-to-plugin coupling or compaction-specific knowledge inside `feature-system-message`
6. no work on improving the visible transcript representation of compacted native history; that should be handled as a separate follow-up task

## Design constraints

1. Keep ownership in core for dispatch/order and in plugins for transformation behavior.
2. Keep the contract serializable and language-neutral.
3. Avoid persisting any session mutations during preparation.
4. Prefer one shared preparation path that can be reused by future session actions, but do not over-generalize beyond this need.

## Suggested implementation shape

1. Add generic action lifecycle names owned by `AgentApplication`, for example an action-prepare and action-complete phase.
2. The pre-action lifecycle should pass serializable context such as action owner, plugin id, action id, selected params, and the current native message list when available.
3. `AgentCore` should expose the narrow execution support needed so matching features/provider extensions can transform the working native message list for that action context without persisting session mutations.
4. `AgentApplication` should invoke the pre-action lifecycle automatically before action execution and the post-action lifecycle automatically after action execution.
5. Update `OpenAIResponsesNativeCompactionExtension.execute_action(...)` to use the prepared native working set produced by that lifecycle.
6. Add the cooperating action/hook in `feature-system-message` so it can render instruction content for the compaction action context.

## Test plan

### Test group A: narrow core preparation contract

Add focused core tests proving that:

1. `AgentApplication` executes the new pre-action lifecycle automatically for an action
2. matching feature and/or provider-extension preparation logic runs in deterministic order
3. the preparation path returns a transformed working native list without rebuilding or persisting the session
4. the corresponding post-action lifecycle is also emitted around the same action path

Use simple dummy fixtures so the base contract is not OpenAI-specific.

### Test group B: compaction uses prepared working history

Add or update `openai_responses` tests proving that:

1. compaction receives prepared native messages through the new pre-action lifecycle before sending compact input to the SDK
2. the compact API input reflects the prepared instruction content, not the raw retained native history

### Test group C: motivating `feature-system-message` regression

Add a focused regression that:

1. retains template-form native instruction history
2. prepares native messages for compaction
3. asserts the compaction input uses rendered instruction content
4. proves the compaction extension remains decoupled from the specific feature implementation

## Likely files to touch

1. `core/python/agent_core/core.py`
2. `core/python/agent_core/types.py`
3. `core/python/agent_app/application_future.py`
4. `plugins/feature-system-message/src/feature_system_message/system_message_feature.py`
5. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py`
6. focused tests under `core/python/tests/`, `application/python/tests/`, and `plugins/openai_responses/tests/`

## Notes for follow-up tasking

The separate question of how compacted native segments should appear in visible `session.messages` is not part of this task.

That follow-up belongs in `tasks/20260310-openai-responses-provider/044-visible-rebuild-from-compacted-native-output.md`.