# React Native macOS Component Extraction Resources

Reference notes for extracting app-local native UI pieces into standalone React Native component packages. This document captures the official guidance, local repository examples, and repo-specific lessons learned during the `MacTextView` extraction so future component extractions do not need to rediscover the same material.

Parent Task: `tasks/20260419-react-native-macos-component-extraction/000-main.md`

## Why this exists

When a native UI piece starts inside an app target, it is easy to optimize only for "make it work here." The cost shows up later:

- the native code is hard to reuse across projects
- the JavaScript API drifts away from normal React Native patterns
- app-level behavior and component-level behavior get mixed together
- debugging and ownership become less clear

This document is a handoff/reference for future extractions so we can start from a consistent shape.

## Official references

### React Native New Architecture library guidance

- React Native: Create a Library for Your Module
  - `https://reactnative.dev/docs/the-new-architecture/create-module-library`
  - Why it matters:
    - recommends extracting reusable native work into a standalone library
    - uses `create-react-native-library` as the starting point
    - expects a package-owned example/test app
    - frames New Architecture support as part of the package shape, not an afterthought

- React Native: Using Codegen
  - `https://reactnative.dev/docs/0.78/the-new-architecture/using-codegen`
  - Why it matters:
    - explains `codegenConfig` in `package.json`
    - explains generated native interfaces and metadata
    - shows how Apple-side component registration uses `componentProvider`

### React Native macOS guidance

- React Native macOS: Native Platform
  - `https://microsoft.github.io/react-native-macos/docs/guides/native-development`
  - Why it matters:
    - says to follow the normal Apple native-library model and add macOS support explicitly
    - documents adding `:osx` to podspec platform declarations
    - supports shared Apple code with `TARGET_OS_OSX` branches or parallel Apple-platform files

### Package ecosystem metadata

- React Native Directory
  - `https://github.com/react-native-community/directory`
  - Why it matters:
    - treats `macos` support as explicit package metadata
    - treats `newArchitecture` support as explicit package metadata
    - encourages example apps and observable package quality signals

## Local package examples already inspected

These sibling repositories were inspected during the `MacTextView` research and are useful templates for future extractions.

### `../react-native-webview`

- Good reference for:
  - a standalone reusable package
  - `codegenConfig` in `package.json`
  - package-owned Apple/native integration
  - New Architecture component registration metadata

- Useful places to inspect:
  - `../react-native-webview/package.json`
  - `../react-native-webview/react-native-webview.podspec`
  - `../react-native-webview/src/RNCWebViewNativeComponent.ts`
  - `../react-native-webview/example/macos`

### `../react-native-svg`

- Good reference for:
  - broad Apple-platform support including macOS
  - podspec platform declarations for `:osx`
  - platform-specific Apple file organization
  - a library that clearly treats macOS as a first-class supported target

- Useful places to inspect:
  - `../react-native-svg/package.json`
  - `../react-native-svg/RNSVG.podspec`
  - `../react-native-svg/src/fabric/`
  - `../react-native-svg/apps/paper-macos-example`
  - `../react-native-svg/apps/fabric-macos-example`

### `../react-native-gesture-handler`

- Good reference for:
  - monorepo package layout
  - package-owned example app structure
  - Codegen-backed package organization

- Useful places to inspect:
  - `../react-native-gesture-handler/packages/react-native-gesture-handler/package.json`
  - `../react-native-gesture-handler/packages/react-native-gesture-handler/RNGestureHandler.podspec`
  - `../react-native-gesture-handler/packages/react-native-gesture-handler/src/specs/`
  - `../react-native-gesture-handler/apps/macos-example`

## Recommended package shape for future extractions

For new reusable native components in this repo, prefer a package shape like:

- `packages/<package-name>/package.json`
- `packages/<package-name>/src/index.ts`
- `packages/<package-name>/src/specs/<NativeComponent>NativeComponent.ts`
- `packages/<package-name>/apple/...` or `packages/<package-name>/ios/...` with explicit macOS support
- `packages/<package-name>/<package-name>.podspec`
- `packages/<package-name>/example-macos/...` or another package-owned example app

Recommended package characteristics:

- standalone package boundary, not app-local native files
- `codegenConfig` present in `package.json`
- macOS declared explicitly in the podspec
- public JS API exported from the package, not imported from app-local compatibility shims
- example app or clearly testable consumer path

