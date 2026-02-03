# Subtask: Desktop Metro + TS wiring for workspace packages

Configure the desktop RN macOS project to import monorepo packages via `file:` dependencies without Metro resolution issues.

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260202-desktop-macos-frontend/020-rn-macos-scaffold-and-version.md`

## Status

- [x] Done

Implemented wiring:

- `desktop/crystal-lattice-control-desktop-rn/metro.config.js:1` (watchFolders + symlinks + `extraNodeModules`)
- `desktop/crystal-lattice-control-desktop-rn/tsconfig.json:1` (`preserveSymlinks: true`)

## Reference (what worked for mobile)

The mobile app needed Metro symlink support + explicit package mapping:

- `mobile/crystal-lattice-control-rn/metro.config.js:10`
  - `watchFolders` includes SDK roots
  - `resolver.extraNodeModules` maps package names to local paths
  - `resolver.unstable_enableSymlinks: true`
- `mobile/crystal-lattice-control-rn/tsconfig.json:1` sets `preserveSymlinks: true`

## Work plan

### 1) Metro config

Create `desktop/crystal-lattice-control-desktop-rn/metro.config.js` similar to mobile, but including the new shared components package:

- `@crystal-lattice/frontend-sdk`
- `@crystal-lattice/frontend-sdk-react`
- `@crystal-lattice/frontend-rn-components`

### 2) TypeScript config

Set `preserveSymlinks: true` in the desktop TS config.

### 3) Validate

- Confirm desktop Metro can resolve imports from all shared packages.
- Confirm hot reload works without duplicate module copies.
