# CL-150 Implementation Tasks

Status key: ✅ Done | ⚠️ Partial | ❌ Not done

---

## Phase 1 — Restore V1 Contract Boundary (F4, F5)

- [x] Narrow interception scope to tool plugins only — extensions/features excluded from interceptor chain in `tool_loop.py`
- [x] Remove `get_interception_ui_schema()` and `materialize_interception_prompt()` from V1 public contract (still present in `interceptor_tool.py` test helper for backward-compat reference; not enforced in core)
- [x] Remove `GET /sessions/{session_id}/tool-prompts` endpoint from `server.py` (not present)

---

## Phase 2 — Generic Core Metadata-Mutation Primitive (F2, F13)

- [x] `modify_message_metadata()` added to `core/python/agent_core/core.py`
- [x] Native-first patching when `session.metadata["native_messages"]` is present
- [x] Core-direct mutation fallback when no native history
- [x] Preserves `role`, `content`, `multipart_content`, `tool_result` across mutations
- [x] Operation is immutable / session-safe

---

## Phase 3 — Application-Level Prompt Submission Orchestration (F2, F7, F8, F13)

- [x] `AgentApplication.submit_interceptor_prompt_answer()` added in `application_future.py`
- [x] Validates `message_index`, `phase`, `tool_call_id`, `prompt_id`
- [x] Appends `prompt_response` to `interception_phases` on submit
- [x] Clears `pending_prompt` from `interception_current` on submit
- [x] Preserves original `request_overrides` / `config_overrides` for resume

---

## Phase 4 — Thin Transport Layer (F7, F8, F13)

- [x] `POST /sessions/{id}/tool-prompts/respond` calls `AgentApplication.submit_interceptor_prompt_answer()` in `server.py`
- [x] No manual `Message(...)` / `Session(...)` construction in server endpoint
- [x] Payload requires `message_index`, `phase`, `tool_call_id`, `prompt_id`, `button_id`, `values`

---

## Phase 5 — Complete Prompt Lifecycle in Tool Loop (F6)

- [x] Resume reads persisted `prompt_response` from `interception_phases` in `tool_loop.py`
- [x] Re-enters same phase with original payload + prompt + answer
- [x] `tool_result`-phase prompting with `kind == "prompt"` support added
- [x] Active result prompts stored on tool message
- [x] Answered result prompts appended to that tool message's `interception_phases`

---

## Phase 6 — Auto-Preserve Interception Metadata for Native-History Providers (F3)

- [x] `ToolInterceptorMetadataPreserver` added to `plugins/openai_responses/agent_plugin.json`
- [x] `ToolInterceptorMetadataPreserver` added to `plugins/openrouter/agent_plugin.json`

---

## Phase 7 — Remove Secondary Prompt Channel in Frontend/SDK (F5, F12)

- [x] No `GET /sessions/{id}/tool-prompts` list endpoint present in `server.py`
- [x] `/messages` is the only prompt read path
- [x] Frontend renders prompts from `metadata.interception_current.pending_prompt` — `MessageBubble.tsx` already uses `interception_current.pending_prompt`; `selectPendingToolPrompts` selector confirmed as the read path
- [x] `listSessionToolPrompts()` removed from `AgentBackend` interface (`backend.ts`), `RestAgentBackend` (`restBackend.ts`), and `index.ts` exports
- [x] `ToolPromptListItem` type removed from all SDK surfaces
- [x] `tool_interceptor_prompt` dirty-mark and `scheduleAutoReload` block removed from `chatController.ts` — prompt arrival no longer forces an out-of-band reload
- [x] Integration test updated to poll via `selectPendingToolPrompts(controller.getSnapshot().messages)` instead of `listSessionToolPrompts`
- [x] `submitSessionToolPromptResponse` updated throughout (SDK interface, REST implementation, mobile app, integration test) to send `message_index`, `phase`, `tool_call_id` — matching the server's strengthened payload contract

---

## Phase 8 — Fix Reference Interceptor Behavior (F9)

- [x] `deny` returns synthetic error tool result with `continue_loop=True` in `interceptor_tool.py`
- [x] `deny_stop` stops the loop (`continue_loop=False`) in `interceptor_tool.py`

---

## Phase 9 — Tests (F1, F11)

### Core metadata mutation tests (`test_metadata_mutation.py`)
- [x] `test_modify_message_metadata_core_only` — PASS
- [x] `test_modify_message_metadata_with_native` — PASS
- [x] `test_modify_message_metadata_syncs_interception_phases` — PASS
- [x] `test_modify_message_metadata_preserves_tool_result` — PASS

### Prompt submission tests (`test_submit_prompt.py`)
- [x] `test_submit_interceptor_prompt_answer_valid` — PASS
- [x] `test_submit_interceptor_prompt_answer_invalid` — PASS
- [x] `test_submit_interceptor_prompt_answer_preserves_overrides` — PASS
- [x] `test_submit_interceptor_prompt_answer_no_overrides` — PASS

### Interceptor ordering tests (`test_interceptor_ordering.py`)
- [x] `test_interceptor_priority_ordering` — PASS (fixed: chain metadata now propagated between interceptors)
- [x] `test_interceptor_equal_priority_registration_order` — PASS (same fix)

### Provider matrix tests (`test_interceptor_provider_matrix.py`)
- [x] Matrix tests — skipped (require live API keys, marked `requires_keys`)

### Application layer tool tests (`test_application_layer_tools.py`)
- [x] `test_execute_tool_calls_non_streaming` — PASS
- [x] `test_execute_tool_calls_streaming` — PASS
- [x] `test_pending_tool_calls_ignored_after_follow_up_user_message` — PASS
- [x] `test_pending_tool_calls_returned_for_unresolved_tail_assistant` — PASS
- [x] `test_interceptor_tool_prompt_title_overridable_from_config` — PASS
- [x] `test_interceptor_deny_does_not_execute_add[deny]` — PASS
- [x] `test_interceptor_deny_does_not_execute_add[Deny]` — PASS
- [x] `test_interceptor_unknown_button_does_not_execute_add` — PASS
- [x] `test_interceptor_resume_denies_when_metadata_tool_call_id_is_int` — PASS
- [x] `test_interceptor_prompt_suspend_and_resume` — PASS
- [x] `test_interceptor_transform_and_stop_semantics` — PASS
- [x] `test_interceptor_transform_responses_shaped_tool_call` — PASS
- [x] `test_interceptor_tool_result_phase_prompting` — PASS