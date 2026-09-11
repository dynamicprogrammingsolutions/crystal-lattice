# Message API projection and incremental history

Define a bounded frontend message representation and avoid retransmitting an unchanged last-50 window on ordinary reloads.

## Requirements checklist

- [ ] **MAPI-001** Ordinary message-list responses use an explicit documented frontend message representation rather than exposing the complete persisted message dictionary by default.
- [ ] **MAPI-002** The frontend message representation contains every field required to render supported user, assistant, reasoning, tool, system, attachment-reference, usage, and action states.
- [ ] **MAPI-003** Provider-native history, internal lifecycle state, cumulative attribution details, and other storage-only fields are excluded from ordinary message responses unless a documented frontend behavior requires them.
- [ ] **MAPI-004** Message listing does not read or embed session asset bodies.
- [ ] **MAPI-005** A frontend that knows its current message/history revision can request and receive only added or changed message state during an ordinary reload.
- [ ] **MAPI-006** Cursor expiry, history slicing/modification, restore, and incompatible revision changes trigger a defined bounded full-refresh fallback.
- [ ] **MAPI-007** Stable message identity and ordering semantics support insertion, replacement, deletion, and streamed-to-final reconciliation without ambiguity.
- [ ] **MAPI-008** Existing supported message rendering remains functionally equivalent across mobile and desktop production consumers.
- [ ] **MAPI-009** A full-fidelity administrative/import/export path remains available without forcing that representation onto ordinary frontend traffic.
- [ ] **MAPI-010** Direct HTTP and bridge integration tests exercise the production backend adapter and message consumer.
- [ ] **MAPI-011** Shared benchmark results record last-50 and incremental response sizes, backend serialization time, frontend parse time where measurable, and bridge transfer impact.

## Scope

In scope:

- HTTP message-list and incremental-history contracts.
- Application-to-frontend message conversion.
- Frontend SDK types, backend adapter behavior, and mobile/desktop message consumers.
- Message/history revision, cursor, deletion/replacement signaling, and full-refresh fallback.
- Payload and parsing measurements.

Out of scope:

- Physical session storage layout.
- UI schema/settings synchronization.
- Actual session asset downloads.
- Bridge compression implementation.

Parent Task: `tasks/20260911-session-performance-and-storage-optimization/000-main.md`

Depends On: `tasks/20260911-session-performance-and-storage-optimization/010-session-growth-and-benchmark-foundation.md`

## Requirement questions

- Which current message metadata fields are consumed by each production frontend renderer?
- Is the incremental contract index-based, message-ID-based, cursor-based, revision-based, or a combination?
- How are edits and deletions represented without making the frontend infer them from a complete replacement list?
- Does a streamed assistant message retain one stable ID through finalization?
- How is API compatibility negotiated for older frontend clients?
- Should reasoning and large tool results have independently pageable or collapsible payload representations?

## Research details and suggested direction

Measured mature-session last-50 payloads were approximately 4.0-4.8 MB even though the frontend does not need the complete persisted/native representation. The current `be5e...` sample was 4,805,958 bytes uncompressed and 658,349 bytes with gzip.

The task should first inventory production consumers and define the smallest stable message view that supports them. Incremental updates can then use a history revision plus ordered change records, with a conservative full-window fallback after destructive history operations or missed revisions.

A compound session bootstrap response may reuse this representation, but it should not become the only way to query messages.

Because this changes a cross-package API contract, implementation should be preceded by the owning API/frontend contract specification and compatibility decision.