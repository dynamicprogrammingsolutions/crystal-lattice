# Session snapshots

Session snapshots preserve a complete readonly copy of a session so a user can
inspect or restore earlier conversational and provider-native state.

Snapshots are stored beside the session store under its `.snapshots`
directory. A snapshot contains the session messages and metadata that existed
when it was created. Selecting a snapshot opens a readonly view; returning to
the live session or restoring a snapshot clears that selection.

## Manual snapshots

Clients can create a named snapshot before an experiment or other significant
change:

```http
POST /sessions/{session_id}/snapshots
Content-Type: application/json

{
  "reason": "Before trying a different approach"
}
```

The mobile and desktop snapshot surfaces expose the same operation through
their Create controls.

## Automatic pre-mutation snapshots

The built-in session-actions and OpenAI Responses plugins create snapshots
before these destructive operations:

- deleting one or more messages;
- committing successful OpenAI provider-native compaction.

Automatic snapshots are created only after an operation has valid work to
apply. A no-op deletion, cancelled compaction, provider failure, interrupted
operation, or conflicting compaction commit does not retain an automatic
snapshot. If persistence fails after a provisional snapshot is created, the
plugin removes that snapshot before returning the failure.

Reasons describe the operation whose previous state was preserved:

```text
Before deleting message [14]
Before deleting messages [18, 22, 25]
Before deleting messages [357:]
Before compacting conversation [:277]
```

Structured snapshot metadata records that the snapshot is automatic, the
contributing plugin and action, and the normalized range or indices. Current
clients display the human-readable reason.

## Restore behavior

Restoring a snapshot replaces the live conversational and provider-native
session state with the preserved state. When the live session differs, the
application first creates another snapshot with the reason `before restore`,
so the restore itself can be reversed.

Live session-notification history is not rewound by snapshot restoration.
Notifications describe current operations and user acknowledgement state, so
the application preserves the live notification container while restoring the
conversation.

## Storage and deletion

Snapshots contain the full serialized session and can be large when a session
contains extensive provider-native history or tool output.

Automatic snapshots are enabled by default. There is currently no automatic
age limit, count limit, or pruning policy. Users must delete snapshots they no
longer need through the mobile or desktop snapshot controls or through:

```http
DELETE /sessions/{session_id}/snapshots/{snapshot_id}
```

Deleting a live session and managing snapshot retention are separate
operations.

## HTTP API

The snapshot routes are:

- `GET /sessions/{session_id}/snapshots`
- `POST /sessions/{session_id}/snapshots`
- `GET /sessions/{session_id}/snapshots/selected`
- `POST /sessions/{session_id}/snapshots/{snapshot_id}/select`
- `POST /sessions/{session_id}/snapshots/selected/clear`
- `POST /sessions/{session_id}/snapshots/{snapshot_id}/restore`
- `DELETE /sessions/{session_id}/snapshots/{snapshot_id}`

The frontend SDK exposes corresponding `AgentBackend` methods for the mobile,
desktop, and other clients.