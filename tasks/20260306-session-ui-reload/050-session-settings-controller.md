# Session Settings Controller

Parent Task: `tasks/20260306-session-ui-reload/000-main.md`

Depends On:
- `tasks/20260306-session-ui-reload/010-a1-sdk-local-invalidation.md`
- `tasks/20260306-session-ui-reload/040-settings-ui-use-shared-schema-controller.md`

Description:
Add a shared frontend SDK controller for session settings data so the settings UIs can open immediately from cached data, refresh asynchronously, and show accurate loading/saving status instead of blocking on ad-hoc fetches and optimistic-only local state.

Problem summary:
- The settings UIs now reuse cached session UI schema via `useSessionUiSchemaController`, but they still perform separate async fetches for:
  - `getSessionOverrides(sessionId)`
  - `getSessionConfigSchema(sessionId)`
  - `getSessionBaseConfig(sessionId)`
- Because the modal/window renders behind a `loading` gate, users still see a spinner before the content appears even when UI schema is already cached.
- Saving is currently optimistic in the settings UIs (`setOverrides(...)` before server confirmation), but there is no shared controller state that cleanly expresses:
  - initial loading
  - background refresh
  - save in progress
  - save succeeded
  - save failed / reverted
- The current settings UIs also own too much fetch/mutation state locally, making it harder to preserve draft text while schema changes live.

Relevant existing code:
- Mobile settings modal:
  - `mobile/crystal-lattice-control-rn/src/components/SessionSettingsModal.tsx`
- Desktop settings window:
  - `desktop/crystal-lattice-control-desktop-rn/src/windows/SessionSettingsWindow.tsx`
- Existing shared schema controller / hook:
  - `packages/frontend-sdk/src/uiSchema/sessionUiSchemaController.ts`
  - `packages/frontend-sdk-react/src/useSessionUiSchemaController.ts`
- Existing shared plugins controller / UX reference:
  - `mobile/crystal-lattice-control-rn/src/components/SessionPluginsModal.tsx`
  - `desktop/crystal-lattice-control-desktop-rn/src/windows/SessionPluginsWindow.tsx`
  - `packages/frontend-sdk-react/src/useSessionPluginsController.ts` (or equivalent shared plugin controller hook)
- Settings item derivation:
  - `packages/frontend-sdk-react/src/sessionSettings/logic.ts`
  - `packages/frontend-sdk-react/src/sessionSettings/SessionSettingsHost.tsx`

Goal:
Create a shared controller in the frontend SDK that owns all session-settings data needed for rendering and mutation, similar in spirit to the session plugins controller.

Proposed controller responsibilities:
- Load and cache, per `(backend, cacheKey, sessionId)`, the combined settings inputs:
  - filtered session UI schema config elements
  - session overrides
  - session config schema
  - session base config
- Hydrate synchronously from cache when available.
- Refresh asynchronously in the background.
- Subscribe to session UI invalidation events and reload affected data.
- Expose mutation helpers for:
  - patching overrides
  - deleting overrides
- Track mutation state cleanly so the UI can represent saving/refreshing without guessing from local optimistic state.

Recommended API shape:
- SDK class in `packages/frontend-sdk`, e.g. `SessionSettingsController`
- React hook in `packages/frontend-sdk-react`, e.g. `useSessionSettingsController`
- State shape should include at least:
  - `elements`
  - `overrides`
  - `baseConfig`
  - `schemaByKey` or raw `configSchema`
  - `loading`
  - `refreshing`
  - `savingKeys` (or mutation map by key)
  - `error`
  - `statusMessage` and/or `lastSavedAt`
  - `lastLoadedAt`

Suggested loading model:
- `loading` = no cached snapshot yet and first fetch is in progress.
- `refreshing` = cached snapshot already exists, but a background refetch is happening.
- The UI should render cached content immediately when present.
- Do not block the settings list behind `loading` once cached data exists.

