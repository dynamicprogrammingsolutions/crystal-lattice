# Subagent Session Notifications

Use the generic session notification substrate as the first real feature integration by publishing persistent, non-model-visible parent-session notifications for important child-agent lifecycle transitions.

## Requirements checklist

- [ ] Wait for the persistent subagent core and generic session notification Stage 1 to be complete.
- [ ] Publish a persistent parent-session notification when a child run completes, fails, is interrupted, or is recovered.
- [ ] Store notifications through the generic notification API rather than adding model-visible parent messages.
- [ ] Correlate and deduplicate notifications by child session and child run identity.
- [ ] Include enough structured information to identify the child session, originating parent session, run status, and relevant error/recovery detail.
- [ ] Reuse existing action-display/follow-up capabilities for child inspection or applicable subagent actions without requiring custom notification UI.
- [ ] Ensure notification creation failure never breaks the parent or child request.
- [ ] Add real integration coverage proving persistence, event delivery, deduplication, and action execution where applicable.
- [ ] Keep blocking user interactions and approval/question flows outside this Stage 1 consumer.

Depends On:

- `tasks/20260715-persistent-plugin-subagents/000-main.md`
- `tasks/20260619-generic-session-notifications/040-stage-1-dummy-plugin-integration-tests.md`

## Relationship and purpose

This task is intentionally not part of the core persistent subagent definition of done. Core subagent execution, waiting, result delivery, persistence, and restart recovery must work without generic notifications.

The generic notifications task requires its substrate to be proven with dummy plugins before feature-specific adoption:

- `tasks/20260619-generic-session-notifications/000-main.md`

Subagents are intended to be the first real feature consumer after that Stage 1 proof.

## Notification scope

Notifications should be useful when child work changes state outside the user's immediate view, especially for:

- Background Codex-compatible child completion
- Child failure
- Child interruption after shutdown or cancellation
- Successful recovery/restart of an interrupted child

Notifications remain persistent session metadata and are not inserted into model-visible conversation history by default.

The existing generic action display and action follow-up shapes should be reused. New frontend components are out of scope unless the generic notification task itself identifies a platform gap.

## Non-goals

- Making generic notifications a dependency of core subagent tools
- Replacing Codex `wait` or blocking Kimi/Gemini tool results
- Automatically steering or resuming the parent model
- Blocking a child while awaiting a user response
- Child approval or question workflows
- Parent/child tree navigation UI

Blocking child interactions may be planned later after generic session notification Stage 2 is complete:

- `tasks/20260619-generic-session-notifications/070-stage-2-sdk-and-rn-interaction-tests.md`

## Definition of done

- Lifecycle notifications are persisted on the parent session through the generic notification substrate.
- Restarting the application does not lose unresolved notifications.
- Duplicate lifecycle processing does not create duplicate notifications for the same child run and transition.
- Notifications are observable through generic events and existing SDK/UI support.
- Available actions execute through the existing generic application action flow.
- Notification failures are isolated from subagent execution.