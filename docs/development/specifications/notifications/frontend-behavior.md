# Portable frontend notification behavior

This page defines framework-independent frontend behavior. Current TypeScript,
React, React Native, mobile, and desktop implementation names are not part of
the contract.

## Inputs

A frontend combines:

- persisted session notification records;
- application notification events/state;
- session notification lifecycle events;
- action-display payloads embedded in notification records.

Stable IDs upsert existing lifecycle items. A later `updated_at` replaces the
displayed revision.

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

## Current dismissal and resolution

The implemented frontend keeps dismissed display revisions locally. Local
dismissal leaves backend notification state unchanged. A later notification
revision is eligible for presentation. Backend resolution removes the
notification from active presentation.

## Follow-up actions

Notification actions use the common action-display follow-up contract. The
frontend preserves connection and session context when executing an action and
routes a returned display through the same presentation policy.

## Reconnect

Session metadata is authoritative after session reload or reconnect.
Application notification events are owner-lifetime state and are not durable
across owner-process restart.