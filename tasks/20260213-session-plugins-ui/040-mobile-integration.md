# Mobile: add “Plugins” to session actions + modal UI

Parent Task: tasks/20260213-session-plugins-ui/000-main.md

Depends On:
- tasks/20260213-session-plugins-ui/030-shared-ui-and-controller.md

## Description

Add a “Plugins” session action to the mobile app (Crystal Lattice Control RN) in the same places “Session settings” exists today:

1) Chat screen session actions bar
2) Sessions list per-session actions

Both should open a modal that lists plugins with switches, and supports reset.

## Background / current code

- Chat screen actions handling:
  - `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`
  - `handleSessionAction` currently checks `action === 'settings'` and opens `SessionSettingsModal`.

- Sessions list actions handling:
  - `mobile/crystal-lattice-control-rn/src/SessionsScreen.tsx`
  - Built-in session list actions are `['agentSwitch', 'settings']`.

## Steps

### 1) Add modal component

Create `mobile/crystal-lattice-control-rn/src/components/SessionPluginsModal.tsx`.

Suggested behavior (similar shape to `SessionSettingsModal.tsx`):

- Props:
  - `backend: AgentBackend | null`
  - `sessionId: string`
  - `visible: boolean`
  - `onRequestClose: () => void`

- Use the shared hook/controller from `@crystal-lattice/frontend-sdk-react` (created in subtask 030):
  - load plugin list on open
  - toggle switches via controller method
  - reset button calls controller.resetToDefaults()

- Render the list UI using the shared presentational component from `@crystal-lattice/frontend-rn-components`.

- Capability gating:
  - If `!backend` show “No active connection”.
  - If `backend.getCapabilities().sessionPlugins` is false, show “Not supported” message.

### 2) Wire into Chat screen session actions

In `mobile/.../src/SessionChatScreen.tsx`:

- Add state:
  - `const [pluginsVisible, setPluginsVisible] = useState(false);`

- In `handleSessionAction`, add:
  - `if (action === 'plugins') { setPluginsVisible(true); return; }`

- Render `<SessionPluginsModal ... />` similarly to how `SessionSettingsModal` is rendered.

### 3) Wire into Sessions list per-session actions

In `mobile/.../src/SessionsScreen.tsx`:

- Update the built-in actions list to include `plugins`:

```ts
const BUILTIN_SESSION_LIST_ACTIONS: SessionActionKey[] = ['agentSwitch', 'settings', 'plugins'];
```

- Add state to track the active session id for the plugins modal:
  - `pluginsVisible`, `pluginsSessionId`

- Update `handleBuiltinSessionAction` to open the modal:
  - `if (action === 'plugins') { setPluginsSessionId(s.session_id); setPluginsVisible(true); return; }`

### 4) Ensure the action is available

If `SessionActionsBar` uses an `availableActions` allowlist, ensure `plugins` is included where appropriate.
Mobile currently pins actions and merges plugin actions; confirm `plugins` is not filtered out.

## UX notes

- Toggling should feel immediate (optimistic UI is fine) but must reconcile with server results.
- Show “Inactive” indicator (from `active === false`) even if enabled.
- Reset-to-default should confirm (optional) or just do it.

## Done when

- Mobile chat screen can open “Plugins” and toggle plugin enabled state.
- Mobile sessions list can open “Plugins” per session.
- Modal works in manual, discovery, and bridge connection modes (it’s just HTTP paths).
