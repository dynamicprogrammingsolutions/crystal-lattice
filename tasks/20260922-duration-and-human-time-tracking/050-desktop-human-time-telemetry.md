# 050 — Desktop human time telemetry collection

Bring the landed mobile human-time collection to the React Native macOS
desktop app (`desktop/crystal-lattice-control-desktop-rn`): the same span
contract, durable cache, simplified upload triggers, partial-rejection
handling, opt-in settings, compact diagnostics, and warning behavior,
verified by unit tests and the real-backend Jest integration tier. Native
macOS UI-test verification is explicitly delegated to
`tasks/20260922-duration-and-human-time-tracking/060-desktop-xctest-verification.md`;
this task runs no XCTest.

## Requirements checklist

- [x] The desktop app collects user activity as human time spans with the
  same contract as mobile: an activity burst opens a span, ~30s inactivity
  closes it (`from` = first, `to` = last activity), surface switches close
  and reopen, spans carry the open session's id or null on session-less
  surfaces (session list, connections, home).
- [x] Collectors attach to the real desktop surfaces: composer typing,
  transcript scrolling, send, and session-list/list interactions.
- [x] Every collected span has an owning connection for cache and upload
  routing. Session activity uses the tab/session connection; session-list
  activity uses the list's focused connection; known list/card activity uses
  that item's connection; otherwise generic session-less activity uses the
  currently focused connection and is not collected when no target connection
  exists.
- [x] Spans persist locally (AsyncStorage) until confirmed by the server and
  survive app restarts. Transient and definitive action failures retain all
  unconfirmed spans. When a successful action response reports skipped
  spans, the uploader isolates the batch, removes accepted spans by value,
  continues through later entries, and retains only rejected spans.
- [x] Uploads batch through the existing `executeAction` path with
  content-derived request ids stable across retries. Upload starts after a
  span closes (2-second debounce), when its connection becomes usable, when
  the app returns to the foreground, or on **Upload now**; it never waits for
  agent/network idleness. Only transient failures schedule the fixed
  30-second retry.
- [x] An opt-in time-tracking setting in the desktop global settings
  surface with the telemetry-plugin id configuration right under it
  (defaulting to the plugin name), mirroring the mobile settings model.
- [x] The desktop Global Settings window provides compact diagnostics:
  collection/connection readiness, open and last-collected span, pending
  count, last upload and error/counts, **Upload now**, **Refresh**, and the
  latest ten entries with status, connection context, session id, end time,
  and duration. The separate settings window receives a serializable
  snapshot from the main application root through an established desktop
  window/event boundary.
- [x] A one-time warning through the desktop's standard notification
  display on a genuinely definitive plugin/action failure; transient
  failures retry silently, and rejected span data never produces the
  misleading unavailable-plugin warning.
- [x] Unit tests plus a real-backend Jest integration tier prove the
  desktop pipeline end to end from deterministic seeded spans: real
  transport → real server → real plugin → stored rows, including the
  session total surfacing at the next request finalize, request-id retry
  dedup, definitive-failure retention, and rejected-span isolation where
  valid session/session-less neighbors upload while only the rejected span
  remains cached — the same stored-rows touch point as the mobile tiers.
- [x] No XCTest/native macOS test invocations in this task (delegated to
  060); verification stays within Jest and TypeScript checking.

Parent Task: tasks/20260922-duration-and-human-time-tracking/000-main.md

Depends On:
- tasks/20260922-duration-and-human-time-tracking/030-human-time-telemetry.md
- tasks/20260922-duration-and-human-time-tracking/035-human-time-upload-and-diagnostics.md

## Open requirement questions

None. On 2026-09-24 the user approved:

- Move the platform-neutral tracker, cache, uploader, warning, and diagnostic
  transformations into `@crystal-lattice/frontend-rn-components`, with an
  injected `KeyValueStore`; keep thin app-specific providers/settings UIs.
