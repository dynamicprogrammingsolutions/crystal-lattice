# 070 — Session presence and inactivity semantics

Revise frontend human-time collection so desktop activity spans include the
configured inactivity grace period, mobile tracks foreground session presence
without activity events, and neither frontend creates new session-less spans.

Parent Task: tasks/20260922-duration-and-human-time-tracking/000-main.md

Depends On:
- tasks/20260922-duration-and-human-time-tracking/035-human-time-upload-and-diagnostics.md
- tasks/20260922-duration-and-human-time-tracking/050-desktop-human-time-telemetry.md

## Requirements checklist

- [x] Desktop spans start on the first session activity, extend across
  subsequent session activity, and close at the last activity plus the
  configured inactivity interval unless a session/surface switch,
  backgrounding, disabling, or explicit flush closes them earlier.
- [x] Desktop session/surface selection alone does not open a span, and
  desktop no longer collects session-less activity.
- [x] The desktop maximum inactivity interval is configurable in global
  settings, persists through the existing native settings authority, defaults
  to 30 seconds, and affects subsequently collected spans.
- [x] Mobile spans cover the time that a session is selected while the app is
  foregrounded and tracking is enabled; they close on backgrounding, leaving
  the session, changing session/connection, disabling tracking, or explicit
  flush, and restart when an eligible session becomes active again.
- [x] Mobile no longer depends on typing, scrolling, or send events and no
  longer collects session-less activity.
- [x] Durable caching, upload triggers, retry behavior, diagnostics, warning
  behavior, the plugin action contract, and historical/session-less server
  compatibility remain intact.
- [x] Focused deterministic tests cover both timing models and stale native
  test expectations are aligned without adding a simulator test matrix.

## Requirement questions

None. The user approved the behavior and requested implementation on
2026-09-25. For simplicity, foreground mobile time continues to count while
the Messages tab remains selected even if an in-app modal overlays it.

## Supporting details

- The shared tracker currently closes inactivity spans at the last activity,
  which explains sub-second spans after a 30-second wait.
- Desktop already closes an open span when `activeSurfaceKey` changes and does
  not open the next span until a collector reports activity.
- Mobile `ConnectedRoot` already owns the active tab and selected session, so
  it can pass one active session identity to the telemetry provider.
- The plugin already accepts both session-bearing and null-session spans.
  Null-session support remains for historical data and other future
  collectors; this task only stops desktop/mobile production.

## Execution plan

Status: Approved (user, 2026-09-25)

Update the shared activity tracker so its inactivity callback closes at the
scheduled deadline and external close operations use the earlier of the
current time and that deadline. Allow the desktop provider to update the
inactivity interval, defensively ignore null-session activity, and pass the
persisted setting from the native global-settings path.

Remove desktop session-less collector calls while retaining current
session-attributed composer/send/transcript activity. Replace the mobile
activity API with a small provider-owned foreground-session state machine
driven by app state plus `ConnectedRoot`'s active session identity. Keep the
existing cache/uploader/diagnostics pipeline beneath both collection models.

Update focused unit/component tests first, align the existing native test
flows and documentation with session-only collection, and run package-level
Jest/TypeScript/shared-package checks. Do not add or run additional simulator
or XCTest coverage solely for this follow-up.

### Implementation decisions and open questions

- Desktop configuration uses a persisted global inactivity-seconds setting
  with a 30-second default.
- Changing the desktop interval closes any currently open activity span under
  the old interval and applies the new value to subsequent activity.
- Mobile modal overlays do not pause tracking while the Messages tab remains
  selected and the app remains foregrounded.
- Abrupt process-kill recovery for an unclosed mobile foreground span remains
  deferred; normal app-state and navigation transitions are the persistence
  boundary.
- No open material decisions remain.

### Documentation

- Update desktop and mobile human-time development pages with their distinct
  collection models and session-only scope.
- Correct native test descriptions that still require session-less rows.
- Update superseded frontend-collection statements in the parent/current task
  records without changing the server ingestion contract.

