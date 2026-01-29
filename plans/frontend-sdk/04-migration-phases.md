# Migration phases

This is an incremental plan that keeps the current mobile app working while extracting code into `@crystal-lattice/frontend-sdk`.

## Phase 0: Monorepo layout (no behavior change)

- Add a JS monorepo structure at repo root (recommended: `pnpm` or `npm workspaces`).
- Create packages:
  - `packages/frontend-sdk/` (`@crystal-lattice/frontend-sdk`)
  - `packages/frontend-sdk-react/` (`@crystal-lattice/frontend-sdk-react`, optional)
- Configure TS project references so frontends can import from the SDK.

Suggested layout:

```
packages/
  frontend-sdk/
    src/
  frontend-sdk-react/
    src/
mobile/
  crystal-lattice-control-rn/
desktop/
  crystal-lattice-control-desktop-rn/
```

## Phase 1: Extract pure TS helpers + types

Move (or copy then rewire) into `frontend-sdk`:

- Domain types: messages/events/ui schema
- `extractByPath`, `renderTemplate`, footer/status filters
- `selectDisplayContent`

Update the mobile app to import these from the SDK.

Success criteria:

- Mobile app compiles and behaves the same.
- SDK has zero React/React Native dependencies.

## Phase 2: Extract REST client and backend interface

1) Introduce `AgentBackend` interface (SDK-owned).

2) Implement:

- `RestAgentBackend` using the existing HTTP routes.

3) Update the mobile app:

- Replace direct use of `src/api.ts` with `backend.*` calls.
- Keep existing UI and caching.

Success criteria:

- Mobile app no longer imports `src/api.ts`.
- All backend calls go through `AgentBackend`.

## Phase 3: Extract Bridge transport (Phoenix protocol)

Move the logic currently in `App.tsx`’s `BridgeAdapter` into SDK:

- `BridgeTransport` (WebSocket)
- `BridgeAgentBackend` or `BridgeTransport + RestAgentBackend` composition

Design note:

- The bridge protocol is fundamentally “proxy HTTP requests”, so the cleanest design is:
  - `BridgeTransport` implements `Transport`.
  - `RestAgentBackend` uses `Transport`.

Success criteria:

- Mobile bridge mode works with SDK backend.
- Transport interface works in RN and Node runtimes.

## Phase 4: Extract headless controllers

This is the major “logic/UI separation” milestone.

### 4.1 Chat controller

- Create `ChatController` in SDK.
- Port logic from `src/SessionChatScreen.tsx`:
  - Message range parsing
  - Load/append/send/resend/cancel/modify/delete
  - Poll events and apply `partial/final/tool_results` updates
  - Track `activeRequestId`, `cursorEventId`, and `error` state

Additional extraction targets to make screens representation-only:

- **UI schema loading**: move per-session schema loading (`getSessionUiSchema`) into a headless controller.
- **Chat view-model helpers**: move status bar/footer derivation (template + `extractByPath`) into SDK pure helpers.
- **Action semantics**: move “interpret plugin action result and decide reload/navigate” into SDK as an `effects`-returning helper.
- **Cache hydration helper**: provide a reusable hook/helper so screens don’t duplicate "hydrate cached props into controller" boilerplate.
- **Agents list controller**: move listAgents caching/loading out of screens.
- **Dialog helper**: move the small “auto-run vs open dialog” decision out of screens (reusable hook/controller).

The RN screen becomes mostly:

- subscribe to controller state
- render
- call controller actions

### 4.2 Sessions controller

- Create `SessionsController` in SDK.
- Port logic from `src/SessionsScreen.tsx`:
  - reload/staleness
  - create session (choose default agent)
  - derive title/subtitle/meta from UI schema fields

Additional extraction targets to make screens representation-only:

- **Staleness policy**: move "load if stale" decision into the controller (based on controller state), not the screen.
- **Session list presentation derivation**: move `deriveTitle/deriveSubtitle/deriveMeta` into SDK helpers.
- **Action semantics**: move “interpret plugin action result and decide reload/navigate” into SDK as `effects`.
- **Cache hydration helper**: same as chat; avoid repeated hydration logic in screens.

### 4.3 Plugins registry

- Create `PluginsRegistry` in SDK.
- Port logic from `src/ApplicationPluginsContext.tsx`.
- Remove React Context usage from the core; provide a React hook wrapper in `frontend-sdk-react`.

Additional targets:

- Consider consolidating action/dialog plumbing into an SDK "action runner" that can be driven by different UIs.

### 4.4 Chat persistence, scrolling, and reconcile-on-completion

This is a cleanup stage that makes chat behavior both correct and fast across representations.

- Persist controller-derived chat snapshots (including event-applied messages and the poller cursor).
- Replace raw scroll offset persistence with a bottom-anchor model.
- Make send event-driven (no immediate reload) and reconcile once on completion.

See:

- `plans/frontend-sdk/09-chat-persistence-scroll-and-reconcile.md`

Success criteria:

- RN UI files shrink and become UI-only.
- Controllers can be reused unchanged by a new desktop RN app.

See also:

- `plans/frontend-sdk/08-ui-representation-boundaries.md`

## Phase 5: Desktop frontend (RN macOS)

- Add `desktop/crystal-lattice-control-desktop-rn/`.
- Start by reusing the same screens/components as mobile (import from a shared UI package or copy initially).
- Use the same `@crystal-lattice/frontend-sdk` controllers/backends.

Decision point:

- Either keep one shared “RN UI package” (mobile+desktop), or allow divergence once SDK is stable.

## Phase 6: VS Code extension (future)

- Create a Node-targeted frontend that uses:
  - `RestAgentBackend` to talk to the Python server initially, or
  - `InProcessAgentBackend` once a TS port exists.

The core requirement is that the UI uses only `AgentBackend` + controllers.
