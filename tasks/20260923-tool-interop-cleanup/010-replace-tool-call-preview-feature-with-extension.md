# Replace ToolCallPreviewFeature with a tag-gated provider extension

Short description: Replace the `ToolCallPreviewFeature` feature plugin and the core-owned `response_finalize` lifecycle with a single provider extension gated by `required_tags() == ["supports_tools"]`, and move the preview formatting helper from `AgentCore` to `tool_interop.py`. Restore the pre-refactor always-on behavior where any provider emitting `supports_tools` gets tool-call previews without explicit config registration.

Parent Task: tasks/20260923-tool-interop-cleanup/000-main.md

## Requirements checklist

- [ ] Tool-call previews on `metadata.tool_call_previews` are produced by a single provider extension, not by `ToolCallPreviewFeature` or the `response_finalize` lifecycle.
- [ ] The extension is enabled automatically for any provider emitting `supports_tools` (no config registration required).
- [ ] Previews survive rebuild-from-native via the extension's `from_native_messages`, without persisting into native `_metadata`.
- [ ] The preview output shape is preserved: `[{"id": <call_id>, "preview": <str>}, ...]` on `metadata.tool_call_previews` for assistant messages with `metadata.tool_calls`.
- [ ] `core/python/plugins/tool_call_preview_feature.py` is removed.
- [ ] The `response_finalize` lifecycle and its executor are removed from `AgentCore` (pending Q1).
- [ ] `AgentCore.format_tool_call_preview`, `format_tool_call_previews`, and `patch_native_internal_metadata` are removed or relocated to `tool_interop.py` (pending Q2).
- [ ] Existing tests asserting preview behavior pass against the new implementation with the same output shape.
- [ ] Tests and fixtures referencing `response_finalize` only to exercise the lifecycle mechanism are updated or removed.

## Open requirement questions

**Q1 — Remove `response_finalize` entirely?**
The `response_finalize` lifecycle was introduced in commit `dceca8dfe` specifically for `ToolCallPreviewFeature`. Its only non-test consumer is that plugin. Test fixtures and tests reference it to verify context enrichment, not to use it for real work.
- Recommendation: remove it. A core-owned lifecycle with one consumer is dead surface, and the tag-gated extension approach covers this use case without it.
- If retained: scope shrinks to replacing the plugin only; the lifecycle stays as a general extension point. Valid but leaves an unused hook.

**Q2 — Where does the preview formatting helper live?**
`AgentCore.format_tool_call_preview` / `format_tool_call_previews` compose three steps: interop inspection (already in accessors), tool resolution (needs prepared tool states), and the tool's `format_tool_call_preview` method (already on the tool). Only tool resolution is core-specific.
- Recommendation: move to `tool_interop.py` as a free function taking `inspected_call` + `tool_states`. Consistent with `inspect_call` / `inspect_schema` already there. Extensions already call `DEFAULT_TOOL_INTEROP_REGISTRY.inspect_call(...)` directly.
- Alternative: keep on `AgentCore` as a thin wrapper. Less churn but leaves a public core method with one consumer.
- `patch_native_internal_metadata` has no reason to exist after this refactor (no native `_metadata` persistence). Remove it regardless of Q2.

**Q3 — Does the extension's `from_native_messages` context include what's needed?**
The extension needs the interop registry (available via `get_registry_from_context(context)`, already used by existing tools extensions) and prepared tool states (unclear — needs verification at start of execution). If tool states aren't in context, a context builder change or a different access path is needed. This is a feasibility question, not a scope question.

**Q4 — Where does the extension package live?**
- Recommendation: new repo-root package `plugins/tool-call-preview/`, consistent with `plugins/cost-tracking/` (the existing cross-provider extension pattern).

## Supporting details

**Current implementation (to be removed):**
- `core/python/plugins/tool_call_preview_feature.py` — feature plugin with `trigger: "response_finalize"` action.
- `core/python/agent_core/core.py:4424-4487` — `format_tool_call_preview` / `format_tool_call_previews`.
- `core/python/agent_core/core.py:4489+` — `patch_native_internal_metadata`.
- `core/python/agent_core/core.py:2547-2563, 2781-2797, 2984-3000` — `response_finalize` execution in `send_request` / `send_request_stream` / `send_request_stream_async`.
- `core/python/agent_core/core.py:3758+` — `execute_response_lifecycle_actions` executor.
- `core/python/agent_core/types.py:993, 1383-1420` — `response_finalize` docstrings.

