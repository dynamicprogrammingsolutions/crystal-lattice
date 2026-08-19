# Kimi compaction parity correction

Short description: Bring the manual `compact_conversation` action in `plugins/kimi-tools` into parity with `kimi-cli`'s `SimpleCompaction` for request shape, system prompt, tool suppression, preserved tail, summary injection format, prompt body, and enablement enforcement.

## Requirements checklist

- [x] Compaction request is a single synthetic `user` message built from `## Message N\nRole: <role>\nContent:\n<text>` blocks, with the compaction prompt appended at the end, matching `kimi-cli` `SimpleCompaction.prepare`.
- [x] Only text content is included in the synthetic compaction message; structured tool calls/results, media parts, and think parts are dropped.
- [x] The compaction request session's leading system message is `"You are a helpful assistant that compacts conversation context."`, not the agent's normal system message.
- [x] The merged compaction request config sets `disable_all_tools: True` unconditionally after configurable overrides.
- [x] When no explicit `end` is supplied, the last `max_preserved_messages` user/assistant messages (default 2) are preserved verbatim and excluded from the synthetic compaction message.
- [x] When fewer than `max_preserved_messages` user/assistant messages exist in the compactable range, the action returns a no-op result instead of forcing compaction with no preserved tail.
- [x] The compacted session's summary user message wraps the prefix as `<system>Previous context has been compacted. Here is the compaction output:</system>` followed by the summary body, matching `kimi-cli` `system(...)` wrapping.
- [x] The compaction prompt body matches `kimi-cli/src/kimi_cli/prompts/compact.md` exactly, without the local "CRITICAL: TEXT ONLY" preamble or trailing "REMINDER" text.
- [x] Custom instructions are appended to the compaction prompt in the same text block, matching `kimi-cli` `SimpleCompaction.prepare` custom-instruction handling.
- [x] `get_ui_elements` returns `[]` when `config` is provided and `compaction.enabled` is not `true` or `compaction.type` is not `"kimi"`.
- [x] `execute_action` returns an error with `type: "disabled"` when compaction is not enabled for the agent.
- [x] Agent compaction settings are read from the `compaction` block, and the session UI's top-level `compaction_model` override takes precedence.
- [x] Unit tests cover the synthetic-message builder, text-only filtering, preserved-tail behavior, tool suppression, model override, generic compactor system prompt, summary prefix, and enablement enforcement.
- [x] The existing Ollama integration test passes with the new request shape and enablement enforcement.
- [x] The module/class documentation accurately describes the implemented behavior.
- [x] The spec directory contains `index.md`, `product-spec.md`, `technical-spec.md`, and `requirements.md`, including intentional deviations.

## Scope

In scope: the manual `compact_conversation` and `compact_up_to_here` actions in `plugins/kimi-tools/src/kimi_tools/kimi_compaction_feature.py`, their unit tests, and the plugin's spec directory.

Out of scope: auto-compaction (tracked by task `20260315-gemini-qwen-grok-tool-packages/222-lifecycle-auto-compaction.md`), checkpoint/D-Mail behavior (tracked by task `20260315-gemini-qwen-grok-tool-packages/240-kimi-compaction-and-checkpoints.md`), and cross-vendor shared compaction helpers (task `250`).

## Resolved decisions

These were open questions in the investigation; the user approved the recommendations on 2026-08-16.

1. **Helper API backward compatibility.** Remove the Claude-shaped `build_compaction_session` and `build_compaction_request_session` helpers and rewrite the tests against the new Kimi-shaped builder. Keeping Claude-shaped helpers in a Kimi plugin invites future drift.
2. **Explicit-range vs. preserved tail.** Apply preserved-tail only when no explicit `end` is supplied. When `end` is supplied (including `compact_up_to_here`), compact exactly the selected range.
3. **`max_preserved_messages` config location.** Read it from `compaction.max_preserved_messages` via `_get_compaction_config`, default `2`.
4. **Auto-compaction scope.** Leave auto-compaction to task 222. This correction is manual-action parity only.
5. **Checkpoint/context rewrite.** Document the deviation in the spec page. Do not add a checkpoint mechanism or a Claude-style pre-compaction transcript snapshot in this correction.

## Supporting details

### Reference sources

All `kimi-cli` paths are relative to `../kimi-cli`, commit `7ba9695`.

