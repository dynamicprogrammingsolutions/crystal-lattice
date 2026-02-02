# Subtask: RN macOS scaffolding + version selection

Create the new desktop app at `desktop/crystal-lattice-control-desktop-rn/` using React Native macOS, intentionally using a different RN version than the mobile app.

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260129-frontend-sdk/000-main.md`

## Status

- [ ] Not started

## Constraints / decisions already made

- This must be React Native macOS.
- It may use a different RN version than mobile.
- Only manual connection required for Phase 5.

## What needs web search

This subtask is the one place where web search access is very helpful.

We need authoritative, up-to-date guidance for:

- Recommended way to initialize a `react-native-macos` project in 2026.
- Compatibility matrix / which `react-native-macos` version corresponds to which `react-native` base.
- Whether the recommended approach is to alias `react-native` to `react-native-macos` in `package.json`.

Additional hint:

- RN macOS exposes macOS-specific `View` props/events (focus ring, key handling, tooltips, hover, etc.).
  - See: `tasks/20260202-desktop-macos-frontend/920-native-elements-notes.md`

If you can enable web search, do it before starting this subtask.

## Work plan

### 1) Choose version strategy

We need to decide:

- `react-native-macos` version to target.
- Whether the desktop app should keep the dependency name as `react-native` (alias) for maximum compatibility with shared packages.

Recommended outcome:

- Desktop `package.json` has `"react-native": "npm:react-native-macos@<version>"` (or equivalent), so imports remain `import { View } from 'react-native'`.

### 2) Scaffold the project

- Create `desktop/` directory (currently absent).
- Create `desktop/crystal-lattice-control-desktop-rn/`.
- Ensure:
  - `react`, `react-native` (alias), and macOS native project files exist.
  - The app boots to a placeholder screen.

### 3) Confirm the build pipeline works

- Document the exact commands used to run the macOS app (Xcode vs CLI).
- Ensure dependencies install with Node >= 20.

## Deliverables

- Desktop app folder exists with a working macOS run target.
- A short README exists at `desktop/crystal-lattice-control-desktop-rn/README.md` explaining how to run it.