Suggested mutation model:
- Keep optimistic updates, but centralize them in the controller.
- For each save/delete operation:
  - mark the affected key as saving
  - apply optimistic local update
  - perform backend request
  - on success, clear saving state and surface success status
  - on failure, revert the optimistic update and surface error status
- Ensure that schema-changing saves trigger a refresh of the full settings snapshot.
- Preserve per-key drafts in the UI layer for unaffected keys.

Status line / indicator requirements:
- The settings UIs should show a top status line similar to the one used in the plugins window, not a full-screen/blocking spinner once cached content exists.
- Reference behavior / style source:
  - Desktop plugins window status line: `desktop/crystal-lattice-control-desktop-rn/src/windows/SessionPluginsWindow.tsx`
  - Mobile plugins modal status line: `mobile/crystal-lattice-control-rn/src/components/SessionPluginsModal.tsx`
- Reuse the same UX pattern:
  - small spinner at the top when refreshing or saving
  - concise one-line status text
  - success/error tone handling
- Include explicit save feedback because settings currently use optimistic UI and there is no clear indication that the change actually reached the server.
- The status line should communicate at least:
  - loading / refreshing
  - saving
  - saved
  - error

UX requirements:
- Opening settings after chat already loaded data should feel immediate.
- Background refresh should not replace the whole view with a spinner.
- Unchanged rows should remain mounted; rely on stable `item.key` keys.
- Draft text for unaffected keys must not be lost during refresh.
- If an element disappears because another setting changed the schema (example: `reasoning_effort` removed after switching to a non-reasoning model), remove only that row while preserving the rest of the UI.

Implementation notes:
- A good approach is to let the controller own server state and mutation status, while the screen/modal still owns purely local draft text (`pendingTextByKey`) and dropdown-open state.
- Consider pruning draft text only for keys that no longer exist in the refreshed elements, rather than resetting all drafts.
- The controller should probably reuse the same cache key convention already used by `SessionUiSchemaController` so chat and settings stay aligned per connection.
- Prefer additive changes; do not do a major refactor of the existing settings rendering helpers.

Acceptance criteria:
- Settings modal/window can render immediately from cached settings snapshot when available.
- A top status line indicates background refresh and save progress in the same style/pattern as the plugins window.
- Saving a setting shows clear success/error feedback; users are no longer left guessing whether the optimistic change was persisted.
- Schema-changing settings updates refresh the list live without wiping unaffected drafts.
- Mobile and desktop both use the shared controller with minimal UI-specific glue code.

---

## Plan added during completion

1. Define shared controller contract
   - Add a `SessionSettingsController` in `packages/frontend-sdk` with a cached snapshot keyed by `(backend, cacheKey, sessionId)`.
   - Shape the state to include `elements`, `overrides`, `baseConfig`, `schemaByKey`/raw schema, `loading`, `refreshing`, `savingKeys`, `error`, `statusMessage`, `lastSavedAt`, and `lastLoadedAt`.
   - Make the controller the single owner of server-backed settings state and optimistic mutation state, while leaving per-row draft text and dropdown-open UI state in the screen/modal layer.

2. Implement cached loading + background refresh
   - Hydrate synchronously from any cached snapshot so settings can render immediately when chat or a prior open already loaded the data.
   - Distinguish `loading` from `refreshing`: first open without cache shows initial load state, but any later reload keeps rendering cached content and only updates the top status line.
   - Load the combined settings inputs together: filtered config UI schema elements, session overrides, session config schema, and session base config.
   - Reuse the existing session UI schema cache key convention so chat and settings stay aligned per connection.

3. Handle invalidation + race safety
   - Subscribe the controller to session UI invalidation events so settings data reloads when config/plugin changes alter the schema.
   - Add request sequencing so stale fetches or mutation follow-up reloads cannot overwrite newer state.
   - On refresh, preserve existing cached content and only replace the snapshot when the newest request resolves.

