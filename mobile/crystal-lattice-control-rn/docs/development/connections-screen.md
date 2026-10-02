# Connections screen

This page describes the mobile Connections screen: saved-card actions,
navigation, responsive headers, settings-modal composition, and focused
verification. Bridge transport construction and recovery are documented
separately in [Bridge connection integration](bridge-connection-integration.md).

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

Maintainer entry points:

- `App.tsx`
- `src/ConnectedRoot.tsx`
- `src/ConnectionsScreen.tsx`
- `src/SessionsScreen.tsx`
- `src/responsiveHeaderActions.ts`
- `src/testing/MobileSessionListHarness.tsx`
- `src/testing/MobileConnectionsSettingsHarness.tsx`
- `e2e/sessionList.e2e.test.ts`
- `e2e/connectionsSettings.e2e.test.ts`

`MobileConnectionsSettingsHarness` mounts the production connected navigation
root, Connections screen, settings modals, pinnable actions, and persistence
owners with deterministic connection data. The focused Detox scenario verifies
card versus Open-action navigation, action applicability, and modal
transitions. The bridge-transport Detox scenario separately verifies that the
production New Connection action still enters the connection wizard.
