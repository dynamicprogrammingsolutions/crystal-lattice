# React Native Testing Library Setup

Add a reliable React Native Testing Library setup for mobile component tests while keeping existing Jest tests working.

## Requirements checklist

- [x] Add `@testing-library/react-native` to `mobile/crystal-lattice-control-rn`.
- [x] Decide whether additional matchers are needed or whether plain `screen`/`fireEvent` assertions are enough.
- [x] Add a `renderWithMobileProviders` or equivalent helper for theme/safe-area/provider wiring.
- [x] Fix or standardize native-module mocks needed by app-level component tests, including `react-native-gesture-handler`.
- [x] Verify existing mobile tests still pass.
- [x] Add a minimal smoke test proving `render`, `screen`, and `fireEvent.press` work.

Parent Task: tasks/20260615-mobile-component-integration-tests/000-main.md
Depends On: tasks/20260615-mobile-component-integration-tests/010-audit-and-test-tier-design.md

## Known Starting State

The app currently has:

- `react-test-renderer`
- Jest
- React Native `0.82.1`
- React `19.1.1`

The app does not currently have `@testing-library/react-native` in `mobile/crystal-lattice-control-rn/package.json`.

Prior local verification found that `__tests__/App.test.tsx` can fail because `react-native-gesture-handler` attempts to load `RNGestureHandlerModule`. Treat this as part of making component tests reliable, not only as a one-off TestFlight readiness issue.

## Helper Expectations

Create or document a helper that can render mobile components with common providers, such as:

- theme provider;
- safe-area provider or safe-area mocks;
- any application context provider needed by common components.

If the helper is not generic enough for every screen, keep it focused and document how to extend it.

## Acceptance Criteria

- Existing mobile Jest tests pass.
- A new minimal test can render a React Native component, press a visible button/text control, and assert newly visible text.
- Native-module mocks are centralized enough that future app-level component tests do not repeatedly rediscover the same setup failures.

## Completion Notes

Added during completion on 2026-06-15.

- Added `@testing-library/react-native` to the mobile app.
- Added `mobile/crystal-lattice-control-rn/src/testUtils/renderWithMobileProviders.tsx`.
- Added `mobile/crystal-lattice-control-rn/__tests__/testingLibrarySmoke.test.tsx`.
- Added shared Jest setup for `react-native-gesture-handler`.
- Added Jest module aliases so workspace package source resolves React, React Native, Babel runtime, and local `@crystal-lattice/*` packages from the mobile app.
- Chose plain React Native Testing Library `screen`, `fireEvent`, and `waitFor` assertions; no extra matcher package is needed yet.
- Verification passed:

```bash
cd mobile/crystal-lattice-control-rn
npm test -- --runTestsByPath __tests__/testingLibrarySmoke.test.tsx __tests__/SessionSettingsModal.test.tsx --runInBand
```
