# Frontend connection lifecycle and offline continuity

Status: Target documented; current implementation partial

This cross-package specification defines how Crystal Lattice frontends save,
focus, open, reconnect, repair, close, and present connections while preserving
cached work and composed messages through network and application lifecycle
changes.

It treats a saved connection, the workspace the user is viewing, a live
transport/backend runtime, and an in-progress connection attempt as separate
concepts. That separation is the basis for deterministic cancellation,
non-destructive connection switching, offline navigation, durable drafts, and
multiple concurrently open connections.

Specification documents:

- [Product behavior and target user experience](product-spec.md)
- [Portable frontend behavior](frontend-behavior.md)
- [Mobile connection and offline UX](mobile-ux.md)
- [Technical contract](technical-spec.md)
- [Persistence and offline continuity](persistence-and-offline.md)
- [Requirements and evidence](requirements.md)
- [Decision 001: separate saved, focused, runtime, and attempt state](decisions/001-separate-connection-state.md)
- [Decision 002: operation authority and candidate promotion](decisions/002-operation-authority-and-cancellation.md)
- [Decision 003: durable drafts and draft-safe eviction](decisions/003-draft-durability-and-eviction.md)

## Ownership

The target is cross-package because no one package currently owns the complete
user-visible lifecycle:

| Responsibility | Current owner |
| --- | --- |
| Saved connection record types, request transports, backend adapter, and shared cache primitives | `packages/frontend-sdk` |
| React controller bindings used by frontend hosts | `packages/frontend-sdk-react` |
| Direct, discovery, bridge, and cloud connection UX; native application lifecycle; mobile navigation | `mobile/crystal-lattice-control-rn` |
| Focused connection, multiple open runtimes, cached workspaces, and desktop tabs | `desktop/crystal-lattice-control-desktop-rn` |
| Bridge pairing, resume, and proxy transport contract | Bridge service, terminal application, and frontend SDK under the bridge-connectivity specification |
| Cloud connection-link and proxy behavior | `cloud-orchestrator` and the frontend SDK cloud transport |

The shared specification owns portable outcomes and coordination. Each
frontend retains platform-specific presentation and native lifecycle
integration.

## Scope

The target covers:

- connection records and stable connection identity;
- focus independently from live runtime availability;
- opening, validating, reconnecting, repairing, cancelling, closing, and
  superseding connection attempts;
- lifecycle status and portable error categories across direct, discovery,
  bridge, and cloud connections;
- navigation authority when asynchronous operations overlap;
- offline access to cached sessions and messages;
- per-connection and per-session workspace state;
- durable text and attachment drafts;
- cache freshness, hydration, eviction, and explicit local-data removal;
- a runtime model capable of multiple open connections;
- mobile and desktop refinements and verification boundaries.

## Relationship to existing specifications

- [Bridge connectivity](../bridge-connectivity/index.md) owns bridge discovery,
  pairing credentials, resume, transport-mode routing, wire protocol, and
  proxy behavior. This specification owns how a frontend presents and
  coordinates those operations with focus, cancellation, repair, offline
  state, and navigation.
- [Chat transcript navigation](../chat-transcript-navigation/index.md) owns
  loaded message ranges and transcript viewport behavior. This specification
  owns whether a connection/session workspace remains available and correctly
  scoped while offline or switching connections.
- [Notifications](../notifications/index.md) owns notification lifecycle and
  presentation. This specification owns which connection runtimes are open or
  focused and requires background lifecycle effects not to take navigation
  control.
- Application route payloads, session consistency, and provider behavior
  remain with their existing owners.

## Current and target boundary

Implementation is tracked by
`tasks/20260823-frontend-connection-lifecycle/000-main.md`.

Current frontends already provide portions of the target:

- saved connection records for direct, discovery, bridge, and cloud access;
- per-connection session caches and per-connection/session message caches;
- cached mobile screens that can render without a backend when a connection
  is already focused;
- partial mobile text-draft persistence;
- desktop focus independent from runtime status and multiple direct HTTP
  runtimes.

The complete requirements remain partial because current asynchronous
connection operations lack common authority and cancellation semantics,
mobile focus is normally established only after network success, drafts do not
durably include attachments, and desktop connection completion can outlive a
close operation.

## Explicit exclusions

This specification does not define:

- bridge or cloud wire formats;
- the semantics of proxied application routes;
- automatic replay of failed mutations;
- an automatic offline send queue;
- one shared native navigation implementation;
- background push delivery;
- transcript range or viewport behavior;
- notification content or lifecycle;
- permanent storage of server-owned session data beyond frontend cache policy.