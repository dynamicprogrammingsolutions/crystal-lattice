# Markdown Renderers and Selectable Native Text

Research and staged planning for configurable markdown/code rendering, math
formula support, selectable prose, cross-platform selectable code, and a
possible native selectable-markdown renderer across the mobile and macOS apps.

## Requirements checklist

- [ ] Mobile exposes markdown-renderer and code-block-renderer choices alongside
      the existing markdown typography settings; `react-native-markdown-display`
      is the stable default and the currently active enriched renderer is a
      secondary choice labeled explicitly `(experimental)`.
- [ ] Renderer choices are persisted, normalized from older saved settings, and
      honored by all in-scope markdown surfaces, with the selectable native code
      renderer used wherever its platform implementation is verified.
- [ ] The `react-native-markdown-display` path renders supported TeX formulas
      safely on the required platforms and falls back legibly for malformed or
      unsupported formulas.
- [ ] Rendered markdown prose is selectable on mobile and macOS without an
      inner selectable text control intercepting transcript scrolling.
- [ ] The existing selectable code-block package provides one public component
      contract backed by working iOS, Android, and macOS implementations.
- [ ] A separate reusable React Native markdown-component repository provides
      iOS, Android, and macOS implementations; native selection spans compatible
      differently sized markdown content, and tables, code blocks, links, and
      math are supported through replaceable rendering boundaries.
- [ ] The separate native markdown component provides platform-native usability
      and accessible semantic reading/navigation/interaction on iOS, Android,
      and macOS across both default and replacement renderers.

## Open requirement questions

1. Must the first math release support true inline formulas with surrounding
   prose, or is block math (`\[...\]` and `$$...$$`) sufficient initially?
   Inline baseline alignment and line wrapping materially change the renderer
   choice.
2. Are markdown-renderer and code-renderer selectors required only in the
   mobile Settings modal, or should the macOS Settings window also expose them?
   macOS currently has only one markdown renderer, but it will have at least two
   code-renderer paths once the native code component is ported.
3. Should the code-renderer selector expose all three implementations already
   represented in mobile code (`syntax-highlighter`, enriched renderer-owned
   code, and selectable native code), or only stable syntax-highlighter and
   selectable-native choices?
4. Should renderer preferences affect action-result markdown and other
   markdown-bearing surfaces as well as chat messages? Recommendation: yes, so
   the preference does not produce inconsistent rendering within one app.

## Scope and workstreams

| Workstream | Current finding | Readiness |
| --- | --- | --- |
| Renderer configuration | Mobile chat is fixed to enriched markdown while action cards use `react-native-markdown-display`; shared display preferences currently contain typography only. | Plan-ready after questions 2–3 are answered. |
| Math | RNMD accepts a custom Markdown-It instance and rules. The screenshot-style formula was successfully tokenized and converted to SVG in local research. | Block-math spike is plan-ready; inline scope is unresolved. |
| Selectable RNMD prose | RNMD already groups styled inline content under a root `Text`; React Native macOS has a non-scrolling native implementation for `Text selectable`. | Plan-ready, with native interaction verification. |
| Selectable code | The pinned package already contains iOS and Android implementations. Android needs product-level verification; macOS is absent. | Android verification is plan-ready; macOS port needs an ownership decision. |
| Native selectable markdown | The current code-block API assumes one font size, but iOS `UITextView`/TextKit natively supports selection across mixed-size attributed text. The installed enriched renderer already demonstrates this architecture. RNMD itself delegates parsing to `markdown-it`. | High iOS feasibility. Product requirements now call for a separate iOS/Android/macOS repository with representative sample apps, Detox/XCTest coverage, replaceable table/code/link/math rendering, and Crystal Lattice-identical production components. Architecture remains unapproved. |

## Research summary

- The active mobile message renderer is
  `SelectableMarkdownMessageContent`, backed by
  `react-native-enriched-markdown`. The older-named
  `MarkdownMessageContent`, backed by `react-native-markdown-display`, remains
  in use for mobile action displays and is the only desktop markdown renderer.
- RNMD does not own a separate markdown grammar implementation. It delegates
  parsing to its external `markdown-it` dependency, then performs
  React-renderer-specific token cleanup/grouping and converts the token stream
  to its own AST. A native renderer should consume `markdown-it` directly
  through a small shared normalization layer rather than depend on RNMD's
  React adapter.