4. Centralize optimistic patch/delete mutations
   - Expose controller helpers for patching and deleting overrides.
   - For each changed key, optimistically update the cached snapshot, mark that key in `savingKeys`, and issue the backend request.
   - On success, clear the key’s saving state, update timestamps, and surface an explicit saved status.
   - On failure, revert only the affected optimistic change, clear saving state, and surface an error status without disturbing unrelated rows.
   - After mutations that can alter available settings/schema, trigger a full snapshot refresh.

5. Add explicit status-line semantics
   - Make the shared controller expose enough status metadata for a top indicator line to show `loading`, `refreshing`, `saving…`, `saved`, and `error` states.
   - Ensure saves are visible in the status line even for optimistic updates, so users can tell whether a change is still in flight or has already persisted.
   - Use a small spinner for `refreshing` and `saving…`, a concise success message for `saved`, and error styling/message for failed operations.
   - Clear or expire transient saved messages predictably without hiding active refresh/save activity.

6. Refactor mobile settings UI to use the controller
   - Replace local fetch/mutation ownership in `mobile/crystal-lattice-control-rn/src/components/SessionSettingsModal.tsx` with the shared controller.
   - Keep only local draft text and dropdown state in the modal.
   - Add a plugins-style top status line that reflects controller state, including explicit `saving…` and `saved` feedback.
   - Prune draft text only for keys that disappear after schema refresh, preserving drafts for unaffected rows.

7. Refactor desktop settings UI to use the controller
   - Apply the same controller integration to `desktop/crystal-lattice-control-desktop-rn/src/windows/SessionSettingsWindow.tsx`.
   - Replace the blocking load UX with cached-first rendering plus the same top status line behavior used on mobile.
   - Preserve row stability via existing item keys so unaffected controls remain mounted across refreshes.

8. Add focused tests
   - Cover controller cache hydration, first-load vs background-refresh behavior, invalidation-driven reload, optimistic patch/delete success and rollback, and status transitions for `saving…`/`saved`/`error`.
   - Add UI-level regression coverage where there is already a suitable test pattern, especially for not wiping unaffected drafts when schema changes remove only some rows.

---

## Completion notes added during completion

- Added shared controller + hook:
  - `packages/frontend-sdk/src/sessionSettings/sessionSettingsController.ts`
  - `packages/frontend-sdk-react/src/useSessionSettingsController.ts`
- The controller now owns combined settings data (`elements`, `overrides`, `configSchema`, `baseConfig`), cached snapshot hydration, background refresh, optimistic patch/delete mutations, per-key `savingKeys`, and derived status line state for `loading`, `refreshing`, `saving…`, `saved`, and `error`.
- Exported the new controller/hook from:
  - `packages/frontend-sdk/src/index.ts`
  - `packages/frontend-sdk-react/src/index.ts`
- Refactored both settings UIs to use the shared controller and keep only local draft UI state:
  - `mobile/crystal-lattice-control-rn/src/components/SessionSettingsModal.tsx`
  - `desktop/crystal-lattice-control-desktop-rn/src/windows/SessionSettingsWindow.tsx`
- Both UIs now show a top status line with explicit `saving…` and `saved` feedback and no longer block cached content behind a full-screen loading gate once data exists.
- Added eager background warm-up from chat surfaces so opening a session chat preloads the settings snapshot before the user opens the settings UI:
  - `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`
  - `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`
- Draft pruning is now key-based: only drafts for removed settings are cleared after schema refresh.
- Added focused controller tests in `packages/frontend-sdk/src/sessionSettings/sessionSettingsController.test.ts` covering cached hydration/background refresh, optimistic save + saved state, and rollback on failed save.
- Validation run:
  - `cd packages/frontend-sdk && npm test -- sessionSettingsController.test.ts` ✅
- Additional TypeScript checks were sampled, but repo-wide `tsc` in these packages still reports unrelated pre-existing errors outside this task (for example existing generic mock typing in `packages/frontend-sdk/src/backend/*.test.ts` and existing `ApiMessage` casting issues in chat/message rendering files).
