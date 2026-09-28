# Markdown display and Connections hosting

Mobile loads one versioned markdown display preference record from
AsyncStorage before leaving the application loading boundary. The application
supplies the normalized value through the shared markdown preference provider.
Global Settings uses the standard `PanelModalFrame` and option-picker surfaces
to update the 14, 15 (Default), 16, or 17 font size, Normal/Small headers, the
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
Both the enriched selectable renderer and the RNMD renderer map the
shared semantic body and H1–H6 metrics to their renderer-specific style keys.

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

The Connections header uses the shared pinnable action bar for Global Settings
and New Connection. Saved connection cards share a separate pin preference.
Only the active record is Open; inactive records are Closed. Open/Delete are
available for closed records, while Disconnect, Health Check, Server Settings,
and Delete are available for the active record. Health results and server
settings use the standard modal frame.

Pressing any saved connection card changes to Sessions immediately. If the
record is not active, opening begins without delaying navigation; pressing an
already-open card does not reconnect. The card's Open action uses a separate
callback and leaves the user on Connections. Other card actions likewise do
not trigger card navigation.

`ConnectedRoot` owns one horizontal content gutter and compact top inset for
Home, Connections, Sessions, and Messages. Child screens must not add another
outer gutter. Connections and Sessions offset their visible screen titles by
the card content inset, and the Sessions search input uses the same content
inset, so screen titles, search placeholder text, and card titles share one
optical left edge.

The Sessions header shows the active saved-connection name, with `Sessions` as
the fallback when no matching record is available. Sessions and Messages use
one-line shrinkable titles beside responsive action bars. Mobile computes the
maximum compact pinned-action count from current window width, the common
screen gutter, a minimum useful title reservation, and complete shared action
slots. The shared bar independently keeps its triple-dot trigger in a fixed
non-shrinking slot; pins beyond the compact limit remain pinned and available
inside that menu.

Actions-menu panels constrain long titles to two lines before a fixed close
control. Mobile Connections supplies the same compact `x` close icon used by
Sessions and Messages.

Global Settings renders `OptionsPickerModal` as an overlay within its existing
native modal. Do not present the picker as a second nested React Native
`Modal`; iOS does not reliably present a second modal while the first remains
active.

Native verification uses `MobileConnectionsSettingsHarness`, which mounts the
production connected navigation root, Connections screen, settings modals,
pinnable actions, persistence owners, message footer, and markdown renderer
with deterministic connection data. The focused Detox scenario runs on iOS
and Android and verifies card versus Open-action navigation, action
applicability, modal transitions, typography and renderer preference
persistence, active markdown/code implementations, and screenshot-derived
prose/header/footer geometry. The bridge-transport Detox scenario separately
verifies that the production New Connection action still enters the connection
wizard.

Maintainer entry points:

- `App.tsx`
- `src/useMarkdownDisplayPreferences.ts`
- `src/markdownRendererPreferences.ts`
- `src/components/GlobalSettingsModal.tsx`
- `src/components/ConfiguredMarkdownMessageContent.tsx`
- `src/components/ConfiguredCodeBlock.tsx`
- `src/components/SelectableMarkdownMessageContent.tsx`
- `src/components/MarkdownMessageContent.tsx`
- `src/ConnectedRoot.tsx`
- `src/ConnectionsScreen.tsx`
- `src/SessionsScreen.tsx`
- `src/responsiveHeaderActions.ts`
- `src/testing/MobileSessionListHarness.tsx`
- `src/testing/MobileConnectionsSettingsHarness.tsx`
- `e2e/sessionList.e2e.test.ts`
- `e2e/connectionsSettings.e2e.test.ts`