### Task checklist

- [x] Record the approved follow-up and superseded collection semantics
- [x] Update shared desktop activity-span timing
- [x] Add persisted configurable desktop inactivity setting
- [x] Remove desktop session-less collectors
- [x] Replace mobile activity collection with foreground session presence
- [x] Remove mobile session-less and per-action collectors
- [x] Align focused tests, native test expectations, and documentation
- [x] Run focused/package verification and record evidence

### Requirement verification

| Requirement | Evidence |
|---|---|
| Desktop deadline/early-close semantics | Shared tracker tests plus desktop provider tests with configurable fake-timer intervals and surface/background closes |
| Desktop setting persists and applies | Desktop settings normalization/window tests and provider prop behavior |
| No desktop session-less collection | Collector component assertions/source wiring plus provider null-session rejection |
| Mobile foreground-session spans | Provider tests covering foreground start, background close/restart, tab/session/connection switch, disable, and manual upload |
| No mobile activity/session-less dependency | Screen tests/source wiring and provider API no longer exposing activity recording |
| Upload/diagnostics compatibility | Existing uploader/cache tests and focused provider diagnostics tests |
| Minimal native coverage | Existing Detox/XCTest scenarios updated to session-only expectations; no new simulator matrix |

### Additional implementation verification

- Shared RN components package tests.
- Desktop Jest tests and focused TypeScript checking, reporting known unrelated
  baseline errors separately.
- Mobile Jest suite and TypeScript checking.
- `git diff --check` and a final dirty-worktree scope audit preserving
  unrelated changes and the reviewer CA deletion.

## Implementation Notes

- The shared activity tracker stores the last activity time and closes at
  `min(explicit close time, last activity + inactivity interval)`. Its timer
  emits the scheduled deadline even if the JavaScript timer fires late.
- Desktop Global Settings persists `timeTrackingInactivitySeconds` through
  the existing native `NSUserDefaults` authority and event bridge. The UI
  offers 10 seconds, 30 seconds, 1 minute, 2 minutes, and 5 minutes; the
  default remains 30 seconds.
- Desktop providers ignore null-session activity defensively. Session-list,
  connection-list, Home, and History collector calls were removed; chat
  typing, send, and transcript-scroll collectors remain.
- Mobile `ConnectedRoot` passes the active Messages session into the provider.
  The provider owns one foreground presence span, closes and durably appends
  it on lifecycle/session/connection/setting changes, and reopens after
  foregrounding or manual upload when the session remains eligible.
- Closing an already-open span no longer depends on the new enabled setting,
  so disabling tracking persists the span collected while tracking was on.
- Existing Detox and XCUITest sources now assert session-only collection.
  They were not run for this follow-up.

## Completion Notes

Completed 2026-09-25.

- Desktop now records from first session activity through the configured
  inactivity deadline, or through an earlier surface/lifecycle close. The
  maximum inactivity setting is native-persisted and defaults to 30 seconds.
- Mobile now records the full foreground interval while a session is open.
  Typing, scrolling, and sending no longer drive mobile collection.
- Neither frontend creates new session-less spans. The plugin and integration
  fixtures continue to accept null-session spans for compatibility and
  historical data.
- Verification:
  - Shared RN components: 8 files / 74 tests passed.
  - Mobile: 52 suites / 253 tests passed; `npx tsc --noEmit` passed.
  - Desktop: 40 suites / 192 tests passed.
  - Mobile and desktop real-backend human-time integrations: 4/4 passed each.
  - The updated macOS UI-test Swift source passed `swiftc -parse`.
  - Desktop `npx tsc --noEmit` still reports the same 19 documented baseline
    errors in frontend-sdk URL typing, pre-existing ChatPane declarations and
    optional plugin ids, and `Theme.shadow`; no new telemetry error appeared.
- No Detox, simulator, XCTest, or `xcodebuild test` run was added. The existing
  native scenarios were only aligned to the new session-only contract.