# Kimi-Compatible Persistent Subagent Tools

Implement the inspected Kimi CLI model-facing `Task` behavior on top of the working persistent shared runtime, extending shared code only for functionality that is genuinely reusable.

## Requirements checklist

- [ ] Capture the inspected Kimi `Task` schema, descriptions, argument rules, outputs, and errors in contract fixtures or equivalent tests.
- [ ] Implement blocking `Task` behavior using a persisted child application session.
- [ ] Preserve the upstream model-facing isolated/fresh task context behavior.
- [ ] Return the child's final answer in the Kimi-compatible tool-result shape.
- [ ] Forward child activity through the tool stream where required for Kimi-compatible observability.
- [ ] Keep approvals, questions, or other root-actionable events from being hidden behind an unusable nested stream when the existing framework can represent them.
- [ ] Reuse the shared persistence, request exclusivity, idempotency, and restart recovery behavior.
- [ ] Keep Kimi-specific prompts, minimum-summary behavior, schemas, formatting, and errors in `kimi-tools`.
- [ ] Extract blocking-run or event-forwarding support into shared code only when it is vendor-neutral.
- [ ] Add deterministic unit, application integration, and restart tests.

Parent Task: `tasks/20260715-persistent-plugin-subagents/000-main.md`

Depends On: `tasks/20260715-persistent-plugin-subagents/030-subagent-restart-recovery.md`

## Upstream references

- `../kimi-cli/src/kimi_cli/tools/multiagent/task.py`
- `../kimi-cli/src/kimi_cli/soul/agent.py`
- `../kimi-cli/src/kimi_cli/session_state.py`

The upstream `Task` invocation creates a fresh child context and returns a final child answer. V1 should preserve that model-facing behavior while retaining the resulting child as a visible persisted session.

## Scope constraints

- Do not change the Kimi model-facing tool into the Codex lifecycle surface.
- Do not expose shared-engine data structures directly to the model.
- Dynamic `CreateSubagent` support is not required unless separately approved.
- No new UI is required.
- Normal manual use of the visible child session remains existing framework behavior rather than a Kimi tool requirement.

## Verification

- Contract tests for schema and result formatting.
- Full blocking child tool-loop integration.
- Child session remains persisted and visible after the parent tool returns.
- Replayed parent `Task` invocation resolves or recovers the same child.
- Child events do not corrupt or become model-visible parent history beyond the expected tool result.