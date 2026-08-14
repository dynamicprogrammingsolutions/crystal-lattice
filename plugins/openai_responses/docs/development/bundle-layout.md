# Bundle layout

This page describes how the `openai_responses` bundle splits responsibilities
across its provider and extensions, and lists the implementation classes
registered by the bundle. It is intended for contributors extending or
debugging the package.

## Responsibility split

- **provider**: transport, SDK calls, Responses-native conversion, and native
  history replay.
- **attachments**: attachment upload policy/UI plus PDF composer UI.
- **tools**: tool schema injection and tool-call reconstruction.
- **reasoning**: reasoning request shaping and reasoning metadata.
- **usage**: usage formatting and pricing metadata.
- **verbosity**: `text.verbosity` request shaping.
- **prompt caching**: `prompt_cache_key` / retention request shaping and
  session-key lifecycle.
- **ChatGPT auth feature**: saved-credential loading plus `api` / `chatgpt` /
  `auto` auth-mode selection.
- **native compaction**: shared backend, application-owned background action
  and process, plus synchronous provider-extension compatibility adapter.

## Implementation classes

The bundle registers the following implementation classes:

- `openai_responses_plugins.openai_responses_provider.OpenAIResponsesProvider`
- `openai_responses_plugins.openai_responses_attachments_extension.OpenAIResponsesAttachmentsExtension`
- `openai_responses_plugins.openai_responses_chatgpt_auth_feature.OpenAIResponsesChatGPTAuthFeature`
- `openai_responses_plugins.openai_responses_flex_processing_extension.OpenAIResponsesFlexProcessingExtension`
- `openai_responses_plugins.openai_responses_fast_mode_extension.OpenAIResponsesFastModeExtension`
- `openai_responses_plugins.openai_responses_native_compaction_app.OpenAIResponsesNativeCompactionAppPlugin`
- `openai_responses_plugins.openai_responses_native_compaction_extension.OpenAIResponsesNativeCompactionExtension`
- `openai_responses_plugins.openai_responses_prompt_caching_extension.OpenAIResponsesPromptCachingExtension`
- `openai_responses_plugins.openai_responses_tools_extension.OpenAIResponsesToolsExtension`
- `openai_responses_plugins.openai_responses_reasoning_extension.OpenAIResponsesReasoningExtension`
- `openai_responses_plugins.openai_responses_usage_extension.OpenAIResponsesUsageExtension`
- `openai_responses_plugins.openai_responses_verbosity_extension.OpenAIResponsesVerbosityExtension`

## Native compaction implementation

Native compaction is implemented by:

- `openai_responses_native_compaction.py` for API and ChatGPT transports;
- `openai_responses_native_compaction_extension.py` for session-history
  selection, compaction application, and transcript rebuilding;
- `openai_responses_native_compaction_app.py` and
  `openai_responses_native_compaction_process.py` for the background action,
  cancellation, notifications, and reconciled persistence.

The native compaction protocol, compatibility, lifecycle, and verification
contract are defined in the
[native compaction specification](specifications/native-compaction/index.md).

## Native compaction behavior

Native compaction is meant for Responses-native context maintenance, not
transcript summarization.

- It can compact the full native history or a visible prefix.
- It uses the OpenAI Python SDK rather than application-layer summary logic.
- It uses `compaction_model` when configured, otherwise it uses the normal
  request `model`.
- It rebuilds visible messages after compaction directly from the compacted
  native output, whose visible assistant/user shape may vary by model.
- If `use_compaction_placeholder_transcript: true` is enabled, it instead
  shows the compacted region as a single placeholder message in the visible
  transcript while still preserving the underlying retained native compaction
  artifacts.
- Future requests continue from the compacted native history.

See the [native compaction product specification](specifications/native-compaction/product-spec.md)
for the target behavior and the
[technical specification](specifications/native-compaction/technical-spec.md)
for the protocol and implementation details.

## Background compaction notification handling

The background compaction process uses one stable notification key per session
rather than a per-operation key. Each heartbeat republishes the same stable
key through `create_session_notification`; the notification service applies
the update to the current active occurrence and increments revision internally.
The process does not pass `expected_revision` on producer updates and does not
retain or track the notification revision. The unique operation ID is kept in
the structured `operation.id` field and in the Cancel follow-up parameters so
the notification service can reject late updates from a superseded compaction
occurrence. If the user dismisses the progress banner, the next heartbeat
creates a new pending occurrence and the banner reappears; dismissing the
presentation does not cancel the underlying operation.

The progress banner is `dismissible: true` by default. The user can dismiss it
at any time; Cancel remains an explicit follow-up action for operation
cancellation. `dismissible: false` is not used for compaction progress because
a persistent notification must never become a dead end.

Ordinary requests and compaction use the same session operation admission.
Starting either while the other is active is rejected before provider work.

The process checks cancellation immediately before its reconciled session
save so a late result cannot be applied even if the HTTP cancellation arrives
after the provider call completes.

The successful notification requests `ui_effects.reload_session_ids` for the
compacted session, so connected frontends refresh a mounted transcript without
opening or navigating to another session. The invalidation remains pending for
inactive or later-mounted cache consumers until an authoritative reload
succeeds. Dismissing the completion notification does not repeat the reload.

The synchronous provider-extension compatibility action
(`compact_native_history_sync`) and the primary background action share the
same native compaction backend.

See the [notification specification](../../../../docs/development/specifications/notifications/index.md)
for the stable-key publication, revision-scoped dismissal, and durable
refresh invalidation contracts that the background compaction process relies
on.