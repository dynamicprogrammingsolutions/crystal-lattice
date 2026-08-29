# Markdown display and Connections hosting

Mobile loads one versioned markdown display preference record from
AsyncStorage before leaving the application loading boundary. The application
supplies the normalized value through the shared markdown preference provider.
Global Settings uses the standard `PanelModalFrame` and option-picker surfaces
to update the 14, 15 (Default), 16, or 17 font size and Normal/Small headers.
Legacy 13 and 19 records migrate to 14 and 17 and are rewritten in normalized
form.

The application overlays the selected shared typography preset on its
light/dark color theme. Message, footer, reasoning, tool, composer, settings,
actions, and code consumers use responsive semantic font-size and line-height
tokens; explicit card/screen/modal titles and layout dimensions remain fixed.
Both the enriched selectable renderer and the legacy markdown renderer map the
shared semantic body and H1–H6 metrics to their renderer-specific style keys.

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

Global Settings renders `OptionsPickerModal` as an overlay within its existing
native modal. Do not present the picker as a second nested React Native
`Modal`; iOS does not reliably present a second modal while the first remains
active.

Native verification uses `MobileConnectionsSettingsHarness`, which mounts the
production connected navigation root, Connections screen, settings modals,
pinnable actions, persistence owners, message footer, and markdown renderer
with deterministic connection data. The focused Detox scenario runs on iOS
and Android and verifies card versus Open-action navigation, action
applicability, modal transitions, preference and pin persistence, and
screenshot-derived prose/header/footer geometry. The bridge-transport Detox
scenario separately verifies
that the production New Connection action still enters the connection wizard.

Maintainer entry points:

- `App.tsx`
- `src/useMarkdownDisplayPreferences.ts`
- `src/components/GlobalSettingsModal.tsx`
- `src/components/SelectableMarkdownMessageContent.tsx`
- `src/components/MarkdownMessageContent.tsx`
- `src/ConnectedRoot.tsx`
- `src/ConnectionsScreen.tsx`
- `src/testing/MobileConnectionsSettingsHarness.tsx`
- `e2e/connectionsSettings.e2e.test.ts`