# Core finalize/native processing correction plan

Goal
- Make finalize pipeline operate entirely on provider-native data (`final_messages` are provider-native deltas; `native_messages` is full provider-native history for the turn).
- Convert to core message format only after finalize pipeline completes.
- Persist the full provider-native `native_messages` onto the session (implementation detail) so the original provider-native history is retained across Core instances.
- Update pre-request to reuse retained provider-native history and append only the new- turn messages converted to native.

Changes
1) core/python/agent_core/core.py
   - send_request:
     - Keep `final_messages` from provider as native (`final_native_1`, `final_native_2`).
     - Merge to `final_native = final_native_1 + final_native_2`.
     - Run `feature.finalize(final_native, native_messages, state)` for each feature (still provider-native).
     - Convert once at the end via `provider.from_native_messages(final_native, state)` to obtain the final core messages.
     - Append final core messages to the session.
     - Save full provider-native `native_messages` to session metadata (implementation detail), and return `(new_session, final_core_messages)`.
   - send_request_stream/send_request_stream_async:
     - Aggregate streaming finals as provider-native deltas.
     - After streaming completes, run provider.finalize and feature.finalize (still provider-native).
     - Convert combined finals to core via provider.from_native_messages.
     - Append final core messages; save provider-native `native_messages` in the session metadata; yield final event with core messages.
   - _pre_request:
     - If session contains retained provider-native history, rebuild the input native messages as:
       - `base_native` = retained.
       - `base_core` = provider.from_native_messages(base_native, state).
       - If session core `messages` begins with `base_core`, take the suffix of new core messages and compute `suffix_native = provider.to_native_messages(suffix_core, state)`, then `native_messages = base_native + suffix_native`.
       - Else, fall back to the non-retained path using provider.to_native_messages(messages, state), then extension/feature stateless transforms.

2) core/python/agent_core/types.py (docstrings only)
   - Clarify finalize in ProviderPlugin, ProviderExtensionPlugin, FeaturePlugin:
     - `final_messages` are provider-native deltas (new messages only for this turn).
     - `native_messages` are full provider-native history (not deltas).
     - Conversion to core happens after finalize pipeline (outside these methods).
   - Fix stray incorrect docstring under BasePlugin.get_config_schema.

Tests
- New tests under core/python/tests/:
  1) test_native_retention_across_core_instances.py
     - Custom provider + provider extension:
       - Extension.finalize marks provider-native messages with `preserved: True`.
       - Provider.to_native_messages does not emit `preserved` when converting from core, causing lossy round-trip (so `to_native(from_native(native)) != native`).
       - Provider.finalize inspects baseline `native_messages` and emits final content `Preserved` if any `preserved: True` exists; else `Lost`.
     - Turn 1: send request, then reuse the same returned Session with a fresh Core for Turn 2.
     - Assert:
       - The round-trip inequality holds for the provider’s conversion functions.
       - Turn 2 final content is `Preserved` (proves retained native history was used by the new Core instance).

  2) test_conversion_hooks_used.py
     - Custom provider + extension + feature:
       - Provider.from_native_messages annotates core finals metadata (evidence of from_native being used).
       - Provider.to_native_messages annotates native user suffix (evidence of to_native being used); provider.finalize echoes a marker when it detects it.
       - Feature.finalize mutates native finals (e.g., prefix tag) before conversion; the effect must appear in returned core finals.
     - Assert:
       - Final core message metadata contains provider’s from_native marker.
       - Final core content contains the feature prefix and provider echo marker (shows native finalize + conversion was used).

Notes
- Existing providers where native equals core shape keep passing behaviorally; the ordering fix makes the pipeline robust for providers whose native shape differs from core.
- Tests do not assert specific metadata key names on the Session object; retention is validated behaviorally across Core instances. Metadata assertions are limited to per-message metadata produced by the custom test plugins.
