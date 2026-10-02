# Cross-Platform Native Selectable Markdown Repository

Define and, after architecture approval, build a separate reusable React Native
repository that parses markdown with an established parser and renders it with
native selectable text on iOS, Android, and macOS.

## Requirements checklist

- [ ] The native selectable markdown component is developed and maintained in a
      separate repository from the AI Agent Platform.
- [ ] The repository provides supported native implementations for iOS,
      Android, and macOS behind one documented React Native package API.
- [ ] The component provides good platform-native usability for reading,
      selecting, copying, scrolling, activating links, and interacting with
      supported complex renderers on iOS, Android, and macOS.
- [ ] The component is accessible through the supported platform assistive
      technologies and preserves meaningful markdown semantics, reading order,
      navigation, and interaction across its default and replacement
      renderers.
- [ ] Markdown interpretation is delegated to an established parser package
      that defines the source tokens/nodes; the repository does not depend on
      the full `react-native-markdown-display` rendering layer or implement its
      own markdown grammar.
- [ ] Native selection can span compatible markdown content with different font
      sizes and styles, including a selection beginning in a heading and
      continuing into body text, with standard platform selection usability.
- [ ] The component supports tables, code blocks, links, and math formulas on
      all supported platforms.
- [ ] Tables, code blocks, links, and math renderings can each be replaced
      through supported public component behavior without forking or replacing
      the markdown parser and the rest of the renderer.
- [ ] The repository contains runnable React Native sample projects covering
      iOS, Android, and macOS and demonstrating the most important scenarios
      and happy paths.
- [ ] Sample projects use the same public package components and the same
      table, code, link, and math renderer components/configuration used by
      Crystal Lattice; they do not contain sample-only copies of production
      rendering behavior.
- [ ] The repository contains Detox and XCTest coverage for the most important
      scenarios and happy paths, and those tests exercise the production
      package components used by Crystal Lattice.
- [ ] Crystal Lattice can consume the repository package and its selected
      renderer components without app-specific forks of the package.

Parent Task: `tasks/20260918-markdown-renderers-selectable-text/000-main.md`

## Requirement scope clarifications

The following are approved requirements or constraints:

- separate repository ownership;
- native iOS, Android, and macOS support;
- platform-native usability;
- platform accessibility and meaningful markdown semantics;
- an established markdown parser defining the nodes;
- native selection across differently sized compatible content;
- tables, code blocks, links, and math;
- replaceable rendering for those four feature areas;
- representative sample projects;
- Detox and XCTest coverage;
- samples and tests using the same production components as Crystal Lattice.

The requirements intentionally do not prescribe:

- the repository's internal package or directory layout;
- the number of sample applications;
- the renderer-replacement API shape;
- the native view composition strategy;
- which test runner covers each individual scenario;
- the exact test matrix beyond representative important scenarios and happy
  paths;
- the exact gestures, menu layout, accessibility implementation, or automation
  used to prove usability and accessibility;
- the implementation language used by each native platform.

Those are design and testing-strategy decisions that must be discussed before
they are added to an approved execution plan.

## Open requirement questions

1. Must one native selection remain continuous through tables, code blocks, and
   block math, or may intrinsically separate/scrollable renderers form explicit
   selection boundaries while preserving their own native selection/copy
   behavior?
2. Which React Native and React Native macOS versions form the initial support
   range? Recommendation: at minimum, the versions currently consumed by
   Crystal Lattice mobile and desktop.
3. Must math rendering be entirely offline, and which input delimiters are
   required (`\(...\)`, `\[...\]`, `$...$`, and `$$...$$`)?
4. Should XCTest coverage be required for both iOS and macOS native behavior,
   or is Detox on iOS plus XCTest/XCUITest on macOS the intended boundary?
5. What repository/package name, owner, license, and publication model should
   be used?
6. What Copy outputs and actions are required for full and partial selections:
   rendered plain text, original Markdown, rich text, or a user-visible choice
   among formats?

## Material design decisions to discuss

- Whether the separate repository contains one package or a small workspace of
  parser/model, native view, and default renderer packages.
- The platform-neutral node/document contract passed from the parser to native
  renderers.
- How replacement renderers are registered or supplied and whether replacement
  occurs at build time, component composition time, or runtime.
