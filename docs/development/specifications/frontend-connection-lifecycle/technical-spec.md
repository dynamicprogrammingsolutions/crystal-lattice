# Frontend connection lifecycle technical specification

## Architecture

The target separates durable records, workspace selection, runtime resources,
attempt coordination, and cached data:

```text
saved connection store
        |
        v
connection lifecycle controller ---- connection-kind adapters
        |                                      |
        |                                      v
        |                               transport + backend
        v
focused workspace/navigation
        |
        v
session/message/draft caches
```

The lifecycle controller is a shared portable abstraction. React bindings and
application hosts adapt its state to platform UI. Native discovery and
application-lifecycle signals remain in the owning frontend but invoke typed
controller operations.

## State model

A representative portable state shape is:

```ts
type ConnectionRuntimeStatus =
  | 'closed'
  | 'opening'
  | 'open'
  | 'reconnecting'
  | 'unavailable'
  | 'repair_required'
  | 'error';

interface ConnectionRuntimeState {
  connectionId: string;
  generation: number;
  status: ConnectionRuntimeStatus;
  transport?: Transport;
  backend?: AgentBackend;
  error?: ConnectionLifecycleError;
  lastConnectedAt?: number;
}

interface ConnectionAttemptState {
  attemptId: string;
  connectionId?: string;
  generation: number;
  kind: 'open' | 'reconnect' | 'repair' | 'pair' | 'validate';
  status: 'active' | 'cancelling' | 'succeeded' | 'failed' | 'cancelled' | 'superseded';
}

interface ConnectionWorkspaceState {
  focusedConnectionId: string | null;
  selectedSessionByConnectionId: Record<string, string | null>;
}
```

Runtime objects are not persisted. Saved records, workspace selection, caches,
and drafts use versioned persistent representations.

The controller supports a runtime map keyed by connection ID. A host may apply
a one-open-runtime policy without reducing the underlying state to one global
transport/backend pair.

## Connection-kind adapter contract

Transport request semantics remain in the existing `Transport` interface.
Lifecycle behavior uses a separate adapter contract so stateless HTTP,
stateful bridge transports, and cloud routing are not forced into one concrete
transport class.

A connection-kind adapter provides the equivalent of:

```ts
interface ConnectionKindAdapter<TRecord extends ConnectionRecord> {
  createCandidate(
    record: TRecord,
    context: ConnectionOperationContext,
  ): Promise<ConnectionCandidate>;
  validate(
    candidate: ConnectionCandidate,
    context: ConnectionOperationContext,
  ): Promise<void>;
  close(candidateOrRuntime: ConnectionCandidate | ConnectionRuntime): void;
}
```

`ConnectionOperationContext` includes attempt ID, generation, abort signal,
timeouts, and diagnostic hooks that do not contain credentials.

Bridge adapters additionally coordinate discovery, pairing, credential
validation, resume, and repair while retaining the same operation-authority
contract. Platform discovery may produce a direct record candidate but does
not bypass validation.

Every adapter maps non-success responses and transport exceptions into
portable lifecycle errors. Cloud HTTP non-success responses do not count as
successful validation.

## Operation authority

Every asynchronous lifecycle operation has a unique attempt ID and captures
the owning connection generation. Starting a conflicting operation increments
the generation and supersedes the previous attempt.

The operation checks authority:

1. before creating resources;
2. after candidate creation;
3. after every awaited network or native boundary;
4. before mutating a saved record;
5. before promoting or closing a runtime;
6. before publishing an error or repair state;
7. before returning any user-navigation outcome.

An operation that is no longer authoritative disposes resources it owns and
returns `superseded`. It does not modify current focus, runtime, wizard, cache,
draft, or navigation state.

Cancellation:

- marks the attempt cancelling before aborting work;
- increments or invalidates the applicable generation;
- aborts requests where supported;
- calls the adapter's idempotent close for candidate resources;
- completes as cancelled without error presentation.

Transport abort is an optimization and resource guarantee. Generation checks
remain mandatory because some native APIs and completed promises cannot be
physically aborted.

## Candidate promotion

Opening a connection is transactional:

