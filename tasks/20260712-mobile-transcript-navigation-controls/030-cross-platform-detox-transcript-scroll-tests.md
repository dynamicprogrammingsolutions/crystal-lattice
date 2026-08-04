# Add Cross-Platform Detox Transcript Scroll Tests

Set up Detox as the single long-term mobile E2E framework and verify the production transcript chevron controls on both an iOS Simulator and Android Emulator.

## Requirements checklist

- [x] Detox is the only new native E2E framework; do not add a separate XCUITest, Maestro, Appium, or Espresso-only suite.
- [x] One TypeScript Detox suite runs against both iOS and Android configurations.
- [x] Tests launch a deterministic transcript harness through cross-platform launch arguments.
- [x] The harness reuses the production transcript viewport, inverted FlatList behavior, geometry handling, and chevron controls rather than duplicating them.
- [x] The fixture contains enough deterministic variable-height messages to exercise virtualization.
- [x] Tests verify initial bottom state, top navigation, bottom navigation, middle-state affordances, and repeated top/bottom round trips.
- [x] Primary assertions use visible oldest/newest rows and edge-button state; internal metrics are diagnostic only.
- [x] Detox artifacts and concise diagnostics are available for failures.
- [x] Local scripts support focused iOS and Android build/test commands without requiring a separate native test framework.

## Task checklist

- [x] Add Detox dependencies and lockfile updates.
- [x] Add `.detoxrc.js` with iOS Simulator and Android Emulator bundled-build configurations.
- [x] Add Detox Jest runner configuration and lifecycle setup.
- [x] Add Android Detox instrumentation dependency, runner, and test build configuration.
- [x] Add cross-platform native launch-argument handling for selecting the harness component.
- [x] Register `MobileTranscriptScrollHarness` in `index.js`.
- [x] Extract or expose the production transcript viewport so the harness and `SessionChatScreen` share the tested scroll implementation.
- [x] Add deterministic variable-height transcript fixtures and stable native test IDs.
- [x] Add cross-platform Detox launch, edge-navigation, middle-position, and repeated-round-trip tests.
- [x] Add package scripts and documentation.
- [x] Run pure/mobile tests and TypeScript checks.
- [x] Build and run the focused Detox suite on iOS Simulator.
- [x] Build and run the focused Detox suite on Android Emulator.
- [x] Record artifacts, failures, environment limitations, and follow-up findings.

Parent Task: `tasks/20260712-mobile-transcript-navigation-controls/000-main.md`

Depends On:

- `tasks/20260712-mobile-transcript-navigation-controls/010-mobile-message-range-controls.md`
- `tasks/20260712-mobile-transcript-navigation-controls/020-mobile-transcript-edge-buttons.md`

## Context and references

- Mobile app root: `mobile/crystal-lattice-control-rn`.
- Existing edge controls: `src/components/TranscriptEdgeButtons.tsx`.
- Existing inverted geometry and commands: `src/invertedTranscriptScroll.ts`.
- Existing transcript implementation: `src/SessionChatScreen.tsx` and `src/components/DependencyFlatList.tsx`.
- Existing stable edge IDs: `transcript-scroll-to-top` and `transcript-scroll-to-bottom`.
- iOS native entry point: `ios/CrystalLatticeControlRN/AppDelegate.swift`.
- Android native entry point: `android/app/src/main/java/com/dynamicprogrammingsolutions/crystallatticecontrolrn/MainActivity.kt`.
- Available local devices at planning time: iPhone 17 Pro/iOS 26.1 and Android AVD `Medium_Phone_API_36.1`.
- Detox and AppleSimUtils were not installed at planning time.

## Approved implementation plan

