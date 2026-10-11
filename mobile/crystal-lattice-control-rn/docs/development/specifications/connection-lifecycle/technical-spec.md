# Mobile connection lifecycle host technical specification

## Architecture

The target mobile host composes shared lifecycle and storage abstractions with
React Native integration:

```text
saved records + workspace persistence
                |
                v
mobile lifecycle host ---- shared lifecycle controller ---- kind adapters
        |                           |                            |
        |                           v                            v
        |                    runtime snapshots          transport/backend
        v
Home / Connections / Sessions / Messages
        |
        v
session caches + complete drafts
```

`App.tsx` or a focused host hook owns application-wide integration. It does not
implement operation authority by coordinating unrelated booleans. Screen
components consume connection-scoped snapshots and typed commands.

## Controller ownership

The mobile application creates one shared lifecycle-controller instance for
the mounted application host. It:

- injects mobile transport factories and timeout policy;
- subscribes through the existing shared React binding;
- disposes attempts and runtimes at host teardown;
- exposes backend lookup by connection ID;
- preserves immutable snapshots in React state;
- never persists runtime resources.

The final snapshot may contain several open runtimes. A staged compatibility
policy may temporarily retain one runtime while screens migrate, but no
component assumes that the runtime map has at most one entry.

## Durable and transient state

Durable state includes:

- saved connection records and credentials;
- focused connection ID;
- selected session per connection;
- sessions/messages caches and freshness;
- transcript preferences;
- complete session drafts.

Transient state includes:

- runtime transport/backend objects;
- active attempts and abort controllers;
- temporary wizard/repair candidates;
- current native discovery scan;
- in-memory event-stream state;
- non-durable visual progress.

Durable writes wait for store hydration. Initial empty React state cannot
overwrite loaded records.

## Connection factory injection

The host supplies:

- manual/discovery direct HTTP factory using mobile timeout rules;
- bridge factory using HTTP by default or an app-wide development override,
  retaining saved server identity and pairing fields;
- cloud factory retaining orchestrator routing and token fields;
- readiness functions where the shared adapter requires them;
- redacted diagnostic callbacks.

The shared controller owns attempt authority and candidate promotion. The host
does not set a backend or navigate directly after an unguarded await.

All historical saved bridge modes resolve to HTTP unless an explicit app-wide
development override is active. No mobile lifecycle operation adds
fallback/replay between bridge transport families. Preference changes affect
later construction and do not replace an active runtime.

## Wizard attempt model

An unsaved wizard owns one temporary operation scope. Method selection,
Bonjour scan, bridge discovery, pairing request, code submission, manual/cloud
validation, and Cancel all use that scope.

Cancel:

- invalidates authority before physical cleanup;
- stops the current discovery scan;
- disconnects temporary bridge resources;
- clears method-specific presentation;
- prevents late alert, record creation, credential update, focus, or
  navigation.

Starting a later wizard creates a new scope/generation. Native discovery
callbacks carry the owning generation so old results cannot populate it.

Successful unsaved validation creates exactly one saved record and then may
focus it under current user intent.

## Saved open and repair

Opening a saved record:

1. focuses its workspace if requested;
2. begins an authoritative connection-scoped attempt;
3. creates and validates a candidate;
4. promotes it without closing other runtimes in final multi-open mode;
5. returns a typed result to current navigation intent.

Bridge repair carries the existing saved connection ID. It may update pairing
credential, server metadata, and mode-compatible runtime fields only while
authoritative. Cache, selected session, and draft ownership never migrate to a
new ID.

Repair cancellation leaves the saved connection focused/offline as applicable
and permits a later newly initialized repair attempt.

## Focus and navigation mapping

The host persists one focused connection and one selected session per
connection. Bottom navigation remains one UI selection independent from
runtime state.

Screen identity and callbacks use `(connectionId, sessionId)`:

- Home aggregates cached summaries across saved connections and navigates only
  under current explicit user intent;
- Sessions uses the focused connection;
- Messages uses that connection's selected session;
- switching focus restores the destination state for the new connection;
- same-named sessions on different connections cannot share controllers,
  caches, subscriptions, or drafts.

Lifecycle state changes do not call navigation APIs. Typed success from a
current user intent may select a destination; background recovery never does.