## Recommended extraction checklist

Use this checklist when moving another app-local macOS-native component into a reusable package:

1. Identify the current app-local JS wrapper and native implementation.
2. Decide which parts of the public API must remain compatible.
3. Decide what belongs in the package versus what belongs in the application.
4. Create a standalone package under `packages/`.
5. Add `package.json`, `tsconfig.json`, and package entrypoints.
6. Add a Codegen native component spec under `src/specs/`.
7. Add a podspec with explicit macOS platform support.
8. Move Apple native implementation into the package.
9. Update the app to consume the package rather than the app-local native files.
10. Update Metro or local workspace resolution if the package is consumed via local dependency links.
11. Run `pod install` for the desktop app.
12. Build the macOS app and test the existing user flows.
13. Add or update an example app when the package is intended for reuse beyond this repo.
14. Document what intentionally remains custom compared with stock `react-native-macos` behavior.

## App-level vs component-level ownership

One of the most important lessons from the `MacTextView` work is that not every bug near a custom component belongs inside the component.

### Component package should usually own

- native control implementation details
- measurement and layout behavior
- placeholder behavior
- editing behavior
- Codegen spec / commands / events
- control-specific alignment with stock RN text input behavior

### Application should usually own

- Dock reopen behavior
- app-level window restoration policy
- app-owned transient popovers and windows
- global menu configuration
- any logic that restores or orders front app windows

If a bug depends strongly on app activation, Dock clicks, or app-level window restoration, inspect the app before adding more component-level workaround logic.

## `MacTextView` lessons learned

### Extraction outcome

- `MacTextView` was extracted from app-local code into:
  - `packages/react-native-mac-text-view`
- It now owns:
  - the public JS wrapper
  - the native component spec
  - the Apple native implementation
  - package metadata and podspec

### Useful alignment retained in the package

- dedicated backing `NSTextView` subclass
- stock-like macOS text-system toggle methods:
  - `toggleAutomaticSpellingCorrection:`
  - `toggleContinuousSpellChecking:`
  - `toggleGrammarChecking:`
  - `setEnabledTextCheckingTypes:`
- custom multiline auto-grow behavior remained intentionally custom

### What turned out to be a dead end

- trying to fully solve the Dock-specific spelling-window bug from inside the component
- repeatedly closing shared spelling/substitution panels from inside `MacTextView`
- using component-level activation/deactivation suppression as the primary fix

These mitigations helped investigation, but the final reliable fix did not depend on them.

### What the final fix actually was

- The key app-level cause was in:
  - `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/AppDelegate.mm`
- `applicationShouldHandleReopen:hasVisibleWindows:` was restoring every key-capable window from `NSApp.windows`
- That broad restore behavior could revive shared AppKit panels and stale auxiliary windows

Final app-level fixes:

- restrict Dock reopen restoration to tracked main windows only
- clear transient popover references consistently in:
  - `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/DesktopWindowManager.mm`

### Rule of thumb from this case

If a bug looks like "clicking the Dock icon brings back weird windows," inspect app-level window restoration before adding more native component workarounds.

## Known pitfalls

- Metro may not automatically resolve a newly extracted local package without config updates in the consuming app.
- A multiline standalone `NSTextView` is not behaviorally the same as stock single-line RN `TextInput`, which uses `NSTextField` and the field editor.
- AppKit shared panels and auxiliary windows can make a component bug look worse than it really is if the app aggressively restores all windows.
- Temporary native instrumentation is useful during investigation, but remove it before finalizing the change.
- Task notes can drift from the final shipped solution if the real fix ends up in a different layer than initially expected.

## Repo-specific references

- Extracted package:
  - `packages/react-native-mac-text-view`
- App-level Dock/window restore behavior:
  - `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/AppDelegate.mm`
- App-owned transient popovers/windows:
  - `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/DesktopWindowManager.mm`
- Extraction task:
  - `tasks/20260419-react-native-macos-component-extraction/010-extract-mac-text-view-library.md`
- Alignment and bugfix task:
  - `tasks/20260419-react-native-macos-component-extraction/020-mac-text-view-rn-text-input-alignment.md`

## Suggested use for future tasks

When creating a new extraction task in this directory:

- link this resources file from the task
- explicitly state whether the task is:
  - package extraction
  - RN/macOS behavior alignment
  - app-level integration cleanup
- avoid mixing all three until the ownership boundaries are clear