- Whether complex renderers participate inside one native attributed-text
  surface, use native text attachments, or mount separate native/React views.
- Which default table, code, link, and math renderer components the samples and
  Crystal Lattice share.
- How source ranges, native selection, Copy, link activation, accessibility,
  and streamed updates interact.
- Sample-project topology and the focused Detox/XCTest matrix.

No option above is approved merely by being listed.

## Usability requirement meaning

Usability is a user-visible completion outcome, while the mechanism used to
achieve it remains an implementation decision. At minimum, the requirement
means:

- selection starts, extends, adjusts, dismisses, and invokes the platform's
  expected native menu/handles without unusual gestures;
- a user can begin normal transcript/page scrolling over selectable markdown
  without an unintended child text or renderer scroll trap;
- deliberately scrollable content such as an overflowing table or code block
  has understandable parent-versus-child scrolling behavior;
- links remain discoverable and activatable while their visible text remains
  selectable;
- table, code, link, and math replacements do not create inconsistent or
  surprising interaction compared with the default components;
- resizing, orientation changes, and supported font-size changes preserve
  readable layout and operable selection.

The exact interaction design, native view hierarchy, gesture arbitration, and
test cases are not requirements until discussed and approved.

## Accessibility requirement meaning

Accessibility is also a public behavior requirement, not merely a testing
task. At minimum, the completed package must:

- expose content in logical reading order to VoiceOver on iOS/macOS and
  TalkBack on Android;
- preserve meaningful semantics for headings, paragraphs, lists, links,
  tables, code, and math rather than exposing an undifferentiated or empty
  native view;
- make interactive links and any interactive table/code/math controls
  discoverable and operable through assistive technologies;
- provide useful accessible content for formulas and non-text attachments;
- support the applicable platform keyboard/focus navigation, including macOS;
- respect the approved text scaling and contrast behavior;
- require replacement renderers to preserve the relevant accessibility
  contract rather than bypass it.

The exact accessibility tree, rotor/actions, labels, formula descriptions, and
automation strategy remain architecture/testing decisions.

## Copy capabilities and unresolved semantics

The native platforms can support more than one Copy policy:

- iOS `UITextView` exposes a selected attributed range. The installed enriched
  renderer demonstrates publishing plain text, Markdown, HTML, RTF, and RTFD
  representations together through `UIPasteboard`.
- Android selectable `TextView` exposes the selected character range and native
  selection action mode. The current selectable-code component copies selected
  plain text through `ClipboardManager`; custom actions or richer clipboard
  representations are possible but not currently selected.
- macOS `NSTextView` exposes native selection and `NSPasteboard`. The React
  Native macOS selectable paragraph implementation demonstrates rich-text
  pasteboard output in addition to normal native Copy behavior.

The product policy remains open:

- whether default Copy means rendered plain text or original Markdown;
- whether the menu offers separate actions such as Copy, Copy as Markdown, or
  Copy Rich Text;
- how partial selections containing math, images, table cells, or renderer
  boundaries map back to source;
- whether a replacement renderer supplies its own Copy behavior or participates
  in a package-wide source-range/copy contract;
- what happens when one visual selection cannot cross an independently mounted
  renderer boundary.

These are durable product questions and platform facts. The eventual pasteboard
formats, menu design, source mapping, and ownership are implementation
decisions.

## Parser boundary

The approved direction is analogous to the existing syntax-highlighting flow:

```text
Code source
  -> lowlight nodes
  -> compact syntax token contract
  -> native attributed text

Markdown source
  -> established markdown parser nodes
  -> compact native-renderer contract
  -> native attributed text/components
```

`react-native-markdown-display` delegates its actual parsing to the external
`markdown-it` package. Its remaining cleanup, `tokensToAST`, `AstRenderer`, and
React render rules are tailored to its own React component output and are not
needed by the new repository.

The current recommendation is to use a direct, pinned `markdown-it` dependency
because it is the parser already exercised by RNMD and the current mobile code.
It produces established block tokens and nested inline tokens. Some thin,
project-owned serialization or normalization is still necessary to create a
versioned, JSON-safe native boundary, but that layer must not reimplement
markdown parsing.

The exact parser version, extension/plugin set, and wire contract remain
implementation decisions for the architecture discussion.

## Native feasibility

### iOS

