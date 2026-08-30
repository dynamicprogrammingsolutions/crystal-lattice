# Mobile connection lifecycle host requirements

These package requirements refine the root `FCL-*` contract. They track mobile
host implementation and native verification without duplicating portable
product requirements.

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
| --- | --- | --- | --- | --- | --- |
| MCL-001 | The mobile application hosts one shared multi-runtime lifecycle controller and derives backends/status from its immutable connection-scoped snapshot rather than one global transport/backend pair. | Not started | Unverified | Pending | Current `App.tsx` owns one global runtime; implementing work is tracked by the lifecycle task set. |
| MCL-002 | Mobile injects direct, discovery, bridge, and cloud factories/readiness policy into shared adapters while preserving mobile timeout rules and redacted diagnostics. | In progress | Unverified | Pending | Current factories exist in `App.tsx`; shared adapter host wiring is not implemented. |
| MCL-003 | Every unsaved wizard, Bonjour scan, bridge pairing/repair, saved open, and foreground recovery uses an authoritative operation scope whose cancellation/supersession prevents late effects. | Not started | Unverified | Pending | Current wizard and repair callbacks lack shared generation authority. |
| MCL-004 | Saved bridge repair updates the same connection identity, retains mode/cache/workspace/draft ownership, and disconnects temporary resources on cancellation. | Not started | Unverified | Pending | Current repair can clear selection and normal pairing creates a new record ID. |
| MCL-005 | Background and foreground processing flushes durable UI state and recovers every eligible user-open runtime independently without navigation. | Not started | Unverified | Pending | Current recovery handles one selected bridge runtime through one global in-flight flag. |
| MCL-006 | Focused connection and selected session per connection persist independently from runtime availability and map every screen/controller/callback by connection/session identity. | In progress | Unverified | Pending | Caches are scoped; selected connection/session and Chat component identity remain partly global. |
| MCL-007 | Saved-record, workspace, Sessions cache, Messages cache, and draft hydration cannot be overwritten by pre-hydration empty state, and malformed entries are isolated. | In progress | Unverified | Pending | Message cache has a hydration queue; other mobile stores remain inconsistent. |
| MCL-008 | Home, Connections, Sessions, and Messages present scoped runtime/offline/freshness state and keep local navigation/actions available while gating server-authoritative actions. | In progress | Automated partial | Documented | Home and cached screens accept nullable backends; unreachable saved focus and complete status/action behavior remain incomplete. |
| MCL-009 | Mobile durably restores complete text/attachment drafts, surfaces persistence failure, protects drafts from eviction, and retains uncertain-send recovery. | In progress | Unverified | Pending | Text is partially stored; attachments and recovery remain component/in-memory state. |
| MCL-010 | Mobile keeps several user-open runtimes concurrently, switches one focused workspace without closing others, isolates failure/background activity, and closes only an explicitly chosen runtime. | Not started | Unverified | Pending | Current mobile owns one global runtime. |
| MCL-011 | Connection-targeted deep links, notifications, displays, and invalidations resolve across all matching open runtimes while focus/navigation remains explicit current intent. | In progress | Unverified | Pending | Current deep-link backend lookup is limited to the selected connection. |
| MCL-012 | Runtime Close, credential reset/repair, cache clear, draft discard, and saved-record deletion execute distinct storage/resource scopes and communicate every local consequence. | In progress | Unverified | Pending | Existing mobile delete clears cache/drafts without complete local-data wording. |
| MCL-013 | Stable production selectors and component/native tests cover connection rows, wizard/repair, offline screens, drafts, and multi-open switching on supported iOS and Android targets. | In progress | Unverified | Pending | Selected bridge/transcript Detox coverage exists; complete lifecycle scenarios do not. |
| MCL-014 | Mobile lifecycle changes preserve saved WebSocket compatibility default, explicit HTTP/hybrid selection, foreground adapter behavior, and no cross-family fallback/replay. | In progress | Unverified | Pending | Current bridge mode behavior is implemented under `BRG-013`–`BRG-014`; lifecycle migration evidence is pending. |
| MCL-015 | Mobile Home derives a composite local Watchlist, session-ID notes, strict recent sessions, and connection-scoped status batches; polling does not open or focus runtimes and current user intent owns cross-connection session navigation. | Implemented | Automated | Documented | `HomeWorkspaceProvider`, `HomeScreen`, stateless status reader/poller, Jest coverage, and `e2e/home.e2e.test.ts`. |

## Root requirement mapping

- Controller, attempts, adapters, and recovery: `FCL-001`–`FCL-008`
- Focus, navigation, offline state, and deep links: `FCL-009`–`FCL-015`
- Drafts and deletion: `FCL-016`–`FCL-020`
- Accessibility/native verification: `FCL-021`
- Mobile multiple-open behavior: `FCL-023`
- Mobile Home behavior: `FCL-024`

Primary work tracking:

- `tasks/20260823-frontend-connection-lifecycle/000-main.md`