# Fix infinite "range not available" popup loop after session compaction

After a session is compacted, chat screens on both desktop and mobile that hold
an absolute message range (e.g. `100:150`, produced by transcript range
pagination or the Message Limit popover and persisted in the messages cache)
fail every message load with HTTP 400 "range selects no messages". A
session-refresh invalidation (e.g. the compaction completion notification's
`reload_session_ids` ui-effect) then retries the failing reload forever,
showing an error popup in an infinite cycle. Correct both problems: stop the
infinite retry, and recover gracefully by falling back to the default range
`-50:`.

## Requirements checklist

- [x] A failed session-refresh invalidation reload is not retried indefinitely;
      the repeated-popup cycle no longer occurs when a reload failure persists
      (both desktop and mobile, which consume the shared frontend SDK).
- [x] Other reload failures still surface at most once per emitted
      invalidation (single error surface; no silent swallowing of the first
      failure).
- [x] When a message load fails because an absolute range selects no messages
      (e.g. after session compaction), the client automatically falls back to
      the default suffix range `-50:` and completes a successful load of that
      window.
- [x] After the fallback, the effective range is reflected in the chat UI
      range state and persisted per frontend (desktop messages-cache range
      texts; mobile saved history range), so subsequent reloads, tab switches,
      and app restarts do not reapply the invalid range.
- [x] Both corrections are covered by automated tests at the shared
      frontend-sdk layer where they are implemented, and the frontend
      range-state sync is covered by at least one test in each frontend app.

## Open questions (before execution)

1. **Retry semantics for refresh invalidations** (material, shared-package
   contract; current behavior is documented): choose between
   (a) consume/acknowledge an invalidation after one reload attempt
   regardless of outcome, (b) keep the invalidation pending but stop
   replaying pending invalidations to new subscribers (live delivery only),
   or (c) keep replay with per-revision throttling/backoff.
   Recommendation: (a) — simplest and robust; combined with the range
   fallback it removes both the loop and its trigger. Verify no consumer
   (desktop ChatPane, mobile SessionChatScreen, SessionsPanel-style list
   reloads, plugins registry) depends on retry-until-success.
2. **Detection of "range selects no messages"**: SDK-side helper matching the
   transport error (HTTP 400 + detail substring) versus adding a structured
   error code server-side. Recommendation: SDK-side helper now (contained,
   no API change); a structured server error code can be a follow-up.

## Supporting details (verified facts)

- Server rejects out-of-bounds absolute ranges:
  `application/python/agent_terminal_app/server.py:811-843`
  (`_normalize_slice_bounds` clamps both bounds; `start_idx >= end_idx` →
  `ValueError("range selects no messages")`) raised as HTTP 400 at
  `server.py:2337-2340`. Failure is persistent because compaction shrinks
  the message list and nothing resets the range.
- Compaction emits the invalidation trigger: a pending session notification
  with `ui_effects: {reload_session_ids: [sessionId]}` on success
  (`plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_process.py:561-564`,
  status stays "pending" per
  `plugins/openai_responses/tests/test_openai_responses_native_compaction_app.py:274-281`).
  Additionally `core/python/agent_app/application_future.py:3456-3459`
  always appends the session to `reload_session_ids` for session-mutating
  actions.