## Multiple open runtime host

The Connections screen derives each row from its saved record plus runtime and
attempt snapshots. Several rows may be Open.

The host:

- keeps every user-open runtime in the shared map;
- provides all open backends to connection-level display/notification hosts;
- provides only the focused backend to focused Sessions/Chat consumers;
- preserves each connection's selected session and draft while unfocused;
- closes only the explicitly selected runtime;
- reports any resource limit before asking the user which runtime to close.

No silent least-recently-used runtime closure is allowed.

## Application lifecycle

On background:

- flush focused and unfocused draft/workspace writes;
- invalidate non-durable native wizard callbacks as required;
- call adapter preparation/disconnect for each stateful open runtime;
- retain the in-process desired-open set for foreground recovery;
- keep focus/cache/navigation unchanged.

On foreground:

- start independent generation-scoped recovery for eligible desired-open
  runtimes;
- update each row independently;
- route repair-required results to their rows without opening a modal or
  changing focus;
- never serialize unrelated runtime recovery through one global flag.

After process restart, runtime objects and the desired-open set are rebuilt
only under the documented reopen policy. The baseline restores workspaces
offline and does not open every saved connection automatically.

## Events, notifications, and deep links

Open runtimes may continue connection-level event and notification
observation while unfocused. Every envelope retains connection ID.

Session event streaming remains active only under the package's bounded
resource policy. If unfocused Chat controllers are unmounted, authoritative
connection-level invalidations remain observable and session state converges
when remounted.

Deep links resolve a backend by target connection ID across all open runtimes.
If none exists, the action remains pending and offers opening that connection.
Any focus/session navigation is explicit current deep-link intent.

## Offline caches

Saved records, focused workspace, and caches hydrate independently from
runtime opening. A focused closed/unavailable connection supplies:

- cached Sessions and freshness to Sessions;
- cached Messages/range/viewport/draft to Messages;
- `null` backend to server-authoritative controllers.

Local actions remain active. Server actions are gated at their action
boundary. A failed refresh retains prior cache and server freshness.

Sessions cache persistence uses a guarded/versioned structure. A malformed
entry is isolated. Message-cache and draft writes use separate freshness and
retention semantics.

## Complete mobile drafts

The package consumes the shared versioned draft contract. Mobile-specific
content storage:

- copies ephemeral picker content into app-private storage before claiming
  durability;
- retains durable server asset references where available;
- persists attachment order, placement, metadata, readiness, preview identity,
  and recovery state;
- cleans app-owned content only after no draft revision references it;
- surfaces storage/quota failure.

Text and attachment changes flush on bounded debounce, blur, navigation,
background, and host disposal. Acknowledgement clears only the submitted
revision. Uncertain sends persist idempotent recovery.

## Deletion boundaries

Mobile commands distinguish:

- close runtime;
- forget/repair credentials;
- clear server-derived cache;
- discard one draft;
- delete saved connection and selected local state.

UI confirmation and storage commands share one explicit deletion scope. A
connection row cannot remove drafts through an unlabelled cache operation.

## Accessibility and native verification

Production selectors derive from stable connection/session IDs. Required
selectors cover:

- row focus/status/Open/Cancel/Close/Retry/Re-pair;
- wizard method, server rows, pairing fields, and Cancel;
- Sessions/Messages offline and freshness state;
- selected session per connection;
- draft save/error and attachment recovery;
- connection-scoped displays.

Shared deterministic tests own operation order. Mobile Jest/component tests own
host mapping and presentation. Detox on iOS and Android verifies:

- Cancel with a late result;
- A/B reversed completion;
- bridge repair cancel/reopen;
- offline relaunch;
- complete draft restoration;
- two concurrently open runtimes, focus switching, failure isolation, and
  closing one into offline continuity.

Native tests use production screens and adapters or deterministic production
adapter injection rather than duplicate test-only UI.

## Compatibility

The host migration preserves:

- existing saved connection IDs and records;
- HTTP product mode for new and historical bridge records;
- explicit legacy development overrides and no fallback;
- current backend HTTP contracts;
- connection/session cache key identity;
- bottom navigation;
- explicit user control over connection opening.