- `src/kimi_cli/soul/compaction.py:56-72` — `should_auto_compact` threshold logic (out of scope here).
- `src/kimi_cli/soul/compaction.py:103-189` — `SimpleCompaction` with `prepare` and `compact`.
- `src/kimi_cli/soul/compaction.py:117-122` — `kosong.step` call with `system_prompt="You are a helpful assistant that compacts conversation context."` and `toolset=EmptyToolset()`.
- `src/kimi_cli/soul/compaction.py:130-139` — output injection with `system(...)` prefix and preserved tail.
- `src/kimi_cli/soul/message.py:19-20` — `system(message)` wraps as `<system>{message}</system>`.
- `src/kimi_cli/prompts/compact.md:1-74` — exact compaction prompt body.
- `src/kimi_cli/tests/core/test_simple_compaction.py:44-77` — upstream test confirming `## Message N` block format and preserved tail.
- `src/kimi_cli/config.py:81,85` — defaults `reserved_context_size=50_000`, `compaction_trigger_ratio=0.85` (auto-compaction, out of scope).

### Local implementation state

- `plugins/kimi-tools/src/kimi_tools/kimi_compaction_feature.py` — current implementation.
- `plugins/kimi-tools/tests/test_kimi_compaction_feature.py` — current unit tests.
- `plugins/kimi-tools/tests/test_kimi_compaction_feature_ollama_integration.py` — Ollama integration test; already sets `compaction.enabled: true` and `type: "kimi"`.
- `plugins/gemini-compaction-feature/src/gemini_compaction_feature/__init__.py:98-109,490,654-658,698-716` — Gemini reference for `disable_all_tools`, enablement enforcement, and `_get_compaction_config` pattern.
- `core/python/plugins/tool_gating_feature.py` — platform's `disable_all_tools` feature plugin.
- `application/python/agent_terminal_app/default_config/config.json` — the default
  `kimi` and `kimi-ollama` agents enable Kimi compaction.

### Confirmed parity gaps

Nine gaps were confirmed by direct source inspection on 2026-08-16:

1. Request shape is multi-turn (prompt appended to last user message), not a single synthetic user message.
2. `max_preserved_messages` is declared at `kimi_compaction_feature.py:133,516` but never read.
3. Tools are not disabled; `_merge_request_config` does not set `disable_all_tools`.
4. Summary prefix is plain text, not `<system>…</system>` wrapped.
5. Prompt has extra "CRITICAL: TEXT ONLY" preamble and trailing "REMINDER" not in `compact.md`.
6. Auto-compaction is absent (out of scope here).
7. Enablement docstring claims `enabled`/`type` gating but code never checks; default config has no `compaction` block.
8. Checkpoint/context rewrite not matched (out of scope here; documented deviation).
9. System prompt is the agent's normal one, not the generic compactor prompt.

### Historical task

Task `20260315-gemini-qwen-grok-tool-packages/240-kimi-compaction-and-checkpoints.md` is the original research-and-implementation task. It is left unchanged as a historical record. This correction task supersedes the manual-compaction portion of 240; the checkpoint/D-Mail portion of 240 remains open and separate.

## Execution plan

Status: Completed

### Approach

Rewrite the compaction request path in `kimi_compaction_feature.py` to follow `kimi-cli`'s `SimpleCompaction` structure, add enablement enforcement matching Gemini's pattern, and update the unit tests to assert the Kimi-faithful shape.

### New request builder

Add `build_kimi_compaction_request_session(session, *, prompt_text, start, end, end_inclusive, max_preserved_messages)` that returns `(request_session, compact_indices, preserved_indices)`:

1. Resolve the compactable range using the existing `_normalize_slice_bounds` and leading-system-message logic.
2. If no explicit `end` was supplied, scan backward from the end of the compactable range for the last `max_preserved_messages` messages with role `user` or `assistant`. If fewer than N are found, return a sentinel indicating no compaction is needed.
3. Build the synthetic user message content by iterating the compactable messages and emitting `## Message N\nRole: <role>\nContent:\n` followed by the message's text-only content for each.
4. Append `\n` + `prompt_text` at the end of the synthetic user message content.
5. Build the request session with exactly two messages: `system: "You are a helpful assistant that compacts conversation context."` and `user: <synthetic content>`.
6. Return the request session, the indices to remove from the original session, and the preserved-tail indices (empty when explicit `end` is supplied).

### Compacted session builder

Update `build_compacted_session` to:
1. Rebuild native history via `core.rebuild_native_history`.
2. Remove the compacted indices via `core.slice_session`.
3. Insert the summary user message (with `<system>…</system>` prefix) at the position of the first removed message.
4. Leave preserved-tail messages in place.

### Config merge

Update `_merge_request_config` to set `disable_all_tools: True` before applying `settings_overrides` and `compaction_model`.