- Retry loop mechanics in `packages/frontend-sdk/src/plugins/uiEffects.ts`:
  - `subscribeMatchingRefreshInvalidations` (lines 161-199): failed reload →
    claim released, invalidation stays pending ("keep pending for a later
    consumer or retry").
  - `subscribeRefreshUiEffects` (lines 83-90): every new subscriber receives
    all pending invalidations (replay on subscribe).
  - Desktop subscriber `desktop/.../src/chat/ChatPane.tsx:2651-2658`
    (`handleReload`, whose deps include `reloadInFlight`, so its identity
    changes after every attempt → resubscribe → replay).
  - Mobile subscriber `mobile/.../src/SessionChatScreen.tsx:2257-2278`
    (`loadMessages`, whose deps include `onUpdateCache` — an inline arrow in
    `ConnectedRoot.tsx:453-467` — and whose failing attempts call
    `appendDebugNote` → App-level `setDebugTimeline` → parent re-render →
    resubscribe → replay).
  - Net effect: claim release (microtask) always precedes the
    resubscription render, so the replay claims again → reload → fail →
    `Alert.alert` → release → … One popup plus at least one HTTP GET per
    iteration (three more UI-schema loads per iteration on mobile via
    `refreshUiSchema: true`).
- Alert sources for the failing load: desktop `ChatPane.tsx:1268-1289`
  (initial load), `ChatPane.tsx:2609-2645` (`handleReload`),
  `ChatPane.tsx:3071-3115` (`applyMessageLimitAndReload`); mobile
  `SessionChatScreen.tsx:2071-2126` (`loadMessages`),
  `SessionChatScreen.tsx:2128-2204` (`reloadMessagesForRange`).
- Absolute ranges are normal, not exotic:
  `packages/frontend-sdk/src/chat/messageRangeControls.ts:98-151`
  converts suffix ranges to absolute windows once pagination exceeds
  `maxRangeSize`; the Message Limit popover accepts arbitrary ranges
  (`desktop/.../src/windows/MessageLimitPopoverContent.tsx`). Range texts
  are persisted (desktop `persistCacheSnapshot`; mobile `onSaveHistoryRange`
  → `saveMessagesHistoryRange`).
- Load path that must fall back: `ChatController.reloadMessages` /
  `loadMessagesFromRangeText`
  (`packages/frontend-sdk/src/chat/chatController.ts:204-217, 494-553`);
  range text parsing in `packages/frontend-sdk/src/utils/range.ts`.
  App effects re-apply the UI range text on every change (desktop
  `ChatPane.tsx:1252-1261`; mobile `SessionChatScreen.tsx:1305-1313`), so a
  controller-side fallback alone would be overwritten unless the apps sync
  their range state from the controller's effective range.
- Current retry semantics are documented in
  `packages/frontend-sdk/docs/development/notification-implementation.md`
  (lines 51-60) and must be updated with the new behavior.
- Default window constants: desktop `DEFAULT_HISTORY_WINDOW = 50`
  (`ChatPane.tsx:172`); mobile `DEFAULT_MOBILE_TRANSCRIPT_RANGE`
  (`mobile/.../src/transcriptRange.ts`). Suffix range `-50` never fails
  server-side (bounds clamp to the tail).

## Execution plan

Status: Approved

### 1. SDK: consume refresh invalidations after one attempt

In `packages/frontend-sdk/src/plugins/uiEffects.ts`, change
`subscribeMatchingRefreshInvalidations` so an invalidation is acknowledged
(consumed) after a single reload attempt regardless of outcome (pending
question 1). Keep claim-based in-flight dedupe unchanged. Do not change
`emitRefreshUiEffects` fan-out or the plugins-registry invalidation path
unless tests show a dependency on retry-until-success.

### 2. SDK: default-range fallback in ChatController

In `packages/frontend-sdk/src/chat/chatController.ts`:

- Add a shared default range constant (`-50` suffix window; export it so both
  apps alias it) and an error-detection helper (pending question 2) such as
  `isRangeSelectsNoMessagesError(err)` — transport errors surface as
  `HTTP 400 ... range selects no messages` (`fetchTransport.ts:156`).
- In `reloadMessages`, when the current range is not the default suffix
  window and `listMessages` fails the detection helper, reset
  `historyRange`/`lastLoadRange` to the default window and retry once.
  Surface the effective range to consumers (e.g. add the effective
  start/end range text to `ChatControllerState`, or an `onRangeFallback`
  callback option) so apps can sync their UI state. Non-range failures
  propagate unchanged.

### 3. Frontends: sync range state after fallback

- Desktop `ChatPane.tsx`: when the controller reports the fallback, set
  `rangeStartText`/`rangeEndText` to the default texts. The existing cache
  persist effect then persists `-50`/`` automatically.
- Mobile `SessionChatScreen.tsx`: same state update plus
  `onSaveHistoryRangeRef.current('-50', '')` so the saved history range is
  corrected.

### 4. Hardening (recommended, low risk)

- Desktop: keep `reloadInFlight` in a ref so `handleReload`'s identity is
  stable across attempts (subscription effect no longer churns).
- Mobile: wrap `onUpdateCache`/`onUpdateSessionSummaries` in `useCallback`
  in `ConnectedRoot.tsx` (or subscribe through a ref-held `loadMessages`).

### 5. Tests

- `packages/frontend-sdk/src/plugins/uiEffects.test.ts` (layer of
  correction 1): emit a `reloadSession` invalidation; subscriber reload
  fails → resubscribe (new listener) → assert the reload was attempted
  exactly once and the pending invalidation is no longer replayed. Keep/extend
  the success-path acknowledgement test.
- `packages/frontend-sdk/src/chat/__tests__/chatController.test.ts` (layer
  of correction 2): fake backend rejects `listMessages` with the range error
  for the absolute range and succeeds for `{start: -50}` → assert exactly one
  fallback retry, final `historyRange` is the default suffix window, messages
  loaded, and state exposes the effective range; also assert a non-range
  failure still rejects without retry.
- Desktop app test (`__tests__/ChatPaneTabStack.test.tsx` or a focused
  ChatPane test): simulate fallback → range text state and cache persist
  call carry `-50`/``.
- Mobile app test (new focused `SessionChatScreen` test or nearest existing
  screen harness): simulate fallback → range state updated and
  `onSaveHistoryRange` called with `-50`/``.

### 6. Documentation

Update `packages/frontend-sdk/docs/development/notification-implementation.md`
(retry/acknowledgement semantics) and document the default-range fallback
behavior where the chat controller is described (frontend-sdk docs/development
index or README section, smallest fitting place).

### Implementation decisions and open questions

- Open questions 1 and 2 above must be answered before implementation;
  recommendations are (a) consume-after-one-attempt and SDK-side detection.
- Local decisions assumed: fallback retries exactly once per load call; the
  fallback applies only when the requested range differs from the default;
  the effective-range surface is additive (no breaking ChatController API
  change).
- No server-side changes in this task.

### Documentation

- `packages/frontend-sdk/docs/development/notification-implementation.md` —
  replace the "releases the claim while retaining the invalidation" wording
  with the new once-per-attempt semantics.
- Frontend-sdk development docs — brief note on the default-range fallback
  and the exported default constant + error helper.

### Task checklist

- [x] Answer open questions 1–2 (approved: consume-after-one-attempt;
      SDK-side detection).
- [x] SDK: uiEffects once-per-attempt semantics + unit tests.
- [x] SDK: ChatController default-range fallback, effective-range exposure,
      detection helper + unit tests.
- [x] Desktop: range-state sync test.
- [x] Mobile: range-state sync (+ `onSaveHistoryRange`) test.
- [x] Hardening: desktop `reloadInFlight` ref; mobile `useCallback` wrappers.
- [x] Docs updates.
- [x] Run `npm --workspace @crystal-lattice/frontend-sdk test`,
      `npm test` in desktop and mobile app packages.

## Implementation Notes

- `releaseRefreshUiEffect` became dead code after the consume-after-one-attempt
  change and was removed; `claimRefreshUiEffect` still provides in-flight
  dedupe, and revision comparison still protects newer invalidations emitted
  while a reload is in flight.
- The pre-existing uiEffects test "keeps a cached session stale until an
  active consumer reloads it" encoded the old retry-until-success contract
  and was replaced by consume-after-failure / consume-after-rejection /
  acknowledge-after-success tests.
- `useChatController` forwards `onRangeFallback` through a
  `setRangeFallbackListener` effect so the controller captures a stale
  callback never (unlike constructor-only options).
- Desktop `handleReload` keeps the `reloadInFlight` state for UI gating but
  guards with a ref, so the invalidation subscription in
  `subscribeSessionRefreshInvalidations` no longer resubscribes per attempt.
- The desktop fallback test renders the real `ChatPane` via
  `ChatPaneTabStack` with a Proxy-based fake backend; the mobile fallback
  test renders the real `SessionChatScreen` inside the production provider
  stack (Theme + PinnedActions + ApplicationPlugins) following the
  `src/testing/` harness pattern.

## Completion Notes

**Outcome.** Both corrections are implemented in the shared frontend SDK
with frontend integration, and all suites pass:

- `packages/frontend-sdk/src/plugins/uiEffects.ts`: a claimed refresh
  invalidation is consumed after one reload attempt regardless of outcome
  (success acknowledges; failure/rejection also consumes). The loop
  mechanism (pending-invalidation replay to every new subscriber combined
  with per-render resubscription) is eliminated; in-flight dedupe via
  claims and newer-revision protection are unchanged.
- `packages/frontend-sdk/src/chat/chatController.ts`: new exports
  `DEFAULT_HISTORY_RANGE` (`{start: -50}`) and
  `isRangeSelectsNoMessagesError`; `reloadMessages` retries once with the
  default suffix window when a non-default range fails the detection
  helper, updates `historyRange` accordingly, and notifies via the
  constructor `onRangeFallback` option or `setRangeFallbackListener`.
- `packages/frontend-sdk-react/src/useChatController.ts`: forwards
  `onRangeFallback` to the controller (kept current via effect).
- Desktop `ChatPane.tsx`: `onRangeFallback` handler syncs
  `rangeStartText`/`rangeEndText` (cache persist effect persists them);
  `handleReload` in-flight guard moved to a ref so its identity (and the
  invalidation subscription) is stable across attempts.
- Mobile `SessionChatScreen.tsx`: `onRangeFallback` handler syncs range
  texts and calls `onSaveHistoryRange`; `ConnectedRoot.tsx` stabilizes the
  messages-cache and sessions-list cache-update callbacks with
  `useCallback` so subscriptions no longer churn on every parent render.

**Requirement evidence.**

- No-infinite-retry: `uiEffects.test.ts` "consumes an invalidation after
  one failed reload attempt" and "consumes an invalidation after a rejected
  reload attempt" prove a failing reload is attempted once and not replayed
  to resubscribed consumers.
- Range fallback: `chatController.test.ts` "falls back to the default range
  when an absolute range selects no messages" proves one fallback retry,
  final `historyRange` `{start: -50}`, loaded messages, and listener
  notification; "does not fall back for non-range failures" and "does not
  retry the fallback when the default range itself fails" bound the
  behavior.
- Durable recovery per frontend: desktop
  `__tests__/ChatPaneRangeFallback.test.tsx` (real ChatPane via
  ChatPaneTabStack; asserts `listMessages` calls `100:150` then `-50`,
  `onUpdateCache` persists `-50`/``, and `Alert.alert` is never called) and
  mobile `__tests__/SessionChatScreenRangeFallback.test.tsx` (real
  SessionChatScreen in the production provider stack; same backend
  assertions plus `onSaveHistoryRange('-50','')` and no alert).
- Other failures surface at most once per invalidation: consume-after-one-
  attempt semantics plus the consumers' existing single-alert error paths
  (unchanged).

**Verification performed.** `npm test` in `packages/frontend-sdk`
(48 files / 349 tests), `packages/frontend-sdk-react` (6 files / 24 tests),
desktop app (41 suites / 193 tests), mobile app (53 suites / 254 tests) —
all passing, including the four new/updated test groups.

**Deviations / findings.**

- The pre-existing uiEffects test encoding retry-until-success was
  intentionally replaced (documented in Implementation Notes).
- `releaseRefreshUiEffect` was removed as dead code.
- An earlier background mobile jest run executed from the repo root
  (background tasks start in the primary working directory) and produced a
  meaningless 460-suite failure listing; it was re-run from the app
  directory with the results above.
- No server-side or Python changes; no API break — the new controller
  surface is additive.

**Deferred.** Optional follow-ups not in scope: a structured server error
code instead of detail-substring detection; converting the mobile
`onSaveHistoryRange`/compose/scroll inline arrows to stable callbacks
(only the cache-update drivers were required); native (macOS UI) test
coverage for the popup-free recovery.

### Requirement verification

- No-infinite-retry requirement → new unit test in
  `packages/frontend-sdk/src/plugins/uiEffects.test.ts` proving a failed
  invalidation reload is attempted once and not replayed to new subscribers
  (the exact loop mechanism), plus the existing acknowledgement tests
  staying green.
- Range-fallback requirement → new unit test in
  `packages/frontend-sdk/src/chat/__tests__/chatController.test.ts` proving
  an absolute-range "range selects no messages" failure falls back to
  `-50:`, retries once, and loads the default window; non-range failures
  still propagate.
- Durable-recovery requirement → one app-level test per frontend verifying
  the range texts (and mobile's persisted history range) are updated to the
  default after fallback.
- Test-coverage requirement → the four tests above, run via
  `npm --workspace @crystal-lattice/frontend-sdk test` and each app's
  `npm test`.

### Additional implementation verification

- Re-run desktop `ChatPaneTabStack.test.tsx` and mobile
  `ConnectedRoot.connections.test.tsx` to confirm no regression in
  subscription-driven reload behavior.
- Manual smoke (optional, if a compaction-capable agent is available):
  paginate an older absolute range, compact the session, confirm a single
  recovery to the last-50 window with no repeated popups.
