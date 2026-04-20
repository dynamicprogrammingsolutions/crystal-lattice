# Align MacTextView With React Native macOS Text Input Behavior

Improve the extracted `MacTextView` package so it integrates more like a first-class React Native macOS text input, especially around spelling/grammar behavior, native text-system actions, and other text-input lifecycle details that the stock `react-native-macos` controls already manage.

## Requirements checklist

- [x] Parent Task: `tasks/20260419-react-native-macos-component-extraction/000-main.md`
- [x] Depends On: `tasks/20260419-react-native-macos-component-extraction/010-extract-mac-text-view-library.md`
- [x] Compare the extracted `MacTextView` implementation against the stock `react-native-macos` text-input stack, not just AppKit in isolation:
  - `desktop/crystal-lattice-control-desktop-rn/node_modules/react-native-macos/Libraries/Text/TextInput/Multiline/RCTUITextView.mm`
  - `desktop/crystal-lattice-control-desktop-rn/node_modules/react-native-macos/Libraries/Text/TextInput/Singleline/RCTUITextField.mm`
  - `desktop/crystal-lattice-control-desktop-rn/node_modules/react-native-macos/Libraries/Text/TextInput/RCTBaseTextInputView.mm`
  - `desktop/crystal-lattice-control-desktop-rn/node_modules/react-native-macos/Libraries/Text/TextInput/RCTBaseTextInputViewManager.mm`
- [x] Investigate and document which parts of the stock React Native macOS text-input behavior should be adopted by `MacTextView` and which parts should remain intentionally custom.
- [x] Improve spelling and grammar integration without assuming the feature should be globally disabled for the custom control.
- [x] Evaluate responder-chain and text-system action handling for the custom control, including:
  - spelling and grammar panels
  - substitutions panel
  - menu-item validation and enablement
  - native toggle actions for spelling, grammar, and substitution behaviors
- [x] Decide whether `MacTextView` should expose additional React-level props and events that better match React Native macOS text inputs, for example:
  - spell-check-related props
  - grammar-check-related props
  - native state-change events if AppKit toggles those features
- [x] Preserve the custom value of `MacTextView` as a multiline auto-grow editor with custom measurement behavior. Alignment should not force a rewrite into the stock RN text-input stack unless clearly justified.
- [x] Any fix for the spelling/grammar panel bug should prefer the narrowest solution that preserves useful text-checking functionality when possible.
- [x] If alignment work requires changing the public API of the extracted package, document compatibility and migration implications explicitly.

## Current findings

- The stock `react-native-macos` multiline text input uses `RCTUITextView`, which explicitly implements text-system toggle actions such as:
  - `toggleAutomaticSpellingCorrection:`
  - `toggleContinuousSpellChecking:`
  - `toggleGrammarChecking:`
- The stock RN macOS single-line text input uses `RCTUITextField`, which configures the field editor with spelling, grammar, and text-replacement settings while editing.
- The current app-local `MacTextView` is a more bare-metal standalone `NSTextView` wrapper and does not currently implement comparable action-handling or text-input integration surfaces.
- The earlier investigation concluded that the bug with `Spelling and Grammar` / `Languages` windows is likely tied to how the custom `NSTextView` participates in AppKit responder-chain behavior, not simply to whether spell checking exists.
- The extraction task intentionally keeps this behavior area unchanged so it can be addressed cleanly here afterward.

## Suggested exploration areas

- Determine whether the extracted package should implement explicit text-system toggle methods similar to `RCTUITextView`.
- Determine whether menu validation methods such as `validateUserInterfaceItem:` or related responder overrides should be added for the custom control.
- Determine whether the custom control should expose props aligned with RN macOS concepts like:
  - `autoCorrect`
  - `spellCheck`
  - `grammarCheck`
- Determine whether Fabric/Codegen commands or events are needed so JS can stay synchronized with native text-system state.
- Confirm whether there are harmless integration improvements beyond spelling behavior, such as focus/blur lifecycle details, selection handling, or responder semantics, that should be aligned with stock RN behavior.

## Implementation plan

This plan was added during task creation so the follow-up work is ready once extraction lands.

1. Re-read the extracted package implementation and the stock RN macOS text-input sources side by side.
2. Build a concrete gap list:
   - current custom behavior
   - stock RN macOS behavior
   - desired retained differences
3. Decide which behaviors should be aligned through:
   - added props
   - added events
   - responder/menu validation changes
   - native action handlers
4. Implement the smallest safe alignment changes first, prioritizing:
   - spelling/grammar/substitutions panel handling
   - native menu and responder integration
   - JS-visible prop/event parity where helpful
5. Add focused tests or example coverage for any new text-system behavior that becomes part of the package contract.
6. Document the resulting behavior clearly so consumers know where `MacTextView` intentionally matches or intentionally differs from stock RN text inputs.

## Execution plan

This execution plan was added during task completion before implementation began.

