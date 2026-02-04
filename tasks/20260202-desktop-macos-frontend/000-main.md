# Desktop macOS frontend (React Native macOS)

Build a desktop-focused macOS frontend using React Native macOS. The desktop app should:

- Use a different RN version than mobile.
- Use `@crystal-lattice/frontend-sdk` + `@crystal-lattice/frontend-sdk-react` for all business logic.
- Support manual connections only (host/port) for now.
- Use a desktop layout:
  - Left column: connections (top) + sessions (bottom)
  - Main column: multiple sessions open simultaneously as tabs
- Multiple connections can be open at the same time; tabs may span connections.
- Share *mid-level* RN components between mobile and desktop (not low-level primitives like `Button`, and not the entire chat view).

This task directory is a handoff package for implementing Phase 5 of `tasks/20260129-frontend-sdk/000-main.md`.

## Parent / context

- Phase 5 placeholder task: `tasks/20260129-frontend-sdk/070-phase-5-desktop-frontend.md`
- SDK is already extracted and used by mobile:
  - `packages/frontend-sdk/`
  - `packages/frontend-sdk-react/`

## Decisions already made (authoritative)

- Desktop tech: React Native macOS (not Catalyst/iOS-on-mac).
- Desktop UI is *desktop-first* and can diverge from mobile.
- Only **manual connections** needed for this milestone.
- Want shared components that include *some logic*, e.g. action bars/menus/tabs—not basic buttons, and not the entire messages view.
- “Tabs” means **multiple open sessions as tabs** in the main column (not “screen tabs” like mobile).
- Layout preference:
  - Two column layout.
  - Left column split vertically: connections above sessions.
  - Main column uses session tabs.
  - Settings should be dropdowns (not modal popups).

## Open decisions (need your input during implementation)

1) RN macOS scaffolding method + version selection
   - We need to choose a `react-native-macos` version and how it maps to `react-native` in `package.json`.
   - This likely benefits from web search (version compatibility / recommended init command).

2) Shared components package name + scope
   - Proposed: `packages/frontend-rn-components/` published as `@crystal-lattice/frontend-rn-components`.
   - Scope proposal is in `tasks/20260202-desktop-macos-frontend/900-shared-components-scope.md`.

3) Desktop tab UX details
   - Closable tabs? Reorder? Max tabs?
   - “Open session” behavior when already open: focus existing tab.
   - Proposed default behavior in `tasks/20260202-desktop-macos-frontend/910-desktop-ux-spec.md`.

4) “Native element” strategy on macOS
   - Summary of what RN macOS supports and what likely requires native modules:
     - `tasks/20260202-desktop-macos-frontend/920-native-elements-notes.md`

## Notes from repo review (helpful references)

- Connection record model + persistence currently live in mobile, not the SDK:
  - `mobile/crystal-lattice-control-rn/App.tsx:42` (types)
  - `mobile/crystal-lattice-control-rn/App.tsx:77` (`STORAGE_KEY_CONNECTIONS`)
- Mobile already solved Metro/TS workspace import issues; desktop should mirror this pattern:
  - `mobile/crystal-lattice-control-rn/metro.config.js:1`
  - `mobile/crystal-lattice-control-rn/tsconfig.json:1`
- Multi-tab chat needs careful polling start/stop behavior; see existing gating logic:
  - `packages/frontend-sdk-react/src/useChatController.ts:1`

## Suggested implementation bundles

- Desktop bootstrap: `020` + `030` (scaffold macOS app, then wire Metro/TS)
- Shared foundations (can happen early / in parallel): `010` + `040` (shared UI package + shared connection model)
- Desktop shell + left column: `050` + `060` + `070` (layout, connections, sessions; relies on `010` + `040`)
- Chat + docs: `080` + `090` (tabs/chat, then smoke checklist + README)

## Tasks that need more planning up front

- `020-rn-macos-scaffold-and-version`: version compatibility + init/scaffolding approach is high-uncertainty.
- `010-shared-components-package`: shared component API boundaries (dropdown vs modal surface, icon strategy).
- `080-desktop-chat-tabs-and-chat-pane`: per-tab controller lifecycle + polling cleanup (avoid background work leaks).

## Subtasks

- `tasks/20260202-desktop-macos-frontend/010-shared-components-package.md`
- `tasks/20260202-desktop-macos-frontend/020-rn-macos-scaffold-and-version.md`
- `tasks/20260202-desktop-macos-frontend/030-desktop-metro-and-ts-wiring.md`
- `tasks/20260202-desktop-macos-frontend/040-shared-connection-model.md`
- `tasks/20260202-desktop-macos-frontend/050-desktop-shell-layout.md`
- `tasks/20260202-desktop-macos-frontend/060-desktop-connections-panel.md`
- `tasks/20260202-desktop-macos-frontend/065-desktop-tab-strip-styles-and-view-menu.md`
- `tasks/20260202-desktop-macos-frontend/070-desktop-sessions-pane.md`
- `tasks/20260202-desktop-macos-frontend/080-desktop-chat-tabs-and-chat-pane.md`
- `tasks/20260202-desktop-macos-frontend/090-smoke-tests-and-docs.md`

## Supporting docs

- Shared component boundaries + candidates: `tasks/20260202-desktop-macos-frontend/900-shared-components-scope.md`
- Desktop UX spec + tab semantics: `tasks/20260202-desktop-macos-frontend/910-desktop-ux-spec.md`
- Native elements notes (RN macOS): `tasks/20260202-desktop-macos-frontend/920-native-elements-notes.md`
- Extractable subcomponents (mobile → shared candidates): `tasks/20260202-desktop-macos-frontend/930-extractable-subcomponents.md`
