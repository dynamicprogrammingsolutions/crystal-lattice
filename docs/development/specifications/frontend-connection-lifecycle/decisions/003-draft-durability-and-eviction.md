# Decision 003: Durable drafts and draft-safe eviction

Status: Accepted

Date: 2026-08-23

## Context

Current message-cache entries can include composer text, but mobile persists
active edits only at selected lifecycle boundaries. Attachment drafts remain
component-local. Message-history limits can select a draft-only entry as the
oldest cache entry because it has no message load timestamp.

Composed work has different retention value from replaceable server-derived
message history.

## Decision

A draft is versioned durable state keyed by connection and session. It includes
text, attachment state, and recoverable send state.

Edits update memory immediately, persist with a bounded debounce, and flush at
navigation/application lifecycle boundaries. A Saved indication means the
current revision reached durable storage. Persistence failure is visible.

Non-empty drafts are protected from ordinary message-cache eviction. An
implementation may store drafts separately or mark draft-bearing cache entries
non-evictable.

Attachment restoration may use app-managed local content or durable
server-owned references, but cannot rely solely on ephemeral picker access. An
unrestorable attachment remains visible as a recoverable draft error rather
than disappearing.

## Consequences

- The shared text-only cache schema must evolve compatibly.
- Attachment cleanup requires reference-aware ownership.
- Draft write ordering needs revisions or equivalent stale-write protection.
- Storage pressure may require an explicit user decision rather than silent
  eviction.
- Existing text-only entries migrate to drafts with no attachments.

## Alternatives not selected

Treating the composer as ordinary screen state was rejected because navigation,
connection failure, and process termination are normal application events.

Keeping drafts inside an unqualified least-recently-loaded message cache was
rejected because server-derived history can be reloaded while unsent work
cannot.