1. Update the extracted package's backing native text view so the first-responder object is a dedicated `NSTextView` subclass rather than a plain `NSTextView`.
2. Remove the hard-coded disabling of AppKit text-checking and substitution features that diverges from stock `react-native-macos` multiline input defaults.
3. Implement the same spelling/grammar toggle selectors that `RCTUITextView` defines on macOS:
   - `toggleAutomaticSpellingCorrection:`
   - `toggleContinuousSpellChecking:`
   - `toggleGrammarChecking:`
   - plus `setEnabledTextCheckingTypes:` alignment for data detectors
4. Keep the rest of the custom multiline editor behavior intact:
   - measurement
   - auto-grow
   - placeholder handling
   - submit behavior
   - focus behavior
5. Rebuild the macOS app and package integration to ensure the new package still compiles cleanly under Fabric/Codegen.
6. Leave broader responder/menu validation changes for a later step unless this RN-style action/default alignment proves insufficient.

## Completion Notes

These notes were added during task completion after the first alignment pass was implemented.

- Implemented a first RN-style alignment pass in `packages/react-native-mac-text-view/apple/CLCMacTextView.mm`.
- Replaced the plain backing `NSTextView` with a dedicated subclass used as the actual first responder for the custom control.
- Removed the hard-coded disabling of AppKit text-system features that diverged from stock `react-native-macos` multiline input defaults:
  - automatic quote substitution
  - automatic dash substitution
  - automatic text replacement
  - automatic spelling correction
  - continuous spell checking
  - grammar checking
- Added the same macOS text-system toggle methods that stock `RCTUITextView` implements:
  - `toggleAutomaticSpellingCorrection:`
  - `toggleContinuousSpellChecking:`
  - `toggleGrammarChecking:`
  - `setEnabledTextCheckingTypes:`
- Preserved the custom editor's measurement, auto-grow, placeholder, submit, and focus behavior.

- Validation completed:
  - `npx tsc -p packages/react-native-mac-text-view/tsconfig.json --noEmit`
  - `xcodebuild -workspace CrystalLatticeControlDesktopRN.xcworkspace -scheme CrystalLatticeControlDesktopRN-macOS -configuration Debug -sdk macosx build`

- Remaining work:
  - Manual verification of the Dock-icon spelling/grammar window repro is still required.
  - If the bug still reproduces, the next step is targeted responder/menu validation work rather than broader feature suppression.

These notes were expanded during follow-up implementation after reproducing the Dock-icon issue in the extracted package and comparing it with stock RN macOS inputs.

- Verified that the bug followed the standalone multiline `NSTextView` path rather than the single-line `NSTextField` / field-editor path used by the stock RN macOS `TextInput`.
- Implemented and kept the useful RN-style alignment in `packages/react-native-mac-text-view/apple/CLCMacTextView.mm`:
  - dedicated backing `NSTextView` subclass for the custom control
  - stock-like macOS text-system toggle methods:
    - `toggleAutomaticSpellingCorrection:`
    - `toggleContinuousSpellChecking:`
    - `toggleGrammarChecking:`
    - `setEnabledTextCheckingTypes:`
  - preservation of the custom multiline editor's measurement, auto-grow, placeholder, submit, and focus behavior
- Determined that the Dock-specific reopening behavior was not fully explained by the component alone. The actual app-level cause was the desktop app's custom Dock reopen behavior in `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/AppDelegate.mm`, which restored every key-capable window from `NSApp.windows`.
- Implemented the final Dock-reopen fix in `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/AppDelegate.mm`:
  - `applicationShouldHandleReopen:hasVisibleWindows:` now restores only tracked main windows from `self.mainWindows`
  - shared AppKit windows such as `Spelling and Grammar`, `Languages`, `Substitutions`, and other auxiliary windows are no longer revived by Dock clicks
- Implemented related transient popover cleanup in `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/DesktopWindowManager.mm`:
  - `actionsPopover` and `messageLimitPopover` now set `delegate = self`
  - `popoverDidClose:` now clears stored references for those popovers when they are dismissed by clicking outside
- The final behavior was verified manually with debug instrumentation and then cleaned up:
  - opening `Show Spelling and Grammar` on the custom multiline editor still works
  - switching away and back via the Dock no longer reopens `Languages`, `Spelling and Grammar`, or `Substitutions`
  - transient popovers dismissed by outside click no longer get revived by Dock reopen
  - temporary debug logging and comparison UI used during investigation were removed after verification
- Decided not to add new React-level spell-check/grammar props or events in this task. The final fix did not require public API changes to the extracted package.

- Final validation completed:
  - `npx tsc -p packages/react-native-mac-text-view/tsconfig.json --noEmit`
  - `xcodebuild -workspace CrystalLatticeControlDesktopRN.xcworkspace -scheme CrystalLatticeControlDesktopRN-macOS -configuration Debug -sdk macosx build`