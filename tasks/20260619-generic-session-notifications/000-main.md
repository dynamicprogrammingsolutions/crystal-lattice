# Generic Session Notifications And Interactions

Create a generic platform feature for persistent, evented session notifications that can reuse existing action display/action form UI. Implement it in two stages: non-blocking notifications first, then interactive/blocking flows.

## Task checklist

- [x] `tasks/20260619-generic-session-notifications/010-stage-1-notification-design.md`
  — `COMPLETED VIA tasks/20260729-staged-application-config-and-full-reload.md`
- [x] `tasks/20260619-generic-session-notifications/020-stage-1-backend-notification-substrate.md`
  — `COMPLETED VIA tasks/20260729-staged-application-config-and-full-reload.md`
- [x] `tasks/20260619-generic-session-notifications/030-stage-1-sdk-and-rn-notification-ui.md`
  — `COMPLETED VIA tasks/20260729-staged-application-config-and-full-reload.md`
- [x] `tasks/20260619-generic-session-notifications/040-stage-1-dummy-plugin-integration-tests.md`
  — `COMPLETED VIA tasks/20260729-staged-application-config-and-full-reload.md`
- [ ] `tasks/20260619-generic-session-notifications/045-stage-1-authoritative-dismissal-retention-history-and-interaction-readiness.md`
- [ ] `tasks/20260619-generic-session-notifications/050-stage-2-interaction-flow-design.md`
- [ ] `tasks/20260619-generic-session-notifications/060-stage-2a-backend-wait-only.md`
- [ ] `tasks/20260619-generic-session-notifications/070-stage-2a-sdk-and-rn-tests.md`
- [ ] `tasks/20260619-generic-session-notifications/080-stage-2b-real-suspend.md`

## Background

MCP auth-required runtime handling exposed a larger platform gap: backend components and tool/runtime plugins need a generic way to communicate useful, actionable information to the user while a request is running or after request preparation finds a recoverable issue.

The immediate MCP/Figma need should use **Mode A** first:

- request continues safely with available tools
- unavailable/auth-required MCP server contributes zero tools
- user receives visible persistent feedback
- user can start login from that feedback
- no blocking wait/resume is required in the first stage

The generic platform feature should be implemented and tested with simplistic dummy plugins first. MCP should consume the generic feature only after the substrate is proven and covered.

## Key Principles

- Reuse existing `ActionDisplayPayload` and action follow-up shapes (`run_action`, `open_url`, `copy_text`, etc.).
- Store notifications persistently in `Session.metadata`, not as model-visible messages by default.
- Publish notification lifecycle events so clients can update in real time.
- Keep notification/interaction semantics plugin-defined. Core should not hardcode choices such as "allow", "deny", or "continue".
- Avoid taking a dependency on the unaccepted CL-150 implementation. Borrow concepts only where they are clean:
  - pending/resolved lifecycle
  - event emission
  - response submission
  - frontend selectors
- Ensure notification failure never breaks the user request.

## Existing Patterns To Reuse

- Backend event store and `/events` endpoint:
  - `core/python/agent_app/events.py`
  - `application/python/agent_terminal_app/server.py`
- Existing session metadata persistence:
  - `core/python/agent_app/application_future.py`
  - `application/python/agent_terminal_app/server.py`
- Existing action display/action follow-up types:
  - `packages/frontend-sdk/src/types/plugins.ts`
  - `mobile/crystal-lattice-control-rn/src/components/ActionDisplayCard.tsx`
  - `mobile/crystal-lattice-control-rn/src/components/ActionResultInlineCard.tsx`
- Existing SDK integration pattern:
  - `packages/frontend-sdk/src/integration/__tests__/actionDeepLinks.integration.test.ts`
- Existing React Native real-backend component integration pattern:
  - `mobile/crystal-lattice-control-rn/__integration__/ServerSettingsModal.realBackend.integration.test.tsx`
  - `mobile/crystal-lattice-control-rn/__integration__/SessionSettingsModal.realBackend.integration.test.tsx`
- Existing React Native real-backend deep-link routing pattern:
  - `mobile/crystal-lattice-control-rn/__integration__/actionDeepLinkRouting.realBackend.integration.test.ts`

## Relationship To MCP Follow-Up

MCP work should depend on Stage 1 of this task. The MCP-specific follow-up details are recorded in:

`tasks/20260611-mcp-oauth-action-deeplinks/015-mcp-auth-required-no-hang-and-login-flow.md`

## Dependencies

- Stage 1 (010–040) has no new task dependencies.
- Stage 2 (050–080) depends on `tasks/20260717-tool-call-interceptor-capability.md` for the blocking-via-tool-call flow. The interceptor task provides the pre-execution hook; this task provides the interaction lifecycle and notification substrate. The two tasks are independent in implementation; the combined user flow (request → tool call → interceptor blocks + emits notification → user responds → interceptor passes through) is proven in Stage 2a/2b of this task.

