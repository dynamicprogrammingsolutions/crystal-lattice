# Align MacTextView With React Native macOS Text Input Behavior

Improve the extracted `MacTextView` package so it integrates more like a first-class React Native macOS text input, especially around spelling/grammar behavior, native text-system actions, and other text-input lifecycle details that the stock `react-native-macos` controls already manage.

## Requirements checklist

- [ ] Parent Task: `tasks/20260419-react-native-macos-component-extraction/000-main.md`
- [ ] Depends On: `tasks/20260419-react-native-macos-component-extraction/010-extract-mac-text-view-library.md`
- [ ] Compare the extracted `MacTextView` implementation against the stock `react-native-macos` text-input stack, not just AppKit in isolation:
  - `desktop/crystal-lattice-control-desktop-rn/node_modules/react-native-macos/Libraries/Text/TextInput/Multiline/RCTUITextView.mm`
  - `desktop/crystal-lattice-control-desktop-rn/node_modules/react-native-macos/Libraries/Text/TextInput/Singleline/RCTUITextField.mm`
  - `desktop/crystal-lattice-control-desktop-rn/node_modules/react-native-macos/Libraries/Text/TextInput/RCTBaseTextInputView.mm`
  - `desktop/crystal-lattice-control-desktop-rn/node_modules/react-native-macos/Libraries/Text/TextInput/RCTBaseTextInputViewManager.mm`
- [ ] Investigate and document which parts of the stock React Native macOS text-input behavior should be adopted by `MacTextView` and which parts should remain intentionally custom.
- [ ] Improve spelling and grammar integration without assuming the feature should be globally disabled for the custom control.
- [ ] Evaluate responder-chain and text-system action handling for the custom control, including:
  - spelling and grammar panels
  - substitutions panel
  - menu-item validation and enablement
  - native toggle actions for spelling, grammar, and substitution behaviors
- [ ] Decide whether `MacTextView` should expose additional React-level props and events that better match React Native macOS text inputs, for example:
  - spell-check-related props
  - grammar-check-related props
  - native state-change events if AppKit toggles those features
- [ ] Preserve the custom value of `MacTextView` as a multiline auto-grow editor with custom measurement behavior. Alignment should not force a rewrite into the stock RN text-input stack unless clearly justified.
- [ ] Any fix for the spelling/grammar panel bug should prefer the narrowest solution that preserves useful text-checking functionality when possible.
- [ ] If alignment work requires changing the public API of the extracted package, document compatibility and migration implications explicitly.

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