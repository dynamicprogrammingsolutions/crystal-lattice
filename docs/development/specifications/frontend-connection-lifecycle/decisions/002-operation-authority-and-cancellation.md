# Decision 002: Operation authority and candidate promotion

Status: Accepted

Date: 2026-08-23

## Context

Transport abort alone cannot guarantee cancellation. Some native discovery
operations cannot be aborted reliably, and promises may resolve after the user
has cancelled, switched connections, closed a runtime, or started a newer
attempt.

Disconnecting the current runtime before a candidate has validated also turns
an ordinary failed switch into an avoidable outage.

## Decision

Every open, reconnect, validation, pairing, and repair operation receives a
unique attempt ID and captures an owning generation. The controller checks
authority after every asynchronous boundary and before every externally
visible mutation.

Cancellation and supersession invalidate authority first, then abort and
dispose resources where supported. A late operation may clean up only resources
it owns.

A new candidate is validated before promotion. A previous runtime is closed
only after authoritative promotion and only when the host's runtime policy
requires replacement.

Navigation is an explicit outcome applied by the host under a current
user-intent token. Background lifecycle work never navigates.

## Consequences

- Tests can deterministically reverse promise completion order.
- Cancellation remains correct even for non-abortable APIs.
- Candidate failure preserves a working runtime.
- Adapter close operations must be idempotent.
- Attempts need diagnostic state distinct from user-visible errors.

## Alternatives not selected

Relying only on `AbortController` was rejected because bridge sockets, Bonjour,
and already-resolved operations require a logical stale-result guard.

Serializing all connection work globally was rejected because independent
connections should be able to open and recover concurrently.