# Desktop connection lifecycle host

Status: Target documented; implementation partial

This package specification refines the cross-package frontend connection
lifecycle for the Crystal Lattice macOS desktop application. It owns the
desktop lifecycle-controller host, multiple-runtime mapping, focused
connection and active-tab coordination, native connection-window events,
cached pane restoration, complete desktop drafts, and macOS verification
needed to conform to the broader contract.

Broader contracts:

- [Frontend connection lifecycle and offline continuity](../../../../../../docs/development/specifications/frontend-connection-lifecycle/index.md)
- [Desktop connection and offline UX](../../../../../../docs/development/specifications/frontend-connection-lifecycle/desktop-ux.md)
- [Chat transcript navigation](../../../../../../docs/development/specifications/chat-transcript-navigation/index.md)
- [Notifications](../../../../../../docs/development/specifications/notifications/index.md)

Package specification documents:

- [Technical host contract](technical-spec.md)
- [Requirements and evidence](requirements.md)

## Ownership

The root specification owns product behavior, portable lifecycle semantics,
shared controller/adapter requirements, persistence guarantees, and desktop
UX. This package refinement owns:

- the lifecycle-controller instance hosted by `DesktopRoot`;
- manual direct HTTP adapter consumption and later supported-kind host wiring;
- Connections/Sessions/session-tab/Chat state mapping;
- separate native connection-editor and popover event authority;
- persistent tabs, bounded warm panes, and cache/draft remount behavior;
- connection-level display aggregation from several runtimes;
- production selectors and macOS XCUITest boundaries.

Current package development pages describe delivered code and must not present
this target as already available.

## Scope

The initial target covers:

- migration of the manual direct HTTP runtime hook to the shared controller;
- authoritative Open/Cancel/Close/Retry and edited candidate promotion;
- existing several-open-runtime behavior;
- deterministic focused-connection and active-tab policy;
- runtime status convergence after later failures;
- offline Sessions and persistent cached Chat tabs;
- offline text composition and complete draft restoration;
- native window cancellation and macOS acceptance tests.

## Current and target boundary

Desktop currently has:

- saved manual records and a separate connection editor window;
- several open direct HTTP runtimes;
- focused connection independent from active session tab;
- cached offline Sessions and Messages;
- persistent connection/session tabs with a bounded warm-pane set;
- debounced text-draft persistence;
- connection-scoped notification aggregation.

The package target remains partial because Open has no stale-completion
authority, Connecting cannot be cancelled from the row, later failures do not
converge runtime status, follow-active-tab does not focus another connection,
offline Chat is read-only, and attachment/uncertain-send drafts are not
durable.

## Explicit exclusions

This initial package target does not:

- add desktop bridge, cloud, or Bonjour connection UI;
- redefine shared lifecycle/controller contracts;
- redefine backend session/message behavior;
- automatically reopen every connection represented by a restored tab;
- automatically send/replay offline work;
- replace macOS native window/popover conventions;
- redefine transcript viewport or notification lifecycle behavior.