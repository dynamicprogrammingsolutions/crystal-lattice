# Plan: RN macOS scaffolding + version selection

Create the new desktop app at `desktop/crystal-lattice-control-desktop-rn/` using React Native macOS, intentionally using a different RN version than the mobile app.

Parent task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Related subtask: `tasks/20260202-desktop-macos-frontend/020-rn-macos-scaffold-and-version.md`

## Decisions

- Mobile is currently `react-native@0.82.1` (`mobile/crystal-lattice-control-rn/package.json:1`).
- Desktop must intentionally use a different RN version.
- Prefer aliasing so imports remain `import ... from 'react-native'`:
  - Desktop `package.json`: `"react-native": "npm:react-native-macos@<version>"`.

## Plan

### 1) Choose version strategy

- Pick a `react-native-macos@X` whose base RN version is not `0.82.x`.
- Document the chosen version and rationale in `desktop/crystal-lattice-control-desktop-rn/README.md`.

### 2) Scaffold the project

- Create `desktop/crystal-lattice-control-desktop-rn/`.
- Initialize a React Native app (TypeScript) and add the macOS platform using the recommended `react-native-macos` init flow.
- Ensure the tree includes:
  - `macos/` native project
  - `App.tsx` renders a placeholder view

### 3) Configure for monorepo usage

- Keep Node >= 20.
- Set `name`/bundle identifiers to something stable (can be updated later).

### 4) Verify locally (as much as possible)

- `npm install` succeeds in `desktop/crystal-lattice-control-desktop-rn/`.
- `npx react-native config` succeeds (sanity-check CLI wiring).
- If running on macOS:
  - `cd macos && pod install`
  - `npx react-native run-macos`
  - or open Xcode workspace and run.

## Deliverables

- `desktop/crystal-lattice-control-desktop-rn/` exists in-repo.
- `desktop/crystal-lattice-control-desktop-rn/README.md` includes exact run commands.
