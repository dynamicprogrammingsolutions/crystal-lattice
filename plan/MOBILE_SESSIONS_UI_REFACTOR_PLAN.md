# Mobile Sessions & Messages Refactor Plan

This document describes follow‑up refactors for the mobile app
(`mobile/crystal-lattice-control-rn`) around the Sessions and
SessionChat screens. It is intended to be self‑contained so it can be
used later without referring back to conversation history.

The current code already includes:

- Shared application‑plugin loading (`useApplicationPlugins`).
- Shared application action execution (`executeApplicationAction`).
- Shared pinned‑actions persistence (`usePersistentPinnedActions`).
- Shared plugin dialog orchestration (`usePluginActionDialog`).
- Shared agent list loading (`useSessionAgents`).

The refactors below focus on **screen structure and separation of
concerns** beyond those shared hooks.

---

## Goals

- Reduce the amount of state and logic in individual screens
  (`SessionsScreen.tsx`, `SessionChatScreen.tsx`).
- Improve separation between **data/behavior** and **presentation** by
  extracting reusable hooks and components.
- Eliminate obvious duplication between Sessions and Messages screens
  that is not already handled by the shared plugin/agent hooks.
- Keep behavior unchanged; this is a structural/refactoring effort.

---

## Phase 1 – Sessions list data hook

**Objective:** Move sessions data loading, auto‑reload logic, and cache
sync out of `SessionsScreen.tsx` into a dedicated hook.

### Current pain points

- `SessionsScreen.tsx` manages:
  - `sessions` state that mirrors `cachedSessions` props.
  - `loading` and `error` state for `/sessions`.
  - Auto‑reload based on `isActive`, `adapter`, and `lastLoadedAt`.
  - Local `hasAutoLoaded` flag.
- All of this is mixed with UI code, plugin actions, and modal
  handling.

### Planned hook: `useSessionsListData`

**Location:** `mobile/crystal-lattice-control-rn/src/useSessionsListData.ts`

**Signature (proposed):**

```ts
interface UseSessionsListDataArgs {
  adapter: ConnectionAdapter | null;
  isActive: boolean;
  cachedSessions: SessionSummary[] | null;
  lastLoadedAt: number | null;
  onUpdateCache: (sessions: SessionSummary[]) => void;
}

interface UseSessionsListDataResult {
  sessions: SessionSummary[];
  loading: boolean;
  error: string | null;
  loadSessions: () => Promise<void>;
}
```

**Behavior:**

- Owns `sessions`, `loading`, and `error` state.
- On mount and when `cachedSessions` changes:
  - If `cachedSessions` is non‑null, uses it to initialize `sessions`
    and clears `error`.
  - If `adapter` becomes null, clears `sessions` and leaves `error` as
    is.
- Provides `loadSessions` that:
  - Validates `adapter`.
  - Calls `apiListSessions(adapter)`.
  - Updates `sessions` and calls `onUpdateCache`.
  - Sets `loading`/`error` appropriately.
- Handles auto‑reload:
  - When `isActive && adapter` is true, compares `Date.now()` to
    `lastLoadedAt`.
  - If there is no timestamp or the cache is older than a threshold
    (e.g. 30 seconds), calls `loadSessions()`.
  - Keeps the current `hasAutoLoaded` behavior to avoid constant
    reloads but encapsulates it inside the hook.

**Call site changes:**

- `SessionsScreen.tsx` will:
  - Replace local `sessions`, `loading`, `error`, `hasAutoLoaded`, and
    `loadSessions` with this hook.
  - Keep only UI and plugin/modal logic.

---

## Phase 2 – SessionsScreen structure split

**Objective:** Extract presentational components from
`SessionsScreen.tsx` so the main screen file focuses on wiring hooks and
event handlers.

### 2.1 `SessionListItem` component

**Location:** `mobile/crystal-lattice-control-rn/src/components/SessionListItem.tsx`

**Responsibilities:**

