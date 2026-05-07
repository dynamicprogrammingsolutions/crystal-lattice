# Durable Request Error Log And Lightweight Client Cache

Draft a focused plan for guaranteeing that a request failure can still be shown when the user reopens the session later, even if live events were missed, without relying on the expensive full-session cache.

Parent Task: tasks/20260414-tool-loop-session-concurrency-followups/000-main.md
Depends On: tasks/20260414-tool-loop-session-concurrency-followups/010-tool-loop-session-settings-concurrency.md

## Requirements checklist

- [ ] Capture a focused plan for durable request error visibility without waiting for the broader conflict-handling design.
- [ ] Ensure a request error can be auto-shown the next time the user opens the session.
- [ ] Ensure the same error stops auto-showing after dismissal or after the user starts a new request.
- [ ] Keep the durable store append-only and suitable for viewing past session errors.
- [ ] Avoid relying on the expensive full-session cache; use a larger-budget lightweight request pointer cache instead.

## Scope

This is a narrower draft than `tasks/20260414-tool-loop-session-concurrency-followups/020-request-conflict-handling-draft.md`.

It focuses only on this guarantee:

- if a user starts a request and that request does not finish successfully, the reason should still be available and auto-shown the next time the user opens the session, even if live events were missed

It does not try to solve all cross-process conflict handling in one step.

## Problem statement

Current live behavior is good but not durable:

- The server publishes request `error` events to the shared event stream.
- Terminal and mobile surface those errors while attached to the live request.
- If the client closes, misses events, reconnects later, or no longer has the full session cached, there is no durable per-request error source tied to the session that can reliably restore the reason.

The important failure mode to avoid:

- a request starts
- it later fails or is stopped with an error
- the user reopens the session later
- no visible reason is shown

## Draft plan

### 1. Durable append-only request outcome log

Add a per-session NDJSON log, separate from the main session JSON.

Suggested path:

- `sessions/<session_id>.request-outcomes.ndjson`

Each appended line represents a request lifecycle record.

Suggested record shapes:

```json
{"event_id":"...","session_id":"s1","request_id":"r1","kind":"started","created_at":"..."}
{"event_id":"...","session_id":"s1","request_id":"r1","kind":"error","detail":"Concurrent session modification detected ...","backup_path":"...","created_at":"..."}
{"event_id":"...","session_id":"s1","request_id":"r2","kind":"completed","created_at":"..."}
```

Recommended terminal kinds:

- `started`
- `completed`
- `cancelled`
- `error`

Optional later additions:

- `rejected`
- `conflict`
- `abandoned`

Why append-only:

- fits the durability requirement
- preserves past errors for later inspection
- avoids mutating the main session file when we do not want to overwrite legitimate session state

### 2. Lightweight client-side request pointer cache

Do not rely on the full session cache for this feature.

Instead, add a separate tiny cache with a larger budget and longer retention.

Suggested cached fields per session:

```json
{
  "sessionId": "s1",
  "lastStartedRequestId": "r123",
  "lastDismissedRequestId": "r122",
  "updatedAt": 1776202000
}
```

Important design note:

- this cache should be independent from the expensive transcript/session cache
- even if the full session cache is evicted, the lightweight request pointer should likely remain

### 3. Auto-show logic on session reopen

When the user opens a session:

1. Read the lightweight request pointer cache for that session.
2. If `lastStartedRequestId` exists, ask the server for the terminal outcome of that request.
3. If the terminal outcome is `error` and it was not dismissed already, auto-show it.
4. If the outcome is `completed`, show nothing.
5. If the outcome is `cancelled`, likely show nothing by default.
6. If there is only `started` and no terminal outcome, but the request is no longer active, show a generic fallback warning such as:
   - "The last request did not complete successfully, but no explicit error was recorded."

This fallback matters because silence is worse than an imperfect generic warning.

### 4. Dismiss and replace semantics

To satisfy the UX constraints:

- if the user dismisses an auto-shown error, record that dismissal in the lightweight cache
- once dismissed, the same request error should not auto-show again
- if the user starts a new request, overwrite `lastStartedRequestId`
- that naturally makes the previous request stop being the auto-show target

### 5. Past errors view

Use the same NDJSON request outcome log for a session-level past errors view.

Behavior:

- list recent `kind == "error"` records for the session
- allow the user to inspect old errors even if they came from another client or server

This matches the stated requirement that users will naturally see errors emitted by other clients/servers too.

## Suggested server API

A focused first version can be very small.

Recommended helpers/endpoints:

1. Lookup terminal outcome for one request:
   - `GET /sessions/{session_id}/requests/{request_id}/outcome`

2. List recent session errors:
   - `GET /sessions/{session_id}/request-errors?limit=50`

Possible response for request outcome:

```json
{
  "session_id": "s1",
  "request_id": "r123",
  "terminal_outcome": {
    "kind": "error",
    "detail": "Concurrent session modification detected ...",
    "backup_path": "/path/to/backup.json",
    "created_at": "..."
  }
}
```

This keeps the frontend logic straightforward and does not require the full session payload to carry extra data.

## Frontend notes

Terminal:

- live event errors already render through `event_rendering.py`
- this plan adds durable follow-up visibility when reopening the session later

Mobile:

- live request errors already show through `chatState.requestError`
- this plan adds a reopen path that can query the last started request outcome using the lightweight request pointer cache

Why this is preferable to tying it to the session cache:

- the transcript cache is expensive and intentionally limited
- the request pointer cache is tiny, so it can have a much larger budget

## Relationship to the broader draft

This subtask is intentionally narrower than `tasks/20260414-tool-loop-session-concurrency-followups/020-request-conflict-handling-draft.md`.

It can be implemented earlier and independently, even before:

- cross-process request leases
- full stale-session preflight rejection
- broader durable conflict-state modeling

Those broader mechanisms may still be valuable later, but this smaller plan already guarantees that missed request failures do not disappear silently.

## Open questions

- Should `cancelled` ever auto-show, or only appear in the past errors/history view?
- Should the server expose only terminal outcomes, or also allow querying the raw request-outcome records?
- Should the generic fallback for `started` without terminal outcome use a special synthetic code like `incomplete_request`?
- Should dismissal be tracked per `request_id` or per request outcome `event_id`?