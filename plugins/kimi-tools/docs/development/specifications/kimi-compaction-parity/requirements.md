# Kimi compaction parity requirements

These requirements track the live implementation of the
[Kimi compaction parity specification](index.md).

Stable IDs follow the `KCP-NNN` convention. Implementation values use
`Not started`, `In progress`, `Implemented`, `Deferred`, or `Removed`.
Verification values use `Unverified`, `Automated`, `Human verified`, or
`Not applicable`. Documentation values use `Pending`, `Documented`, or
`Not applicable`.

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| KCP-001 | The compaction request session contains exactly two messages: a `system` message with `"You are a helpful assistant that compacts conversation context."` and a single synthetic `user` message built from the compactable range. | Implemented | Automated | Documented | `build_kimi_compaction_request_session` in `kimi_compaction_feature.py`; `TestBuildKimiCompactionRequestSession::test_request_session_has_generic_compactor_system_prompt` |
| KCP-002 | The synthetic user message flattens each selected prefix message into `## Message N\nRole: <role>\nContent:\n<text>` blocks in order, including a selected leading agent system message, with the compaction prompt appended at the end. The leading system message remains preserved in the final platform session. | Implemented | Automated | Documented | `TestBuildKimiCompactionRequestSession::test_synthetic_message_uses_message_n_block_format`, `test_synthetic_message_appends_prompt_at_end`, `test_leading_system_message_is_in_request_but_preserved_in_session` |
| KCP-003 | Only text content is included in the synthetic compaction message. Structured tool-call/tool-result payloads, media parts, and think parts are dropped; textual content from any role is retained. | Implemented | Automated | Documented | `TestBuildKimiCompactionRequestSession::test_text_only_filtering_drops_media_and_think_parts`, `test_text_tool_message_keeps_text_but_drops_structured_result` |
| KCP-004 | The merged compaction request config sets `disable_all_tools: True` after applying configurable request overrides, so `settings_overrides` cannot re-enable tools. | Implemented | Automated | Documented | `_merge_request_config` in `kimi_compaction_feature.py`; `TestMergeRequestConfig::test_disable_all_tools_set_unconditionally`, `test_settings_overrides_cannot_reenable_tools`, `test_compaction_model_takes_precedence_over_settings_overrides_model` |
| KCP-005 | When no explicit `end` is supplied, the last `max_preserved_messages` user/assistant messages (default 2) are preserved verbatim and excluded from the synthetic compaction message. A value less than or equal to zero returns a no-op, matching `SimpleCompaction.prepare`. | Implemented | Automated | Documented | `TestBuildKimiCompactionRequestSession::test_preserved_tail_with_default_max_preserved_messages`, `test_custom_max_preserved_messages`, `test_nonpositive_max_preserved_messages_is_noop_like_kimi_cli` |
| KCP-006 | When fewer than `max_preserved_messages` user/assistant messages exist in the compactable range, the action returns a no-op result instead of forcing compaction. | Implemented | Automated | Documented | `TestBuildKimiCompactionRequestSession::test_noop_when_too_few_user_assistant_messages`, `test_noop_when_only_preserved_messages_exist`; `TestKimiCompactionFeature::test_execute_action_returns_noop_when_only_preserved_tail_exists` |
| KCP-007 | When an explicit `end` is supplied, preserved-tail does not apply and the selected range is compacted exactly. | Implemented | Automated | Documented | `TestBuildKimiCompactionRequestSession::test_explicit_end_compacts_exactly_selected_range` |
| KCP-008 | The compacted session's summary user message wraps the prefix as `<system>Previous context has been compacted. Here is the compaction output:</system>` followed by the summary body. | Implemented | Automated | Documented | `build_compact_summary_text` in `kimi_compaction_feature.py`; `TestBuildCompactSummaryText::test_wraps_prefix_with_system_tags`, `test_summary_body_follows_system_prefix_on_new_line` |
| KCP-009 | No assistant acknowledgment message and no Claude-style `local-command-caveat` artifact is added to the compacted session. | Implemented | Automated | Documented | `build_compacted_session` inserts exactly one user summary message; `TestBuildCompactedSession` asserts no extra assistant message |
| KCP-010 | The compaction prompt body matches `kimi-cli/src/kimi_cli/prompts/compact.md` exactly, without the local "CRITICAL: TEXT ONLY" preamble or trailing "REMINDER" text. | Implemented | Automated | Documented | `_KIMI_COMPACTION_PROMPT` constant; self-contained pinned-hash test plus direct sibling-source comparison in `TestBuildCompactionPrompt` |
| KCP-011 | Custom instructions are appended to the compaction prompt in the same text block, matching `kimi-cli`'s custom-instruction handling. | Implemented | Automated | Documented | `TestBuildCompactionPrompt::test_custom_instructions_in_same_text_block` |
| KCP-012 | `get_ui_elements` returns `[]` when `config` is provided and `compaction.enabled` is not `true` or `compaction.type` is not `"kimi"`. | Implemented | Automated | Documented | `TestKimiCompactionFeature::test_feature_ui_elements_empty_when_compaction_disabled`, `test_feature_ui_elements_empty_when_type_not_kimi` |
| KCP-013 | `execute_action` returns an error with `type: "disabled"` when compaction is not enabled for the agent. | Implemented | Automated | Documented | `TestKimiCompactionFeature::test_execute_action_returns_disabled_when_compaction_not_enabled`, `test_execute_action_returns_disabled_when_type_not_kimi` |
| KCP-014 | `max_preserved_messages`, `compaction_model`, `prompt`, and `settings_overrides` are read from the agent's `compaction` config block. The top-level per-session `compaction_model` emitted by the configuration UI takes precedence over the agent model setting. | Implemented | Automated | Documented | `_get_compaction_config` and `_get_effective_compaction_config`; `TestGetCompactionConfig`; `TestGetEffectiveCompactionConfig` |
| KCP-015 | The Claude-shaped `build_compaction_session` and `build_compaction_request_session` helpers are removed; tests use the new `build_kimi_compaction_request_session` builder. | Implemented | Automated | Documented | `__all__` and module body of `kimi_compaction_feature.py`; `TestBuildKimiCompactionRequestSession` |
| KCP-016 | The module and class docstrings accurately describe the implemented behavior, including system-message inclusion, text-only semantics, unconditional tool suppression, and unstructured-response fallback. | Implemented | Automated | Documented | Source/doc consistency review; focused tests for each stated behavior |
| KCP-017 | The existing Ollama integration test continues to pass with the new request shape and enablement enforcement. | Implemented | Automated | Documented | `pytest plugins/kimi-tools/tests/test_kimi_compaction_feature_ollama_integration.py -m 'integration and not api and not slow_integration' -q` with a reachable Ollama endpoint |
| KCP-018 | Ruff and Black pass on the compaction implementation and its unit/Ollama tests. Package-wide unrelated pre-existing lint and formatting are not claimed as compaction verification. | Implemented | Automated | Documented | Focused `ruff check` and `black --check` commands listed in the follow-up task verification |
| KCP-019 | Current package-user documentation describes manual compaction, enablement, configuration, preserved-tail behavior, model override behavior, and response fallback. | Implemented | Automated | Documented | `plugins/kimi-tools/README.md`; source/doc consistency review against focused tests |
| KCP-020 | The generated default-configuration reference reflects enabled Kimi compaction in both default Kimi agents. | Implemented | Automated | Documented | `application/python/agent_terminal_app/default_config/config.json`; `docs/reference/default-config.md`; documentation build |

