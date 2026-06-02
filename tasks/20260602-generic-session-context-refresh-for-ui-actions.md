# Generic Session Context Refresh For UI Actions
Add a generic SDK/API mechanism for refreshing session summary/context data used by UI action conditions, action parameter mapping, and session metadata displays. The goal is for all plugin-driven UI surfaces to assume session metadata can change in the background and refresh it without plugin-specific frontend code.

## Requirements checklist

- [x] Add a backend endpoint that returns a fresh summary/context for one session.
- [x] Add frontend SDK backend support for fetching one session summary/context.
- [x] Add a frontend SDK controller, modeled after session settings, that keeps cached context usable while refreshing in the background.
- [x] Use the controller in React/mobile UI action surfaces so action conditions and `$session...` parameter maps use the freshest available generic session context.
- [x] Ensure session agent id UI reads from refreshed session context rather than a stale sessions-list prop.
- [x] Add tests covering stale-while-refresh behavior and metadata/action-condition refresh behavior.

## Background

The mobile message screen currently receives a `sessionSummary` prop from the sessions-list cache. Plugin action visibility and `$session...` parameter mapping use that prop. If session metadata changes in the background while the user remains on the message screen, the UI can stay stale until the user navigates to the sessions list and refreshes there.

This should not be solved by adding plugin-specific code to the mobile UI. The frontend should treat session metadata and other session-summary fields as background-mutable data. When those fields are used by UI actions, the SDK should provide a generic cached value and refresh it in the background.

The intended behavior should match the existing session settings UX: show the old values immediately, refresh in the background, replace the UI state on success, and keep the old values usable on failure.

## Relevant current code

- `application/python/agent_terminal_app/server.py`
  - `GET /sessions` is implemented at approximately line 2238.
  - It builds session summary objects containing `session_id`, `modified`, `preview`, `metadata`, and `pinned`.
  - It also runs configured session-list trigger actions and merges returned `session_list_fields`.
- `packages/frontend-sdk/src/backend/backend.ts`
  - `AgentBackend` currently exposes `listSessions(params?: { limit?: number })`.
  - There is no single-session summary/context method yet.
- `packages/frontend-sdk/src/backend/restBackend.ts`
  - `RestAgentBackend.listSessions()` maps to `GET /sessions`.
- `packages/frontend-sdk/src/sessions/sessionsController.ts`
  - Manages a session list, but does not provide per-session stale-while-refresh state.
- `packages/frontend-sdk/src/sessionSettings/sessionSettingsController.ts`
  - Useful model for this task.
  - It distinguishes initial `loading` from background `refreshing`.
  - It keeps old values available when refresh fails.
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`
  - Computes visible session actions from `sessionSummary`.
  - Uses `sessionSummary` in plugin action dialog/context paths.
  - Separately derives `agent_id` from `sessionSummary?.metadata`.
- `packages/frontend-sdk/src/plugins/actionRunner.ts`
  - `buildActionInputs()` resolves `$session...` values from `context.sessionSummary`.
  - The controller introduced by this task should become the source for that context on UI action surfaces.

## Desired API Shape

Add a single-session summary endpoint:

```http
GET /sessions/{session_id}/summary
```

Return the same shape as one item in `/sessions`:

```ts
interface SessionSummary {
  session_id: string;
  modified: number;
  preview: string;
  metadata?: Record<string, any>;
  pinned?: boolean;
  [key: string]: any;
}
```

Prefer refactoring the existing `/sessions` summary-building code into a helper so `/sessions` and `/sessions/{id}/summary` stay consistent, including metadata stripping, pinned-state handling, and session-list contributed fields.

## Desired SDK Shape

Add to `AgentBackend`:

```ts
getSessionSummary(sessionId: string): Promise<SessionSummary>;
```

Add a controller, suggested name:

```ts
SessionContextController
```

Suggested state:

```ts
interface SessionContextControllerState {
  summary: SessionSummary | null;
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  lastLoadedAt: number | null;
}
```

The controller should:

- hydrate from an initial/cached summary.
- use `loading` only when no summary is available.
- use `refreshing` when a summary exists and a new request is in flight.
- keep the current summary on refresh failure.
- expose `load()`, `refresh()`, `loadIfStale()`, and `invalidate()`.
- use cache keys by backend/connection/session in the same spirit as session settings and plugin controllers.

Add a React hook:

```ts
useSessionContextController({
  backend,
  cacheKey,
  sessionId,
  initialSummary,
  enabled,
})
```

## Desired UI Behavior

In mobile and any shared frontend surfaces using session action UI:

- Continue showing cached session context immediately.
- Trigger a generic background refresh when session action UI is shown or when the message screen becomes active/stale.
- Use the refreshed controller summary for:
  - session action condition evaluation.
  - `$session...` parameter maps.
  - agent id display/switch state.
  - plugin dialogs that prefill from session metadata.
- Do not add code that knows about the cloud plugin or any other individual plugin.
- When refresh fails, keep old values usable and avoid blocking the user from opening menus/settings.

## Testing Notes

Add focused tests before or with implementation:

- Server test: `GET /sessions/{id}/summary` returns the same summary shape as `/sessions` for that session.
- Server test: session metadata changes are reflected by the single-session summary endpoint.
- SDK unit test: `SessionContextController` shows cached data while refreshing and preserves it on failure.
- SDK/unit test: refresh success updates the summary and `lastLoadedAt`.
- UI/shared component test: opening an action surface can trigger a generic refresh callback without blocking the menu/display.
- Mobile-level or SDK action-runner test: `$session.metadata...` mapping uses the refreshed session context when available.

## Execution plan

Added during completion after user approval.

1. Add generic session summary refresh API first.
   - Refactor `/sessions` summary-building into a shared helper.
   - Add `GET /sessions/{session_id}/summary`.
   - Add server tests proving metadata changes are reflected and the single-session shape matches `/sessions`.
2. Add frontend SDK support.
   - Add `AgentBackend.getSessionSummary(sessionId)`.
   - Implement `RestAgentBackend.getSessionSummary`.
   - Add `SessionContextController` with stale-while-refresh behavior modeled after `SessionSettingsController`.
   - Add `useSessionContextController`.
3. Wire generic UI refresh.
   - Use `SessionContextController` in `SessionChatScreen` as the source for action conditions, plugin dialog session context, `$session...` action params, and displayed/current `agent_id`.
   - Add a generic action-surface refresh callback in shared RN components so opening session actions can refresh context in the background without blocking display.
   - Do not add cloud-specific UI code.
4. Test in layers.
   - Python server tests for the summary endpoint.
   - SDK unit tests for context controller refresh/failure semantics.
   - RN/shared component test or focused unit test for generic action-surface refresh-on-open behavior.

## Completion Notes

Added during completion.

- Added `GET /sessions/{session_id}/summary` and refactored session summary construction so the single-session endpoint and `/sessions` share metadata stripping, preview, pinned state, cached summaries, and session-list contributed fields.
- Added `AgentBackend.getSessionSummary`, `RestAgentBackend.getSessionSummary`, `SessionContextController`, and `useSessionContextController`.
- Updated mobile `SessionChatScreen` to use refreshed session context for session action conditions, plugin dialog context/prefill, `$session...` action params, and current agent id state.
- Added generic `onOpenMenu` support to shared RN action bars and used it to refresh session context in the background when session actions are shown.
- Added server and SDK tests for summary refresh and stale-while-refresh controller behavior.