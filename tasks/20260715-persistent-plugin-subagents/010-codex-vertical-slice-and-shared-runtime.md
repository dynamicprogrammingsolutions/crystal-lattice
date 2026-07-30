# Codex Vertical Slice And Minimal Shared Subagent Runtime

Build the first real persistent subagent implementation using the selected upstream Codex tool surface, while extracting only the vendor-neutral shared functionality required by that implementation.

## Requirements checklist

- [ ] Capture the selected Codex model-facing schemas, descriptions, arguments, outputs, and errors in contract fixtures or equivalent tests.
- [ ] Create a minimal non-plugin shared library for vendor-neutral child-session execution and lifecycle data.
- [ ] Implement the Codex-compatible spawn, wait, persistent follow-up/input, list/status, and close behavior selected for V1.
- [ ] Run spawned children in the background so multiple sequential spawn tool calls can produce concurrent child work.
- [ ] Create every child as a persisted, visible application session using a configured agent.
- [ ] Resolve subagent definitions to existing configured application agents instead of duplicating their provider, model, plugin, and tool configuration.
- [ ] Preserve configured subagent order through loading and Codex model-facing presentation.
- [ ] Store authoritative relationship and run information in child metadata.
- [ ] Append the child ID exactly once to the parent session's `subagent_session_ids` metadata list.
- [ ] Add useful existing title/subtitle metadata to child sessions without requiring new UI.
- [ ] Keep live worker objects in `RuntimeStore` while ensuring session storage remains authoritative.
- [ ] Verify that persistent follow-up input reuses the same child session and observes its prior history.
- [ ] Add deterministic tool, shared-library, and application integration tests using fake providers/tools.
- [ ] Avoid adding Kimi-, Gemini-, or speculative future behavior to the shared API.

Parent Task: `tasks/20260715-persistent-plugin-subagents/000-main.md`

## Scope and implementation guidance

Use existing public application capabilities where safe:

- `AgentApplication.create_session(...)` / `create_session_ephemeral(...)`
- `AgentApplication.load_session(...)`
- `AgentApplication.save_session(...)`
- `AgentApplication.send_request(...)`
- `AgentApplication.acquire_session_lock(...)`
- Tool context access to the application and runtime store

The shared package should initially expose only structured operations needed by the Codex adapter, such as:

- Create or resolve a child invocation.
- Start a child request.
- Query durable status.
- Wait for a run.
- Append persistent follow-up input.
- Close or cancel a run.

The Codex tool plugin owns all model-facing shape, including exact names, descriptions, parameter schemas, result text, and errors.

The parent child-ID append must be tested while the parent tool loop is active. Existing non-protected metadata reconciliation is relevant:

- `core/python/tests/test_application_tool_loop_session_concurrency.py`

For idempotency groundwork, preserve enough originating invocation information in child metadata to identify a replay later. Full restart recovery is completed in the dependent recovery task.

## Non-goals

- Kimi or Gemini adapters
- Eager startup recovery
- New parent/child navigation UI
- A broad application plugin control plane
- Exactly-once execution of arbitrary nested tools
- Dynamic subagent creation beyond the selected Codex-compatible surface

## Verification

- Run shared-library and Codex tool unit tests.
- Run application integration tests proving a child executes the normal full tool loop.
- Verify two child sessions can make progress concurrently after sequential spawn calls.
- Verify a follow-up call observes prior child conversation state.
- Verify normal session listing data includes the child with recognizable metadata.