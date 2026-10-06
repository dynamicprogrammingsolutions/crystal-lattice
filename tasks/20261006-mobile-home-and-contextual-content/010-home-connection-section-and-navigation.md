# Move Connection Management onto Home

Make connection setup and switching discoverable at the top of Home, remove
the separate Connections bottom tab, and retain the existing connection and
session workflows. This is independently useful before contextual guidance
is adopted.

## Requirements checklist

- [ ] H1 — The first Home section provides connection management and state;
  the bottom navigation no longer contains Connections.
- [ ] H2 — Users can create, open/switch, reconnect, disconnect, and remove
  saved connections, and reach connection/server/global settings through
  Home. The existing iOS Local agent entry and available connection methods
  remain accessible.
- [ ] H3 — Existing connection records, transport behavior, cached sessions,
  Watchlist/Recent navigation, selected sessions, and relaunch persistence
  remain compatible with the navigation change.

Parent Task: tasks/20261006-mobile-home-and-contextual-content/000-main.md

Depends On:
tasks/20260910-ios-embedded-runtime-poc/027-local-agent-provider-settings-usability.md

This dependency preserves the user's first-round priority and supplies the
approved Local agent/settings names. There is no dependency on `020`;
contextual-content adoption belongs to `030`.

## Open questions

- Should tapping a closed connection open it and navigate to Sessions, as
  connection-card navigation currently does, or open it while remaining on
  Home? Recommendation: retain explicit Open as an action that stays on Home,
  and card navigation as the path to Sessions; confirm the interaction before
  implementing it.
- Should the top section initially show all saved connection cards, or the
  active connection plus a compact list/expand affordance? Recommendation:
  a compact presentation that keeps the active connection and setup actions
  visible without pushing Watchlist/Recent far down. The exact initial
  presentation is not settled.
- Recommendation: host the existing connection wizard in an app-owned
  modal/sheet opened from Home. Confirm this presentation; the request
  settles location but not modal versus in-place wizard behavior.

## Supporting facts

- `App.tsx` owns persisted connections, selection, connection wizard state,
  and creation of `Transport` and `RestAgentBackend`. That ownership need
  not move into Home.
- `ConnectedRoot.tsx` starts on Home and keeps tab contents mounted. New
  connection requests currently navigate to the Connections tab, where
  either the wizard or `ConnectionsScreen` is displayed.
- `ConnectionsScreen.tsx` already provides production connection cards and
  their action menus. It embeds its own list ScrollView, so simply nesting
  the whole screen in Home would introduce competing scroll regions.
- Home's Watchlist drag geometry depends on measured card and scroll
  positions. Adding a section above it must not assume the old vertical
  offsets.
- Existing `home.e2e.test.ts` and `connectionsSettings.e2e.test.ts` render
  production screens with deterministic native harness state. They cover UI
  interaction and geometry, not a real connection to a backend.

## Execution plan

Status: Draft

### Component and lifecycle responsibilities

Extract the reusable connection card/list content from the current screen
into a Home section. Keep one Home scroll owner and preserve connection
actions, pinning, and production entity IDs. Select the section density only
after the recorded UX decision.

Keep `App.tsx` as the connection/wizard authority. `ConnectedRoot.tsx` owns
navigation and modal coordination, passing existing lifecycle callbacks into
Home. Move wizard presentation to the agreed Home-owned surface and replace
references to the removed tab in placeholders, tests, and navigation.

Opening/switching continues through the existing transport construction and
saved-record code. Preserve pending-navigation intent handling and cached
connection/session identities. Do not add automatic connection selection or
change reconnect/failure policies as part of moving the controls.

Provide an independently testable Home navigation slice with the existing
empty labels/actions where necessary. `030` replaces them with the shared
contextual presentation after `020`; do not create a parallel guidance
component here.

### Delivery steps

1. Update focused production shell/connection tests for the removed tab and
   new Home entry points.
2. Extract and integrate connection content, keeping lifecycle ownership and
   safe scrolling/drag behavior.
3. Move the wizard host and update navigation references/affected native
   harnesses.
4. Prove a real server connection and session journey from Home, then update
   current mobile navigation documentation.

### Implementation decisions and open questions

- Open decisions are card/Open interaction, section density, and wizard
  presentation as listed above. Resolve them before execution.
- Preserve saved IDs, existing transport semantics, pinning preferences, and
  connection deletion behavior. Native folders and provider settings are not
  part of this delivery.
- Shared mobile changes retain Android support. Native testing uses the iOS
  simulator and supported Android emulator path.

### Documentation

Update `mobile/crystal-lattice-control-rn/docs/home.md` and the applicable
README/development navigation guidance to describe the new Home entry points.
Remove current instructions that direct users to the deleted tab. Keep
first-round authentication/reviewer wording owned by subtask `027`.

### Task checklist

- [ ] Confirm the Home interaction/density/wizard choices and execution plan.
- [ ] Extract production connection controls into the top Home section.
- [ ] Move wizard presentation and remove Connections-tab navigation.
- [ ] Preserve saved connection/session state and Home drag behavior.
- [ ] Update affected component/native tests and pass the real connection
  journey.
- [ ] Update maintained mobile navigation documentation and requirement
  evidence.

### Requirement verification

- **H1/H2:** component and native UI checks prove section ordering, removed
  tab, action availability, wizard presentation/cancellation, and settings.
  Retain the existing Home and connection-action consumers as regressions.
- **H2/H3 — decisive `Home connection public flow`:** add a Detox scenario
  starting a local real HTTP server with the existing
  `startBackendServer` harness. Launch the production app without substituting
  connection callbacks, use Home's manual connection wizard with that
  server's address, open the connection, create a session through the normal
  agent picker, and confirm it through `RestAgentBackend`. Relaunch and
  reopen the same saved connection/session. This crosses App transport
  creation, public backend routes, and production navigation together.
  No hosted model or production server is necessary.
- Planned decisive invocation, from the mobile package:
  `npx detox test -c ios.sim.release e2e/homeConnections.e2e.test.ts --cleanup`.
  Add the named scenario during execution; lack of an existing harness
  consumer does not waive the actual connection boundary.

### Additional implementation verification

Run the affected mobile Jest/TypeScript checks and existing Home native
geometry/Watchlist scenario. Check that new top content does not displace
drag calculations or create nested full-screen scroll owners. Native
harness-only runs are reported separately from the real HTTP scenario.