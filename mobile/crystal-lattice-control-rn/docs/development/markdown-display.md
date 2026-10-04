# Markdown display

This page describes how the mobile application persists markdown display
preferences, resolves platform capabilities, and dispatches markdown and code
renderers. The shared React Native package owns the portable preference model.

Mobile loads one versioned markdown display preference record from AsyncStorage
before leaving the application loading boundary. The application supplies the
normalized value through the shared markdown preference provider. Global
Settings uses the standard `PanelModalFrame` and option-picker surfaces to
update the 14, 15 (Default), 16, or 17 font size, Normal/Small headers, the
markdown renderer, and the block-code renderer. Legacy 13 and 19 records
migrate to 14 and 17. Older typography-only records retain those values, gain
the renderer defaults, and are rewritten in normalized form.

The mobile renderer choices are:

- `React Native Markdown Display`, the stable default;
- `Enriched Markdown (experimental)`;
- `Selectable native code`, the requested default code implementation;
- `Syntax highlighter`.

The stored IDs are requested preferences. A mobile capability resolver derives
effective IDs without overwriting a known request. RNMD and syntax-highlighter
are stable fallbacks. Settings displays a fallback notice only when the
requested and effective values differ. Selectable native code is currently
verified and enabled on iOS. Android falls back to syntax-highlighter because
the existing native package's Fabric measurement path crashes when the
optional false `wrapLines` prop is absent; the native-code workstream owns
correcting that backend and enabling its capability.

The application overlays the selected shared typography preset on its
light/dark color theme. Message, footer, reasoning, tool, composer, settings,
actions, and code consumers use responsive semantic font-size and line-height
tokens; explicit card/screen/modal titles and layout dimensions remain fixed.
Both the enriched selectable renderer and the RNMD renderer map the shared
semantic body and H1–H6 metrics to their renderer-specific style keys.
For user messages, both renderers use `theme.bubbleUserText` for prose,
headings, list markers, links, and inline code. Raw user text and
bubble-owned header/footer copy use the same token. `textOnPrimary` remains
reserved for solid primary controls rather than the translucent light-theme
user bubble.

`ConfiguredMarkdownMessageContent` is the production dispatch boundary for
user/assistant chat markdown and markdown action-display bodies. Raw chat
messages and text-format action displays bypass it. Both markdown
implementations send fenced and indented block-code segments through
`ConfiguredCodeBlock`, which selects the existing native selectable component
or the syntax-highlighter component. Inline code remains part of each markdown
renderer's prose layout. Syntax-highlighted code passes the semantic `code`
font size and line height directly to the `feature/native-line-height` branch
of the `ferenci84/react-native-syntax-highlighter` fork.

Session cards use semantic typography from the selected preset: `large` for
the title, `normal` for the subtitle or preview, `small` for the session ID,
and `tiny` for metadata. Each field uses the corresponding semantic line
height. Component and native geometry tests obtain expectations from the
selected preset or compare rendered bounds; they do not copy the preset's
numeric entries.

See the shared React Native
[markdown display preferences](../../../../packages/frontend-rn-components/docs/development/markdown-display-preferences.md)
for the portable preference and typography contract.

Maintainer entry points:

- `src/useMarkdownDisplayPreferences.ts`
- `src/markdownRendererPreferences.ts`
- `src/components/GlobalSettingsModal.tsx`
- `src/components/ConfiguredMarkdownMessageContent.tsx`
- `src/components/ConfiguredCodeBlock.tsx`
- `src/components/SelectableMarkdownMessageContent.tsx`
- `src/components/MarkdownMessageContent.tsx`
- `src/testing/MobileConnectionsSettingsHarness.tsx`
- `e2e/connectionsSettings.e2e.test.ts`

The focused native scenario verifies preference persistence, active
markdown/code implementations, and screenshot-derived prose, header, and
footer geometry on iOS and Android.