Feasibility is high. One non-editable, non-scrolling, selectable `UITextView`
backed by `NSMutableAttributedString` can natively select across different
fonts, sizes, styles, links, and paragraph boundaries. Fixed message width
allows TextKit to wrap and measure the actual attributed content through
`NSTextContainer` and `NSLayoutManager` without a global line-height
approximation.

The installed enriched-markdown implementation is a concrete proof of the
platform capability: it already applies mixed heading/body/list/code styles to
one selectable text view, measures at a finite width, custom-draws block
decorations, and supplies link, menu, and accessibility behavior. Its parser
and product maturity are separate concerns from this feasibility result.

### Android

Android `TextView` and `Spannable` support native selection across per-range
font sizes, styles, colors, links, paragraph spans, and replacement spans. The
existing selectable-code repository also demonstrates the React Native native
component, measurement, span, and selection foundation on Android. Full
markdown composition and complex-feature behavior still require a designed
implementation and native verification.

### macOS

AppKit `NSTextView`, `NSMutableAttributedString`, TextKit layout, and native
selection provide the corresponding macOS primitives. The existing
selectable-code repository does not yet contain an AppKit backend, but
`packages/react-native-mac-text-view` demonstrates a Fabric/Codegen macOS
component package consumed by Crystal Lattice desktop.

## Complex feature observations

- Wrapped syntax-colored code can participate in a continuous attributed-text
  selection. Independently horizontally scrolling code may require a separate
  renderer and selection boundary.
- Links are naturally represented by attributed ranges, but click/preview and
  drag-selection precedence needs a defined interaction contract.
- Inline images or formulas can potentially use native text attachments;
  meaningful Copy output then needs source mapping rather than the default
  object-replacement character.
- A visually faithful multi-column table is the clearest feature likely to need
  a separate renderer or a more specialized native composition.

These observations establish feasibility and tradeoffs. They do not approve an
architecture.

## Existing selectable-code repository conventions

The current `@ferenci84/react-native-selectable-code-block` repository is a
useful reference, not a mandatory template. It currently demonstrates:

- a TypeScript Codegen native-component spec and one JavaScript API;
- separate UIKit and Android native backends;
- native attributed/spanned text construction and measurement;
- autolinking metadata, podspec, Gradle package, and React Native config;
- a runnable example project;
- a pinned git dependency consumed by Crystal Lattice.

The new repository must additionally solve macOS support, markdown parsing,
replaceable complex renderers, representative cross-platform samples, and the
requested Detox/XCTest boundary.

## External implementation references

These references inform the later design discussion and are not requirements:

- React Native Codegen and typed native component specifications:
  `https://reactnative.dev/docs/the-new-architecture/pillars-codegen`
- React Native native-component guide:
  `https://reactnative.dev/docs/fabric-native-components-introduction`
- `create-react-native-library` scaffolding and example-app conventions:
  `https://github.com/callstack/react-native-builder-bob/blob/main/packages/create-react-native-library/README.md`
- React Native macOS implementation, examples, and platform documentation:
  `https://github.com/microsoft/react-native-macos`
- Detox setup and project integration:
  `https://wix.github.io/Detox/docs/introduction/getting-started`
- XCTest/XCUIAutomation UI testing:
  `https://developer.apple.com/documentation/xctest/user-interface-tests`

## Additional research concerns that are not requirements

The following concerns must be addressed during architecture and planning, but
they are not currently completion requirements:

- Graceful degradation: malformed markdown/math or an unavailable/failing
  replacement renderer should ideally retain readable source content rather
  than crash or hide the message.
- Renderer-contract evolution: a versioned compatibility boundary may be
  needed so independently replaceable table/code/link/math components do not
  become coupled to undocumented parser or native internals.
- Shared conformance fixtures: the repository samples and Crystal Lattice could
  consume a common fixture set to detect parser/configuration/renderer drift
  without making a particular fixture or test topology a requirement.
- Offline math: local rendering would improve privacy, reliability, and
  deterministic testing, but it remains an open product question rather than a
  requirement.
- Performance: parsing, native document construction, fixed-width layout,
  streaming updates, selection preservation, memory use, and virtualized-list
  recycling need measurement before implementation choices are accepted.
- Compatibility and release management: React Native, React Native macOS,
  parser, native renderer, and Crystal Lattice version compatibility need an
  explicit policy.