- Route known session/list/card activity to its owning connection; route
  otherwise generic session-less activity to the currently focused
  connection; collect nothing without a target connection. Aggregate Global
  Settings diagnostics across connection caches and include a compact
  connection column.

## Supporting details

### Mobile reference implementation (current working tree)

- Module: `mobile/crystal-lattice-control-rn/src/humanTimeTelemetry/`
  (`spans.ts`, `spanTracker.ts`, `spanCache.ts`, `uploader.ts`,
  `warning.ts`, `HumanTimeTelemetryProvider.tsx`).
- Wiring: provider mounted in `ConnectedRoot`; collectors in
  `SessionChatScreen` (composer typing, transcript scroll, send) and
  `SessionsScreen` (list scroll, row taps); settings in
  `GlobalSettingsModal` + `HomeWorkspaceContext`/`homeWorkspaceState`.
- Tests: six unit files under `__tests__/humanTime*` plus
  `__integration__/humanTimeSpanUpload.realBackend.integration.test.ts`
  (4 tests: upload + finalize surfacing, retry dedup, definitive-failure
  retention, and rejected-span isolation).

### Contract facts (landed, do not re-derive)

- Wire format is snake_case at the uploader boundary:
  `{session_id, from, to}` ISO-8601 UTC; the app-internal type is
  camelCase `sessionId`.
- Action-level failures arrive as HTTP 200 `{status: 'error', error_type}`
  (the action protocol, not HTTP errors). Definitive types:
  `unknown_action`, `unknown_plugin`, `ambiguous_action`, `validation`,
  `not_found` → one-time warning + span retention; everything else is
  transient → silent retry.
- Batch caps: 1000 server-side / 100 frontend. Upload triggers are
  close-debounce, connection usable, foreground, and manual upload; there is
  no busy/network-idle gate and no max-age polling. Transient failures use
  one 30-second retry timer.
- A positive `skipped` count is data rejection, not plugin unavailability.
  The uploader isolates the batch and removes only confirmed spans.
- Mobile diagnostics retain at most ten recent in-memory entries while
  pending rows are restored from the durable cache.

### Desktop facts (verified in the working tree)

- The same test tiers already exist: `__tests__` (jest unit),
  `__integration__` via `jest.integration.config.js` — the real-backend
  pattern (`startBackendServer` from the frontend-sdk harness +
  `RestAgentBackend`) is proven in
  `__integration__/DesktopGlobalDisplay.realBackend.integration.test.tsx`.
- `executeAction` is already used in production
  (`src/ui/DesktopGlobalDisplayLayer.tsx`).
- Settings surface: `GlobalSettingsWindow` (`src/windows`); chat
  surfaces: `src/chat` (`ChatPane`, composer components, `chatScroll*`);
  sessions: `src/sessions`; root: `src/DesktopRoot.tsx`.
- `@react-native-async-storage/async-storage` is already a dependency.
- `DesktopRoot` already tracks `AppState` foreground state and owns
  `focusedConnectionId`, `getBackend`, open connections, tabs, session
  panels, and home collections—the information needed for routing.
- `GlobalSettingsWindow` is registered as a separate React Native root and
  reads/writes settings through `DesktopWindowManager`; diagnostics therefore
  need an explicit serializable cross-window snapshot/event contract rather
  than direct React context access.

### Server config for the integration tier

- The duration-tracking feature needs the timestamp extension
  (`path:${env:REPO_ROOT}/plugins/timestamp-extension`) — without it the
  feature's finalize silently stamps nothing.
- Use the `deterministic_stream` provider, NOT the echo provider — the
  echo provider's streaming path hangs on the HTTP runner (pre-existing
  issue, out of scope).
- Both the provider `duration_tracking_db_path` AND the application
  plugin's `application.duration_tracking.db_path` must point at the
  hermetic database: session-less spans follow the application plugin's
  path and otherwise land in the default store outside the queried DB.
- Set `application.duration_tracking.working_directory` explicitly to the
  hermetic test workspace. Production now defaults this setting to
  `WORKING_DIR`, but an explicit fixture value keeps attribution deterministic.

