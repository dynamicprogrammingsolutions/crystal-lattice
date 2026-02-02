# SDK: windowed history + atomic reload + auto-recover dirty (rate limited)

Parent Task: `tasks/20260129-events-no-full-session/000-main.md`

Depends On:

- `tasks/20260129-events-no-full-session/060-chatcontroller-integration.md`
- `tasks/20260129-events-no-full-session/070-mobile-remove-reloads.md`

## Goal

Move recovery and reload coordination into the SDK `ChatController` so that:

- The message history stored in memory is a **window** (range-limited), not always the full session.
- `IndexedMessage.index` remains the **real session-global index** (what the user sees/uses).
- When events append new messages, the controller trims/drops older messages to maintain the configured window.
- When the reducer cannot apply an event safely (marks `dirty`), the controller automatically reloads once per "epoch" (opening a session or a user action), otherwise requires manual reload.
- Reload is **atomic** with respect to polling event application (fixes out-of-sync issues when reloading while events arrive).

Primary motivating case: the `system_message_feature` can cause the server to implicitly insert a system message into stored history during the first user append, shifting indices and making strict index-based event application correctly report `dirty`.

## Status

Subtask checklist:

- [x] Write down final plan in this task file
- [x] Implement window-aware reducer that operates on **global indices** and supports trimming
- [x] Implement delete shifting + backfill signal for windowed history
- [x] Update `ChatController` to store range/window settings and apply events with the new reducer
- [x] Make `ChatController.loadMessages*` pause/resume polling so reload is atomic
- [x] Add `ChatController` epoch budget + auto-recover (one auto reload per epoch)
- [x] Update `useChatController` to not restart polling while `loading`
- [x] Update/extend SDK tests (window append + trimming + delete shifting/backfill)
- [x] Update mobile to keep existing range UI but rely on controller behavior (minimal/no change expected)
- [x] Update this file with implementation notes discovered during coding

## What’s happening today (root cause)

### Symptom

- First user message in a new session can trigger `dirty` as soon as streaming starts or final arrives.

### Why it happens

- The server publishes `message_appended` with the post-append index of the *last* message:
  - `application/python/agent_terminal_app/server.py:734` calls `core.add_message(...)` with a provider config.
  - `application/python/agent_terminal_app/server.py:739` computes `last_index = len(new_session.messages) - 1` and publishes it.

- When `SystemMessageFeature` is enabled, it can insert a system message into provider-native history:
  - `core/python/plugins/system_message_feature.py:405` inserts a synthetic `{"role":"system", ...}` when the native history has no system message.

- On an empty session, `AgentCore.add_message(..., config=...)` may rebuild canonical core messages from native history; that rebuild can introduce the system message into stored core history.
  - So the very first “append user message” effectively becomes two messages in stored history: `[system, user]`.
  - The server then emits `message_appended.index = 1`.

- The strict reducer expects `message_appended.index === localMessages.length`.
  - On the client, local length is `0`, so `index=1` becomes a mismatch and returns `dirty`.
  - See `packages/frontend-sdk/src/chat/messageHistoryReducer.ts:80`.

This reducer also assumes it owns the full session history (local indices `0..n-1`), which is incompatible with a true windowed history (e.g. only last 50 messages).

## Requirements

- If the session becomes `dirty`, the UX should recover automatically via a reload.
- Avoid excessive reloading:
  - At most **one auto reload per “epoch”** (epoch = “opening a session” or “a single user action”).
  - If the session goes dirty again within the same epoch, require manual reload.

- Range selection must actually bound stored history:
  - When configured for tail behavior (e.g. `start=-50,end=`), the controller must keep at most 50 messages.
  - As new messages are appended via events, older messages are dropped.
  - Indices shown to the user must remain the real session-global indices.

- Reload must be atomic wrt event polling:
  - Manually reloading while events are arriving should not frequently trigger out-of-sync / dirty.

## Complete plan (approved direction: Option B with true windowed history)

