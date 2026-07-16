# Persistent Plugin-Driven Subagents

Implement persistent subagents through vendor-compatible tool plugins backed by a gradually developed, vendor-neutral shared runtime. Child agents must use normal application sessions, survive process restart at persisted-checkpoint granularity, and preserve the model-facing behavior of the corresponding upstream tools.

## Task checklist

- [ ] `tasks/20260715-persistent-plugin-subagents/010-codex-vertical-slice-and-shared-runtime.md`
- [ ] `tasks/20260715-persistent-plugin-subagents/020-application-session-request-exclusivity.md`
- [ ] `tasks/20260715-persistent-plugin-subagents/030-subagent-restart-recovery.md`
- [ ] `tasks/20260715-persistent-plugin-subagents/040-kimi-compatible-subagent-tools.md`
- [ ] `tasks/20260715-persistent-plugin-subagents/050-gemini-compatible-subagent-tools.md`
- [ ] `tasks/20260715-persistent-plugin-subagents/060-cross-adapter-integration-and-docs.md`
  - FOLLOW-UP: `tasks/20260715-subagent-session-notifications.md` is intentionally not required for core subagent completion. It adds persistent parent-session notifications after both this task and generic session notifications Stage 1 are complete.

## Background and research

The design was informed by these local sibling checkouts:

- Codex at revision `c10f95ddac`
- Kimi CLI at revision `7ba9695`
- Gemini CLI at revision `020da58`

Key upstream findings:

- Codex has persistent child threads and explicit lifecycle tools for spawning, waiting, follow-up input, listing, and closing. It is the primary reference for persistent model-facing child identity.
- Kimi exposes blocking `Task` behavior, isolated child contexts, nested child events, and a final answer returned to the parent. Its agent definitions persist, but each upstream task invocation creates a fresh execution context.
- Gemini exposes configured specialists as dynamically generated tools, creates an isolated executor for each invocation, enforces limits/completion behavior, and records child sessions separately.

Relevant upstream sources include:

- `../codex/codex-rs/core/src/agent/control.rs`
- `../codex/codex-rs/protocol/src/protocol.rs`
- `../codex/codex-rs/tools/src/agent_tool.rs`
- `../kimi-cli/src/kimi_cli/tools/multiagent/task.py`
- `../kimi-cli/src/kimi_cli/soul/agent.py`
- `../gemini-cli/packages/core/src/agents/subagent-tool.ts`
- `../gemini-cli/packages/core/src/agents/local-invocation.ts`
- `../gemini-cli/packages/core/src/agents/local-executor.ts`

The internal-call pattern is similar to existing compaction features, but subagents must use persisted application sessions and the full application tool loop rather than temporary core-only requests:

- `plugins/kimi-tools/src/kimi_tools/kimi_compaction_feature.py`
- `plugins/claude-tools/src/claude_tools/claude_compaction_feature.py`
- `plugins/gemini-compaction-feature/src/gemini_compaction_feature/__init__.py`

## Architectural requirements

### Vertical-slice development

- Develop the first real Codex-compatible tool implementation together with only the shared runtime functionality it requires.
- Add shared abstractions gradually as Kimi and Gemini behavior is implemented.
- Do not build a broad speculative subagent framework before a real model-facing implementation is testable.
- Keep each stage runnable and covered by deterministic tests.

### Engine versus shape

Follow the existing principle documented in `plugins/tool-compat-shared/README.md`:

- Shared code owns session execution, persistence, recovery, lifecycle state, waiting, cancellation, and structured results.
- Vendor tool packages own tool names, schemas, descriptions, prompts, argument interpretation, model-facing formatting, and errors.
- Shared code must not contain Codex-, Kimi-, or Gemini-specific tool contracts.

The shared implementation should be a normal non-plugin library package. Vendor-facing tool plugins should live in the relevant existing vendor tool packages.

### User configuration

- Users must be able to configure an ordered list of subagent definitions that resolve to existing configured application agents.
- Configuration order must be preserved. Some vendor adapters may include available agents in model-facing tool descriptions or system instructions where ordering can affect behavior.
- A definition must contain enough information to identify the model-facing subagent and resolve its target configured agent. The exact required fields are not fixed by this plan.
- Vendor adapters may use different configuration fields or structures only when the difference is justified by their upstream model-facing behavior. Shared concepts should remain consistent where practical.
- Subagent configuration must not duplicate provider, model, plugin, or tool configuration already owned by the referenced application agent unless an adapter-specific override is explicitly required.

A conceptual example, not the approved final schema:

```json
{
  "subagents": [
    {
      "name": "researcher",
      "agent_id": "research-agent",
      "description": "Investigate the codebase and return technical findings."
    },
    {
      "name": "reviewer",
      "agent_id": "review-agent",
      "description": "Review proposed changes for correctness and missing tests."
    }
  ]
}
```

The array order is significant and must survive configuration loading. The final location of this list, field names, optional fields, defaults, validation behavior, and vendor-specific extensions are intentionally not decided here.

### Model-facing behavior

Provide separate model-facing implementations:

- Codex-compatible persistent lifecycle tools with background execution and persistent follow-up input.
- Kimi-compatible blocking `Task` behavior with isolated context and a final tool result.
- Gemini-compatible configured-specialist tools generated from agent definitions, with blocking execution and appropriate limits/completion behavior.

