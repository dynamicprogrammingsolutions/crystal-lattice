# Shared: reusable session plugins controller + UI list

Parent Task: tasks/20260213-session-plugins-ui/000-main.md

Depends On:
- tasks/20260213-session-plugins-ui/020-shared-frontend-sdk.md

## Description

Create reusable building blocks so mobile and desktop don’t each reimplement:

- loading the plugin list
- toggling a plugin and persisting the resulting enabled set
- resetting session plugin overrides

This should mimic terminal `/plugins` UX: switches, “inactive” indicator, and reset-to-default behavior.

## Where to put shared code

Recommended split:

1) **Controller/hook** in `packages/frontend-sdk-react` (data fetching + mutations)
2) **Presentational UI** in `packages/frontend-rn-components` (rendering list, switches)

This matches existing patterns:
- `frontend-sdk-react` already owns controller hooks (sessions, chat, UI schema controllers).
- `frontend-rn-components` already owns shared action bars and theme primitives.

## Controller: suggested API

Create something like:

```ts
export interface SessionPluginsState {
  loading: boolean;
  error: string | null;
  plugins: SessionPluginEntry[];
  lastLoadedAt?: number | null;
}

export function useSessionPluginsController(params: {
  backend: AgentBackend | null;
  sessionId: string | null;
  enabled?: boolean;
}): {
  state: SessionPluginsState;
  reload: (opts?: { force?: boolean }) => Promise<void>;
  setEnabled: (pluginId: string, enabled: boolean) => Promise<void>;
  resetToDefaults: () => Promise<void>;
}
```

Implementation notes:

- `reload`:
  - call `backend.listSessionPlugins(sessionId)`
  - store as state

- `setEnabled(pluginId, enabled)`:
  - compute **next explicit enabled list** from current entries:
    - If current `plugins` state includes `enabled` flags, use that to build `enabledIds`.
    - If enabling: add id.
    - If disabling: remove id.
  - call `backend.setSessionPlugins(sessionId, enabledIds)`.
  - then reload (or optimistically update + reload in background).

- `resetToDefaults()`:
  - call `backend.clearSessionPlugins(sessionId)` then reload.

Edge cases:

- If plugin list hasn’t loaded yet, `setEnabled` should either no-op with error or force a reload.
- If backend capabilities say `sessionPlugins: false`, set a friendly error.

## UI component: suggested API

Create a shared list component that’s easy to embed in either a modal or a window:

```ts
export function SessionPluginsList(props: {
  plugins: SessionPluginEntry[];
  onToggle: (pluginId: string, nextEnabled: boolean) => void;
  onReset?: () => void;
  loading?: boolean;
  error?: string | null;
}): React.JSX.Element;
```

Rendering requirements:

- Group by `kind` in order: providers, extensions, features, tools.
- Each row shows:
  - plugin id (and optional `name`)
  - a `Switch` bound to `enabled`
  - small “Inactive” label when `active === false`.
- A Reset button:
  - show always, or show only when any plugin has `source === 'session'`.

Avoid coupling to app-specific containers:
- Mobile will wrap in a React Native `Modal`.
- Desktop can wrap in a `Modal` or a dedicated window view.

## Add a session action key

Add a new built-in session action to the shared actions registry:

- File: `packages/frontend-rn-components/src/sessionActions.ts`
- Add:
  - key: `plugins`
  - label: `Plugins`
  - iconName: choose something consistent (e.g. `toggle-left` or `package` if available in Feather; Feather has `package`, `sliders`, `toggle-left`).
  - defaultPinned: false

This will automatically make it available to `SessionActionsBar` consumers if they include it in `availableActions`.

## Done when

- `frontend-sdk-react` exposes a controller/hook that mobile+desktop can share.
- `frontend-rn-components` exposes a list UI component.
- `frontend-rn-components` includes the new `plugins` session action definition.

---

## Implementation notes (added during completion, 2026-02-13)

### What was implemented

- Added a shared React hook/controller (`useSessionPluginsController`) in `@crystal-lattice/frontend-sdk-react`.
  - Loads plugins via `backend.listSessionPlugins(sessionId)`.
  - Persists toggles by computing the next explicit enabled-id list and calling `backend.setSessionPlugins(sessionId, enabledIds)`.
  - Supports reset-to-defaults via `backend.clearSessionPlugins(sessionId)`.
  - Capability-gates on `backend.getCapabilities().sessionPlugins` and surfaces a friendly error.
- Added a shared presentational list component (`SessionPluginsList`) in `@crystal-lattice/frontend-rn-components`.
  - Groups entries by `kind` (providers/extensions/features/tools/other), renders a per-plugin `Switch`, and shows an “Inactive” label when `active === false`.
  - Includes a “Reset to defaults” button (disabled unless any plugin has `source === 'session'`).
- Added a new session action definition `plugins` to the shared session actions registry.

### Files created

- `packages/frontend-sdk-react/src/useSessionPluginsController.ts`
- `packages/frontend-sdk-react/src/sessionPlugins/logic.ts`
- `packages/frontend-sdk-react/src/sessionPlugins/logic.test.ts`
- `packages/frontend-rn-components/src/SessionPluginsList.tsx`

### Files modified

- `packages/frontend-sdk-react/src/index.ts` (exported `useSessionPluginsController` + types)
- `packages/frontend-rn-components/src/index.ts` (exported `SessionPluginsList`)
- `packages/frontend-rn-components/src/sessionActions.ts` (added `plugins` action key)

### Validation

- `npm test -w @crystal-lattice/frontend-sdk-react`
- `npm test -w @crystal-lattice/frontend-rn-components`
