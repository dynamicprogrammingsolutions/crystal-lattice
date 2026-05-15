# Cache Observability And Production Support Logs
Add durable observability for cache checkpoints and storage flushes so support can inspect what happened before a slowdown or crash without requiring a debug build.

## Requirements checklist
- [ ] Inventory and preserve the useful existing debug hooks.
- [ ] Define a structured cache observability model that works across SDK and app layers.
- [ ] Choose a production-safe log sink that can be enabled permanently with bounded storage use.
- [ ] Make cache checkpoint and cache flush activity inspectable after the fact.
- [ ] Add a simple support workflow for collecting logs from affected users.

## Context

The cache-timing work should not ship blind. The goal of this task is to make cache activity observable in production, especially just before Hermes memory pressure or repeated AsyncStorage writes.

This task is intentionally separate from the timing task so the logging design can be evaluated on its own. The preferred outcome is something that can stay on in production in a bounded form and be exported by users when support asks for it.

## Existing debugging options

### Desktop has targeted console-based debug flags already

- `desktop/crystal-lattice-control-desktop-rn/src/chat/usePersistedChatDraft.ts:54-56`
  - `CLC_DEBUG_DRAFT_PERSIST`
- `desktop/crystal-lattice-control-desktop-rn/src/chat/usePersistedChatDraft.ts:74-80`
  - logs draft flushes
- `desktop/crystal-lattice-control-desktop-rn/src/chat/usePersistedChatDraft.ts:133-137`
  - logs draft init
- `desktop/crystal-lattice-control-desktop-rn/src/chat/usePersistedChatDraft.ts:149-154`
  - logs draft restore

- `desktop/crystal-lattice-control-desktop-rn/src/chat/useProactiveChatScrollPersistence.ts:92-94`
  - `CLC_DEBUG_SCROLL_PERSIST`
- `desktop/crystal-lattice-control-desktop-rn/src/chat/useProactiveChatScrollPersistence.ts:161-178`
  - logs scroll persistence pulls
- `desktop/crystal-lattice-control-desktop-rn/src/chat/useProactiveChatScrollPersistence.ts:218-225`
  - logs restore reset reasons

Limitations:

- these are JS console logs only
- they are flag-driven developer diagnostics, not support-grade retained logs
- they do not capture message snapshot writes or AsyncStorage flush size/duration centrally

### Mobile already has a useful debug timeline pattern

- `mobile/crystal-lattice-control-rn/src/debugTimeline.ts:1-42`
  - defines a bounded debug timeline entry structure
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:890-905`
  - `appendDebugNote(...)` writes structured notes
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:907-914`
  - keeps a bounded event buffer
- `mobile/crystal-lattice-control-rn/src/components/DebugEventsView.tsx:16-120`
  - renders a support-friendly expandable view for notes and streamed events

This is the strongest existing pattern to build on.

## Recommended observability model

### 1. Separate SDK checkpoints from app flushes

Two different things should be logged:

- SDK cache checkpoints
  - "a persist-worthy snapshot changed"
- app/storage flushes
  - "we serialized and wrote cache data to storage"

Those are different events and should be visible separately.

### 2. Use structured log entries, not ad hoc strings

Suggested log record fields:

- `timestampMs`
- `scope`
  - `sdk`
  - `cache`
  - `storage`
  - `chat`
- `connectionId`
- `sessionId`
- `reason`
- `messageCount`
- `firstMessageIndex`
- `lastMessageIndex`
- `activeRequestId`
- `eventsCursorId`
- `dirty`
- `payloadBytes`
- `flushDurationMs`
- `coalescedWriteCount`
- `success`
- `errorMessage`

### 3. Keep always-on logging bounded

Recommended baseline:

- always-on minimal ring buffer
- cap by entry count, for example last 200-500 entries
- keep per-entry metadata compact

This should be safe to leave on in production if the payload is small and bounded.

## Production-safe sink options

### Option A: AsyncStorage-backed ring buffer

Pros:

- cross-platform
- simple to implement
- easy to expose in-app for export

Cons:

- writing logs into AsyncStorage adds more AsyncStorage activity
- if not carefully bounded and coalesced, it can contribute to the very problem being investigated

### Option B: Native rolling file under app support directory

Pros:

- best for post-crash support collection
- avoids mixing support logs with the app cache store
- can be viewed or exported outside the app

Cons:

- requires native app integration per platform
- more implementation effort

### Option C: OS logging only (`NSLog` / `os_log` on macOS)

Pros:

- production-safe
- visible in Console.app
- no extra app UI required initially

Cons:

- less convenient for end users to export
- retention/collection story is weaker unless support already knows the tooling

### Recommended path

Best long-term fit:

- SDK emits structured observability events
- app layer routes them to:
  - a bounded in-memory ring buffer for live inspection
  - a bounded persisted support log sink

Most practical first version:

- reuse the mobile debug timeline data model
- add a production-safe persisted sink, preferably a rolling file on desktop and a bounded local store on mobile if file logging is too much initially

## Suggested implementation shape

### SDK layer

Add a small observability hook or sink interface near `ChatController`, for example:

- cache checkpoint emitted with structured metadata
- no app-specific storage assumptions inside the SDK

### App layer

Desktop and mobile subscribe to SDK observability events and record:

- checkpoint events
- cache update requests
- actual storage flushes

Also log debounce behavior:

- flush scheduled
- flush coalesced
- flush started
- flush completed
- flush failed

## Suggested support workflow

1. Keep a bounded support log always enabled in production.
2. Add a simple export or copy action in-app, or document the file path on desktop.
3. When a user reports instability, ask for:
   - the support log
   - the crash report
4. Inspect the last 1-2 minutes of:
   - checkpoint frequency
   - flush sizes
   - flush durations
   - repeated draft/scroll/cache events

## Data points worth capturing just before crashes

- number of cache checkpoints in the last minute
- number of actual storage flushes in the last minute
- max serialized cache byte length recently seen
- whether recent writes came from:
  - message commit
  - reload
  - draft update
  - scroll update
- time spent serializing and writing

## Reuse opportunities

Use the mobile debug timeline pattern as a reference instead of inventing a new shape:

- `mobile/crystal-lattice-control-rn/src/debugTimeline.ts:1-42`
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:890-914`
- `mobile/crystal-lattice-control-rn/src/components/DebugEventsView.tsx:16-120`

That existing pattern already solves:

- structured entries
- bounded retention
- inspection UI

The main missing piece is durable persistence suitable for support after a crash.