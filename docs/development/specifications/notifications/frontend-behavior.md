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
- Mobile modal notifications use the full-application native modal boundary,
  matching ordinary modal action responses.

Info, success, warning, and error variants must remain visually and
accessibly distinguishable.

## Dismissal, refresh, and resolution

Dismissal invokes the owning server notification operation and targets the
displayed notification ID. It accepts an optional `expected_revision` so a
stale user gesture cannot hide a newer revision. The initiating frontend may
first persist a local dismissal entry for the exact displayed revision and hide
that revision optimistically.

If the mutation fails, that exact revision remains hidden. When the same active
ID and revision is observed again, the frontend may resend the unchanged
dismissal request.

If a later producer publishes a newer revision for the same notification key,
the frontend can present that newer revision even when a cached dismissal exists
for the older revision.

The cache is never promoted to a newer revision. If authoritative state
contains the same ID at a newer pending revision, the cached dismissal is
obsolete, is removed, and the newer revision is presented normally. A
terminal or missing record also removes the cache entry.

### Race behavior

When a producer publication and a user dismissal race, the revision decides:

```text
frontend displays revision 5
        ↓
plugin publishes revision 6
        ↓
dismiss(expected_revision=5) conflicts
        ↓
revision 6 remains visible
```

The reverse order creates a new occurrence:

```text
frontend dismisses occurrence A revision 5
        ↓
occurrence A becomes terminal
        ↓
plugin publishes the stable key again
        ↓
new pending occurrence B becomes visible
```

The frontend never retargets a dismissal to the newer revision or occurrence.
A stale dismissal cannot hide a newer revision or a later stable-key
occurrence.

An already-open frontend on another device may keep its current display until
it refreshes or reconnects. Immediate cross-device removal is not required.
A newly opened or rehydrated frontend uses authoritative state and does not
present dismissed, resolved, or expired records as active.

## Refresh effects

Only a pending notification revision that explicitly carries a refresh effect
requests execution. Snapshot and event observation of the same revision does
not repeat the request. Presentation-only updates and dismissed, resolved, or
expired revisions do not inherit or repeat an earlier effect.

Refresh effects are limited to the owning connection:

- a session reload refreshes the matching active or mounted session;
- a session-list reload refreshes the owning connection's collection;
- an application-action reload refreshes definitions and related application
  UI schema for the owning connection.

The frontend does not navigate because of a notification effect.

If a matching consumer cannot reload immediately, the invalidation remains
available. An inactive mounted consumer may defer until activation. A consumer
mounted later receives the pending invalidation. Cached data is not considered
authoritative after the invalidation until reload succeeds.

A successful authoritative reload acknowledges the invalidation. Failure
leaves it pending. Frontend rerender or resubscription does not create
concurrent duplicate reloads for the same target and invalidation revision.
A late completion for an older invalidation does not clear a newer one.

Action responses use the same explicit refresh field meanings, but they remain
one-shot and may additionally navigate or derive policy from declared
mutations. Those action-only behaviors are not inferred for notifications.

## TTL presentation

A TTL deadline is checked when a frontend host first observes or rehydrates a
notification. An elapsed TTL record is not presented by that fresh host.

Once a host has accepted a notification before its deadline, passage of time
does not remove it. The accepted identity is retained only in host memory.
Reopening the application, reconnecting, or reconstructing the owning host
performs the deadline check again. TTL alone does not create a lifecycle event
or replace explicit dismissal and resolution.

An explicit dismissed, resolved, or expired record is terminal regardless of
its TTL deadline and is not presented as active on a fresh host.

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

Application notification records and terminal history use the configured
durable store. Records with explicit server-lifetime retention expire according
to owner-restart recovery semantics rather than disappearing because the whole
store is memory-only.