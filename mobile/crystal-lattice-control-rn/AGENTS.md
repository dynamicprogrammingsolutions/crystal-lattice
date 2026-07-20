# Agent Guidelines – `mobile/crystal-lattice-control-rn`

This app is the **Crystal Lattice Control** React Native client for the AI Agent Platform.
It connects to the Python terminal/HTTP app (and optionally the bridge service) to let
users manage sessions and exchange messages with agents from a phone or simulator.

These guidelines apply to everything under `mobile/crystal-lattice-control-rn/`.

---

## 1. Purpose & High‑Level Architecture

- **Entry point**: `App.tsx`
  - Handles connection method selection (manual IP, Bonjour discovery, bridge).
  - Owns the active SDK `Transport` + `AgentBackend` instances.
  - Creates a `RestAgentBackend` over either `FetchTransport` (direct HTTP) or `BridgeTransport` (Phoenix/WebSocket proxy).
  - On successful connect, renders `src/ConnectedRoot.tsx`.
- **Main navigation**: `src/ConnectedRoot.tsx`
  - Bottom tab navigation with three tabs: `Connection`, `Sessions`, `Messages`.
  - Manages currently selected session ID and which tab is active.
  - Starts on the **Sessions** tab by default after connect.
- **Screens** (`src/`):
  - `ConnectionScreen.tsx`: shows which backend we are connected to, runs `/api/hello` health checks, and exposes a disconnect button.
  - `SessionsScreen.tsx`: lists sessions from `/sessions`, provides filter, reload, and "New Session" actions.
  - `SessionChatScreen.tsx`: shows messages for the active session, lets users append, send, and resend requests.
- **HTTP / API wiring**:
  - Screens call the backend through the SDK `AgentBackend` interface.
  - The concrete implementation used today is `RestAgentBackend` (which maps to the Python server routes).
  - `src/api.ts` is now **types only** (re-exported from `@crystal-lattice/frontend-sdk`) to keep local imports stable.
  - The backend endpoints are implemented in `application/python/agent_terminal_app/server.py`.
  - **Do not change API paths or semantics from this app**; instead, update the backend first if the API needs to evolve.
- **Message rendering**:
  - Implemented in `src/components/MessageBubble.tsx`.
  - Uses `ApiMessage`/`IndexedMessage` shapes from `src/api.ts`.
  - Rendering is split per role (user, system, tool, assistant) with a small dispatcher wrapper.

---

## 2. Message Rendering & UX Rules

**Role‑specific components** (`src/components/MessageBubble.tsx`):

- `UserMessageBubble`
  - Renders `role === 'user'`.
  - Blue background, white monospace text.
  - Keep the layout compact and left‑aligned.
- `SystemMessageBubble`
  - Renders `role === 'system'`.
  - Transparent background with a subtle border; text is monospace, slightly smaller and italic.
  - Intended for system prompts / configuration messages.
- `ToolMessageBubble`
  - Renders `role === 'tool'`.
  - Bordered bubble with a header row `[index] Tool` and a small chevron icon in the top‑right.
  - **Tool result body is collapsible and collapsed by default**.
  - When expanded, the content lives in a height‑limited container (currently ~220px) with an inner `ScrollView` (`nestedScrollEnabled`) so very long payloads scroll without growing the whole page.
  - When collapsed, show a brief text hint (not the full content) so the user knows there is hidden tool output.
- `AssistantMessageBubble`
  - Renders `role === 'assistant'`.
  - Always shows the final answer content directly.
  - If `metadata.reasoning` is present as a string, show a chevron in the header and treat reasoning as a **separate collapsible block**:
    - Collapsed by default with a short hint.
    - Expanded body is height‑limited with its own scroll.

**Common behaviors**:

- Content selection:
  - Prefer `message.metadata.display` when it is an object with `type === 'text'` and non‑empty `content`.
  - Otherwise fall back to `message.content`.
- Fonts & wrapping:
  - Use a fixed‑width font (e.g. `Courier`) for all message text and reasoning.
  - Let React Native wrap text naturally; avoid manual line splitting.