1. Install Detox as a mobile development dependency and update `package-lock.json`.
2. Add `.detoxrc.js` with `ios.sim.release` and `android.emu.release` configurations so bundled E2E binaries do not require Metro.
3. Allow device names to be overridden with `DETOX_IOS_DEVICE` and `DETOX_ANDROID_AVD`.
4. Configure iOS to build the existing app scheme for the simulator; do not add a separate XCUITest target.
5. Configure Android with the Detox instrumentation dependency, `testInstrumentationRunner`, test build type, and a Detox runner under `android/app/src/androidTest`.
6. Add a dedicated Detox Jest configuration, environment/lifecycle setup, and TypeScript E2E suite under `e2e/`.
7. Register a `MobileTranscriptScrollHarness` component alongside the normal app.
8. Use Detox `device.launchApp({launchArgs: ...})`; select the harness module in `AppDelegate.swift` and `MainActivity.kt` only when the launch argument is present.
9. Extract or expose the exact production transcript viewport so the normal screen and harness share `DependencyFlatList`, inversion, metric callbacks, edge-button state, commands, and `maintainVisibleContentPosition`.
10. Seed approximately 300 deterministic messages with stable indices and variable heights, without network, polling, storage, plugins, or other unrelated runtime dependencies.
11. Add stable IDs for the transcript list, harness-ready marker, oldest row, newest row, and edge controls; prevent Android flattening where necessary.
12. Add one shared test suite covering:
    - Initial bottom state.
    - Chevron-up reaching the oldest loaded message.
    - Chevron-down returning to the newest loaded message.
    - A middle position showing both controls.
    - Repeated bottom/top round trips.
13. Use Detox `waitFor` and visibility/existence assertions instead of fixed sleeps.
14. Configure screenshots, logs, and optional video artifacts for failures.
15. Add focused build/test scripts for iOS and Android.
16. Run existing pure tests and TypeScript first, then an E2E harness-ready smoke test, then the full focused transcript suite on each platform.

## Testing plan

1. Existing mobile Jest suite and `npm run tsc`.
2. Detox configuration validation and environment checks.
3. iOS bundled app build and harness-ready smoke test.
4. Android bundled app/test APK build and harness-ready smoke test.
5. Shared transcript suite on iOS:
   - Newest row visible initially.
   - Top button visible and bottom button absent.
   - Oldest row visible after top navigation.
   - Bottom button visible and top button absent.
   - Newest row visible again after bottom navigation.
   - Both buttons visible after a real middle-position swipe.
   - Repeated top/bottom cycles remain stable.
6. The same shared suite on Android.
7. Repeat each platform suite during stabilization to identify timing-sensitive failures.
8. Preserve failure screenshots, logs, and videos; report any simulator/emulator or signing/tooling blockers without weakening the test.

## Completion Notes

Added during completion on 2026-07-13.

- Installed Detox `20.51.4` and AppleSimUtils `0.9.12`.
- Added one shared TypeScript Detox suite with bundled iOS and Android E2E builds.
- Added `MobileTranscriptScrollHarness` with 300 deterministic variable-height rows.
- Extracted `InvertedTranscriptViewport`, which is now used by both the production `SessionChatScreen` transcript and the harness.
- Added stable transcript list/message test IDs and preserved the existing chevron IDs.
- Added iOS process-argument routing and Android launch-option routing into the shared app component.
- Added a dedicated Android `e2e` build type so Detox WebSocket traffic is allowed without weakening the production release manifest.
- Added Android test dependency alignment for the React Native 0.82 AndroidX Test constraints.
- Added Android AVD preparation and ignored debug-keystore generation scripts.
- Configured failure logs/screenshots on both platforms, iOS failure video, and iOS view-hierarchy capture. Android video is disabled because the selected AVD could not reliably encode the 1080x2400 screen during failure capture.
- The first realistic iOS run exposed a product regression: plain `FlatList.scrollToEnd()` stopped around message 221 of 300. The production viewport now uses a bounded, drag-cancellable, alternating `scrollToIndex`/measured-offset convergence operation for explicit top navigation. Bottom navigation remains an independent offset-zero command.
- Added a pure regression test for far top-navigation retries and cancellation by an explicit bottom command.
- Android uses a real swipe on a visible transcript row for the middle-position assertion because swiping the inverted FlatList host itself did not move reliably through Detox on Android.

Verification:

- `npm test -- --runInBand`: 20 suites, 70 tests passed.
- `npm run tsc`: passed.
- Focused formatting checks: passed.
- `npm run detox:build:ios`: passed.
- `npm run detox:test:transcript:ios`: passed on iPhone 17 Pro/iOS 26.1.
- `npm run detox:build:android`: passed.
- `npm run detox:test:transcript:android`: passed on `Medium_Phone_API_36.1`.
