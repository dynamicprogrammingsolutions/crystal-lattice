# Decision 001: Separate saved, focused, runtime, and attempt state

Status: Accepted

Date: 2026-08-23

## Context

Mobile currently coordinates one saved selection, transport/backend, wizard,
and asynchronous connection work through overlapping component state. Desktop
already distinguishes focused and open connections but keeps its runtime
coordinator locally. Conflating these concepts makes offline focus difficult
and allows runtime completion to control navigation.

Future multiple-open behavior requires the same separation even if mobile
initially permits one live runtime.

## Decision

The portable model distinguishes:

- durable saved connection records;
- focused connection/workspace;
- zero or more live runtimes keyed by connection ID;
- in-progress attempts with independent identity and terminal state;
- connection/session-scoped navigation, caches, and drafts.

The shared lifecycle controller is multi-runtime-capable. A frontend may apply
a one-open-runtime policy as presentation/runtime policy rather than changing
the state model.

## Consequences

- Cached content can be focused without network success.
- Closing a runtime does not imply deleting or unfocusing a connection.
- Multiple open connections become an incremental UI capability.
- Mobile and desktop can share lifecycle semantics while retaining platform
  navigation.
- Existing global transport/backend consumers require an adapter or staged
  migration.

## Alternatives not selected

Keeping a single global active connection and adding more booleans would be a
smaller immediate edit, but would preserve the source of stale-operation,
offline-focus, and future multi-open problems.

Persisting runtime status was not selected. Runtime resources and transient
status are reconstructed; durable focus, cache, and draft state are restored.