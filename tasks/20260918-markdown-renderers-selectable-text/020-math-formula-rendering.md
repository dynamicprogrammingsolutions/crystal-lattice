# Math Formula Rendering in React Native Markdown Display

Add safe TeX formula parsing and rendering to the stable
`react-native-markdown-display` path, starting from the block formula shown in
the reported screenshot.

## Requirements checklist

- [ ] RNMD recognizes the approved TeX delimiter set without interpreting
      formulas as ordinary markdown text.
- [ ] Valid formulas render with theme-appropriate sizing and color on every
      required platform.
- [ ] Invalid, unsupported, or excessively costly formulas do not crash or hide
      message content and have a readable/copyable fallback.
- [ ] Formula rendering does not introduce a WebView scroll trap inside the
      transcript.
- [ ] Formula parsing and rendering are covered with the exact reported
      expression and representative delimiter/error cases.

Parent Task: `tasks/20260918-markdown-renderers-selectable-text/000-main.md`

## Open requirement questions

1. Is block math the initial requirement, or must inline formulas wrap and
   baseline-align with prose in the first release?
2. Should all common LLM delimiters be accepted:
   `\(...\)`, `\[...\]`, `$...$`, and `$$...$$`?
3. Must formula glyphs themselves be text-selectable, or is a selectable/copy
   source fallback and accessibility label sufficient?
4. Is offline-only rendering required? Recommendation: yes; chat rendering
   should not depend on a CDN.

## Reproduction and parser finding

With plain Markdown-It 10, the reported shape:

```tex
\[
Q_{\rm saved}=(U_{\rm old}-U_{\rm new})\times A\times72{,}000/1000
\]
```

is one ordinary paragraph. The backslashes escape `[` and `]`, while the TeX
body remains literal text. RNMD is therefore behaving consistently with its
unextended parser; styling changes alone cannot fix the issue.

RNMD exposes both a custom `markdownit` instance and custom render rules. A
local proof configured `markdown-it-math/no-default-renderer` with the
repository's current Markdown-It 10 and successfully emitted:

- `math_inline` for `\(...\)` and `$...$`;
- `math_block` for `\[...\]` and `$$...$$`.

The plugin's current package is ESM and developed against a newer Markdown-It,
so the proof establishes parser API compatibility, not Metro/Hermes support.
Its small ruler implementation could instead be adapted locally with license
attribution if dependency compatibility is poor.

## Formula engine research

| Candidate | Strength | Constraint |
| --- | --- | --- |
| MathJax 3 to SVG plus `react-native-svg` | Offline, no WebView, and `react-native-svg` officially supports iOS, Android, and macOS. The exact reported formula converted successfully in a local proof. | `mathjax-full` occupied about 34 MB unpacked in the proof; actual Metro bundle/startup and conversion cost must be measured. Inline placement inside RN text is unresolved. |
| `ratex-react-native` | Native iOS, Android, and macOS rendering, intrinsic metrics, baseline support, and inline attachments. Architecturally the best match. | Current release requires React Native >=0.84 and React >=19.2; this repo uses mobile RN 0.82.1 and desktop RN/RN-macOS 0.81.x with React 19.1.x. It is not directly installable. |
| Existing enriched-markdown math | Mobile fork already includes iosMath and optional AndroidMath code; the app currently disables it with `latexMath: false`. | No macOS backend and would couple the stable renderer to the experimental renderer's internals. |
| `react-native-math-view` | MathJax/SVG concept is proven and no WebView is needed on iOS. | Archived, last npm release in 2021, old architecture, and package exports only iOS/Android entry points. Not recommended directly. |
| Per-formula WebView/KaTeX | Mature browser rendering. | Heavy in a virtualized transcript and likely to recreate input/scroll interception; reject unless native/SVG spikes fail. |

The SVG proof produced a valid `<svg>` with no MathJax error node for the
reported expression. It did not test Hermes, Metro bundling, native layout,
selection, or long-transcript performance.

## Inline math constraint

Block formulas can be rendered as standalone measured SVG/native views. Inline
formulas are materially harder in the current app versions: RNMD wraps inline
children in a React Native `Text`, while an arbitrary SVG/native view cannot be
assumed to participate in portable text wrapping and baseline layout across
iOS, Android, and macOS.

Possible inline solutions are:

- a native text attachment/replacement span on all platforms;
- a compatible backport of a package such as RaTeX;
- integration with the sectioned native attributed-text prototype in subtask
  050;
- a flex-wrapped fragment layout, which is lower fidelity and can break normal
  word wrapping and selection.

Do not claim full inline support based only on successful token parsing.

## Execution plan

Status: Draft

First, create a renderer-independent math parser fixture around the RNMD
Markdown-It instance and lock down delimiter, escaping, currency, code-span,
fence, malformed-delimiter, and reported-expression behavior.

In parallel, prototype one block formula component behind a small
`MathFormula` interface. Prefer a MathJax-to-SVG proof on all three current
platform versions because it offers one rendering path without a WebView.
Measure cold conversion, cached conversion, bundle growth, dimensions, dark
mode, large formulas, and repeated formulas in a transcript. Cache by formula,
display mode, font size, and color.

If the spike passes, add `math_block` and approved inline rules to RNMD with a
plain TeX fallback on parse/render error. If true inline formulas are required,
pause product integration until one of the native attachment approaches proves
baseline alignment and wrapping on all required platforms.

The experimental enriched renderer may separately enable its existing math
flag, but that does not count as satisfying RNMD support.

### Implementation decisions and open questions

- Recommendation: accept both bracket and dollar delimiters, with conservative
  dollar rules that do not turn currency into formulas.
- Recommendation: ship block math first if allowed, and treat inline math as a
  separate acceptance boundary.
- Recommendation: avoid direct adoption of archived `react-native-math-view`;
  a maintained local abstraction or compatible native package is safer.
- Recommendation: preserve the original TeX and expose it through
  accessibility/copy behavior even when visual output is SVG.
- Questions 1–4 above must be resolved before final product acceptance is
  fixed.

### Documentation

- Document supported delimiters, inline/block behavior, fallback behavior, and
  unsupported TeX commands in mobile and desktop markdown guidance.
- If a shared formula package is introduced, document its engine, cache,
  sizing, accessibility, and platform matrix in that package.
- Record measured bundle/performance costs in package development
  documentation rather than user-facing syntax guidance.

### Task checklist

- [ ] Resolve initial block/inline scope and delimiter set.
- [ ] Add parser fixtures and choose/adapt a token-only math plugin.
- [ ] Build and measure a cross-platform block formula spike.
- [ ] Decide whether the formula engine is acceptable.
- [ ] Integrate RNMD math rules with error fallback and caching.
- [ ] Implement inline layout only if its native baseline/wrapping proof passes.
- [ ] Add unit, component, and native visual/layout tests.
- [ ] Update documentation.

### Requirement verification

- Render the exact reported heat-savings expression and verify that no literal
  `[`/`]` or raw TeX commands remain in the normal success view.
- Verify each approved delimiter, multiple formulas, formulas in lists and
  blockquotes, escaped delimiters, currency, code spans/fences, and malformed
  TeX.
- Verify light/dark colors, all supported markdown font sizes, horizontal
  overflow behavior, accessibility text, and copy/source fallback.
- Run the production renderer on iOS, Android, and macOS; parser-only snapshots
  are not sufficient.

### Additional implementation verification

- Capture cold/cached conversion timing and bundle-size delta.
- Stress repeated and unique formulas in a virtualized transcript and verify
  scrolling remains responsive.
- Confirm all rendering is offline and no formula content is sent to a remote
  service.