**Target design (proven pattern):**
- `plugins/cost-tracking/src/cost_tracking_plugins/cost_tracking_extension.py` — existing cross-provider extension with `required_tags() == ["cost_tracking"]`, `priority = 70`, runs after provider-specific extensions. Same pattern: capability-tag-gated, runs after provider extensions stamp metadata.
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_tools_extension.py:109` — existing tools extension already calls `DEFAULT_TOOL_INTEROP_REGISTRY.inspect_call(...)` directly. The new extension would do the same.

**Providers emitting `supports_tools` (automatic gating):**
`openai_provider.py:131`, `openai_responses_provider.py:390`, `openrouter_provider.py:374`, `openrouter_responses_provider.py:221`, `anthropic provider.py:236`, `reference_openai_compatible_provider.py:916`.

**Consumers of `response_finalize` (must update if removed):**
- `core/python/tests/fixtures/context_recording_feature.py:102`
- `core/python/tests/fixtures/context_recording_plugin/src/context_recording_plugin/__init__.py:140`
- `core/python/tests/test_feature_plugin_context_enrichment.py:226, 380`
- `application/python/tests/test_feature_plugin_context_enrichment.py:380`

**Consumers of the core helpers (only the plugin + tests):**
- `core.format_tool_call_previews` → `tool_call_preview_feature.py:85` + `test_core_execute_tool_calls.py:321`
- `core.format_tool_call_preview` → `test_tool_preparation.py:217, 227`
- `core.patch_native_internal_metadata` → `tool_call_preview_feature.py:103` only

**Tests asserting preview behavior (must pass after refactor):**
- `core/python/tests/test_response_finalize_lifecycle.py` — 4 tests
- `plugins/openai_responses/tests/test_openai_responses_tools_extension_integration.py:265`
- `plugins/openrouter_responses/tests/test_openrouter_tool_call_preview_integration.py:107`

**Documentation referencing `response_finalize`:**
- `plugins/docs/actions.md:275-277, 532-534, 557-559, 613-621`
- `plugins/docs/feature-plugins.md` (added in the same commit)
- `core/python/agent_core/types.py:993, 1383-1420` docstrings

**Original task spec:** `tasks/20260402-response-finalize-tool-preview-lifecycle.md` (completed; this subtask refactors its implementation).

## Execution plan

Status: Draft

### Phase 1 — Verify feasibility (Q3)

Before writing the extension, confirm the extension's `from_native_messages` context has what the preview computation needs.

1. Inspect the context builder path for `from_native_messages` in `core/python/agent_core/core.py` (around lines 2525-2531) and the context helper in `core/python/agent_core/plugin/context_helper.py`.
2. Determine whether prepared tool states are reachable from the context or shared provider state.
3. If not reachable, decide the smallest access path: extend the context builder, or pass tool states through shared provider state. Prefer the option that doesn't widen the public context contract for other plugins.

If Q3 cannot be resolved without a material context contract change, stop and surface it as a requirement question before proceeding.

### Phase 2 — Move the preview helper to `tool_interop.py` (Q2)

1. Add a free function `format_tool_call_preview(inspected_call, tool_states) -> Dict[str, Any]` in `core/python/agent_core/tool_interop.py` that composes tool resolution + the tool's `format_tool_call_preview` method. Reuse `AgentCore._resolve_tool_handler_for_call` logic (extract to a free function or keep as a callable passed in).
2. Add `format_tool_call_previews(inspected_calls, tool_states) -> List[Dict[str, Any]]` as the plural wrapper.
3. Remove `AgentCore.format_tool_call_preview`, `format_tool_call_previews`, and `patch_native_internal_metadata` from `core/python/agent_core/core.py`.
4. Update `test_core_execute_tool_calls.py:321` and `test_tool_preparation.py:217, 227` to call the new helper.

### Phase 3 — Create the tag-gated extension (Q4)

1. Create `plugins/tool-call-preview/` with `agent_plugin.json`, `src/tool_call_preview_plugins/__init__.py`, and the extension class.
2. The extension:
   - `name = "tool_call_preview"`, `priority` set higher than provider-specific tools extensions (verify ordering; `CostTrackingExtension` uses 70, tools extensions use default 100 — confirm which direction "after" means).
   - `required_tags() == ["supports_tools"]`.
   - `from_native_messages(native_messages, messages, state, *, context=None)`: for each assistant message with `metadata.tool_calls`, compute previews via the new `tool_interop` helper and set `metadata.tool_call_previews`. Return updated `messages`.
3. No `finalize`, no `to_native_messages`, no `get_actions` — the extension only annotates core messages on native→core conversion.

### Phase 4 — Update tests

1. Convert `core/python/tests/test_response_finalize_lifecycle.py` to test the extension directly: register the extension, run a request, assert `metadata.tool_call_previews` shape and rebuild-from-native survival. The 4 existing test cases map to extension behavior tests.
2. Update `plugins/openai_responses/tests/test_openai_responses_tools_extension_integration.py:265` and `plugins/openrouter_responses/tests/test_openrouter_tool_call_preview_integration.py:107` to register the new extension instead of `ToolCallPreviewFeature`.
3. Update or remove `response_finalize` references in `context_recording_feature.py`, `context_recording_plugin/__init__.py`, and `test_feature_plugin_context_enrichment.py` (per Q1 outcome).

### Phase 5 — Remove the old implementation (per Q1)

1. Delete `core/python/plugins/tool_call_preview_feature.py`.
2. Remove `execute_response_lifecycle_actions` and the `response_finalize` calls in `send_request` / `send_request_stream` / `send_request_stream_async` from `core/python/agent_core/core.py`.
3. Remove `response_finalize` references from `core/python/agent_core/types.py` docstrings.
4. Remove the `record_response_finalize_context` action from context-recording fixtures and tests.

### Phase 6 — Update docs

1. Remove the `response_finalize` section from `plugins/docs/actions.md`.
2. Remove `response_finalize` references from `plugins/docs/feature-plugins.md`.
3. Add a brief note to `plugins/docs/provider-extensions.md` describing the `supports_tools`-gated preview extension pattern, referencing `plugins/cost-tracking/` as the prior art.

### Implementation decisions and open questions

**Decisions (recommendations, pending approval):**
- D1: Remove `response_finalize` entirely (Q1). Rationale: one consumer, dead surface.
- D2: Move preview helper to `tool_interop.py` as a free function (Q2). Rationale: consistent with existing interop helpers; only tool resolution is core-specific and can take `tool_states` as a parameter.
- D3: New repo-root package `plugins/tool-call-preview/` (Q4). Rationale: consistent with `plugins/cost-tracking/`.
- D4: Recompute previews on rebuild rather than persisting into native `_metadata`. Rationale: `from_native_messages` already runs on every rebuild; persistence is a workaround that's no longer needed.

**Open questions (need user input before execution):**
- Q1, Q2, Q4 as above. Q3 is a feasibility check during execution.

### Documentation

- `plugins/docs/actions.md` — remove `response_finalize` section.
- `plugins/docs/feature-plugins.md` — remove `response_finalize` references.
- `plugins/docs/provider-extensions.md` — add note on `supports_tools`-gated preview extension.
- `core/python/agent_core/types.py` — remove `response_finalize` docstrings.
- `plugins/tool-call-preview/README.md` — package README for the new extension.

### Task checklist

- [ ] Phase 1: Verify `from_native_messages` context has tool states (Q3).
- [ ] Phase 2: Move preview helper to `tool_interop.py`; remove `AgentCore` helpers.
- [ ] Phase 3: Create `plugins/tool-call-preview/` extension package.
- [ ] Phase 4: Convert preview tests to the extension; update `response_finalize` test fixtures.
- [ ] Phase 5: Delete `tool_call_preview_feature.py`; remove `response_finalize` lifecycle.
- [ ] Phase 6: Update docs.

### Requirement verification

- Preview output shape preserved: `test_response_finalize_lifecycle.py` (converted) asserts `metadata.tool_call_previews == [{"id": ..., "preview": ...}]` for sync, streaming, and rebuild-from-native.
- Automatic gating: a test with a provider emitting `supports_tools` and no explicit feature registration produces previews. A test with a provider NOT emitting `supports_tools` produces no previews.
- Rebuild survival: `test_response_finalize_preview_persists_through_rebuild_from_native` (converted) asserts previews survive `_rebuild_core_from_native`.
- Old implementation removed: `grep -r "response_finalize" core/python/agent_core` returns no matches; `core/python/plugins/tool_call_preview_feature.py` does not exist.
- Provider integration: `plugins/openai_responses/tests/test_openai_responses_tools_extension_integration.py` and `plugins/openrouter_responses/tests/test_openrouter_tool_call_preview_integration.py` pass with the extension registered instead of the feature plugin.
- Fast verification: `pytest core/python/tests -q` and `pytest plugins/openai_responses/tests -q` and `pytest plugins/openrouter_responses/tests -q` all pass.

### Additional implementation verification

- `ruff check core/python/agent_core core/python/tests plugins/tool-call-preview`.
- `pytest core/python/tests/test_feature_plugin_context_enrichment.py application/python/tests/test_feature_plugin_context_enrichment.py -q` — confirm context-recording fixtures still pass after `response_finalize` removal.