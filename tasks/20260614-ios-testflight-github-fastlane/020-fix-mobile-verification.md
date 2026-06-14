# Fix Mobile Verification Blockers

Get the React Native app to a clean local verification baseline before adding TestFlight automation.

## Requirements checklist

- [ ] Fix the TypeScript error in the splash/logo code.
- [ ] Fix the Jest environment issue for `react-native-gesture-handler`.
- [ ] Run `npm run tsc` from `mobile/crystal-lattice-control-rn`.
- [ ] Run `npm test -- --runInBand` from `mobile/crystal-lattice-control-rn`.
- [ ] Run `npm run lint` if it is stable in this app, and report any existing lint noise separately from release blockers.

Parent Task: tasks/20260614-ios-testflight-github-fastlane/000-main.md
Depends On: tasks/20260614-ios-testflight-github-fastlane/010-preflight-audit.md

## Known Starting State

Commands previously run from `mobile/crystal-lattice-control-rn`:

```bash
npm run tsc
npm test -- --runInBand
```

Current `npm run tsc` failure:

```text
src/components/AnimatedSplashScreen.tsx(71,20): error TS2322:
Type '{ type: string; width: number; height: number; }' is not assignable to type 'IntrinsicAttributes & AppLogoProps'.
Property 'type' does not exist on type 'IntrinsicAttributes & AppLogoProps'.
```

Relevant files:

- `mobile/crystal-lattice-control-rn/src/components/AnimatedSplashScreen.tsx`
- `mobile/crystal-lattice-control-rn/src/components/AppLogo.tsx`

Current Jest status:

- 7 of 8 suites passed.
- `__tests__/App.test.tsx` failed before executing tests because `react-native-gesture-handler` attempted to load `RNGestureHandlerModule`.

Expected likely fix:

- Remove the unsupported `type="square"` prop from `AppLogo`, or intentionally add a typed prop if the design requires variants.
- Add or adjust Jest setup/mocks for `react-native-gesture-handler` in the existing Jest setup files, following the package's recommended Jest setup and existing local mock style.

## Acceptance Criteria

- `npm run tsc` exits 0.
- `npm test -- --runInBand` exits 0.
- Any remaining warnings are documented and not release-blocking.
