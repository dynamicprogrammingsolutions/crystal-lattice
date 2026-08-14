# Decision: evolve existing instance identity into a durable workspace

## Context

The existing API couples one initiating session, one instance record, one
Docker container, and one connection route. Replacing all identifiers and APIs
would increase migration and frontend scope before the improved model is
proven.

At the same time, connection credentials expire after 24 hours and orchestrator
registries disappear on restart even when host bytes and containers remain.

## Decision

- Keep `instance_id` as the first target's durable workspace handle.
- Keep `connection_id` as the logical cloud connection.
- Persist versioned connection and instance manifests under the orchestrator
  data directory.
- Keep GenServers as caches/serialization boundaries over manifests.
- Represent workspace lifecycle, desired runtime state, and observed runtime
  state separately.
- Make new connection-scoped credentials durable until explicit rotation,
  revocation, or deletion.
- Label and reconcile Docker containers at orchestrator startup.
- Serve a narrow connection control surface from the orchestrator while
  proxying runtime-dependent APIs only to a ready runtime.

## Consequences

Positive:

- Existing links, transports, routes, and deployment concepts can evolve
  incrementally.
- Stopped runtime becomes a normal state without losing the connection.
- Restart recovery works without introducing a database immediately.
- Future runners can implement the same lifecycle primitives.

Costs:

- The name `instance` temporarily represents a durable workspace rather than
  only a running process.
- File manifests require schema versioning, atomic mutation, and recovery
  behavior.
- Control/runtime route ownership must be explicit.

Deferred alternatives:

- New `/workspaces` resources and identifier migration.
- SQL/distributed persistence.
- One-time claim links and per-device credentials.