### Enablement

Add `_is_compaction_enabled(base_config)` and `_get_compaction_config(base_config)` helpers matching Gemini's pattern. Read `max_preserved_messages` (default 2), `compaction_model`, `prompt`, and `settings_overrides` from the `compaction` config block. Gate `get_ui_elements` and `execute_action` on enablement when `config`/`base_config` is available.

### Prompt body

Replace `_KIMI_COMPACTION_PROMPT` with the exact content of `kimi-cli/src/kimi_cli/prompts/compact.md`. Keep `build_compaction_prompt`'s custom-instruction append behavior, matching `kimi-cli`'s custom-instruction block.

### Summary text

Change `build_compact_summary_text` to produce `<system>{_COMPACTION_PREFIX}</system>\n{cleaned}` in a single user message.

### Test updates

Rewrite `tests/test_kimi_compaction_feature.py`:
- Remove `TestBuildCompactionSession` and `TestBuildCompactionRequestSession` tests that assert the old multi-turn shape.
- Add `TestBuildKimiCompactionRequestSession` covering synthetic message format, text-only filtering, `## Message N` block format, prompt append, generic compactor system prompt, and preserved-tail boundary.
- Add tests for `disable_all_tools` in the merged config.
- Add tests for `<system>…</system>` prefix wrap in `build_compact_summary_text`.
- Add tests for enablement enforcement (UI empty when disabled; `error.type == "disabled"`).
- Update `TestBuildCompactedSession` to reflect the new summary shape and preserved-tail behavior.
- Keep `TestBuildCompactionPrompt`, `TestExtractSummaryText`, `TestExtractSummarySections`, `TestValidateSummaryText`, `TestBuildCompactSummaryText` (updated), and `TestPluginRegistration`.

### Implementation decisions and open questions

All five open questions from the investigation were resolved on 2026-08-16; see `## Resolved decisions` above. No unresolved questions remain.

### Documentation

- Update the class docstring in `kimi_compaction_feature.py` to describe the implemented behavior accurately.
- Create the spec directory `plugins/kimi-tools/docs/development/specifications/kimi-compaction-parity/` with `index.md`, `product-spec.md`, `technical-spec.md`, and `requirements.md`, following the documentation and specification standard. The five resolved decisions are recorded in `technical-spec.md` (no separate `decisions/` directory). The checkpoint/context-rewrite, auto-compaction, and D-Mail deviations are recorded in `technical-spec.md` and `requirements.md` (deferred requirements table).

### Task checklist

- [x] Replace `_KIMI_COMPACTION_PROMPT` with exact `compact.md` content.
- [x] Add `build_kimi_compaction_request_session` with synthetic single-user-message builder, text-only filtering, and preserved-tail logic.
- [x] Add generic compactor system prompt to the compaction request session.
- [x] Update `_merge_request_config` to set `disable_all_tools: True`.
- [x] Update `build_compact_summary_text` to wrap the prefix as `<system>…</system>`.
- [x] Update `build_compacted_session` to use the new builder and preserved-tail indices.
- [x] Add `_is_compaction_enabled` and `_get_compaction_config` helpers.
- [x] Gate `get_ui_elements` on enablement when `config` is provided.
- [x] Gate `execute_action` on enablement and return `error.type == "disabled"` when disabled.
- [x] Read `max_preserved_messages` from `compaction` config (default 2).
- [x] Remove `build_compaction_session` and `build_compaction_request_session`.
- [x] Update class docstring to match implemented behavior.
- [x] Rewrite unit tests for the new builder, preserved tail, `disable_all_tools`, generic system prompt, `<system>…</system>` prefix, and enablement.
- [x] Run focused compaction unit and Ollama integration tests.
- [x] Run focused Ruff and Black checks on the compaction implementation and tests. Package-wide unrelated hygiene is not represented as passing.
- [x] Create the spec directory at `plugins/kimi-tools/docs/development/specifications/kimi-compaction-parity/` with `index.md`, `product-spec.md`, `technical-spec.md`, and `requirements.md`.

### Requirement verification

