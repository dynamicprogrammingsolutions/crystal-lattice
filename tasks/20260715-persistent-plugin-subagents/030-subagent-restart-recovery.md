# Subagent Idempotency And Restart Recovery

Harden the Codex vertical slice so parent-child state survives application restart and replayed parent tool calls recover existing child work instead of creating duplicates.

## Requirements checklist

- [ ] Define a stable invocation identity from persisted parent/tool-call information without vendor-specific parsing in shared code.
- [ ] Make child creation idempotent across replayed spawn or blocking invocation calls.
- [ ] Recover child lookup through the parent's `subagent_session_ids` list during normal operation.
- [ ] Add a fallback session scan for the narrow crash window between child persistence and parent-list append.
- [ ] Recover an interrupted child from its latest persisted checkpoint after constructing a new `AgentApplication`.
- [ ] Support recovery when the child tail is a user message, unresolved assistant tool call, tool result awaiting the next assistant response, or completed assistant response with stale metadata.
- [ ] Resume a parent whose unresolved wait/tool invocation was persisted before shutdown.
- [ ] Ensure loss of all `RuntimeStore` state does not lose durable child identity or run intent.
- [ ] Persist and reconcile clear child run states needed for recovery.
- [ ] Verify completed replay returns the existing result rather than rerunning or duplicating the child.
- [ ] Document checkpoint-level recovery and the at-least-once nested-tool limitation.
- [ ] Add deterministic restart tests that use a genuinely new application instance.

Parent Task: `tasks/20260715-persistent-plugin-subagents/000-main.md`

Depends On:

- `tasks/20260715-persistent-plugin-subagents/010-codex-vertical-slice-and-shared-runtime.md`
- `tasks/20260715-persistent-plugin-subagents/020-application-session-request-exclusivity.md`

## Existing recovery mechanism to reuse

The application tool loop already replays unresolved assistant tool calls before issuing another LLM request:

- `core/python/agent_app/tool_loop.py`

The recovery flow should build on that behavior:

1. Load the persisted parent.
2. Replay its unresolved subagent tool call.
3. Resolve the existing child invocation.
4. Inspect the persisted child tail and durable run state.
5. Continue the child request where appropriate.
6. Complete the original parent tool invocation.

No eager scan and restart of all children at application construction is required.

## Persistence rules

- Runtime worker objects are ephemeral.
- Child metadata is authoritative for relationship and recoverable run state.
- Parent metadata is the normal child lookup index.
- Any additional cache or index must be rebuildable and cannot be the only source of truth.

## Recovery guarantee

The implementation guarantees continuation from the latest persisted application checkpoint.

It does not guarantee exactly-once execution of a nested tool whose external side effect completed before its result was persisted. Tests and documentation must not imply a stronger guarantee.

## Verification scenarios

- Crash after child creation but before parent list append.
- Crash after parent list append but before spawn tool result.
- Crash while parent is blocked in `wait`.
- Crash after child user message persistence but before provider response.
- Crash with unresolved child tool calls.
- Crash after child tool results but before its next assistant response.
- Crash after child final response but before durable status update.
- Replay of an already completed invocation.