- Scrolling behavior:
  - `SessionChatScreen` owns an inverted outer messages `FlatList`; offset zero is the visual bottom.
  - Compact chevron controls navigate to the visual top and bottom when those edges are outside the pinned threshold.
  - `maintainVisibleContentPosition` handles normal bottom following while the transcript is pinned.
  - Nested scroll areas inside tool/assistant collapsibles must use `nestedScrollEnabled` so they are scrollable inside the messages list.
- When adding new roles or visual variants, prefer **new small renderer components** that plug into the dispatcher, rather than adding more conditionals into existing ones.

If you need guidance on how messages, tool outputs, and reasoning are conceptually structured,
refer to `application/python/agent_terminal_app/event_rendering.py` and the core types in
`core/python/agent_core/types.py`.

---

## 3. Screens, Navigation & State

**App‑level connection flow** (`App.tsx`):

- Connection methods are enumerated as `ConnectionMethod = 'manual' | 'discovery' | 'bridge'`.
- `App.tsx` constructs an SDK `Transport` and an `AgentBackend`:
  - Direct connections: `FetchTransport({ baseUrl })`
  - Bridge connections: `BridgeTransport({ bridgeUrl, serverId, pairingToken })`
  - Backend implementation: `new RestAgentBackend({ transport })`
- `App.tsx` passes the ready `backend` (and `transport` for generic health checks) into `ConnectedRoot`.

**Connected navigation shell** (`src/ConnectedRoot.tsx`):

- Manages three tabs via local state `tab: 'connection' | 'sessions' | 'messages'`.
- Starts on `'sessions'` when `ConnectedRoot` mounts.
- Holds the current `selectedSessionId` in state.
- Renders:
  - `ConnectionScreen` when `tab === 'connection'`.
  - `SessionsScreen` when `tab === 'sessions'`.
  - `SessionChatScreen` when `tab === 'messages' && selectedSessionId != null`.
  - A simple placeholder in the Messages tab when no session is selected.
- `SessionsScreen` receives `onSelectSession` from `ConnectedRoot` and is responsible
  for choosing a session ID; when called, `ConnectedRoot` moves the user to the Messages tab.

**Sessions list** (`src/SessionsScreen.tsx`):

- Uses `apiListSessions`/`apiCreateSession` to talk to the backend.
- Provides `Reload` and `New Session` actions.
- Filtering is done locally by `session_id` or `preview`.
- When a new session is created, it immediately calls `onSelectSession(newId)` so the user
  flows directly into the chat view.

**Session chat** (`src/SessionChatScreen.tsx`):

- Accepts `backend`, `sessionId`, `onBack`.
- Message loading:
  - Uses the shared chat controller with a configurable Python-style history range.
  - Defaults to `-50:` (the last 50 messages), matching desktop.
  - Contextual transcript controls can show older/newer windows, all messages, or return to the last 50; the settings modal remains available for arbitrary ranges.
- Message composer:
  - `Append` appends a user message only.
  - `Send` optionally appends a user message, then calls `/send`, then reloads messages.
  - `Resend` calls `/send` without appending.
- Settings:
  - Gear icon opens a modal for the "show last N messages" limit.
  - Ensure UX remains simple and modal stays small and phone‑friendly.
- Scrolling:
  - Owns an inverted `FlatList` ref and persists bottom-gap affinity.
  - Visual-bottom navigation maps to offset zero; visual-top navigation maps to the inverted list end.
  - This must continue working when message rendering changes.

When adding new screens, prefer placing them under `src/` and wiring them through
`ConnectedRoot` rather than coupling them to `App.tsx` directly.

---

## 4. Styling & Code Conventions

- **Language & framework**:
  - Use TypeScript for new files; React 19 + React Native 0.82 APIs.
  - Prefer function components with React hooks. Avoid class components.
- **File layout**:
  - Place feature screens and helpers under `src/`.
  - Shared UI pieces go under `src/components/`.
  - Keep files small and focused; if a screen grows too large, extract visual subcomponents.
