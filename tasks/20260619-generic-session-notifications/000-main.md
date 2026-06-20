# Generic Session Notifications And Interactions

Create a generic platform feature for persistent, evented session notifications that can reuse existing action display/action form UI. Implement it in two stages: non-blocking notifications first, then interactive/blocking flows.

## Task checklist

- [ ] `tasks/20260619-generic-session-notifications/010-stage-1-notification-design.md`
- [ ] `tasks/20260619-generic-session-notifications/020-stage-1-backend-notification-substrate.md`
- [ ] `tasks/20260619-generic-session-notifications/030-stage-1-sdk-and-rn-notification-ui.md`
- [ ] `tasks/20260619-generic-session-notifications/040-stage-1-dummy-plugin-integration-tests.md`
- [ ] `tasks/20260619-generic-session-notifications/050-stage-2-interaction-flow-design.md`
- [ ] `tasks/20260619-generic-session-notifications/060-stage-2-backend-interaction-lifecycle.md`
- [ ] `tasks/20260619-generic-session-notifications/070-stage-2-sdk-and-rn-interaction-tests.md`

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

## Non-Goals For Stage 1

- Do not implement full tool-call interception.
- Do not block request execution waiting for a user response.
- Do not persist notification prompts as model-visible assistant messages.
- Do not copy CL-150 wholesale; it is too broad and contains unrelated churn.

## Success Criteria

- A dummy plugin can emit a persistent notification during backend work.
- The notification is persisted in session metadata and emitted through events.
- SDK can observe the notification through a real backend.
- React Native can render the notification using existing display/action components.
- A notification action can execute through the existing application action flow.
- Stage 2 has a clear design path for blocking interactions without forcing Stage 1 to solve suspension/resume.