## Deferred requirements

| ID | Requirement | Reason | Revisit trigger | Owning work |
|---|---|---|---|---|
| KCP-D01 | Auto-compaction triggered by token thresholds matching `kimi-cli`'s `should_auto_compact` with `trigger_ratio=0.85` and `reserved_context_size=50_000`. | Cross-vendor lifecycle concern; this correction is manual-action parity only. | Task 222 implementation. | `tasks/20260315-gemini-qwen-grok-tool-packages/222-lifecycle-auto-compaction.md` |
| KCP-D02 | Checkpoint creation, context clear/rewrite, and estimated token-count update matching `kimi-cli`'s `compact_context`. | Platform has no checkpoint mechanism; cross-vendor concern. | Task 240 checkpoint/D-Mail portion. | `tasks/20260315-gemini-qwen-grok-tool-packages/240-kimi-compaction-and-checkpoints.md` |
| KCP-D03 | D-Mail checkpoint-revert tool. | Out of scope for compaction parity. | Task 240 checkpoint/D-Mail portion. | `tasks/20260315-gemini-qwen-grok-tool-packages/240-kimi-compaction-and-checkpoints.md` |

## Verification notes

The Ollama integration test sends an asset-ref-bearing tool message. Under
the new text-only filtering, the tool message's structured payload is dropped
from the synthetic compaction message. The test asserts that compaction
succeeds, not that the asset ref is preserved in the compaction request.
The follow-up verification reruns this test with a reachable Ollama endpoint.

The Ollama integration test is marked `integration`, `ollama`. It must be run
with those gates enabled and a reachable Ollama endpoint; a skipped run is
not verification.

Requirements intentionally omit helper-only parsing and internal state tests
that do not establish an additional user-facing or compatibility contract.

Package-wide Ruff and Black commands currently include unrelated legacy files
outside this compaction change. KCP-018 deliberately records only the focused
compaction boundary and does not represent those package-wide commands as
passing.