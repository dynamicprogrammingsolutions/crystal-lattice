# Universal Selectable Code Block

Verify the existing Android backend and add a macOS backend to the current
selectable syntax-colored code component under one public JavaScript contract.

## Requirements checklist

- [ ] The same `SelectableCodeBlockView` public API renders and measures
      syntax-colored selectable text on iOS, Android, and macOS.
- [ ] Users can select a substring and invoke Copy through each platform's
      native selection interaction.
- [ ] Wrapped and unwrapped code, horizontal/vertical containers, repeated
      remounts, and long code blocks preserve correct geometry.
- [ ] The component does not capture parent vertical transcript scrolling when
      its own vertical scrolling is disabled.
- [ ] Mobile and desktop use the native selectable code renderer wherever its
      backend has passed verification.

Parent Task: `tasks/20260918-markdown-renderers-selectable-text/000-main.md`

## Open design decision

Choose package ownership before the macOS port:

- continue development in the external
  `@ferenci84/react-native-selectable-code-block` repository and update the
  pinned commit; or
- move/generalize it under this monorepo's `packages/` so mobile, desktop, and
  native tests evolve atomically.

This changes module ownership and release workflow, so it should be approved
rather than inferred.

## Existing platform assessment

### iOS

- Fabric component backed by a non-editable, non-scrolling `UITextView`.
- Builds one `NSAttributedString` from JSON token runs.
- Custom selection menu currently allows Copy.
- Custom measurable shadow node handles wrapped and unwrapped geometry.
- Existing mobile regression coverage checks rendering/geometry/remounting;
  user reports selection works well.

### Android

Android is already implemented in the pinned package, contrary to the initial
appearance of its package root:

- selectable native `TextView`;
- `SpannableStringBuilder` with foreground/background color, typeface,
  bold/italic, and underline spans;
- wrap toggle through horizontal-scrolling behavior;
- custom selection action mode and clipboard handling;
- custom React Native manager measurement;
- generated/build artifacts show the current backend has compiled locally.

The app already defines
`detox:test:selectable-code-block:android`. Its current E2E scenario verifies
native frames, visible painted text, and repeated remounts, but it does not
prove dragging a selection range or invoking the native selection menu.
Android is therefore feasible and implemented, but not yet accepted at the
same interaction level as iOS.

### macOS

There is no macOS backend:

- the podspec declares iOS only;
- Apple source imports UIKit and uses `UITextView`/`UIPasteboard`;
- JS dispatches direct selection callbacks only for `Platform.OS === 'ios'`;
- desktop has no dependency on the package.

## macOS port shape

Use the same token JSON and JS props with an AppKit component:

- `NSTextView`, non-editable and selectable, with an
  `NSMutableAttributedString`;
- no internal `NSScrollView` for the leaf text view, or explicit wheel
  forwarding if a clip/scroll view is unavoidable;
- `NSPasteboard` and the standard Copy action;
- AppKit TextKit measurement for wrapped and unwrapped content;
- conditional Apple source or separate iOS/macOS source files behind the same
  generated component name.

`packages/react-native-mac-text-view` is a useful in-repo reference for the
React Native macOS Fabric/pod shape, but its editable composer behavior should
not be copied wholesale because it owns an internal `NSScrollView`.

A universal component means one JS/package contract with platform-native
backends. Literal sharing of UIKit, AppKit, and Android view source is neither
necessary nor realistic.

## Feasibility assessment

- Android: high; verification and likely small fixes only.
- macOS: high for the current uniform-font code model. AppKit attributed text
  and selection are direct equivalents to the iOS design.
- Shared source compatibility: medium. Mobile uses RN 0.82 while desktop uses
  RN/RN-macOS 0.81.x, so codegen and component registration must be built in
  both consumers.

## Execution plan

Status: Draft

Run the existing Android harness first and add an interaction-level check for
native selection/copy. Fix Android only where real device/emulator behavior
fails; do not replace its existing span implementation without evidence.

After package ownership is approved, add macOS platform metadata and an AppKit
component using the same token schema. Port measurement with native attributed
layout, then integrate the package and the themed `SelectableCodeBlock`
wrapper into desktop RNMD fence rules. Extend the desktop transcript harness
to cover selection, wrap toggling, parent scroll, horizontal scrolling, and
recycling.

Keep syntax tokenization in JavaScript unless profiling shows it is the
bottleneck; native backends should remain presentation/selection primitives.

### Implementation decisions and open questions

- Package ownership is the blocking material decision.
- Recommendation: retain one API and token schema with separate native
  backends.
- Recommendation: replace Android's global `DeviceEventEmitter` callback with
  the generated direct event if current React Native codegen supports it
  consistently; do this only with cross-version tests.
- Recommendation: use Menlo on macOS through the wrapper while retaining the
  package's generic font-family prop.
- Decide whether partial-selection Copy is the only native menu item or whether
  future actions belong in the generic API.

### Documentation

- Update the package README with an honest iOS/Android/macOS support matrix,
  architecture requirements, props, selection events, and measurement model.
- Document app-level toolbar Copy versus native partial-selection Copy.
- Update desktop markdown documentation when native code becomes the default.

### Task checklist

- [ ] Approve package ownership.
- [ ] Run and strengthen Android native verification.
- [ ] Fix any demonstrated Android layout/selection issues.
- [ ] Add the AppKit component and macOS package integration.
- [ ] Add desktop wrapper/theming/toolbars and RNMD code rules.
- [ ] Add iOS, Android, and macOS interaction/geometry regression coverage.
- [ ] Make capability resolution mark all passing platforms supported.
- [ ] Update documentation.

### Requirement verification

- On each platform, drag-select a strict substring spanning differently colored
  tokens, invoke native Copy, and verify only that substring is copied.
- Toggle wrapping for long lines and verify complete text, correct dimensions,
  and expected horizontal-scroll behavior.
- Remount at least five long blocks repeatedly and verify nonzero native frames
  and visible glyphs.
- Start vertical transcript scrolling over the native code text and verify the
  approved parent/child scroll behavior.
- Verify dark/light token colors and all supported code font sizes.

### Additional implementation verification

- Build the package through both the mobile RN 0.82 and desktop RN-macOS 0.81
  consumers.
- Run focused mobile Jest plus iOS/Android Detox and a focused macOS XCUITest.
- Test large token payload serialization and update/recycle behavior for
  regressions in chat-list performance.