# Extract MacTextView Into Reusable RN macOS Library

Extract the desktop app's app-local `MacTextView` native component into a standalone reusable React Native library that follows the New Architecture library shape and explicitly supports macOS.

## Requirements checklist

- [x] Move `MacTextView` from app-local code into a dedicated reusable library package rather than leaving the native code under `desktop/crystal-lattice-control-desktop-rn/macos/...`.
- [x] Use a New Architecture-friendly library shape with a Codegen native component spec instead of an app-only `requireNativeComponent(...)` wrapper with ad hoc native registration.
- [x] Add package-level metadata and structure expected from reusable React Native libraries:
  - `package.json` with `react-native` entrypoint and `codegenConfig`
  - package-owned Apple native source
  - package-owned podspec with explicit `:osx` platform support
  - example app or example package path suitable for validating macOS support
- [x] Keep the component macOS-focused for now. Cross-platform expansion is optional and should not block extraction.
- [x] Preserve the current component's feature set and behavior unless a later approved task intentionally changes behavior:
  - imperative `setText(...)` and `focus(...)`
  - placeholder support
  - editable mode
  - auto-grow and height reporting
  - submit event behavior
  - current custom layout and measurement behavior
- [x] During extraction, compare the package shape against concrete ecosystem examples with explicit macOS support:
  - `../react-native-webview`
  - `../react-native-svg`
  - `../react-native-gesture-handler`
- [x] Use the actual `react-native-macos` implementation in `desktop/crystal-lattice-control-desktop-rn/node_modules/react-native-macos` as the behavioral reference for how stock macOS text inputs are structured and integrated.
- [x] Do not treat this task as the bugfix for spelling/grammar panels by itself. That issue should be handled as a separate behavior task unless the extraction work naturally exposes a harmless alignment improvement that is explicitly approved.
- [x] Design the package and task notes so future app-local custom components can be extracted using the same parent task directory and conventions.

## Current findings

- The current component is app-local:
  - JS wrapper: `desktop/crystal-lattice-control-desktop-rn/src/native/MacTextView.tsx`
  - native view manager: `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/MacTextViewManager.mm`
- The current implementation is a valid native component in the basic React Native sense, but it is packaged as app code rather than as a reusable library.
- The desktop app is using `react-native-macos` `^0.81.1`.
- The stock `react-native-macos` text input stack is more structured than the custom component:
  - multiline input uses `RCTUITextView`
  - single-line input uses `RCTUITextField` with the macOS field editor
  - text-input behavior is routed through `RCTBaseTextInputView`, `RCTBaseTextInputViewManager`, and related delegate adapters
- Real reusable package examples with explicit macOS support were inspected:
  - `../react-native-webview`
    - standalone package
    - `codegenConfig` in `package.json`
    - podspec with `:osx`
    - `example/macos`
  - `../react-native-svg`
    - standalone package
    - `react-native-builder-bob`
    - `codegenConfig`
    - podspec with `:osx`
    - macOS example apps
  - `../react-native-gesture-handler`
    - monorepo package layout
    - `packages/react-native-gesture-handler`
    - `codegenConfig`
    - podspec with `:osx`
    - `apps/macos-example`
- The extraction target shape agreed in discussion:
  - a dedicated package, likely under a reusable package area
  - Codegen-backed native component spec
  - podspec with macOS support
  - example app or example consumer

## Decisions captured so far

- `MacTextView` should become a real reusable package, not remain an app-local native bridge.
- The package should follow the New Architecture library shape used by modern React Native libraries, not the older app-only bridging pattern.
- macOS support should be declared at the package level and demonstrated with an example app or equivalent example target.
- This task is about extraction and packaging first. Behavioral changes, including the spelling/grammar panel issue, should stay separate unless explicitly folded in later.

## Implementation plan

This plan was added during task creation so the extraction direction is preserved for whoever implements it.

1. Choose the target package location and naming.
   - Prefer a reusable package path in this repo, for example under `packages/`.
   - Use a React Native library-style package name with a `react-native-...` prefix if the component is intended to be publishable/discoverable.

2. Scaffold the library in a New Architecture-friendly shape.
   - Add a standalone `package.json`.
   - Add `react-native`, `main`, `types`, and `files` fields.
   - Add `codegenConfig` with the native component spec source directory and Apple component provider mapping.
   - Decide whether to use `react-native-builder-bob` or a simpler in-repo build setup.

3. Create the JS/TS public API and Native Component spec.
   - Move the current `MacTextView` wrapper API into the package.
   - Replace app-local `requireNativeComponent(...)` usage with a Codegen native component spec.
   - Preserve the current imperative API if still needed, likely through Codegen native commands or a thin compatibility wrapper.

4. Move the Apple native implementation into the package.
   - Relocate `MacTextViewManager.mm` and any related native files into package-owned Apple source.
   - Register the component using the package’s New Architecture setup.
   - Keep behavior equivalent to the current component during the move.

5. Add macOS-specific packaging and linking support.
   - Add a podspec with explicit `:osx` support.
   - Mirror the shape used by `react-native-webview`, `react-native-svg`, or `react-native-gesture-handler` for Apple packaging.
   - Add any `react-native.config.js` metadata only if needed for non-Apple platforms or local example wiring.