Schemas, descriptions, supported arguments, result text, and errors must be verified against fixtures or contract tests derived from the inspected upstream revisions.

## Implementation decision requiring user confirmation

The final complete user-facing subagent configuration shape is intentionally not decided by this plan. It is a task-wide public interface decision.

Before implementation commits to a configuration schema, the completing agent must present the proposed common shape, placement, defaults, validation behavior, ordering semantics, vendor-specific variations, and representative examples to the user for confirmation.

This decision applies across all subtasks. It must not be treated as complete or owned solely by the first vendor adapter.

### Child sessions and relationships

- Every child agent is a normal persisted application `Session`.
- Child sessions must remain visible in ordinary session listings.
- Child metadata must identify its parent session, root session, target configured agent, originating invocation, adapter/tool surface, and durable run state.
- Child sessions should receive useful existing title/subtitle metadata identifying them as subagents.
- The parent session must contain an append-only `subagent_session_ids` list.
- Each child ID is appended once when the relationship is established.
- Frequently changing child status must not be stored in the parent list.
- Child metadata is authoritative for relationship and execution details.
- Routine parent-to-child lookup uses the parent list; a session scan is allowed only as a recovery fallback for an interrupted creation.

### Persistent and ephemeral state

- `AgentApplication.get_runtime_store()` may hold live workers, condition variables, cancellation handles, and process-local caches.
- Runtime-store contents are never the authoritative state needed after restart.
- Cheap durable state may be stored in session metadata.
- Recovery must be possible from persisted parent and child sessions after constructing a new `AgentApplication`.

### Restart and idempotency

- Replaying a persisted subagent tool call must locate the existing child rather than creating a duplicate.
- Invocation identity must be derived from stable persisted parent/tool-call information without introducing vendor-specific parsing into shared code.
- Resuming a parent whose unresolved tool call is waiting for a child must recover or restart the child from its latest persisted checkpoint.
- Recovery must support child tails ending in a user message, unresolved assistant tool call, tool result awaiting the next assistant response, or completed assistant response with stale run metadata.
- Eager restart of all detached children at application startup is not required for V1.

### Request safety

- Only one request may actively modify a session at a time across HTTP, terminal, and internal subagent entry points.
- The application must reject or report a busy session before concurrent requests create conflicting histories.
- This requires the separate framework work in `tasks/20260715-persistent-plugin-subagents/020-application-session-request-exclusivity.md`.

### Recovery guarantee

V1 guarantees recovery from the latest persisted application checkpoint.

V1 does not guarantee exactly-once execution of arbitrary nested tools. An external side effect completed immediately before a crash may be replayed if its tool result was not checkpointed. Child creation itself must be idempotent.

## Framework and UI scope

### Mandatory framework work

The only currently identified mandatory framework addition is application-owned per-session request exclusivity shared by all request entry points.

Do not add other framework features unless implementation demonstrates that an existing public API cannot safely satisfy a hard requirement.

### UI

No new UI is required for V1. Existing functionality already supports:

- Visible sessions
- Metadata-derived titles and subtitles
- Opening a session transcript
- Sending a subsequent message when no request is active

Parent/child navigation, tree views, status badges, nested child displays, and explicit restart controls are useful but optional follow-ups.

## User continuation scope

No subagent-specific continuation workflow is required.

- A child remains an ordinary visible session.
- Existing session functionality may be used to continue it after no request is active.
- Application request exclusivity must prevent a user request from racing an active internal child request.

Input queues, interrupt-and-send behavior, special composer handling, automatic parent updates from later manual turns, and custom agent-switch semantics are out of scope.

## Definition of done

- Codex-, Kimi-, and Gemini-compatible model-facing tool surfaces are implemented and contract-tested against the inspected upstream behavior.
- Common functionality is shared without moving vendor schemas, descriptions, prompts, formatting, or errors into the shared library.
- Every subagent invocation creates or reuses a persisted, visible child session.
- Parent metadata contains an append-only `subagent_session_ids` list without duplicate IDs.
- Child metadata contains enough durable information to recover the relationship and run.
- Codex follow-up operations reuse the same child session and history.
- Replayed tool calls do not create duplicate children.
- A newly constructed application can resume a parent waiting for an interrupted child and reach a final parent tool result.
- HTTP, terminal, and internal requests use common application-level per-session request exclusivity.
- No new UI is required for basic operation.
- Recovery guarantees and at-least-once nested-tool limitations are documented.
- Relevant deterministic unit and application integration tests pass.
- Selective hosted-provider smoke tests are run where justified by the final application/tool-loop changes.

## Relevant framework references

- `plugins/tool-compat-shared/README.md`
- `plugins/docs/tool-plugins.md`
- `plugins/docs/application-plugins.md`
- `core/python/agent_app/application_future.py`
- `core/python/agent_app/tool_loop.py`
- `core/python/agent_app/app_context.py`
- `core/python/agent_app/sessions.py`
- `core/python/tests/test_application_tool_loop_session_concurrency.py`
- `application/python/agent_terminal_app/server.py`
- `application/python/agent_terminal_app/terminal_app.py`
- `plugins/session-title-app/src/session_title_app/__init__.py`
- `packages/frontend-sdk/src/sessions/sessionListPresentation.ts`