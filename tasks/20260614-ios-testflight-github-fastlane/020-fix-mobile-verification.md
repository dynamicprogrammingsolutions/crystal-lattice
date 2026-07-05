# Fix Mobile Verification Blockers

Get the React Native app to a clean local verification baseline before adding TestFlight automation.

## Requirements checklist

- [x] Fix the TypeScript error in the splash/logo code.
- [x] Fix the Jest environment issue for `react-native-gesture-handler`.
- [x] Run `npm run tsc` from `mobile/crystal-lattice-control-rn`.
- [x] Run `npm test -- --runInBand` from `mobile/crystal-lattice-control-rn`.
- [x] Run `npm run lint` if it is stable in this app, and report any existing lint noise separately from release blockers.

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

## Partial Progress Notes

Added during follow-up on 2026-06-15.

The Jest blocker has been addressed in the separate testing branch/worktree:

- Branch: `task/20260615-mobile-component-integration-tests`
- Worktree: `/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260615-mobile-component-integration-tests`
- Related task: `tasks/20260615-mobile-component-integration-tests/020-react-native-testing-library-setup.md`

That work centralizes the `react-native-gesture-handler` mock and adds additional app-level native mocks needed by the full mobile Jest suite. Verification passed there:

```bash
cd mobile/crystal-lattice-control-rn
npm test -- --runInBand
```

Result: 10 suites passed, 25 tests passed.

This does not complete this TestFlight verification task yet. `npm run tsc` still fails on the splash/logo type error:

```text
src/components/AnimatedSplashScreen.tsx(71,20): error TS2322:
Type '{ type: string; width: number; height: number; }' is not assignable to type 'IntrinsicAttributes & AppLogoProps'.
Property 'type' does not exist on type 'IntrinsicAttributes & AppLogoProps'.
```

Remaining work:

- Fix `AnimatedSplashScreen` / `AppLogo` typing or prop usage.
- Re-run `npm run tsc`.
- Run/report `npm run lint`.

## Acceptance Criteria

- `npm run tsc` exits 0.
- `npm test -- --runInBand` exits 0.
- Any remaining warnings are documented and not release-blocking.

## Completion Notes

Added during completion on 2026-07-05.

This task is complete in the current checkout.

- The splash/logo TypeScript issue is fixed; `AnimatedSplashScreen` now passes only supported props to `AppLogo`.
- The Jest native-module setup issue was completed via `tasks/20260615-mobile-component-integration-tests/020-react-native-testing-library-setup.md`.
- Verification passed:

```bash
cd mobile/crystal-lattice-control-rn
npm run tsc
npm test -- --runInBand
```

Results:

- `npm run tsc`: passed.
- `npm test -- --runInBand`: passed, 17 suites and 54 tests.

`npm run lint` was attempted earlier and is not currently a stable verification command because ESLint cannot find a configuration file for this app. That is a separate tooling gap, not a TestFlight blocker for this task.
