# Frontend connection persistence and offline continuity

## Purpose

Persistent frontend state exists to preserve user continuity, not to imply
that cached server data is authoritative. This contract defines identity,
hydration, freshness, cache retention, draft durability, and explicit removal.

## Persistent identities

Connection ID is the top-level namespace for frontend state. Session ID is
nested under connection ID.

The following data is scoped by connection:

- saved connection configuration;
- last focused session or open-session collection;
- session summaries;
- application-level UI preferences where applicable;
- connection-level freshness and invalidation state.

The following data is scoped by connection and session:

- indexed messages and consistency cursors;
- transcript range and viewport state;
- composer draft;
- recoverable send state;
- session-specific UI preferences where applicable.

The same server session ID under two saved connections is not the same
frontend cache or draft.

## Hydration

Each persistent store exposes whether hydration has completed. A frontend does
not write initial empty records merely because a component mounted before
storage returned.

User changes made during hydration are queued or merged deterministically.
Hydration failure produces a local persistence error and a safe empty view; it
does not silently claim that stored data was deleted.

Restoring cached content does not wait for network validation. Network refresh
begins only after the applicable workspace/runtime state is ready.

## Saved connections and credentials

Saved records retain stable connection ID through edit and repair. Connection
kind configuration is validated when read; a malformed record is isolated
rather than crashing all connection hydration.

Credentials are stored only in the connection credential boundary and are not
copied into caches, drafts, debug timelines, errors, or analytics. A future
secure-storage migration may change physical storage without changing
connection identity or cache keys.

Removing credentials to require re-pairing is distinct from deleting the saved
connection and its local workspace.

## Session and message caches

Session summaries and message windows include `lastLoadedAt` or equivalent
freshness metadata. Cache invalidation and cache absence are distinct:

- absence means no local content is available;
- stale means content remains viewable but should be refreshed when possible;
- invalidated means a known server-side change requires refresh before the
  cache is considered authoritative.

A failed refresh retains the prior cache and its earlier freshness. It does
not replace the cache with an empty result caused by transport failure.

Message cache limits may evict old message payloads. Eviction does not remove
the saved connection, navigation record, or non-empty draft.

## Draft schema

A versioned session draft contains the portable equivalent of:

```ts
interface SessionDraft {
  version: number;
  connectionId: string;
  sessionId: string;
  text: string;
  attachments: DraftAttachment[];
  updatedAt: number;
  pendingSend?: PendingSendRecovery;
}
```

Attachment state includes order, placement, supported metadata, content
reference, upload/readiness state, and enough display information to restore
the composer.

A durable attachment cannot rely solely on a temporary picker result or an
external URI whose permission ends with the process. Implementations may copy
content into app-managed storage or retain a durable server-owned asset
reference. If restoration cannot make an attachment usable, the draft remains
visible with a recoverable error rather than silently dropping it.

## Draft write policy

Text and attachment changes update the in-memory draft immediately and enqueue
durable persistence with a bounded debounce. Pending writes flush on:

- input blur;
- session or connection switch;
- navigation away from the composer;
- application backgrounding;
- component/controller disposal;
- an explicit send, append, or discard transition.

A frontend may report Saving while a write is pending and Saved only after the
durable store accepts the current revision. Write failure remains visible and
retryable.

Draft revisions prevent an older delayed write from replacing a newer draft.
Hydration does not overwrite locally edited content that became newer while
the read was pending.

## Clearing and uncertain sends

An append/send acknowledgement may clear the exact draft revision submitted.
A later draft revision typed while the request was pending is not cleared by
the earlier acknowledgement.

If request acknowledgement is uncertain, the submitted content and
idempotency/status recovery data remain available until the server outcome is
known or the user explicitly resolves it. Retrying reuses the applicable
idempotency identity.

Explicit discard clears the selected draft after confirmation when content or
attachments are non-empty.

## Eviction

Non-empty drafts are protected from ordinary message-cache eviction. A valid
implementation may:

- store drafts separately from bounded message history; or
- mark draft-bearing entries non-evictable while selecting expendable message
  entries.

If storage pressure makes all normal retention impossible, the frontend
reports the condition and asks for an explicit user choice. It does not
silently delete composed work.

Empty draft records may be removed. Successfully submitted or explicitly
discarded attachments owned only by the draft are cleaned up after no retained
draft references them.

## Offline behavior

Offline views read cache and draft state without constructing a fake backend.
Server-authoritative operations require an open runtime.

Local operations remain available where their inputs are cached, including:

- browsing and filtering session summaries;
- reading and navigating cached messages;
- changing transcript viewport/range preferences without claiming unloaded
  data exists;
- copying content;
- editing and discarding drafts.

Refresh, create, modify, append, send, cancel-server-request, and other server
mutations are disabled or begin an explicit reconnect flow.

## Removal and retention controls

The frontend distinguishes:

- Close runtime: retain saved record, cache, workspace, and drafts.
- Forget credentials: retain local workspace where useful and require
  reauthorization.
- Clear cached server content: retain saved record and, by default, drafts.
- Discard draft: remove one session draft.
- Delete saved connection: explicitly state whether credentials, caches,
  workspace state, and drafts will also be removed.

Bulk clear operations enumerate the local data classes they remove.

## Migration and corruption

Persistent schemas are versioned. Migration is per record or per scoped entry
so one corrupt session cache does not invalidate every connection.

Older text-only drafts hydrate with an empty attachment list. Older bridge
records without a transport mode continue to select WebSocket.

Malformed cached server payloads may be dropped when they cannot be safely
normalized. A valid non-empty draft is preserved independently whenever
possible.

## Verification

Storage tests cover:

- no write before hydration;
- edits during hydration;
- connection/session scope isolation;
- draft revision ordering;
- bounded-debounce and lifecycle flush;
- process-restart restoration;
- attachment reference restoration or recoverable failure;
- draft-safe cache eviction;
- acknowledgement clearing only the submitted revision;
- explicit deletion boundaries;
- partial corruption isolation.

Native relaunch verification uses production composer and cache code. Merely
asserting that a storage method was called does not prove restoration.