### Standing constraints

- Commit only when the user explicitly requests it.
- The reviewer-CA pem deletion
  (`mobile/.../ios/CrystalLatticePythonRuntime/Resources/reviewer-proxy-ca.pem`)
  stays unstaged; other agents' in-flight work stays untouched.
- Stop and ask before any XCTest invocation (that work belongs to 060).

## Execution plan

Status: Approved

1. Apply the approved shared-core boundary and multi-connection
   routing/diagnostics rules recorded above.
2. Under the approved reuse boundary, establish the shared headless
   telemetry core (or the approved app-local equivalent). Preserve the
   current mobile behavior and tests, especially exact cache removal,
   rejected-span isolation, simplified triggers, and warning classification.
3. Implement a desktop telemetry coordinator/provider that owns per-connection
   durable queues and uploaders, closes spans on connection/session/surface or
   foreground changes, and resolves each activity event to the approved
   connection target.
4. Wire collectors into composer typing, transcript scrolling, send,
   session-list interactions, and approved session-less surfaces. Wire the
   global opt-in/plugin-id settings and the standard warning display.
5. Add the compact diagnostics window section. Publish an immutable,
   serializable aggregate snapshot from the main root through the desktop
   window/event boundary; keep the UI to the approved ten-row table and two
   actions.
6. Mirror the relevant mobile unit tiers and port the four-test real-backend
   integration, adapting only app-side imports and hermetic workspace
   fixtures.
7. Document: a desktop `docs/development/` page mirroring the mobile
   `human-time-telemetry.md` (what is collected, settings, upload
   behavior, the two-tier verification and run commands, and the pointer
   to 060 for the native tier).
8. Sweeps: desktop Jest + `tsc --noEmit` + the integration tier; if the
   shared-package route touches the mobile app, the mobile suite, tsc,
   and real-backend integration tier stay green. Do not add a mobile
   simulator/Detox run solely for the extraction.

### Implementation decisions and open questions

- Approved: shared headless core in
  `@crystal-lattice/frontend-rn-components`, with thin app-specific adapters.
- Approved: known activity uses its owning connection; otherwise generic
  activity uses the focused connection; no target means no collection.
  Diagnostics aggregate connections and identify each row's connection.
- The provider/coordinator belongs in the main `DesktopRoot` ownership tree;
  the settings window is a consumer of the serializable diagnostics bridge,
  not a second telemetry owner.
- No production behavior changes beyond the collection feature itself.

### Documentation

- New desktop dev-docs page (audience: desktop developers) + README test
  section entry for the integration command; the 060 native-tier run
  command is added by 060, not here.

### Task checklist

- [x] Reuse mechanism decided by the user
- [x] Multi-connection routing and diagnostics scope decided by the user
- [x] Shared core/app adapters established under the approved boundary
- [x] Pipeline implemented on the desktop
- [x] Collectors + settings + warning wired into the desktop surfaces
- [x] Compact cross-window diagnostics wired and covered
- [x] Unit tests green (mirrored mobile tiers)
- [x] Real-backend integration tier green (4-test port)
- [x] Desktop dev docs + README updated
- [ ] Sweeps green (desktop jest, tsc, integration; mobile unaffected or
      re-verified)
- [x] Task records updated with evidence

### Requirement verification

