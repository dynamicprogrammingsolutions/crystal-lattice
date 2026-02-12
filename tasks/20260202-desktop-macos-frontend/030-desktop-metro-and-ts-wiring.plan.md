# Plan: Desktop Metro + TS wiring

Configure the desktop RN macOS project to import monorepo packages via `file:` dependencies without Metro resolution issues.

Parent task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Related subtask: `tasks/20260202-desktop-macos-frontend/030-desktop-metro-and-ts-wiring.md`

## Reference (mobile working setup)

- Metro config: `mobile/crystal-lattice-control-rn/metro.config.js:1`
- TS config: `mobile/crystal-lattice-control-rn/tsconfig.json:1`

## Plan

### 1) Add workspace dependencies

In `desktop/crystal-lattice-control-desktop-rn/package.json`, add:

- `@crystal-lattice/frontend-sdk`: `file:../../packages/frontend-sdk`
- `@crystal-lattice/frontend-sdk-react`: `file:../../packages/frontend-sdk-react`
- `@crystal-lattice/frontend-rn-components`: `file:../../packages/frontend-rn-components`

Run `npm install` to generate a lockfile.

### 2) Metro config

Create `desktop/crystal-lattice-control-desktop-rn/metro.config.js` mirroring the mobile app:

- `watchFolders` includes the three package roots.
- `resolver.unstable_enableSymlinks = true`.
- `resolver.extraNodeModules` maps package names to their local paths.
- `resolver.nodeModulesPaths` includes both local and repo-root `node_modules`.

### 3) TypeScript config

Create or update `desktop/crystal-lattice-control-desktop-rn/tsconfig.json`:

- `extends: "@react-native/typescript-config"`
- `compilerOptions.preserveSymlinks = true`

### 4) Validate

- Add a tiny import/use from each shared package in `App.tsx`.
- Sanity check:
  - `node -c metro.config.js`
  - `npx tsc -p tsconfig.json --noEmit` (if `typescript` is installed in the desktop app)
- On macOS, also run the app and confirm Metro resolves without duplicate-module issues.

## Deliverables

- Desktop app imports shared packages without Metro symlink issues.