6. Add an example consumer.
   - Prefer a macOS example app or example target owned by the package.
   - Ensure the example exercises focus, setText, auto-grow, placeholder, and submit behavior.

7. Integrate the desktop app with the new package.
   - Replace imports from the app-local native wrapper with imports from the extracted package.
   - Remove or deprecate the old app-local implementation once the package is wired in.

8. Verify New Architecture and macOS behavior.
   - Confirm Codegen runs correctly for the package.
   - Confirm the package builds under the app’s current `react-native-macos` version.
   - Smoke-test the extracted component in both the example app and the desktop app consumer.

9. Document the extraction pattern for future components.
   - Record the package conventions, folder structure, and required metadata so other custom components can be extracted consistently later.

## Execution plan

This execution plan was added during task completion before implementation began.

1. Create a new workspace package at `packages/react-native-mac-text-view` with minimal in-repo packaging conventions matching the existing workspace packages while adding the New Architecture metadata needed for a reusable native component library.
2. Add a Codegen native component spec and native commands spec for the macOS text view so the package is New Architecture-friendly and no longer depends on the app-local `requireNativeComponent(...)` registration model.
3. Refactor the current native behavior into package-owned Apple source:
   - extract the current AppKit text-view logic into a reusable content/view implementation
   - add a Fabric component view that hosts it and bridges generated props, events, and commands
4. Move the JS wrapper and public API into the package, preserving the current prop surface and imperative handle behavior used by the desktop app.
5. Add package-owned Apple integration files:
   - podspec with `:osx`
   - `react-native.config.js` if needed for library metadata
   - any generated-provider-compatible registration needed for the Fabric component
6. Add a lightweight package-owned example surface that can be used to validate the component contract and document intended usage.
7. Update the desktop app to consume `@crystal-lattice/react-native-mac-text-view` from the workspace package and remove the old app-local implementation from active use.
8. Run the highest-signal validation available in this repo:
   - TypeScript checks for the new package and updated consumer
   - macOS pod install for the desktop app
   - targeted smoke checks for imports/build wiring where feasible

## References

- Current app-local wrapper: `desktop/crystal-lattice-control-desktop-rn/src/native/MacTextView.tsx`
- Current app-local native manager: `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/MacTextViewManager.mm`
- Stock RN macOS multiline text input:
  - `desktop/crystal-lattice-control-desktop-rn/node_modules/react-native-macos/Libraries/Text/TextInput/Multiline/RCTUITextView.mm`
  - `desktop/crystal-lattice-control-desktop-rn/node_modules/react-native-macos/Libraries/Text/TextInput/RCTBaseTextInputViewManager.mm`
- Package examples:
  - `../react-native-webview/package.json`
  - `../react-native-webview/react-native-webview.podspec`
  - `../react-native-webview/src/RNCWebViewNativeComponent.ts`
  - `../react-native-svg/package.json`
  - `../react-native-svg/RNSVG.podspec`
  - `../react-native-svg/src/fabric/CircleNativeComponent.ts`
  - `../react-native-gesture-handler/packages/react-native-gesture-handler/package.json`
  - `../react-native-gesture-handler/packages/react-native-gesture-handler/RNGestureHandler.podspec`
  - `../react-native-gesture-handler/packages/react-native-gesture-handler/src/specs/RNGestureHandlerButtonNativeComponent.ts`

## Completion Notes

These notes were added during task completion after implementation and verification.

- Implemented a new reusable workspace package at `packages/react-native-mac-text-view`.
- Added New Architecture package metadata:
  - `packages/react-native-mac-text-view/package.json`
  - `packages/react-native-mac-text-view/CrystalLatticeReactNativeMacTextView.podspec`
  - Codegen native component spec in `packages/react-native-mac-text-view/src/specs/CLCMacTextViewNativeComponent.ts`
- Ported the current macOS text-view behavior into package-owned Apple native source:
  - `packages/react-native-mac-text-view/apple/CLCMacTextView.mm`
  - implemented as a Fabric component view plus package-owned AppKit content view
- Moved the public JS wrapper API into the package:
  - `packages/react-native-mac-text-view/src/MacTextView.tsx`
  - `packages/react-native-mac-text-view/src/index.ts`
- Added a package-owned example surface:
  - `packages/react-native-mac-text-view/example/MacTextViewExample.tsx`
  - `packages/react-native-mac-text-view/example/README.md`
- Updated the desktop app to consume `@crystal-lattice/react-native-mac-text-view` directly and made the old JS wrapper path a thin re-export for compatibility.
- Removed the old app-local `MacTextViewManager.mm` from the macOS Xcode target build so the new package owns the active native implementation path.

- Validation completed:
  - `npm install` in `desktop/crystal-lattice-control-desktop-rn`
  - `npx tsc -p packages/react-native-mac-text-view/tsconfig.json --noEmit`
  - `pod install` in `desktop/crystal-lattice-control-desktop-rn/macos`
  - `xcodebuild -workspace CrystalLatticeControlDesktopRN.xcworkspace -scheme CrystalLatticeControlDesktopRN-macOS -configuration Debug -sdk macosx build`

- Validation gap:
  - `npx tsc -p desktop/crystal-lattice-control-desktop-rn/tsconfig.json --noEmit` still reports existing unrelated type errors outside this extraction work, including files in `@crystal-lattice/frontend-sdk` and `src/ui/ActionResultInlineCard.tsx`.