- Render a single session row:
  - Title (from `preview` or derived from `session_id`).
  - Session id.
  - Optional preview text.
  - Updated/modified timestamp.
  - Per‑row `SessionActionsBar` for builtin + plugin list actions.

**Props (proposed):**

```ts
interface SessionListItemProps {
  session: SessionSummary;
  onSelectSession: (sessionId: string) => void;
  builtinActions: SessionActionKey[]; // e.g. ['resend', 'agentSwitch', 'settings']
  pluginSessionActionDefs: SessionActionDefinition[];
  pinnedActions: SessionActionKey[];
  onChangePinnedActions: (pinned: SessionActionKey[]) => void;
  onBuiltinAction: (action: SessionActionKey, session: SessionSummary) => void;
  onPluginElement: (element: ActionUiElement, session: SessionSummary) => void;
}
```

**Notes:**

- The component will not know about `useApplicationPlugins` or
  `executeApplicationAction`; it only receives `ActionUiElement` via
  `onPluginElement` and builtin keys via `onBuiltinAction`.
- `SessionActionsBar` stays as the shared visual control and continues
  to accept both builtin and plugin `SessionActionDefinition`s.

### 2.2 Sessions header / toolbar

**Location:** `mobile/crystal-lattice-control-rn/src/components/SessionsHeader.tsx`

**Responsibilities:**

- Render the top part of `SessionsScreen`:
  - Reload button.
  - New Session button.
  - Filter input.

**Props (proposed):**

```ts
interface SessionsHeaderProps {
  filterText: string;
  onChangeFilterText: (value: string) => void;
  onReload: () => void;
  onNewSession: () => void;
}
```

**Notes:**

- This split keeps layout logic and styling in a small component while
  `SessionsScreen` only passes in handlers and filter string from
  state.

---

## Phase 3 – Agent picker & switch components

**Objective:** Consolidate agent selection UI into reusable components
to avoid duplicated modal layout across screens.

### 3.1 `AgentPickerModal`

**Location:** `mobile/crystal-lattice-control-rn/src/components/AgentPickerModal.tsx`

**Responsibilities:**

- Present a modal listing available agents with optional loading state.
- Used for "New session" flow (select agent to create session).

**Props (proposed):**

```ts
interface AgentPickerModalProps {
  visible: boolean;
  loading: boolean;
  agents: string[];
  title: string;        // e.g. "New session"
  subtitle?: string;    // optional descriptive text
  onRequestClose: () => void;
  onSelectAgent: (agentId: string | null) => void; // null for default
}
```

**Usage:**

- `SessionsScreen`:
  - Uses `AgentPickerModal` for the "New Session" flow.
  - Passes `agents` from `useSessionAgents` and `loading` from the same
    hook.

### 3.2 `AgentSwitchModal`

**Location:** `mobile/crystal-lattice-control-rn/src/components/AgentSwitchModal.tsx`

**Responsibilities:**

- Present a modal that lets users switch the agent for an existing
  session.
- Shows current agent and highlights the selected one.

**Props (proposed):**

```ts
interface AgentSwitchModalProps {
  visible: boolean;
  loading: boolean;
  agents: string[];
  currentAgentId: string | null;
  title: string;              // usually "Switch agent"
  onRequestClose: () => void;
  onSelectAgent: (agentId: string) => void;
}
```

**Usage:**

- `SessionChatScreen`:
  - Replaces the inline "Switch agent" modal.
  - Uses `ensureAgentsLoaded` + `apiGetSessionAgent` to populate current
    agent.
  - Uses `onSelectAgent` to call `apiSwitchSessionAgent`.
- `SessionsScreen`:
  - Replaces the row‑level "Switch agent" modal in the sessions list.
  - Also uses `ensureAgentsLoaded` and `apiGetSessionAgent` for the
    target session.

---

## Phase 4 – Session UI schema helpers

**Objective:** Extract UI‑schema handling for message footer/status bar
out of `SessionChatScreen.tsx` into reusable utilities/hooks.

### Current situation

