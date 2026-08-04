# Active application operations

The application operation service is a minimal active-registration and
admission boundary shared by ordinary requests and longer-lived plugin work.

It does not store progress, presentation, cancellation behavior, metrics, or
terminal outcomes. Those remain owned by the request coordinator or plugin.

## Responsibilities

`ApplicationOperationService` does only four things:

1. register one active operation;
2. enforce one or more opaque exclusivity keys;
3. look up and list active registrations;
4. release registrations safely.

The service is stored in `RuntimeStore`:

```python
from agent_app.operations import get_application_operation_service

operations = get_application_operation_service(app.get_runtime_store())
```

No additional `AgentApplication` operation-registry methods are required.

## Minimal registration

The public registration contains:

```python
@dataclass(frozen=True)
class ApplicationOperationRegistration:
    operation_id: str
    owner_id: str
    session_id: str | None = None
```

Example request:

```json
{
  "operation_id": "request_123",
  "owner_id": "agent_app.session_request",
  "session_id": "session_456"
}
```

Example plugin operation:

```json
{
  "operation_id": "openai_responses_native_compaction:abc123",
  "owner_id": "openai_responses_native_compaction_app",
  "session_id": "session_456"
}
```

`session_id: null` represents application-wide work. A separate scope field is
not needed.

### Operation ID

The operation ID is unique within the application generation.

- coordinated requests use the request ID;
- a managed plugin operation should normally use the same ID for its operation
  registration and managed process.

Using one ID avoids exposing a separate process correlation field.

### Owner ID

The owner ID is opaque to the service. It identifies the component responsible
for interpreting and controlling the operation.

Examples:

- `agent_app.session_request`;
- `openai_responses_native_compaction_app`;
- a future Claude or Kimi compaction plugin ID.

The service does not import, invoke, or validate the owner.

### Session ID

Session-scoped work includes a session ID so callers can:

- list active work for one session;
- enforce session exclusivity;
- report which operation blocks a request.

## Reservation and exclusivity

Reserve an active operation with one or more opaque exclusivity keys:

```python
from agent_app.operations import session_operation_exclusivity_key

lease = operations.reserve(
    operation_id=operation_id,
    owner_id=plugin_id,
    session_id=session_id,
    exclusivity_keys=(session_operation_exclusivity_key(session_id),),
)
```

The session helper currently returns:

```text
session:<session_id>
```

Exclusivity keys are internal admission details. They are not included in the
public registration.

If another active operation owns a requested key,
`ApplicationOperationBusyError` contains its minimal registration.

Ordinary requests and OpenAI native compaction use the same session key:

- request versus request preserves existing `already_running` behavior;
- request versus compaction returns session busy;
- compaction versus request or compaction returns busy before provider work.

Optimistic session reconciliation is still required to protect against writers
that do not participate in this admission service.

## Lookup and listing

```python
registration = operations.get(operation_id)

all_active = operations.list_active()
session_active = operations.list_active(session_id=session_id)
plugin_active = operations.list_active(owner_id=plugin_id)
```

The service lists active identity only. It does not ask owners for status.

## Identity-safe release

Reservation returns an identity-bound lease:

```python
lease.release()
```

The lease token is private. A stale lease cannot remove a later registration.

Once released, the operation disappears from active lookup and its exclusivity
keys become available.

Application close clears all registrations and rejects future reservations.
Actual workers are closed through their own owners:

- the request coordinator cancels requests;
- `ManagedProcessRegistry` closes plugin process objects.

## What the service deliberately does not store

The active operation registration has no:

- lifecycle state;
- phase;
- timestamps;
- progress;
- metrics;
- display text;
- cancellation capability;
- actions;
- process ID;
- request outcome;
- terminal history.

Existence means active. Absence means not active.

## Owner responsibilities

The request coordinator or plugin owns all operation-specific behavior.

A managed process may keep:

- phase and progress;
- metrics or provider counters;
- task and transport handles;
- cancellation state;
- retry parameters;
- commit authority;
- provider results.

It may expose plugin-specific methods such as:

```python
process.get_status()
process.request_cancel()
```

The generic process registry and operation service do not require a shared
status protocol.

## Notifications

Plugins send and update their own notifications. Notification data may include
any plugin-owned optional details:

```json
{
  "operation": {
    "id": "openai_responses_native_compaction:abc123",
    "phase": "waiting_for_provider",
    "elapsed_seconds": 45,
    "cancellable": true
  }
}
```

This structure is not an application-operation schema. It is presentation data
owned by the notification producer.

OpenAI compaction may report elapsed time. A streaming compaction plugin may
report chunks, characters, or provider token counts. The application operation
service interprets none of them.

### Notification refresh effects

A plugin-owned notification may request connection-scoped refreshes
through `ui_effects`:

- `reload_session_ids`;
- `reload_sessions_list`;
- `reload_application_actions`.

These remain notification data and are not stored, validated, routed, or
executed by `ApplicationOperationService`. The notification contract and
frontend consumers own those responsibilities.

Focus-changing effects such as `navigate_to_session_id` remain action-only.
Operation completion occurring in the background must not navigate the user
away from their current context.

## Future operations menu

A future connection-level operations menu can begin with active registrations:

```text
operation ID
owner ID
session ID
```

Presentation and operation actions should be added through a separate owner
description contract rather than expanding admission semantics.

That future contract should permit arbitrary owner-provided fields. For
example, a plugin may contribute:

```json
{
  "description": "Compacting messages 1–42",
  "operation_actions": [
    {
      "kind": "run_action",
      "label": "Cancel"
    }
  ],
  "provider_status": {
    "chunks": 24
  }
}
```

These fields do not need to be predefined by the application service. A
frontend may implement recognized fields optionally and ignore unknown ones.
The owner remains responsible for their semantics.

This extension mechanism is intentionally deferred until the operations-menu
contract is designed. The active admission registry does not need an opaque
details field today.

## Persistent outcomes

The active operation service removes registrations on release and keeps no
terminal records.

Past outcomes belong to a separate future facility, such as:

- event history;
- notification history;
- plugin-owned persistence;
- a dedicated operation-history store.

That history contract may also preserve arbitrary owner-provided details. It
should not require the admission service to standardize progress, display, or
outcome semantics.

## Tests

Operation-service tests cover:

- registration and lookup;
- filtering by session and owner;
- duplicate exclusivity races;
- identity-safe release;
- application close.

Producer tests separately cover progress, notifications, cancellation,
provider errors, guarded commit, and reload behavior.