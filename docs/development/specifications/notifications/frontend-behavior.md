# Portable frontend notification behavior

This page defines framework-independent frontend behavior. Current TypeScript,
React, React Native, mobile, and desktop implementation names are not part of
the contract.

## Inputs

A frontend combines:

- authoritative persisted session notification records;
- authoritative application notification snapshots;
- session notification lifecycle events;
- application notification lifecycle events;
- action-display payloads embedded in notification records.

Stable IDs upsert existing lifecycle items. Higher revisions supersede lower
revisions.

## Ownership

- Application notifications are connection-level.
- Session notifications belong to one exact session.
- A notification must not appear on an unrelated connection or session.
- Displays received while another surface is active remain eligible for
  presentation when their owning surface opens.

## Presentation

- `banner` uses the owning surface's normal-flow notification rail.
- `inline` uses the owning session or initiating action region.
- `modal` uses a platform-appropriate modal; desktop may provide a documented
  inline fallback.

Info, success, warning, and error variants must remain visually and
accessibly distinguishable.

## Dismissal, refresh, and resolution

Dismissal invokes the owning server notification operation. The initiating
frontend removes the item after a successful response.

An already-open frontend on another device may keep its current display until
it refreshes or reconnects. Immediate cross-device removal is not required.
A newly opened or rehydrated frontend uses authoritative state and does not
present dismissed, resolved, or expired records as active.

## Follow-up actions

Notification actions use the common action-display follow-up contract. The
frontend preserves connection and session context when executing an action and
preserves fixed parameters, parameter mappings, embedded forms, and submitted
form values. A returned display uses the same presentation policy.

Active interactions do not expose ordinary dismiss.

## Notification history

Relevant top action bars expose a stable, pinnable Notifications action.

The history surface provides:

- compact active and terminal rows;
- status, severity, time, connection, and session filtering as applicable;
- scope-correct application and exact-session history;
- a waiting-for-input indicator that navigates to an active interaction;
- local Show again for stored rich inline/modal content.

Show again does not reactivate the record. Historical mutating actions are
hidden unless explicitly safe and server-validated.

## Reconnect

Session metadata is authoritative after session reload or reconnect.
Application frontends hydrate from the current owner notification snapshot
before or alongside event polling.

Server-lifetime application records expire on owner-process restart. Longer
retention requires a correspondingly durable application notification store.