- **Single synthetic user message**: unit test asserts the request session has exactly `[system, user]` and the user message contains `## Message 1\nRole: …\nContent:\n…` blocks.
- **Text-only filtering**: unit test with multipart content (text + image + think) asserts only text appears in the synthetic message.
- **Generic compactor system prompt**: unit test asserts the request session's system message equals `"You are a helpful assistant that compacts conversation context."`.
- **`disable_all_tools`**: unit test asserts the merged request config has `disable_all_tools is True`.
- **Preserved tail**: unit test with 5 user/assistant messages and default `max_preserved_messages=2` asserts the last 2 are preserved and not in the synthetic message.
- **No-op when too few**: unit test with 1 user/assistant message and `max_preserved_messages=2` asserts a no-op result.
- **`<system>…</system>` prefix**: unit test asserts `build_compact_summary_text` output starts with `<system>Previous context has been compacted. Here is the compaction output:</system>`.
- **Exact prompt body**: unit test asserts `build_compaction_prompt()` equals the content of `kimi-cli/src/kimi_cli/prompts/compact.md` (loaded from a fixture or compared to a constant copied verbatim).
- **Custom instructions**: unit test asserts custom instructions are appended in the same text block as the prompt.
- **Enablement UI gating**: unit test asserts `get_ui_elements(config={... disabled ...})` returns `[]`.
- **Enablement execute gating**: unit test asserts `execute_action` returns `error.type == "disabled"` when disabled.
- **Config reading**: unit test asserts `max_preserved_messages`, `compaction_model`, `prompt`, and `settings_overrides` are read from the `compaction` block.
- **Ollama integration**: `pytest plugins/kimi-tools/tests -m 'integration and not api and not slow_integration' -q` passes with the new shape.
- **Lint/format**: focused Ruff and Black checks cover the compaction
  implementation and tests; package-wide unrelated hygiene remains outside
  this correction.

## Approved follow-up: parity review corrections

Approval status: Approved by the user on 2026-08-18.

Execution status: Completed.

### Findings addressed

This follow-up corrects the completion-review findings without expanding into
auto-compaction, checkpoints, D-Mail, or shared cross-vendor compaction:

1. Include a selected leading agent system message in the numbered synthetic
   transcript, matching upstream `SimpleCompaction.prepare`, while preserving
   that system message in the final platform session.
2. Honor the existing top-level per-session `compaction_model` setting emitted
   by the configuration UI, with precedence over
   `compaction.compaction_model`.
3. Return a no-op for unbounded compaction when
   `max_preserved_messages <= 0`.
4. Apply `disable_all_tools: True` after request overrides so tools cannot be
   re-enabled.
5. Clarify that text content from tool-role messages is retained while
   structured tool payloads are dropped.
6. Add self-contained prompt-parity coverage that does not depend on a sibling
   checkout.
7. Update current package documentation, the specification, live
   requirements, generated default-config reference, and completion evidence.

### Follow-up requirements

- KCP-002, KCP-003, KCP-004, KCP-005, KCP-010, KCP-014, and KCP-016 are
  strengthened to capture the corrected contracts.
- KCP-018 records the truthful focused lint/format boundary.
- KCP-019 covers current package-user documentation.
- KCP-020 covers the generated default-configuration reference.

### Implementation checklist

- [x] Separate synthetic request inclusion from final-session deletion for the
  leading system message.
- [x] Resolve the session `compaction_model` override from effective request
  configuration.
- [x] Add zero-preservation no-op behavior.
- [x] Make tool suppression override-proof.
- [x] Add regression tests for all four behavior corrections and textual tool
  result semantics.
- [x] Pin the upstream prompt with a self-contained digest assertion while
  retaining the direct sibling comparison when available.
- [x] Update README, module documentation, specification, and requirements.
- [x] Refresh the generated default-config reference.
- [x] Run focused unit, Ollama, Ruff, Black, and documentation verification.

### Verification commands

```bash
pytest plugins/kimi-tools/tests/test_kimi_compaction_feature.py -q
pytest plugins/kimi-tools/tests/test_kimi_compaction_feature_ollama_integration.py -m 'integration and not api and not slow_integration' -q
ruff check plugins/kimi-tools/src/kimi_tools/kimi_compaction_feature.py plugins/kimi-tools/tests/test_kimi_compaction_feature.py plugins/kimi-tools/tests/test_kimi_compaction_feature_ollama_integration.py
black --check plugins/kimi-tools/src/kimi_tools/kimi_compaction_feature.py plugins/kimi-tools/tests/test_kimi_compaction_feature.py plugins/kimi-tools/tests/test_kimi_compaction_feature_ollama_integration.py
python docs_site/scripts/build_mkdocs_site.py
```

### Verification results

- Focused compaction unit tests: 83 passed.
- Gated Ollama integration: 1 passed against the reachable local endpoint.
- Focused Ruff: passed.
- Focused Black check: passed.
- Documentation preparation, MkDocs build, and committed reference refresh:
  passed. The build retained pre-existing navigation and API-reference
  warnings unrelated to this task.