- `SelectableMarkdownMessageContent` hard-codes
  `CODE_BLOCK_RENDERING_MODE = 'selectable-code-block'`. Its existing union also
  contains `syntax-highlighter` and `enriched-markdown`, which is the natural
  starting point for a persisted code-renderer preference.
- The shared preference owner is
  `packages/frontend-rn-components/src/markdownDisplayPreferences.tsx`.
  Mobile persists its value in AsyncStorage. Desktop separately persists and
  broadcasts settings through `NSUserDefaults`, `AppDelegate.mm`, and
  `DesktopWindowManager.mm`.
- The current formula is not recognized as math by plain Markdown-It. `\[`
  and `\]` are consumed as escaped literal brackets and the TeX body remains
  ordinary text.
- A local parser proof used `markdown-it-math/no-default-renderer` with the
  repository's Markdown-It 10 and produced `math_inline` and `math_block`
  tokens for `\(...\)`, `\[...\]`, `$...$`, and `$$...$$`.
- A local MathJax 3 proof converted the screenshot expression, including
  `\rm`, subscripts, `\times`, and `{,}`, to valid SVG without an error node.
  This proves formula compatibility, not React Native bundle/performance
  suitability.
- The current desktop raw-message `TextInput` is multiline and read-only but
  omits `scrollEnabled={false}`. React Native macOS maps that prop to its inner
  `RCTUIScrollView`; when disabled, the native scroll view forwards wheel input
  to its next responder. This is a high-confidence minimal correction that
  still requires an end-to-end macOS interaction test.
- RNMD's `textgroup` rule is the root `Text` for a styled inline group. Adding
  `selectable` there preserves nested bold/italic/link runs. Replacing leaf
  nodes with `TextInput` would not: `TextInput` cannot host RNMD's nested styled
  children.
- The pinned selectable-code package at commit
  `a06a5b6c0f5be9d247b090c0daa8f6dc05574909` uses:
  - iOS: `UITextView` plus `NSAttributedString` and a custom Fabric shadow-node
    measurement implementation;
  - Android: selectable `TextView` plus `SpannableStringBuilder` and a custom
    manager measurement function;
  - macOS: no implementation or pod platform declaration.
- The package's current run schema has one global font family, font size, and
  line height. Its iOS unwrapped measurement is explicitly
  `hard-line count × global line height`. Mixed heading/body sizes are
  therefore a material constraint of this component, but not of
  `NSAttributedString`, `NSTextView`/`UITextView`, or Android spans.
- The installed enriched-markdown iOS implementation is a concrete proof:
  it builds one mixed-style `NSMutableAttributedString`, displays it in one
  non-editable, non-scrolling, selectable `UITextView`, and measures it at a
  finite width through `NSLayoutManager`. Heading, paragraph, list,
  blockquote, inline-code, and wrapped code-block runs can therefore share one
  native selection.
- Fixed message width materially simplifies the generalized design. TextKit
  can lay out the complete attributed document in an `NSTextContainer` with
  the exact available width and effectively unlimited height; no
  equal-font-size or unbounded-width approximation is needed.

## Subtasks

- [ ] `tasks/20260918-markdown-renderers-selectable-text/010-configurable-renderers.md`
- [ ] `tasks/20260918-markdown-renderers-selectable-text/020-math-formula-rendering.md`
- [ ] `tasks/20260918-markdown-renderers-selectable-text/030-selectable-markdown-and-desktop-scroll.md`
- [ ] `tasks/20260918-markdown-renderers-selectable-text/040-universal-selectable-code-block.md`
- [ ] `tasks/20260918-markdown-renderers-selectable-text/050-cross-platform-native-selectable-markdown-repository.md`

## Execution plan

Status: Draft

Treat the work as shared rendering infrastructure with platform capability
adapters, not as independent conditionals in message bubbles. Land the
preference contract and stable RNMD default first, while retaining an explicit
fallback when a requested native code renderer is unavailable. Correct and
verify desktop wheel routing before expanding selectable controls. Verify the
existing Android code backend, then add macOS under the same package API.

Run the math parser/renderer spike independently. Block formula support may
proceed once its cross-platform rendering cost is acceptable; inline formulas
must wait for the scope decision and a proven baseline/wrapping strategy.

