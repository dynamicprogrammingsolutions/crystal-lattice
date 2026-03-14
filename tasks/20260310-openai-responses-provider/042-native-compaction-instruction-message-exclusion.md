# Native Message Preparation Hook For Compaction

Short description: Add a generic core-owned lifecycle/preparation hook that lets provider extensions and features intercept and rewrite a native message array for a specific action context, then use that mechanism to make `openai_responses` native compaction work correctly with replaceable plugins such as `feature-system-message`.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On:
- `tasks/20260310-openai-responses-provider/041-system-message-rendering-and-developer-role-followup.md`
- `tasks/20260310-openai-responses-provider/070-usage-extension-responses-api.md`
- `tasks/20260310-openai-responses-provider/095-native-compaction-provider-extension.md`

## Status note

This task's original broad scope has since been split into narrower follow-ups:

1. `tasks/20260310-openai-responses-provider/043-native-message-preparation-for-compaction.md`
2. `tasks/20260310-openai-responses-provider/044-visible-rebuild-from-compacted-native-output.md`
3. `tasks/20260310-openai-responses-provider/046-manual-range-selection-native-compaction.md`
4. `tasks/20260310-openai-responses-provider/047-auto-compaction-after-request-complete.md`

This file remains as the broader design umbrella and rationale reference for those splits.

## Goal

Native compaction should not need to know about `SystemMessageFeature` or any other specific plugin.

Instead, the framework should provide a generic way for plugins to say:

1. “When a caller is about to use this native message array for purpose X, let me prepare or rewrite it.”
2. “Here is the transformed native message array for that purpose.”

`openai_responses` native compaction will be the first concrete user of that capability, but the design should remain generic so other actions and future providers can use the same mechanism.

## Problem statement

Today, native compaction works directly from the retained native history supplied to a session action. That bypasses the request-preparation path where plugins like `feature-system-message` perform context-sensitive rendering.

For the motivating example:

1. `SystemMessageFeature` keeps template text such as `{{VARIABLES}}` in retained native history.
2. It renders those variables only during request initialization.
3. Native compaction does not run through that preparation path.
4. As a result, compaction can operate on stale template-form messages instead of the prepared native messages that a real request would send.

The important requirement is not “make compaction call `SystemMessageFeature`.”

The requirement is “give plugins a replaceable, decoupled way to prepare native messages for compaction and similar action contexts.”

## Current code path and why it is insufficient

### Session actions receive retained native history directly

Relevant code:

- `core/python/agent_core/core.py:2266`
- `core/python/agent_core/core.py:2367`

Important behavior:

1. `AgentCore.execute_session_action(...)` resolves the current session action.
2. It gets retained native history through `_native_messages_for_session_action(...)`.
3. It passes that native message list directly into the selected extension/feature action.

There is currently no intermediate generic “prepare this native array for purpose X” phase.

### The compaction extension compacts that array directly

Relevant code:

- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py:385`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py:410`

Important behavior:

1. `OpenAIResponsesNativeCompactionExtension.execute_action(...)` slices the retained native prefix.
2. It sanitizes those native items.
3. It sends them directly to `client.responses.compact(...)`.

That means compaction sees retained native history as-is, not a plugin-prepared view of that history.

### `SystemMessageFeature` prepares outbound request messages, not retained native history

Relevant code:

- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:370`
- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:377`
- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:487`
- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:530`

Important behavior:

1. `from_native_messages(...)` is a no-op.
2. `initialize_request(...)` inserts any needed structural system message into the native request list.
3. It renders the template into `state["request"]["messages"]` for the outbound request only.
4. Retained native history still carries template-form content.

This is valid request behavior, but it means session actions cannot currently reuse the same preparation logic in a generic way.

### The action model already supports dynamic lifecycle names

Relevant docs/code:

- `plugins/docs/actions.md:37`
- `plugins/docs/actions.md:52`
- `core/python/agent_core/core.py:2428`

Important behavior:

1. Lifecycle names are already dynamic strings.
2. Actions can declare arbitrary `trigger` values.
3. `AgentCore.execute_lifecycle_actions(...)` already executes matching extension/feature actions for a named trigger.

This existing design is a good foundation for a generic native-message preparation mechanism.

## Proposed direction

Implement a generic arbitrary lifecycle / preparation hook in core.

The intended shape is:

1. A caller such as native compaction asks core to prepare a native message list for a named purpose.
2. Core executes matching provider-extension and feature actions for that lifecycle/purpose.
3. Those plugins can return a rewritten native message array and optional extra context.
4. The caller receives the prepared native message array and continues its own work.

The compaction extension should depend only on that generic facility. It should not import or special-case `SystemMessageFeature`.

## Architectural constraints

1. Keep plugin replaceability intact. Compaction must not become tied to one feature plugin by name.
2. Keep ownership in core for dispatch and sequencing, not in the compaction extension.
3. Reuse the existing action/lifecycle model where possible instead of inventing a compaction-only hook.
4. Avoid requiring plugins to be implemented in the same language. Future same-language conveniences may pass richer objects in context, but that should not be required for the first version.
5. The minimum useful contract for the first version is the ability to transform a native message array plus receive serializable context.

## Recommended design shape

### Stage 1: generic native-message preparation lifecycle

Add a core capability for preparing native messages for an arbitrary lifecycle-like purpose.

Possible shape:

1. A new `AgentCore` helper dedicated to native-message preparation.
2. Or a careful extension of the existing lifecycle action execution path so a caller can pass:
   - a lifecycle name such as `native_prepare:compact_native_history`
   - the current session
   - the effective config
   - the current native message array
   - optional serializable context describing the caller and requested range