## Active Stage 1 overlap

`OVERLAP: tasks/20260729-staged-application-config-and-full-reload.md`

The application-reload task's manual-checkpoint follow-up is planned to
implement this task's complete non-blocking Stage 1 (010–040) while also
standardizing display presentation across:

- persistent session notifications;
- owner-memory application notifications;
- direct application/session/message/session-list action responses;
- mobile and React Native macOS hosts.

The shared presentation contract is `banner`, `inline`, and `modal`.
Application-global, session-scoped, and action-response banner payloads use one
connection-aware top banner rail on desktop. Session persistence and lifecycle
remain owned by this task's Stage 1 backend design.

The 010–040 checklist items remain incomplete until their own requirements and
real-backend evidence pass. After implementation, record `COMPLETED VIA
tasks/20260729-staged-application-config-and-full-reload.md` only for fully
satisfied subtasks. Stage 2 interaction work remains independent and is not
included in that overlap.

## Non-Goals For Stage 1

- Do not implement full tool-call interception.
- Do not block request execution waiting for a user response.
- Do not persist notification prompts as model-visible assistant messages.
- Do not copy CL-150 wholesale; it is too broad and contains unrelated churn.

## Success Criteria

### Stage 1

- A dummy plugin can emit a persistent notification during backend work.
- The notification is persisted in session metadata and emitted through events.
- SDK can observe the notification through a real backend.
- Mobile and React Native macOS can render notifications through the standard
  banner, inline, and modal hosts using shared display/action components.
- Session notifications, application notifications, and direct action
  responses share the same presentation semantics; desktop banner
  presentations share one location.
- A notification action can execute through the existing application action flow.
- Notification emission failure does not abort the request.
- Pure demonstration plugins can trigger notification and direct action
  displays without being enabled in production default configuration.

### Stage 2a (wait-only)

- A dummy interceptor can block a tool call, emit an interaction, and wait for a response.
- The user can respond via the existing application action flow.
- The interceptor applies the response (proceed or short-circuit).
- Timeout and cancellation are handled gracefully.

### Stage 2b (real suspend)

- A dummy interceptor can short-circuit with a pending result; the request completes.
- The user can respond; the action handler restarts the request.
- The interceptor is idempotent on restart.
- Timeout and cancellation are handled gracefully.

### Stage 1 follow-up

- Notification dismissal is stored by the same server-side authority as the
  notification record.
- Retention and expiration prevent accidentally permanent active records.
- Notification history and safe historical replay are available through
  portable frontend surfaces.
- The record, action, and frontend contracts are generalized enough for Stage
  2 interactions without implementing the wait/suspend execution flows.

## Execution plan

Added during completion on 2026-07-19.

### Scope changes applied

- Split Stage 2 into Stage 2a (wait-only, `060` + `070`) and Stage 2b (real suspend, `080`).
- Renamed `060-stage-2-backend-interaction-lifecycle.md` → `060-stage-2a-backend-wait-only.md`.
- Renamed `070-stage-2-sdk-and-rn-interaction-tests.md` → `070-stage-2a-sdk-and-rn-tests.md`.
- Added `080-stage-2b-real-suspend.md`.
- Added cross-reference to `tasks/20260717-tool-call-interceptor-capability.md` in `050` and `000`.

### Decisions applied (DP1–DP9, DP14)

- DP1: Keep `severity` as stable machine-readable field; `display.variant` defaults to `severity`.
- DP2: `notification_sink` is a safe wrapper that never raises.
- DP3: `dismiss` is frontend-only; persistent resolution is opt-in via a plugin-defined action.
- DP4: Dummy tool plugin starts as a test fixture; promote to `plugins/` only if integration tests need it.
- DP5: Stage 2 split into 2a (wait-only) and 2b (real suspend).
- DP6: `update` by `id` AND `update_by_key` by `key`; `create` with existing pending `key` updates in place.
- DP7: No new HTTP endpoints for Stage 1; use existing action flow.
- DP8: Cap notification list at 50 most recent by `updated_at`; keep all pending.
- DP9: Stage 2a owns the end-to-end wait-only flow; interceptor task stays generic.
- DP14: `000-main.md` references the interceptor task as a dependency for Stage 2.

### Decisions deferred (DP10–DP13)

- DP10: Wait-only signaling mechanism — see `060-stage-2a-backend-wait-only.md`.
- DP11: Real suspend request restart mechanism — see `080-stage-2b-real-suspend.md`.
- DP12: Interaction response routing — see `050-stage-2-interaction-flow-design.md`.
- DP13: Interaction lifecycle module structure — see `050-stage-2-interaction-flow-design.md`.

These will be decided before Stage 2 implementation begins.