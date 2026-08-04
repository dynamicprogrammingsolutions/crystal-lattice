# Core and Application Runtime Implementation Documentation

Document how the current Python packages implement the root reload,
notification, and action-display contracts without making package internals the
normative cross-package source.

## Requirements checklist

- [x] Core Python development documentation explains stable owner internals,
  replaceable application lifetime, operation admission, swap/rollback, and
  cleanup.
- [x] Core Python development documentation explains session-notification
  persistence, locking, event/checkpoint publication, pruning, reconciliation,
  and tool sink behavior.
- [x] Application Python development documentation explains server/terminal
  owner construction, shared server-console wiring, HTTP admission errors,
  event exposure, shutdown, and MCP cleanup.
- [ ] Package docs explicitly map implementation sections to `RLD-*`, `NTF-*`,
  and relevant `DSP-*` requirements.
- [x] User/operator reload guidance is separated from implementation internals.
- [x] Existing useful application README content is moved or linked without
  leaving a competing long-form source.

Parent Task:
`tasks/20260730-runtime-notification-specification-documentation/000-main.md`

Depends On:

- `tasks/20260730-runtime-notification-specification-documentation/010-notification-and-action-display-contracts.md`
- `tasks/20260730-runtime-notification-specification-documentation/030-application-runtime-reload-specification.md`

## Proposed artifacts

```text
core/python/docs/development/
├── application-owner.md
└── notification-implementation.md

application/python/docs/
├── runtime-reload.md
└── development/
    └── runtime-owner-integration.md
```

Use package `docs/index.md` or development indexes only if needed for routing
under the repository documentation profile; do not add empty placeholders.

## Core application-owner content

- Object/lifetime diagram for process → owner → current application.
- `ApplicationOperation` admission and release.
- condition variable and active-operation count.
- factory and `ApplicationControl` relationship.
- reload request uniqueness and retained notification.
- candidate construction, listener update, swap, rollback, and closure.
- owner close and reload-thread behavior.
- event-store ownership and best-effort publication.
- runtime-injected durable application notification storage shared by
  replacement application generations.
- cleanup responsibilities delegated to `AgentApplication.close()`.
- code links to `application_owner.py` instead of duplicating every method.

## Core notification implementation content

- `SessionNotifications` and thin `AgentApplication` APIs.
- application-owner notification storage and lifetime.
- normalized record validation.
- notification/interaction kind and lifecycle transition validation.
- explicit revision and stale mutation handling.
- server-owned dismissal and expiration.
- retention evaluation and active/history pruning.
- live-session loading and readonly snapshot constraints.
- session lock around read-modify-write.
- immutable `Session` replacement and save path.
- checkpoint publication.
- same-key pending update and update-by-ID/key.
- pending-preserving resolved-item pruning.
- interaction with request checkpoint metadata reconciliation.
- `NotificationSink` failure boundary in tool context.
- application current-state snapshot/list support.
- focused unit and concurrency evidence.

This page maps implementation to root requirement IDs. It must not repeat the
root lifecycle, persistence, or frontend behavior explanation.

## Application integration content

- owner creation and `TerminalApplication` role.
- dependency injection into FastAPI routes.
- server and interactive console sharing the same current application.
- which routes/operations acquire and retain admission.
- HTTP 503 payload for pending reload.
- bridge/Bonjour/listener lifetime.
- reload action response versus later notification events.
- dismissal mutation responses and authoritative notification hydration.
- config/env reread and application-config plugin relationship.
- MCP and runtime cleanup before completion.
- graceful process shutdown.
- operator troubleshooting and manual reload test sequence.

Notification HTTP/event/bridge integration belongs as a section of
`runtime-owner-integration.md` unless the package-specific content becomes
large enough to justify extraction.

## Existing documentation to classify

- `application/python/README.md` contains current reload and endpoint text.
- `docs/api/events.md` contains cross-package notification material that should
  point to the root contract, while package-specific transport mechanics can
  move package-locally.
- The application documentation migration directions in
  `tasks/20260728-package-local-documentation-standard/040-application-and-plugin-documentation-migration.md`
  are reference context, not a dependency.

## Status audit — August 3, 2026

The Core and Application implementation pages exist and describe the current
durable notification store and shared request-owner wiring. The remaining
unchecked requirement is explicit section-level mapping to the relevant
`RLD-*`, `NTF-*`, and `DSP-*` identifiers; current pages mostly link to the
root specifications without a concise mapping table.
