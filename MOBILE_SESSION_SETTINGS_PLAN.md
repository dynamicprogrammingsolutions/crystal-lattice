## Mobile Session Settings Plan (/set Parity)

This plan describes how to extend the RN mobile app and the Python
server so that the mobile UI can edit per-session configuration
overrides using the same primitives as the terminal `/set` command.

The work is split into testable chunks, with explicit notes on where to
add tests and which files to touch.

---

## 1. Context & Goals

- Reuse the existing plugin-driven UI schema and per-session overrides
  mechanism currently surfaced only via the terminal `/set` command.
- Expose configuration metadata and overrides over HTTP so the React
  Native app can:
  - List configurable settings for a session.
  - Read and write per-session config overrides.
  - Have those overrides respected by `/send` and any other
    config-sensitive operations.
- Add a "Settings" action in the mobile session actions bar that opens
  a dedicated settings dialog, implemented as a **separate component**
  from `SessionChatScreen`.

Non-goals for the first iteration:

- Type-coercion beyond the existing `/set` semantics
  (i.e. strings for non-boolean values are acceptable initially).
- A full application-level config UI (we only need per-session for now).

---

## 2. Files To Read Before Implementation

### 2.1. Core & terminal behaviour

- `core/python/agent_core/core.py:1690-1760`
  - `AgentCore.get_config_schema()`
  - `AgentCore.get_ui_schema()`
- `core/python/plugins/openrouter_reasoning_extension.py`
  - Example of config schema + UI elements (`enable_reasoning`,
    `reasoning_effort`).
- `core/python/plugins/web_context_feature.py`
  - Another example of config + UI elements (including `options` and
    `condition`).

- `application/python/agent_terminal_app/terminal_app.py`
  - `fork_session`, `delete_messages`, `modify_message`,
    `list_plugins_for_session`, `get_feature_completions` – all show
    how per-session overrides are merged via
    `resolve_request_config(base_config, overrides)`.
  - `session_ui_elements()` – how UI elements for `/set` are filtered
    from `core.get_ui_schema()`.
  - `get_application_config_schema()` – used for application-level
    config (for reference only in this feature).
  - `update_override()` – how terminal `/set` persists overrides into
    `session.metadata["overrides"]`.

- `application/python/agent_terminal_app/terminal.py`
  - `/help config` section – how configurable settings are displayed,
    combining config schema, UI elements, and overrides.
  - `/set` implementation – how values are parsed, normalized for
    selects/booleans, and saved via `update_override`.

### 2.2. HTTP server & tests

- `application/python/agent_terminal_app/server.py`
  - Existing session and message endpoints.
  - `send_request` route and `_run_send_request_background` helper.
  - Existing uses of `resolve_request_config` and
    `metadata["overrides"]` in `update_message`, `delete_messages`,
    and `fork_session`.

- `application/python/agent_terminal_app/server_endpoints_parity.md`
  - "Per-session configuration (/set parity)" section – the intended
    HTTP endpoints for config schema, UI elements, and overrides.

- `application/python/tests/test_agent_terminal_app_server.py`
  - Style for testing server behaviour directly by importing route
    functions and injecting a custom `AgentApplication` instance.
  - Existing tests already cover `/send` and
    `_run_send_request_background` at a high level.

### 2.3. Mobile RN app

- `mobile/crystal-lattice-control-rn/AGENTS.md`
  - High-level architecture, styling, and component organisation
    guidelines.

- `mobile/crystal-lattice-control-rn/src/api.ts`
  - Existing HTTP helpers (`apiListSessions`, `apiListMessages`,
    `apiAppendMessage`, `apiSend`, `apiListAgents`, etc.).
  - Pattern for building query strings and using `ConnectionAdapter`.

- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`
  - Main session chat screen, including message loading, send/append,
    and session actions handling.

- `mobile/crystal-lattice-control-rn/src/sessionActions.ts`
  - Definition of `SessionActionKey` and `SESSION_ACTIONS`, including
    the session actions bar entries.

- `mobile/crystal-lattice-control-rn/src/components/SessionActionsBar.tsx`
  - Rendering of the session actions row and the triple-dot ("more")
    menu.

---

## 3. Implementation Steps (Server)

### 3.1. Add per-session UI elements endpoint

**Goal:** Implement `GET /sessions/{session_id}/ui-elements` to expose
config UI elements (same as terminal `/set`).

**Code changes**

- In `application/python/agent_terminal_app/server.py`:
  1. Add a new route function:

     ```python
     @app.get("/sessions/{session_id}/ui-elements")
     def get_session_ui_elements(
         session_id: str,
         app_instance: AgentApplication = Depends(get_agent_app),
     ) -> Dict[str, Any]:
         # Acquire lock and load session/core
         # Call core.get_ui_schema()
         # Filter config elements using the same predicate as
         # TerminalApplication.session_ui_elements.
         # Return {"elements": filtered_list}.
     ```

  2. Implement an `_is_config_element` helper (or inline pattern
     matching) equivalent to `TerminalApplication.session_ui_elements`:

     - Include elements where:

       ```python
       case {"ui_type": "config", "key": str(key)} if key:
       case {"key": str(key)} if key and "ui_type" not in el:
       ```

     - Ensure only `dict` elements are considered; ignore anything
       malformed.

**Tests**

- In `application/python/tests/test_agent_terminal_app_server.py`:

  - Add `test_get_session_ui_elements_returns_config_elements`:
    - Use `config_openrouter_app_layer.json` with an `AgentApplication`.
    - Create a session via `create_session`.
    - Call the new `get_session_ui_elements` route with
      `app_instance=app`.
    - Assert:
      - Response is a dict with key `"elements"` pointing to a list.
      - At least one element with `key == "enable_reasoning"` and
        `type == "checkbox"`.
      - At least one element with `key == "reasoning_effort"` and
        `type == "select"` and `options` present.
      - No elements with `ui_type == "message_footer"` or
        `ui_type == "status_bar"` appear in the result.

### 3.2. Add per-session overrides endpoints

**Goal:** Implement HTTP CRUD for `session.metadata["overrides"]`.

**Code changes**

- In `server.py`, add:

  1. `GET /sessions/{session_id}/overrides`:

     ```python
     @app.get("/sessions/{session_id}/overrides")
     def get_session_overrides(
         session_id: str,
         app_instance: AgentApplication = Depends(get_agent_app),
     ) -> Dict[str, Any]:
         with app_instance.acquire_session_lock(session_id):
             ctx = app_instance.load_session(session_id)
             if ctx is None:
                 raise HTTPException(status_code=404, detail=...)
             _core, _base_config, session = ctx
             metadata = session.metadata if isinstance(session.metadata, dict) else {}
             raw = metadata.get("overrides")
             overrides = raw if isinstance(raw, dict) else {}
         return {"overrides": overrides}
     ```

  2. `PATCH /sessions/{session_id}/overrides`:

     - Accept body in two shapes (one must be present):
       - `{ "key": str, "value": Any }`
       - `{ "values": { "k": v, ... } }`
     - Validate shape and convert to `updates: Dict[str, Any]`.
     - Under `acquire_session_lock`:
       - Load session, 404 if missing.
       - Read existing `metadata` and `overrides`.
       - `new_overrides = {**overrides, **updates}`.
       - `new_metadata = {**metadata, "overrides": new_overrides}`.
       - Construct new `Session(session_id=session.session_id,
         messages=session.messages, metadata=new_metadata)`.
       - `app_instance.save_session(new_session)`.
     - Return `{ "session": new_session.to_dict() }`.

**Tests**

- In `test_agent_terminal_app_server.py` add:

  1. `test_session_overrides_get_and_patch_round_trip`:
     - Create session.
     - `get_session_overrides` → `{ "overrides": {} }`.
     - `patch_session_overrides` with `{ "key": "reasoning_effort", "value": "high" }`.
     - `get_session_overrides` again → map contains
       `"reasoning_effort": "high"`.
     - Verify via `app.load_session(session_id)` that
       `session.metadata["overrides"]["reasoning_effort"] == "high"`.

  2. `test_session_overrides_patch_bulk_merges_with_existing`:
     - First PATCH `{ "values": {"enable_reasoning": True} }`.
     - Then PATCH `{ "values": {"reasoning_effort": "medium"} }`.
     - GET → overrides contains both keys with updated values.

### 3.3. Ensure send_request honours session overrides

**Goal:** `_run_send_request_background` should merge persistent
per-session overrides with per-request `config_overrides` from HTTP.

**Code changes**

- In `_run_send_request_background(app_instance, session_id, overrides)`:

  - Today it calls:

    ```python
    for ev in app_instance.send_request(core, session, base_config, overrides, stream=True):
        ...
    ```

  - Change to:

    ```python
    metadata = session.metadata if isinstance(session.metadata, dict) else {}
    stored_val = metadata.get("overrides")
    stored_overrides: Dict[str, Any] = (
        stored_val if isinstance(stored_val, dict) else {}
    )
    http_overrides = overrides if isinstance(overrides, dict) else {}
    merged_overrides = {**stored_overrides, **http_overrides}

    for ev in app_instance.send_request(
        core,
        session,
        base_config,
        merged_overrides,
        stream=True,
    ):
        ...
    ```

**Tests**

- In `test_agent_terminal_app_server.py` add a focused test that
  inspects what overrides are passed into `AgentApplication.send_request`:

  - `test_run_send_request_background_merges_session_and_http_overrides`:
    - Use `config_echo_app.json` with `AgentApplication` + `InMemoryEventStore`.
    - Create session and then manually attach metadata overrides:
      `{"overrides": {"foo": "session", "both": "session"}}`.
    - Monkeypatch `app.send_request` with a stub capturing the
      `overrides` argument and returning an empty list.
    - Call `_run_send_request_background(app, session_id,
      {"bar": "http", "both": "http"})`.
    - Assert the captured `overrides` equals:
      `{"foo": "session", "both": "http", "bar": "http"}`.

  - `test_run_send_request_background_uses_session_overrides_without_http`:
    - Similar setup, but call `_run_send_request_background(app, session_id, {})`.
    - Assert `overrides == {"foo": "session", "both": "session"}`.

**3.4. Audit other config usages**

Run a quick audit over `terminal_app.py` and `server.py`:

- Confirm that all operations that derive a config for core helpers
  (`slice_session`, `fork_session`, `modify_message`,
  `get_plugins_for_config`, `get_completions`) already go through
  `resolve_request_config(base_config, overrides)` with overrides
  derived from `session.metadata["overrides"]`.
- Do **not** change append-only paths (`add_message` /
  `append_user_message`), which intentionally use the base config
  without overrides, for consistency with existing terminal behaviour.

---

## 4. Implementation Steps (React Native App)

### 4.1. Extend mobile API helpers

**Goal:** Add thin wrappers around the new HTTP endpoints.

**Code changes**

- In `mobile/crystal-lattice-control-rn/src/api.ts`:

  1. Define types:

     ```ts
     export interface UiConfigElement {
       ui_type?: string;
       type?: string;
       key: string;
       label?: string;
       description?: string;
       plugin?: string;
       options?: any;
       [k: string]: any;
     }

     export interface UiElementsResponse {
       elements: UiConfigElement[];
     }

     export interface SessionOverridesResponse {
       overrides: Record<string, any>;
     }
     ```

  2. Add `apiGetSessionUiElements`:

     ```ts
     export async function apiGetSessionUiElements(
       adapter: ConnectionAdapter,
       sessionId: string,
     ): Promise<UiConfigElement[]> {
       const path = `/sessions/${encodeURIComponent(sessionId)}/ui-elements`;
       const data = (await adapter.get(path)) as UiElementsResponse | UiConfigElement[];
       const elements = Array.isArray((data as any).elements)
         ? (data as UiElementsResponse).elements
         : (data as UiConfigElement[]);
       return Array.isArray(elements) ? elements : [];
     }
     ```

  3. Add `apiGetSessionOverrides`:

     ```ts
     export async function apiGetSessionOverrides(
       adapter: ConnectionAdapter,
       sessionId: string,
     ): Promise<Record<string, any>> {
       const path = `/sessions/${encodeURIComponent(sessionId)}/overrides`;
       const data = (await adapter.get(path)) as SessionOverridesResponse;
       if (data && data.overrides && typeof data.overrides === 'object') {
         return data.overrides;
       }
       return {};
     }
     ```

  4. Add `apiPatchSessionOverrides`:

     ```ts
     export async function apiPatchSessionOverrides(
       adapter: ConnectionAdapter,
       sessionId: string,
       values: Record<string, any>,
     ): Promise<void> {
       const path = `/sessions/${encodeURIComponent(sessionId)}/overrides`;
       await adapter.patch(path, { values });
     }
     ```

### 4.2. Add a dedicated SessionSettingsModal component

**Goal:** Encapsulate all settings-related state and logic in a
stand-alone component, keeping `SessionChatScreen` lean.

**Code changes**

- Create `mobile/crystal-lattice-control-rn/src/components/SessionSettingsModal.tsx`.

  - Props:

    ```ts
    interface SessionSettingsModalProps {
      adapter: ConnectionAdapter | null;
      sessionId: string;
      visible: boolean;
      onRequestClose: () => void;
    }
    ```

  - Internal state:
    - `loading`, `saving`, `error`.
    - `elements: UiConfigElement[]`.
    - `overrides: Record<string, any>`.
    - Optional `pendingTextByKey: Record<string, string>` for text
      inputs.

  - Effects:
    - `useEffect` that triggers when `visible` switches from `false`
      → `true`:
      - If `adapter` is null, set error and skip network calls.
      - Otherwise, fetch `elements` and `overrides` via the new API
        helpers in parallel.

  - Rendering:
    - Use `Modal` styled similarly to existing modals in the app
      (agent switch, delete range, etc.).
    - Header: "Session settings".
    - Body states:
      - Loading: spinner + text.
      - Error: show error message + Close button.
      - No elements: text "No configurable settings for this session.".
      - Otherwise, `ScrollView` of setting rows.

    - For each `UiConfigElement el`:
      - Compute `effectiveValue` as `overrides[el.key]` (for V1 we
        ignore base-config defaults for display).
      - Render label (`el.label` or key) and optional description
        (`el.description`).
      - Control by `el.type`:
        - `checkbox`:
          - Use `Switch` component.
          - `value = Boolean(effectiveValue ?? false)`.
          - `onValueChange`:
            - Optimistically update `overrides` in state.
            - Call `apiPatchSessionOverrides(adapter, sessionId,
              { [el.key]: next })`.
            - On error, revert value and show `Alert`.
        - `select`:
          - Normalize `options` into `{ value, label }[]`.
          - Render them as pill buttons or vertical list; highlight
            the selected option (`value === effectiveValue`).
          - On tap, update local overrides and call
            `apiPatchSessionOverrides` as above.
        - Other types (`string`, `text`, or missing `type`):
          - Render `TextInput` with a small inline "Save" button.
          - On Save, call `apiPatchSessionOverrides(adapter, sessionId,
            { [el.key]: text })`.

    - Footer: Close button → `onRequestClose()`.

**Tests (optional, Jest)**

- Add a small Jest test file for `SessionSettingsModal` that:
  - Mocks `adapter.get`/`patch`.
  - Renders the modal with `visible={true}` and a simple element list
    (one checkbox, one select).
  - Verifies that tapping a control results in the expected
    `patch` call.

### 4.3. Add a "settings" action to the session actions bar

**Goal:** Expose the settings modal via the existing triple-dot
"session actions" menu, with optional pinning.

**Code changes**

- In `src/sessionActions.ts`:

  1. Extend `SessionActionKey`:

     ```ts
     export type SessionActionKey =
       | 'reload'
       | 'resend'
       | 'messageLimit'
       | 'copy'
       | 'deleteRange'
       | 'agentSwitch'
       | 'debugEvents'
       | 'settings';
     ```

  2. Add `settings` to `SESSION_ACTIONS`:

     ```ts
     settings: {
       key: 'settings',
       label: 'Settings',
       iconName: 'settings',
       defaultPinned: false,
     },
     ```

- In `src/SessionChatScreen.tsx`:

  1. Add a small piece of state:

     ```ts
     const [settingsVisible, setSettingsVisible] = useState(false);
     ```

  2. Extend `handleSessionAction` to handle the new key:

     ```ts
     if (action === 'settings') {
       setSettingsVisible(true);
       return;
     }
     ```

  3. Render the new modal near existing modals:

     ```tsx
     <SessionSettingsModal
       adapter={adapter}
       sessionId={sessionId}
       visible={settingsVisible}
       onRequestClose={() => setSettingsVisible(false)}
     />
     ```

  4. No additional state for settings should be introduced into
     `SessionChatScreen`; the modal component owns its internal data
     and network calls.

---

## 5. Validation Checklist

- **Server**
  - New endpoints compile and are covered by unit tests.
  - `_run_send_request_background` tests prove that:
    - Session metadata overrides are merged into every send.
    - HTTP `config_overrides` take precedence over stored overrides.
  - Existing server tests still pass (no regression to other
    endpoints).

- **Terminal**
  - `/set` and `/help config` behaviour unchanged.
  - Per-session overrides set via terminal are respected by HTTP
    `/send` after the change (implicitly validated by merging logic).

- **Mobile RN app**
  - Session settings modal appears when the "Settings" session action
    is tapped.
  - For a server with OpenRouter reasoning/web-context plugins
    enabled, the modal shows the corresponding settings.
  - Toggling a checkbox or changing a select option results in a
    PATCH to `/sessions/{session_id}/overrides` and subsequent sends
    behave as expected.
  - `SessionChatScreen` remains focused on chat, with settings state
    encapsulated in `SessionSettingsModal`.
