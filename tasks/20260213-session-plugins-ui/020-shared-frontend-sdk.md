# Shared: frontend SDK support for session plugin endpoints

Parent Task: tasks/20260213-session-plugins-ui/000-main.md

Depends On:
- tasks/20260213-session-plugins-ui/010-server-endpoints.md

## Description

Extend `@crystal-lattice/frontend-sdk` so both mobile and desktop apps can call the new server plugin endpoints through the existing `AgentBackend` abstraction.

## Background / current SDK structure

- `AgentBackend` interface: `packages/frontend-sdk/src/backend/backend.ts`.
- REST implementation: `packages/frontend-sdk/src/backend/restBackend.ts`.
- Capability flags are already used for Settings (UI schema + overrides) on desktop; mobile currently assumes support but should also check.

## API surface to add

### 1) Types

Add a shared type for plugin entries, matching server response:

```ts
export interface SessionPluginEntry {
  id: string;
  kind: 'providers' | 'extensions' | 'features' | 'tools' | string;
  name?: string;
  class_path?: string;
  class_name?: string;
  enabled: boolean;
  source?: 'session' | 'agent' | 'implicit' | string;
  active?: boolean;
  [k: string]: any;
}
```

Placement suggestions:
- New file `packages/frontend-sdk/src/types/sessionPlugins.ts`, exported from the package index; or
- Add to `packages/frontend-sdk/src/types/plugins.ts` (but that file is currently focused on *application-level* plugins/actions).

### 2) Capabilities

Update `BackendCapabilities` in `packages/frontend-sdk/src/backend/backend.ts` to add:

```ts
sessionPlugins: boolean;
```

Update `RestAgentBackend.getCapabilities()` in `packages/frontend-sdk/src/backend/restBackend.ts` to return `sessionPlugins: true`.

### 3) Backend methods

Extend `AgentBackend` with:

```ts
listSessionPlugins(sessionId: string): Promise<SessionPluginEntry[]>;
setSessionPlugins(sessionId: string, enabled: string[]): Promise<void>;
clearSessionPlugins(sessionId: string): Promise<void>;
```

Implement in `RestAgentBackend`:

- `GET /sessions/:id/plugins` → return `resp.data.plugins` (or tolerate `resp.data` directly if server returns raw array; prefer `{plugins}` response though).
- `PUT /sessions/:id/plugins` body `{ enabled }`.
- `DELETE /sessions/:id/plugins`.

## Compatibility notes

- Bridge mode uses the same REST paths via its transport; adding paths is safe as long as the Python server supports them.
- If older servers are used, the capability flag should allow UIs to hide/disable “Plugins”.
  - Optionally, treat 404 on `/plugins` as “not supported” in UI.

## Tests

Add unit tests for `RestAgentBackend` if the repo has a test harness; otherwise verify typecheck + existing app builds.

## Done when

- `AgentBackend` compiles with the new methods.
- `RestAgentBackend` implements them.
- Desktop/mobile can call `backend.getCapabilities().sessionPlugins` to gate the feature.

---

## Implementation Notes (completed 2026-02-13)

### Summary

Added session plugin support to the shared frontend SDK:

- New `SessionPluginEntry` type exported from the package.
- New `BackendCapabilities.sessionPlugins` capability flag.
- New `AgentBackend` methods + REST implementation for the server endpoints:
  - `GET /sessions/:id/plugins`
  - `PUT /sessions/:id/plugins` with `{ enabled: string[] }`
  - `DELETE /sessions/:id/plugins`

### Files changed / added

- Modified `packages/frontend-sdk/src/backend/backend.ts`
  - Added `sessionPlugins` capability.
  - Added `listSessionPlugins`, `setSessionPlugins`, `clearSessionPlugins` to `AgentBackend`.
- Modified `packages/frontend-sdk/src/backend/restBackend.ts`
  - Implemented the three REST calls; `listSessionPlugins` tolerates both `{ plugins: [...] }` and a raw array.
  - Advertises `sessionPlugins: true` in `getCapabilities()`.
- Added `packages/frontend-sdk/src/types/sessionPlugins.ts`
  - Defines the shared `SessionPluginEntry` interface matching the server response shape.
- Modified `packages/frontend-sdk/src/index.ts`
  - Exports `SessionPluginEntry`.

### Tests

- Added unit tests: `packages/frontend-sdk/src/backend/restBackend.sessionPlugins.test.ts`.
- Updated backend mock capabilities in `packages/frontend-sdk/src/plugins/__tests__/actionRunner.test.ts`.
- Added real-backend integration tests (behind `RUN_BACKEND_INTEGRATION=1`):
  - `D: session plugins list/set/clear roundtrip`
  - `E: disabling system_message removes the synthetic system message from stored history`
  - Both added in `packages/frontend-sdk/src/integration/__tests__/backend.integration.test.ts`.

Commands used:

- `cd packages/frontend-sdk && npx vitest run`
- `cd packages/frontend-sdk && RUN_BACKEND_INTEGRATION=1 npx vitest run`