### 1) Represent the message window in the controller

- Continue to expose `ChatController.loadMessagesFromRangeText({startText,endText})` so the frontend UI can remain unchanged.
- Parse as today (`packages/frontend-sdk/src/utils/range.ts:8`) into `{start?: number; end?: number}`.
- Derive window settings:
  - `followTail = (end === undefined)` (meaning the view is “to the end”).
  - `maxMessages = abs(start)` when `followTail` and `start < 0`.
  - Otherwise `maxMessages = null` (no trimming).
- Store `historyRange` / `followTail` / `maxMessages` in controller state and keep the last used params for future reloads.

### 2) Replace the message history reducer with a window-aware, global-index reducer

Update `packages/frontend-sdk/src/chat/messageHistoryReducer.ts` so it operates on global indices:

- Define `expectedNextIndex` as:
  - `0` when there are no stored messages, else `lastStoredIndex + 1`.
- For `message_appended`, validate `event.index === expectedNextIndex`.
- For `final` / `tool_results`, validate `event.start_index === expectedNextIndex`.
- For `messages_deleted`:
  - Remove any stored messages whose global index is deleted.
  - Shift remaining indices down by `count(deletedIndices < message.index)`.
  - If `maxMessages` is set and the window is now shorter than `maxMessages`, return `needsBackfill: true` (not dirty).
- For `message_modified`:
  - If the message is present in the current window, replace it.
  - If it’s older than the window, treat as noop.
  - If it’s newer than the window end, treat as dirty (client is behind).

Also apply trimming:

- After append/final/tool_results, if `maxMessages` is set, keep only the last `maxMessages` messages.

### 3) Make reload atomic wrt polling

Update `ChatController.loadMessages*`:

- If polling is active, stop it before fetching `/messages`.
- Fetch messages + `cursor_event_id`.
- Update snapshot (messages, cursors, clear dirty).
- Resume polling from `cursor_event_id` (or allow the React hook to restart after `loading=false`).

Update `packages/frontend-sdk-react/src/useChatController.ts`:

- Do not start polling while `state.loading` is true (prevents concurrent poll during reload).

### 4) Auto-recover `dirty` (one per epoch)

- Add an internal epoch counter + “used budget” marker to `ChatController`.
- Begin a new epoch when the user triggers a state-changing action:
  - `appendMessage`, `send`, `modifyMessage`, `deleteMessages`, and manual reload.
- When the reducer returns `dirty` (or `needsBackfill`), schedule an automatic reload if:
  - not already reloading, and
  - the budget for the current epoch has not been used.
- The scheduled auto reload must not advance epochs (prevents loops).

### 5) What happens when the user is not following the tail

When `end` is explicitly provided (`followTail=false`), the controller cannot safely apply append-at-end events to the loaded slice.

Proposed behavior:

- Still apply request-lifecycle / streaming state reducers.
- Skip applying history mutations from events (or immediately mark dirty and require explicit reload).

This keeps complexity bounded; the primary supported UX is `all` or `last N`.

## Suggested acceptance tests

- With `system_message_feature` enabled:
  - Open a fresh session.
  - Send the first user message.
  - Expect at most one automatic reload.
  - After reload, the session is no longer `dirty` and streaming/final events apply cleanly.

- Fault injection:
  - Force `dirty` twice in one epoch (e.g. by resetting local cache mid-stream).
  - Expect: first `dirty` triggers auto reload; second shows banner and requires manual.

## Implementation notes (append as work progresses)

- `PollingEventSource` previously could deliver events after `stop()` if a poll request was already in-flight; this breaks atomic reload. Fixed by adding a `generation` counter and re-checking `stopped/generation` after `await listEvents` in `packages/frontend-sdk/src/events/pollingEventSource.ts`.
- To keep window trimming active even when hydrating from cache (and skipping initial reload), mobile now calls `chatController.setHistoryRangeFromRangeText(...)` whenever the range UI state changes in `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`.