- `SessionChatScreen.tsx` currently:
  - Calls `apiGetSessionUiSchema(adapter, sessionId)` and stores
    `uiSchemaElements` in local state.
  - Uses inline `useMemo` logic to derive:
    - `footerElements` (message footers).
    - `statusBarElements` (status bar definitions).
  - Computes `statusBarParts` from the last assistant message and the
    `statusBarElements` using `extractByPath` and `renderTemplate`.
- This blends configuration parsing with screen behavior.

### Planned helpers

1. **`useSessionUiSchema` hook** (`src/useSessionUiSchema.ts`)

   - Inputs:
     - `adapter: ConnectionAdapter | null`
     - `sessionId: string`
   - Behavior:
     - Fetches session UI schema via `apiGetSessionUiSchema`.
     - Stores `elements: UiSchemaElement[]` plus optional `loading` and
       `error` states.
   - Returns:
     - `{ elements, loading, error }`.

2. **Extend `uiSchemaUtils.ts`** to encapsulate the filtering logic:

   - We already have `extractByPath`, `renderTemplate`,
     `filterFooterElements`, `filterStatusBarElements`.
   - Ensure `SessionChatScreen.tsx` uses these helpers directly instead
     of custom inline filters.

3. **Status bar helper** (optional small function):

   - A pure helper that builds `statusBarParts` given:
     - `elements: UiSchemaElement[]`.
     - `sessionId` and `sessionAgentId`.
     - `lastAssistantMessage`.
   - Returns `string[]` to render.

**Call site changes:**

- `SessionChatScreen.tsx`:
  - Replaces in‑screen `uiSchemaElements` effect with `useSessionUiSchema`.
  - Uses `filterFooterElements` and `filterStatusBarElements` instead of
    inline filters.
  - Optionally uses the status‑bar helper to compute `statusBarParts`.

---

## Phase 5 – Message actions pinned‑state reuse (optional)

**Objective:** Consider reusing `usePersistentPinnedActions` for
message‑action pinning per role, similar to session‑action pinning.

### Current behavior

- `SessionChatScreen.tsx` maintains
  `pinnedMessageActionsByRole: Record<string, MessageActionKey[]>` and
  persists it manually via AsyncStorage under
  `STORAGE_KEY_MESSAGE_ACTIONS`.
- The shape is slightly more complex (by role), so the existing
  simple hook does not directly fit.

### Possible refactor

- Add a variant hook, e.g. `usePersistentPinnedActionsByKey`, that:
  - Takes a `storageKey` and an optional function to validate/normalize
    the parsed value.
  - Returns a generic `Record<string, string[]>` and a setter.
- Alternatively, keep the current custom logic since the complexity
  (per‑role map) is small and localized.

This phase is optional; the benefits are modest compared to earlier
phases.

---

## Phase 6 – Testing & rollout

**Objective:** Ensure that each refactor preserves existing behavior.

### General approach

- Apply changes incrementally per phase, running the app and existing
  Jest tests after each step.
- For hooks (`useSessionsListData`, `useSessionUiSchema`, etc.), prefer
  small integration tests via shallow rendering of the consuming
  screens, rather than over‑mocking.

### Specific checks

1. **Sessions data hook & structure split**
   - Verify that:
     - The sessions list still auto‑loads when the Sessions tab becomes
       active.
     - Cache behavior via `ConnectedRoot` stays the same (switching
       connections returns to cached lists without new network calls
       until staleness threshold).
     - Error handling (`Alert.alert('Error', ...)`) still fires under
       the same conditions.

2. **Agent components**
   - Ensure "New Session" and both agent switch flows (in messages and
     sessions list) behave identically to current behavior.

3. **UI schema helpers**
   - Confirm that message footers and the status bar continue to render
     identically for sessions with UI schema configured.

4. **Pinned actions**
   - Ensure session‑header and session‑list pinned actions are still
     persisted across app restarts and that plugin actions can still be
     pinned alongside builtin ones.

Once all phases are complete, consider a small cleanup pass to remove
any now‑unused state or helpers left in the screens and to align naming
across hooks and components.