- **Styling**:
  - Use `StyleSheet.create` and avoid inline styles except for trivial one‑off tweaks.
  - Reuse existing color palette where possible (notably `#007AFF`, `#E5E5EA`, greys).
  - Maintain a clean, iOS‑inspired aesthetic (subtle borders, rounded corners, light greys).
- **Icons**:
  - Use `react-native-vector-icons/Feather` (already wired into both platforms).
  - Keep icon metaphors simple and consistent (e.g. `refresh-ccw` for reload, `repeat` for resend, `settings` for config).
- **Patterns to follow**:
  - Treat screen components as pure as possible: inputs via props, side‑effects via `useEffect`.
  - Use `useCallback` and `useMemo` only when needed for clarity or to control dependencies.
  - Keep business logic (HTTP calls, data shaping) in `src/api.ts` or small helpers, not inside JSX.
- **Patterns to avoid**:
  - Do not introduce global mutable singletons for app state.
  - Do not mix backend concerns (e.g. rewriting FastAPI routes) into this app.
  - Do not add new lint/format tooling; rely on existing ESLint and Prettier.

These conventions build on the root‑level `AGENTS.md` rules: no one‑letter variable names,
avoid inline comments unless explicitly requested, keep changes small and focused.

---

## 5. Running, Debugging & Testing

**Install dependencies** (from `mobile/crystal-lattice-control-rn/`):

```bash
npm install   # or: npm ci
```

**Start Metro bundler**:

```bash
npm run start
```

**Run on iOS simulator**:

```bash
npm run ios
```

**Run on Android emulator or device**:

```bash
npm run android
```

Make sure the Python terminal/HTTP app is running and reachable from the device/emulator.
For bridge mode, ensure the Elixir bridge is up and reachable at the WebSocket URL you enter.

**Testing**:

- Use the existing Jest setup (`npm test`).
- Prefer **component‑level tests** for new screens/components using `react-test-renderer`.
- Test UI states that involve network errors by mocking `AgentBackend` (and/or a `Transport` passed into `RestAgentBackend`).
- For backend-facing behavior, add a real-backend component integration using
  the shared backend harness, public HTTP routes, `RestAgentBackend`, and actual
  plugins where plugin contributions are part of the behavior.
- Detox harnesses must render production screens/components with deterministic
  state rather than duplicate the tested interaction in test-only UI. Wire new
  harnesses through each platform's launch path and run the scenario on both
  iOS and Android when both are supported.
- Use stable production test identifiers based on entity or action IDs; avoid
  relying only on visible text, row position, or generated menu order.
- Do not add new test frameworks; extend the current Jest configuration in `jest.config.js`.

When you make a behavior change that affects message rendering, session loading, or
connection flows, strongly consider adding or updating tests under `__tests__/`.

---

## 6. Platform Notes

- **Android**:
  - App ID / namespace: `com.dynamicprogrammingsolutions.crystallatticecontrolrn`.
  - `react-native-vector-icons` is already integrated via Gradle.
  - Do not change the application ID or namespace unless explicitly requested.
- **iOS**:
  - Xcode project/workspace name: `CrystalLatticeControlRN`.
  - Bundle identifier: `com.dynamicprogrammingsolutions.crystallatticecontrolrn`.
  - Icon fonts from `react-native-vector-icons` are registered in `Info.plist`.
  - If you modify native iOS files, keep Obj‑C/Swift code minimal and align with Xcode’s
    current project structure.

If something looks inconsistent (e.g., app name, bundle ID, or package name), treat that
as **out of scope to change** unless the user specifically asks you to address it.

---

## 7. When in Doubt

- Keep changes **small, focused, and in line with the existing UI**.
- Respect the separation of concerns:
  - `App.tsx` handles connection and adapter lifecycle.
  - `src/ConnectedRoot.tsx` handles navigation and high‑level layout.
  - Individual screens handle just their own local state and rendering.
  - `src/api.ts` and the Python backend define the HTTP/JSON contract.
- If a requested change seems to require modifying backend behavior, call that out clearly
  in your final message and avoid guessing protocol changes from the mobile side.
