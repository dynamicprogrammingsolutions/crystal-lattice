# Global Attention Frontend Integration

Present eligible notification attention as temporary application-wide overlays
across all open mobile and desktop connections, with explicit navigation and
local acknowledgement.

## Requirements checklist

- [ ] Mobile and desktop can present an eligible attention banner over the
  current application regardless of which screen is visible.
- [ ] Important notifications from an unfocused session or open connection
  retain their source identity and can be presented without changing focus.
- [ ] A View action explicitly focuses/navigates to the owning
  connection/session through the platform connection lifecycle.
- [ ] Timeout, close, or upward swipe removes only the temporary attention
  presentation and leaves the authoritative notification unchanged.
- [ ] Attention preferences apply consistently to request lifecycle and other
  important notification transitions.
- [ ] Visual and native verification covers overlay placement, timing,
  dismissal gestures, source labels, stacking/queuing, and cross-connection
  navigation.

Parent Task: `tasks/20260824-operational-notifications-and-global-attention/000-main.md`

Depends On:

- `tasks/20260824-operational-notifications-and-global-attention/020-global-attention-contract-and-delivery.md`
- `tasks/20260824-operational-notifications-and-global-attention/030-request-operation-notifications-and-status.md`
- `tasks/20260823-frontend-connection-lifecycle/060-mobile-multiple-open-connections.md`
- `tasks/20260823-frontend-connection-lifecycle/070-desktop-connection-workspace-ux.md`

## Supporting details

- Mobile task 060 owns the shared runtime map, all-open-backend exposure,
  focus independent from runtime state, and cross-runtime display/deep-link
  lookup.
- Desktop task 070 owns convergence on the shared lifecycle controller while
  preserving multiple open runtimes and cross-connection workspaces.
- Existing owning-surface notification banners participate in layout and push
  content down. Global attention is a distinct temporary overlay above the
  application content.
- Existing normal notification dismissal is server-authoritative. Attention
  acknowledgement is intentionally local and must use different commands and
  copy.
- A connection may be open but unfocused. Notification arrival from that
  runtime may present attention but may not navigate.
- After process restart, only currently opened/reopened runtimes can provide
  in-app live attention; this task does not introduce push notifications or
  automatically reopen saved connections.

## Execution plan

Status: Draft

Add one root attention coordinator per frontend host. It consumes:

- the set of open connection IDs and backends from the connection lifecycle;
- one attention controller per open backend;
- local acknowledgement state and attention preferences;
- current focused connection/session state.

The coordinator deduplicates and orders eligible items across connections,
suppresses items according to visibility and preferences, and sends a bounded
queue to a shared attention overlay component.

The overlay appears inside the full application safe/native window boundary,
above the current screen rather than in the owning screen's normal-flow
notification rail. It supports:

- source connection label when needed;
- concise title/body and semantic variant;
- automatic timeout;
- explicit local Close;
- upward swipe on touch platforms;
- View when an owning destination exists;
- accessible announcements and controls.

View calls the existing connection lifecycle/focus APIs using the attention
envelope's connection and optional session identity. If the runtime is no
longer open, the frontend may still focus cached workspace according to the
connection-lifecycle contract and offer its normal reconnect action. The
attention host does not silently open a connection.

Mobile must subscribe to all user-open runtimes through the task-060 runtime
map. Desktop uses the shared-controller runtime map after task 070. Runtime
close disposes only that connection's attention subscription and leaves
acknowledged tokens and authoritative server records intact.

Add shared component tests and platform-native screenshot/geometry tests.
Detox should verify full-screen overlay placement, upward swipe, focus
preservation on arrival, and explicit navigation on View. macOS tests should
verify cross-connection source labels, focus preservation, timeout/Close, and
View navigation using production host surfaces.

### Implementation decisions and open questions

- **Decided:** Global attention is an overlay and does not push Sessions or
  Messages content down.
- **Decided:** Arrival never focuses or navigates. View is the only standard
  navigation action.
- **Decided:** Closing/swiping/timing out uses attention-specific local
  acknowledgement wording and behavior, not Dismiss.
- **Decided:** The host observes only runtimes already open under the
  connection-lifecycle policy.
- **Recommendation:** Show one attention item at a time with a short queue and
  coalesce superseded tokens from the same lifecycle item.
- **Recommendation:** Acknowledging by View also records the attention token
  as seen.

### Documentation

- Update shared React Native component documentation for the overlay host,
  queue, gesture, accessibility, and geometry contract.
- Update mobile user/development docs for cross-connection attention,
  preferences, View navigation, and local acknowledgement.
- Update desktop user/development docs for overlay attention across open
  connections and source labels.
- Link connection-lifecycle docs for focus/runtime ownership rather than
  duplicating Open/Close/offline behavior.
- Update notification frontend behavior and requirement evidence after native
  verification.

### Task checklist

- [ ] Add shared attention overlay component and queue behavior.
- [ ] Add mobile root coordinator over every open runtime.
- [ ] Add desktop root coordinator over every open runtime.
- [ ] Integrate focused connection/session suppression and preferences.
- [ ] Implement local timeout, Close, upward swipe, and View acknowledgement.
- [ ] Implement explicit connection/session navigation through lifecycle
  hosts.
- [ ] Add shared/mobile/desktop component and integration tests.
- [ ] Add Detox screenshot/gesture/navigation scenarios.
- [ ] Add macOS production UI scenarios.
- [ ] Complete mobile and desktop manual visual/device checkpoints.
- [ ] Update current docs and notification/connection evidence.

### Requirement verification

- Overlay: screenshots and geometry assertions prove the banner covers the
  application root rather than one screen's content region.
- Scope: attention from connection B while A is focused retains B's label and
  leaves A focused.
- Navigation: pressing View explicitly focuses B and opens the owning session
  when available.
- Acknowledgement: timeout, Close, and upward swipe hide only the attention
  token; reopening the owning session still shows the authoritative
  notification when active.
- Preferences: request lifecycle and general important transitions obey
  configured filters across both frontends.
- Runtime lifecycle: opening/closing one connection starts/stops only its
  attention observation.

### Additional implementation verification

- Several simultaneous eligible items are ordered deterministically without
  unbounded stacking.
- Connection deletion removes local attention keys for that frontend identity
  without mutating server records.
- Foreground/background transitions do not replay already acknowledged tokens.
- Same session IDs on different connections navigate and acknowledge
  independently.
