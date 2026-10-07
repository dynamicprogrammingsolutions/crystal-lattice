# Connections on Home

This page describes the mobile Connections section on Home: saved-card actions,
navigation, responsive headers, settings-modal composition, and focused
verification. Bridge transport construction and recovery are documented
separately in [Bridge connection integration](bridge-connection-integration.md).

The Connections header uses the shared action bar with New connection pinned
and `showMenuButton={false}`. Its single action remains visible independently
of legacy header pin preferences. Global Settings and local provider settings
are available through the Home menu on the left; the former global
Home pinnable bar is removed, leaving the right-hand header area empty until
login is implemented.
Saved connection cards share a separate pin preference.
Only the active record is Open; inactive records are Closed. Open/Delete are
available for closed records, while Disconnect, Health Check, Server Settings,
and Delete are available for the active record. Health results and server
settings use the standard modal frame.

Pressing any saved connection card changes to Sessions immediately. If the
record is not active, opening begins without delaying navigation; pressing an
already-open card does not reconnect. The card's Open action uses a separate
callback and leaves the user on Home. Other card actions likewise do
not trigger card navigation.

Each card has a separate New session plus button. `ConnectedRoot` opens the
chosen connection if necessary, respects newer navigation intent, then
requests the existing Sessions agent picker. Sessions acknowledges the request
so it works on first mount and is not repeated after remounting.

`ConnectedRoot` owns one horizontal content gutter and compact top inset for
Home, Sessions, and Messages. Child screens must not add another
outer gutter. Connections and Sessions offset their visible titles by
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

`HomeConnectionsSection` sorts cards by `lastUsedAt`, initially renders up to
three, and owns the footer expansion state. Home supplies the collapse scroll
callback and keeps one outer scroll view. `ConnectionCard` preserves rendering
and action pinning; `useConnectionActions` owns health-check state and command
dispatch.

`ConnectionWizardModal` presents focused setup steps over the navigation
shell. App still owns connection records and transport/backend construction.
`useConnectionSetup` tracks a provisional transport and generation. Cancellation
invalidates pending results and cleans up the candidate, retaining the active
transport. Successful validation installs the new runtime and closes the old
transport. The wizard and bridge-repair paths use the same modal.

Maintainer entry points:

- `App.tsx`
- `src/ConnectedRoot.tsx`
- `src/connections/`
- `src/SessionsScreen.tsx`
- `src/responsiveHeaderActions.ts`
- `src/testing/MobileSessionListHarness.tsx`
- `src/testing/MobileConnectionsSettingsHarness.tsx`
- `e2e/sessionList.e2e.test.ts`
- `e2e/connectionsSettings.e2e.test.ts`
- `e2e/homeConnections.e2e.test.ts`

`MobileConnectionsSettingsHarness` mounts the production connected navigation
root, Connections section, settings modals, pinnable actions, and persistence
owners with deterministic connection data. The focused Detox scenario verifies
card versus Open-action navigation, action applicability, and modal
transitions. The bridge-transport Detox scenario separately verifies that the
production New Connection action still enters the connection wizard.

`npm run test:ios:home-connections` from the repository root runs the public
connection flow. It uses the production App, a real HTTP backend, and the
production SDK adapter, covering setup cancellation/failure, replacement,
collapse, session creation, and reopening after relaunch.