| Requirement | Evidence |
|---|---|
| Same span contract + collectors on real desktop surfaces | Desktop unit/component tests asserting burst/inactivity/surface-switch/session-vs-null attribution and the approved connection owner |
| Durable cache, retention on failure, restart survival | Shared/desktop cache tests, including exact removal around rejected neighbors and AsyncStorage reload |
| Batched `executeAction` uploads with stable request ids and simplified triggers | Shared/desktop uploader tests for action shape, request-id stability, close debounce, connection/foreground/manual triggers, transient retry, and absence of a busy gate + integration retry-dedup |
| Opt-in setting + telemetry-plugin id config | Settings unit tests (render, persist, gate) in the desktop settings window tier |
| Compact diagnostics across the separate settings window | Main-root coordinator tests for immutable snapshots + window/event bridge and Global Settings rendering tests for the latest ten rows/actions |
| One-time warning on definitive failure only | Warning/provider tests (once for true plugin/action failure, not transient or skipped data, re-armed on setting change) + integration definitive-failure retention |
| Rejected span cannot block valid uploads | Uploader test with a rejected first span and valid same/later-batch neighbors + real-backend isolation integration |
| Integration tier proves seeded spans → stored rows → surfacing | The ported real-backend Jest test: 4/4 green against a spawned server with the real plugins |
| No XCTest in this task | Scope audit of the final diff: no xcodebuild invocations, no UITests target changes |

### Additional implementation verification

- `git status` scope check: no changes under `plugins/duration-tracking`
  or the mobile app unless the approved shared-package route requires
  the mobile import migration (then the mobile tiers re-run green).

## Implementation Notes

- The shared core moved to
  `packages/frontend-rn-components/src/humanTimeTelemetry/`. Storage is
  injected as approved. Mobile retains thin compatibility adapters and its
  app-specific provider; the desktop owns a multi-connection provider.
- The desktop settings window and main application root share one React Native
  bridge, so a small module-level serializable diagnostics bridge carries
  snapshots and manual refresh/upload commands without adding a native
  telemetry store or a second pipeline owner.
- Desktop settings remain native-authoritative through `NSUserDefaults` and
  `DesktopWindowManager` change events. The telemetry coordinator hydrates and
  follows those events.
- Surface switches close an open span through `activeSurfaceKey`; explicit
  collector calls open the next span. Known card/list activity uses its own
  connection and generic list activity uses the focused connection.
- No XCTest or `xcodebuild` command was invoked.

## Completion Notes

Implemented desktop human-time collection, durable per-connection queues,
simplified upload triggers, partial-rejection isolation, global settings,
standard warning behavior, aggregate diagnostics, and the four-case
real-backend tier. Mobile now consumes the same shared tracker/cache/uploader
implementation through thin adapters.

Requirement evidence:

- Shared package: `8` files / `74` tests passed, including exact
  rejected-neighbor cache behavior.
- Desktop Jest: `40` suites / `190` tests passed, including
  multi-connection routing, background/foreground flush, one-time definitive
  warning, skipped-data warning suppression, settings persistence calls,
  collector routing, and the ten-row diagnostics surface.
- Desktop real-backend integration: `4/4` passed for upload/surfacing,
  request-id dedup, definitive-failure retention, and rejected-span
  isolation.
- Mobile regression: `52` suites / `252` tests, TypeScript, and the `4/4`
  mobile real-backend integration passed after the shared-core migration.
- `git diff --check` passed.

Desktop `npx tsc --noEmit` was executed but remains blocked by `19`
pre-existing errors already present in checkpoint `87aa6aa5`: React Native's
ambient `URL` type lacks mutable URL fields used by
`frontend-sdk/httpBridgeTransport.ts`; `ChatPane.tsx` has unrelated
pre-declaration and optional-plugin-id errors; and
`ActionResultInlineCard.tsx` references the existing undeclared
`Theme.shadow`. None of the new telemetry files produced a TypeScript error.
The approved “sweeps green” task item therefore remains unchecked rather than
misreporting this baseline.

Native macOS production-flow verification remains exclusively in
`tasks/20260922-duration-and-human-time-tracking/060-desktop-xctest-verification.md`
and still requires explicit user approval before its first XCTest invocation.

## Post-completion follow-up

On 2026-09-25 subtask
`tasks/20260922-duration-and-human-time-tracking/070-session-presence-and-inactivity-semantics.md`
changed desktop collection to session-only spans whose end includes a
native-persisted configurable inactivity grace period. Session-list,
connection-list, Home, and History collectors were removed. The shared cache,
uploader, diagnostics, warning behavior, and plugin contract remain unchanged.