The native-markdown work now targets a separate reusable repository with iOS,
Android, and macOS implementations, sample consumers, and Detox/XCTest
coverage. It must support tables, code blocks, links, and math while allowing
those renderings to be replaced without replacing the markdown interpreter or
the rest of the component. The concrete parser contract, native view
composition, replacement mechanism, repository layout, samples, and test
matrix are material implementation decisions and must be discussed before they
are added to an approved plan.

### Implementation decisions and open questions

- Recommendation: persist renderer IDs in the shared markdown preference
  contract, but resolve them through a platform capability function so old
  settings and temporarily unsupported choices have deterministic fallbacks.
- Recommendation: use `react-native-markdown-display` as the default renderer
  ID and label enriched markdown `Enriched markdown (experimental)`.
- Recommendation: make selectable-native the preferred code renderer after
  each platform passes native verification; use syntax-highlighter as the
  fallback.
- Recommendation: use selectable RN `Text` groups as the near-term stable RNMD
  improvement, but do not treat per-group selection as satisfying the
  cross-size native-markdown goal. The iOS-first prototype should use one
  attributed `UITextView` selection surface. Reserve read-only `TextInput` for
  plain text because it cannot represent nested attributed markdown runs.
- Recommendation: make `markdown-it` a direct, pinned dependency of the shared
  parser/model owner. Do not rely on RNMD's transitive dependency or its
  React-specific `AstRenderer` internals.
- User-approved requirement: the native markdown component belongs in a
  separate repository and must ship iOS, Android, and macOS implementations,
  representative sample projects, and Detox/XCTest coverage using the same
  public components as Crystal Lattice.
- User-approved requirement: usability and accessibility are completion
  outcomes for the native markdown package, not optional implementation or
  testing tasks.
- Architecture for replaceable tables, code, links, and math remains a
  material open decision and is intentionally not approved by this draft.
- Open requirement questions are listed above. The native markdown component's
  separate-repository ownership is approved. Package ownership for the existing
  selectable-code macOS port remains a separate material decision in subtask
  040.

### Documentation

- Update shared markdown preference development documentation when renderer
  IDs and defaults become public shared behavior.
- Update mobile settings/message-rendering documentation with the stable and
  experimental choices and platform fallback behavior.
- Update desktop markdown preference documentation for selectable text, code
  renderer behavior, math support, and any new native package.
- Give any generalized native text/markdown package a package README and
  focused development page describing run/block contracts, measurement, and
  platform support.

### Task checklist

- [ ] Resolve the outcome-changing questions in this main task and affected
      subtasks.
- [ ] Complete and verify configurable renderer preferences.
- [ ] Correct desktop wheel routing and add selectable RNMD prose.
- [ ] Verify Android and implement/verify macOS selectable code.
- [ ] Complete the math parser/rendering spike and implement the approved math
      scope.
- [ ] Run the native selectable-markdown prototype and record the go/no-go
      decision.
- [ ] Update documentation and requirement evidence in every subtask.

### Requirement verification

- Renderer configuration: select each exposed option in production settings,
  relaunch, and verify all in-scope markdown surfaces use the persisted choice
  and explicit labels/defaults.
- Math: render representative valid, malformed, inline (if required), and block
  formulas through the production RNMD path on every required platform.
- Selection and scrolling: select styled prose and then scroll a long
  transcript with the pointer/touch beginning over selectable content.
- Code: select and copy syntax-colored ranges, toggle wrapping, and remount
  repeated code blocks on iOS, Android, and macOS.
- Native markdown feasibility: demonstrate mixed heading/body metrics,
  representative inline styles, correct fixed-width wrapping, and a single
  native selection dragged from a large heading into smaller body text.
  Separately verify recycling and the declared behavior for blocks that cannot
  remain in the same attributed text flow.
- Native markdown usability/accessibility: verify platform-native selection,
  scrolling, link and complex-renderer interaction, plus meaningful semantic
  reading/navigation through the approved assistive-technology boundaries.

### Additional implementation verification

- Run shared preference unit tests, mobile Jest/typecheck, desktop
  Jest/typecheck, focused iOS/Android Detox scenarios, and focused macOS
  XCUITests.
- Measure formula conversion time, cached rerender time, JS/native bundle
  impact, and long-transcript behavior before selecting a math engine.
- Keep a plain-text/raw fallback so parser or native renderer failures never
  hide message content.