These concerns remain in the task even if the draft execution plan is removed.
They become requirements only through an explicit scope decision.

## Durable documentation expectations

Independent of the eventual architecture:

- the repository needs package-level guidance for installation, supported
  platforms, compatibility, public behavior, feature support, selection,
  usability, accessibility, renderer replacement, samples, and test commands;
- approved parser/model, native ownership, replacement boundaries,
  accessibility, measurement, Copy semantics, and testing strategy need
  development documentation;
- Crystal Lattice documentation needs to identify the consumed package
  version/source and the table, code, link, and math components/configuration
  shared with the samples.

## Execution plan

Status: Draft

The execution plan intentionally stops at an architecture approval gate.

First resolve the open requirement questions, then prepare a design proposal
covering repository/package boundaries, parser-to-native contract, continuous
selection boundaries, replaceable table/code/link/math rendering, default
Crystal Lattice components, sample consumers, test topology, compatibility,
usability, accessibility, Copy behavior, and performance risks. Compare
realistic alternatives and recommend one with explicit tradeoffs.

Present that proposal for user approval. Only after approval should this plan
be expanded with concrete repository creation, implementation sequencing,
platform ownership, sample applications, test scenarios, Crystal Lattice
integration, and release workflow.

### Implementation decisions and open questions

- Approved: use a separate repository with iOS, Android, and macOS
  implementations.
- Approved: use an established parser to define markdown nodes and avoid the
  full RNMD rendering layer.
- Approved: support native selection across differently sized compatible
  markdown content.
- Approved: platform-native usability is a completion requirement.
- Approved: accessibility and meaningful markdown semantics are completion
  requirements across default and replacement renderers.
- Approved: support replaceable tables, code blocks, links, and math.
- Approved: include representative sample projects plus Detox and XCTest
  coverage using Crystal Lattice's production components.
- Open: Copy semantics and all architecture/testing-strategy choices listed
  above.

### Documentation

- Fulfill the durable documentation expectations recorded before this plan.
- Add architecture-specific documentation only after the relevant design is
  approved.

### Task checklist

- [ ] Resolve the open requirement questions.
- [ ] Prepare architecture alternatives and tradeoffs without creating the
      repository or committing to an implementation.
- [ ] Include usability, accessibility, and Copy-policy alternatives in the
      design discussion.
- [ ] Discuss and obtain explicit approval for the selected architecture and
      testing strategy.
- [ ] Replace this architecture-gated draft with a concrete approved execution
      plan.
- [ ] Create and implement the separate repository only after that approval.
- [ ] Integrate the approved package and renderer components into Crystal
      Lattice.
- [ ] Complete requirement evidence and repository documentation.

### Requirement verification

- Repository boundary: inspect the external repository and package metadata;
  Crystal Lattice consumes it as a dependency rather than through copied source.
- Platforms: build and run the production package in representative iOS,
  Android, and macOS sample consumers.
- Selection: use native selection to copy a range spanning differently sized
  compatible markdown content on every supported platform.
- Usability: exercise native selection adjustment, parent/child scrolling,
  links, resizing, and the primary interactions of tables, code, and math on
  every supported platform.
- Accessibility: inspect and operate representative headings, lists, links,
  tables, code, and math through the approved assistive-technology boundaries
  on iOS, Android, and macOS.
- Copy: verify the approved full/partial selection outputs and actions,
  including selections involving supported complex renderers.
- Feature support: render representative tables, syntax-colored code blocks,
  links, inline math, and block math through the public package.
- Replacement: substitute each of the four feature renderings through the
  approved public behavior without forking parser/core code.
- Samples: confirm sample projects import the same production package entry
  points and default renderer components/configuration as Crystal Lattice.
- Tests: run the repository's Detox and XCTest suites and confirm they exercise
  representative production happy paths rather than sample-only renderers.
- Integration: render the same fixtures in Crystal Lattice and the sample
  projects with equivalent selected components/configuration.

### Additional implementation verification

- Measure parsing, native document construction, layout, scrolling, streaming
  updates, selection preservation, and memory use with representative and long
  messages.
- Verify malformed markdown/math fallback, accessibility, bidirectional text,
  dynamic type, dark mode, rotation/resizing, and virtualized-list recycling.
- Verify the package against the approved React Native/mobile and React Native
  macOS compatibility range.