```text
create candidate
    -> validate candidate
    -> confirm operation authority
    -> publish usable runtime
    -> apply explicit focus/navigation result
    -> close replaced runtime if host policy requires it
```

The current usable runtime is not disconnected merely because candidate
validation started.

A candidate becomes visible as the connection's runtime only after validation.
If the host permits one open runtime, replacement closure follows promotion so
candidate failure cannot leave the frontend needlessly disconnected.

## Focus and navigation

Focus is a workspace command independent from opening. Focusing a saved
connection reads cached state immediately and may optionally start a separate
open attempt.

The controller does not directly manipulate native navigation. It returns
typed outcomes or emits connection-scoped state. The host applies a navigation
outcome only if its user-intent token remains current.

Session state is keyed by `(connectionId, sessionId)`. Component identity,
controller ownership, event subscriptions, cache callbacks, and draft writes
use both values.

Deep links identify a connection explicitly. A backend may be used from any
open matching runtime, not only the focused one. Any requested focus/navigation
is an explicit deep-link outcome and remains subject to current user intent.

## Repair and saved identity

Repair operates on one existing stable connection ID. It may update address,
bridge server metadata, pairing credential, or transport mode without creating
a second saved identity.

An unsaved wizard attempt uses a temporary attempt identity until successful
validation creates a saved record. Temporary IDs never become cache keys.

Bridge repair follows bridge-connectivity error meanings. Invalid credentials
may be cleared from the saved record only through an authoritative repair
transition; a superseded operation cannot clear credentials.

## Application lifecycle

Backgrounding may suspend or disconnect transport-specific resources according
to adapter behavior. It does not clear focus, cached workspace state, or
drafts.

Foregrounding starts connection-scoped revalidation for eligible open
runtimes. Each revalidation uses the current generation. It may transition its
runtime to open, unavailable, or repair required, but does not navigate.

When several runtimes are open, recovery is tracked independently. A global
in-flight boolean does not serialize unrelated connections.

## Error contract

`ConnectionLifecycleError` contains a stable category, retryability, optional
repair/edit action, and diagnostic cause. Categories include:

```text
cancelled
superseded
network_unavailable
timeout
authentication_failed
authorization_failed
pairing_required
server_identity_mismatch
invalid_configuration
unsupported_capability
server_error
persistence_failed
```

Cancellation and supersession are terminal results rather than user-visible
errors. Credentials, pairing tokens, cloud tokens, and raw sensitive request
content are excluded from diagnostic metadata.

## Persistence coordination

The controller does not treat initial empty React state as hydrated durable
state. Stores expose hydration completion. Writes caused by user actions before
hydration are queued or merged without allowing initial emptiness to overwrite
stored records.

The detailed cache and draft contract is in
[Persistence and offline continuity](persistence-and-offline.md).

## Compatibility and migration

Existing `ConnectionRecord` IDs remain cache identities. Existing manual,
discovery, bridge, and cloud records remain readable.

An absent bridge transport mode continues to mean WebSocket according to the
bridge-connectivity specification. Lifecycle extraction does not change
bridge request routing or add fallback/replay.

The migration may initially adapt current mobile and desktop hooks through a
compatibility facade. Persisted schema changes are versioned and tolerate
older records. Runtime state is reconstructed rather than persisted.

## Verification

### Shared deterministic verification

Controller tests use deferred adapter promises to prove:

- old attempt completion cannot modify newer state;
- cancel is terminal even when an adapter later resolves;
- candidate failure preserves the previous runtime;
- close during opening prevents late reopen;
- repair preserves stable identity;
- independent connections do not share generations;
- navigation outcomes require current user intent.

Adapter contract tests cover direct, discovery, bridge modes, and cloud
success/error normalization without repeating controller race cases.

### Frontend verification

Component tests cover statuses, actions, offline content, disabled mutations,
repair state, and connection/session scoping.

Native tests use production screens to cover:

- cancel during a pending connection or repair;
- competing attempts with reversed completion order;
- offline launch and cached navigation;
- draft restoration after application relaunch.

One realistic bridge and one direct/cloud path should cross production
adapters. Shared race semantics do not require redundant hosted tests for
every transport kind.