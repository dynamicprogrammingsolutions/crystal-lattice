# Mobile connection lifecycle host

Status: Target documented; implementation partial

This package specification refines the cross-package frontend connection
lifecycle for the Crystal Lattice mobile application. It owns the mobile host
architecture, native application lifecycle integration, connection wizard and
repair coordination, persistence adapters, multi-runtime presentation host,
and iOS/Android verification needed to conform to the broader contract.

Broader contracts:

- [Frontend connection lifecycle and offline continuity](../../../../../../docs/development/specifications/frontend-connection-lifecycle/index.md)
- [Mobile connection and offline UX](../../../../../../docs/development/specifications/frontend-connection-lifecycle/mobile-ux.md)
- [Bridge connectivity](../../../../../../docs/development/specifications/bridge-connectivity/index.md)
- [Chat transcript navigation](../../../../../../docs/development/specifications/chat-transcript-navigation/index.md)
- [Notifications](../../../../../../docs/development/specifications/notifications/index.md)

Package specification documents:

- [Technical host contract](technical-spec.md)
- [Requirements and evidence](requirements.md)

## Ownership

The root specification owns product behavior, portable lifecycle semantics,
shared controller/adapter requirements, persistence guarantees, and mobile UX.
This package refinement owns:

- the lifecycle-controller instance and subscription hosted by the mobile app;
- React Native `AppState`, Linking, Bonjour, and connection-wizard integration;
- direct, discovery, bridge, and cloud factory injection;
- mobile focus, selected-session, and bottom-navigation state mapping;
- native persistence and attachment-file integration;
- multiple open runtime resource handling;
- production selectors and iOS/Android acceptance boundaries.

Current implementation documentation under mobile `docs/development/`
describes delivered code and must not present this target as already
available.

## Scope

The target covers:

- migration from one global transport/backend to the shared runtime map;
- authoritative manual, discovery, bridge, cloud, saved-open, and repair
  attempts;
- one-runtime compatibility during migration and final multiple-open behavior;
- cache-first launch and offline workspace navigation;
- stable connection/session ownership for screens, events, deep links, and
  drafts;
- foreground/background behavior for every open runtime;
- complete mobile draft storage and restoration;
- accessible status/actions and native race/offline/relaunch verification.

## Current and target boundary

Mobile currently has:

- saved records for every supported connection kind;
- direct and bridge/cloud transport factories;
- a connection wizard and bridge repair flow;
- one global runtime and selected connection;
- per-connection sessions and per-connection/session message caches;
- partial cached-screen and text-draft restoration;
- production Detox harnesses for selected connection and transcript behavior.

The package target remains partial until connection operations use shared
authority, focus is independent from runtime success, several runtimes can
remain open, offline navigation is complete, and full drafts survive
application/process lifecycle.

## Explicit exclusions

This package specification does not:

- redefine shared lifecycle state or adapter contracts;
- redefine bridge wire protocol or mode routing;
- define backend session/message semantics;
- add automatic offline sending or mutation replay;
- require automatic reopening of every runtime after process restart;
- redefine transcript viewport or notification lifecycle behavior.