3. Matching extension/feature actions can return a new native message array to be used by the caller.

The key design requirement is that the caller receives prepared native messages without forcing a full session mutation/rebuild cycle when the caller only needs a transformed working set.

### Stage 1 consumer: native compaction uses the generic preparation hook

Once the generic hook exists:

1. The compaction extension asks core to prepare native messages for compaction before slicing/sanitizing the compact input.
2. The preparation context should be rich enough for cooperating plugins to know the purpose, for example:
   - `{"purpose": "compact_native_history"}`
   - requested visible range or resolved native prefix end
   - action id and plugin id
3. `SystemMessageFeature` can then opt in by declaring the relevant lifecycle/action and rewriting the native message array for that context.
4. Other plugins can also participate later without any compaction-specific coupling.

### Stage 2: user-facing native compaction UX

After the generic preparation path works:

1. Keep or improve the compaction action UI so the user can choose a range in the same flavor as `summarize_range`.
2. If provider behavior still only supports prefix compaction, keep that restriction explicit in validation.
3. Add a message action for “compact up to here” if the provider-extension message-action path works cleanly.

This UX stage should sit on top of the new generic preparation path, not replace it.

### Optional Stage 3: auto-compaction after requests

After manual compaction is correct:

1. Use the same lifecycle/action model for `request_complete`.
2. Trigger compaction automatically when usage crosses a configured threshold.
3. Keep this optional stage separate from the core preparation-hook milestone.

## Why this is preferable to action chaining

An alternative idea is to let one action request execution of another action and then re-run with returned context.

That is not the recommended first implementation.

Reasons:

1. It introduces recursive or multi-step action semantics where simple lifecycle dispatch is likely enough.
2. It makes action execution harder to reason about and test.
3. It risks coupling plugins through action names rather than through a generic lifecycle contract.
4. The existing action model already supports arbitrary triggers, which is a cleaner fit.

Action chaining can remain a future option if the lifecycle/preparation approach proves insufficient.

## Expected behavior after Stage 1

1. A caller can ask core to prepare a native message array for an arbitrary purpose.
2. Plugins can intercept that preparation using normal action definitions with a named trigger or equivalent generic hook.
3. The compaction extension receives prepared native messages without knowing which plugins participated.
4. `feature-system-message` can supply rendered/initialized native messages for compaction through the generic mechanism rather than through direct plugin coupling.

## Implementation questions to resolve

1. Should the new core API return only `native_messages`, or also a public/internal result bundle with extra context from participating plugins?
2. Should preparation actions be allowed to mutate the session, or should this new path be explicitly non-persisting and limited to returning a working native message array?
3. Should the mechanism be a brand-new helper, or an extension of `execute_lifecycle_actions(...)` with a mode that avoids rebuilding and saving the session?
4. What trigger naming convention is best for this family of hooks, for example `native_prepare:compact_native_history` or `action_prepare:openai_responses_native_compaction.compact_native_history`?
5. How much caller context is safe and useful to pass in the first version?

## Test plan

Add tests before implementation so the generic contract is locked in clearly.

### Test group A: generic native-message preparation hook

Add core-level tests proving that:

1. a caller can request native-message preparation for an arbitrary lifecycle/purpose name
2. matching provider-extension and/or feature actions run in the expected order
3. a plugin can return a transformed native message array
4. the caller receives the transformed array without needing to persist a rebuilt session

Use a small dummy extension/feature rather than OpenAI-specific fixtures for the base contract.

### Test group B: compaction uses prepared native messages

Add or update `openai_responses` unit tests proving that:

1. the compaction extension invokes the generic preparation mechanism before compacting
2. the compact API input reflects the prepared native message array, not the raw retained native history
3. the compaction extension remains unaware of any specific cooperating plugin implementation

### Test group C: motivating system-message case

Add a focused regression for the motivating example:

1. configure a template-based system-message feature using `{{VARIABLES}}`
2. retain template-form native history in the session
3. run compaction
4. assert the compact input reflects the prepared/rendered native messages that the feature provided through the generic hook

This test should validate decoupling by asserting on behavior, not by making the compaction extension import or reference `SystemMessageFeature` directly.

### Test group D: range/message action UX

If Stage 2 is implemented in the same change, add coverage for:

1. summarize-range-style range parsing
2. prefix-only validation when the effective range is not compactable
3. provider-extension message-action UI schema and execution path

### Test group E: optional request-complete auto-compaction

Only if Stage 3 is implemented:

1. lifecycle-triggered compaction below threshold does nothing
2. lifecycle-triggered compaction above threshold rewrites native history
3. the threshold decision uses usage metadata supplied by the existing usage path

## Likely files to touch

1. `core/python/agent_core/core.py`
2. `core/python/agent_core/types.py`
3. `plugins/docs/actions.md`
4. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py`
5. `plugins/feature-system-message/src/feature_system_message/system_message_feature.py`
6. `core/python/tests/test_provider_extension_session_actions.py`
7. `application/python/tests/test_provider_extension_session_actions_endpoints.py`
8. `plugins/openai_responses/tests/test_openai_responses_native_compaction_extension_unit.py`
9. Additional focused dummy-plugin tests if needed under `core/python/tests/fixtures` or adjacent test helpers

## Definition of done

1. Core exposes a generic arbitrary lifecycle/preparation path for native message arrays.
2. Plugins can participate in that path without direct knowledge of one another.
3. `openai_responses` native compaction uses the generic preparation path rather than raw retained native history.
4. The motivating system-message rendering case is covered by regression tests through the generic mechanism.
5. If later stages are implemented, they build on the same generic preparation design rather than bypassing it.