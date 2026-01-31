# Mobile: auto-reload when session becomes dirty (rate limited)

Parent Task: `tasks/20260129-events-no-full-session/000-main.md`

Depends On:

- `tasks/20260129-events-no-full-session/060-chatcontroller-integration.md`
- `tasks/20260129-events-no-full-session/070-mobile-remove-reloads.md`

## Goal

When the SDK reducer marks a session as `dirty`, automatically recover by reloading once, **but never get stuck in reload loops**.

Primary motivating case: the `system_message_feature` can cause the server to implicitly insert a system message into stored history during the first user append, shifting indices and making the strict index-based reducer correctly report `dirty`.

## Status

- [ ] Not started

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

## Requirements

- If the session becomes `dirty`, the UX should recover automatically via a reload.
- Avoid excessive reloading:
  - At most **one auto reload per “epoch”** (epoch = “opening a session” or “a single user action”).
  - If the session goes dirty again within the same epoch, require manual reload.

## Proposed solution options (decision needed)

### Option A (recommended): implement auto-reload budget in mobile UI

Implement in `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`.

- Add an “auto reload epoch” mechanism:
  - Reset epoch when:
    - the session screen mounts / `sessionId` changes, or
    - the user performs a “write” action (send/resend/append/modify/delete; including plugin actions).
  - Track `usedAutoReloadThisEpoch`.

- Add an effect watching `chatState.dirty`:
  - If `dirty === true` and `usedAutoReloadThisEpoch === false` and not currently loading:
    - call the existing `loadMessages()`
    - set `usedAutoReloadThisEpoch = true`
  - Else keep `dirty` banner visible, allow manual reload.

Pros:
- Localized change; no SDK API expansion.
- Naturally respects the mobile’s current “message range” (e.g. `-50:`) since it reuses `loadMessages()`.
- Avoids reload loops via explicit budget.

Cons:
- Only mobile benefits; other clients would still require manual reload.

### Option B: implement auto-reload in SDK ChatController

Implement rate-limited recovery in `packages/frontend-sdk/src/chat/chatController.ts`.

Pros:
- One shared implementation; all clients benefit.

Cons:
- Controller currently doesn’t know the mobile’s selected message range; adding that plumbing could be invasive.

### Option C: server emits additional events so clients never go dirty

Detect the implicit system insertion and emit an explicit event for it (or make the system message insertion explicit in stored history mutations).

Pros:
- Clients remain purely event-driven; fewer reloads.

Cons:
- More invasive and subtle; must be correct for all provider/features and history rebuild behaviors.

## Suggested acceptance tests

- With `system_message_feature` enabled:
  - Open a fresh session.
  - Send the first user message.
  - Expect at most one automatic reload.
  - After reload, the session is no longer `dirty` and streaming/final events apply cleanly.

- Fault injection:
  - Force `dirty` twice in one epoch (e.g. by resetting local cache mid-stream).
  - Expect: first `dirty` triggers auto reload; second shows banner and requires manual.
