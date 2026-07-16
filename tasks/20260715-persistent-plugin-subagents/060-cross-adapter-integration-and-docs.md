# Cross-Adapter Integration, Configuration, And Documentation

Finish the persistent subagent feature by verifying the shared runtime across all vendor adapters, documenting supported guarantees, and adding only the configuration and integration changes required for practical use.

## Requirements checklist

- [ ] Run cross-adapter tests proving Codex, Kimi, and Gemini tools use the same durable child-session foundation.
- [ ] Verify shared code contains no vendor-specific schemas, prompts, tool names, result formatting, or error text.
- [ ] Verify parent `subagent_session_ids` behavior with mixed adapter invocations and multiple children.
- [ ] Verify child sessions remain visible and have useful existing title/subtitle metadata without frontend changes.
- [ ] Verify application request exclusivity across all adapters and request entry points.
- [ ] Verify restart recovery through newly constructed application instances for background and blocking adapters.
- [ ] Add configuration examples showing how configured agents are exposed to each vendor tool surface.
- [ ] Add or update package manifests, dependencies, and default configuration only where needed.
- [ ] Document persistence, visibility, idempotency, cancellation, and checkpoint-level recovery semantics.
- [ ] Clearly document the at-least-once limitation for interrupted nested tools.
- [ ] Run relevant package tests and selective application integration tests.
- [ ] Run selective hosted-provider smoke tests where justified by the final provider/tool-loop impact.
- [ ] Confirm optional notification and UI enhancements remain outside the core definition of done.

Parent Task: `tasks/20260715-persistent-plugin-subagents/000-main.md`

Depends On:

- `tasks/20260715-persistent-plugin-subagents/030-subagent-restart-recovery.md`
- `tasks/20260715-persistent-plugin-subagents/040-kimi-compatible-subagent-tools.md`
- `tasks/20260715-persistent-plugin-subagents/050-gemini-compatible-subagent-tools.md`

## Documentation scope

Document:

- How to configure available child agents.
- Which vendor surface to use for background lifecycle versus blocking delegation.
- How child sessions appear in the normal session list.
- How persistent Codex follow-up differs from fresh Kimi/Gemini task invocations.
- What survives restart.
- When a child request is considered busy.
- What cancellation and close mean.
- Why arbitrary nested tool effects are not exactly-once across a crash.
- How another vendor adapter should use the shared engine-versus-shape boundary.

## Optional follow-ups not included

- `tasks/20260715-subagent-session-notifications.md`
- Parent/child navigation
- Session tree UI
- Status badges
- Nested child activity cards
- Eager startup recovery
- Persistent event storage
- Per-tool-call durable execution journals
- Exactly-once nested tool infrastructure

## Final verification

At minimum, run:

- Shared subagent library tests.
- `plugins/codex-tools` tests relevant to subagents.
- `plugins/kimi-tools` tests relevant to subagents.
- `plugins/gemini-tools` tests relevant to subagents.
- Core application tests for session persistence, tool-loop recovery, and concurrency.
- Terminal/server tests affected by application-level request exclusivity.

For major request-pipeline changes, explicitly consider follow-up verification in:

- `plugins/openrouter`
- `plugins/openai_responses`
- `plugins/reference-openai-compatible-provider`