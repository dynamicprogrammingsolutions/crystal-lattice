# Desktop connection lifecycle host requirements

These package requirements refine the root `FCL-*` contract. They track
desktop host implementation and macOS verification without duplicating
portable product requirements.

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
| --- | --- | --- | --- | --- | --- |
| DCL-001 | `DesktopRoot` hosts one shared multi-runtime lifecycle controller and maps every panel/tab backend and status by connection ID. | In progress | Unverified | Pending | Current desktop has a local runtime map; shared controller consumption is planned in task 020. |
| DCL-002 | Open, Cancel, Close, Retry, editor validation, and host disposal enforce operation authority so late completion cannot reopen or replace state. | Not started | Unverified | Pending | Current `useOpenConnections` writes completion after awaits without generation checks. |
| DCL-003 | Focused Sessions connection and active Chat tab follow `FCL-022`, including deterministic enabled-follow synchronization and disabled independent-panel behavior. | In progress | Unverified | Pending | Both identities exist; tab activation does not currently focus another connection. |
| DCL-004 | Several runtimes remain independently open, recover, fail, display connection-level activity, and close without affecting other runtimes or workspaces. | In progress | Unverified | Pending | Several manual runtimes and connection-labeled notifications exist; failure/recovery isolation is incomplete. |
| DCL-005 | Connection rows, Sessions, and owning Chat panes converge on normalized runtime status after opening and relevant later transport/backend failure. | Not started | Unverified | Pending | Open currently reflects one readiness request and later failures do not update the runtime map. |
| DCL-006 | New/Edit window submission has explicit Save/Open semantics, preserves stable identity, rejects stale window events, and validates a candidate without destroying an old runtime. | Not started | Unverified | Pending | Current Save emits a manual record then immediately opens it without candidate authority. |
| DCL-007 | Persistent tabs restore by connection/session, remain through runtime closure, and recover cache/draft state after bounded warm-pane unmount/remount. | In progress | Unverified | Pending | Tabs/cache remount exists; complete attachment draft restoration does not. |
| DCL-008 | Focused Sessions remains useful offline with honest cache freshness, retained failed-refresh data, local filtering/open-tab behavior, and gated server actions. | In progress | Unverified | Pending | Current Sessions shows online/offline and cache time with partial action gating. |
| DCL-009 | Cached Chat remains readable and its text composer remains editable offline while Send/server actions are reconnect-gated. | In progress | Unverified | Pending | Cached transcript works; composer is currently explicitly read-only offline. |
| DCL-010 | Complete desktop drafts, including attachment and recovery state, survive pane unmount, application restart, and ordinary cache pressure with visible persistence failure. | Not started | Unverified | Pending | Text is debounced; attachments are component-local and only three recent panes remain mounted. |
| DCL-011 | Desktop uncertain-send state persists submitted draft revision and idempotent Check status/Retry safely behavior without clearing newer edits. | Not started | Unverified | Pending | Current send failure shows an alert without durable idempotent recovery. |
| DCL-012 | Close tab, Close runtime, cache clear, draft discard, Delete connection, and Clear all use distinct scopes and confirmations naming tabs/caches/drafts affected. | In progress | Unverified | Pending | Runtime/tab handlers differ correctly, but delete/clear confirmations omit some local consequences. |
| DCL-013 | Native connection/editor/popover callbacks carry owner identity and cannot commit after cancel, supersession, owner change, or host disposal. | In progress | Unverified | Pending | Native coordinator patterns exist; connection-editor lifecycle authority is not verified. |
| DCL-014 | Connection-level displays from every open runtime remain labeled/scoped and never focus a connection or tab without explicit user navigation. | Implemented | Unverified | Pending | `DesktopGlobalDisplayLayer` aggregates open runtimes with connection names; existing tests cover notification isolation. |
| DCL-015 | Stable accessible production selectors and macOS tests cover connection rows/actions, editor, focus/tab policy, offline Chat, and complete drafts. | Not started | Unverified | Pending | Session/transcript selectors exist; connection/tab/editor lifecycle selectors and XCUITests do not. |
| DCL-016 | The initial desktop host supports manual direct HTTP records and does not present bridge, cloud, or Bonjour as supported until their package UX and native verification are specified. | Implemented | Unverified | Pending | Current editor/runtime hook accept only manual records. |

## Root requirement mapping

- Controller, attempts, adapters, and status: `FCL-001`–`FCL-008`
- Focus, tabs, navigation, cache, and offline state:
  `FCL-009`–`FCL-015`, `FCL-022`
- Drafts and deletion: `FCL-016`–`FCL-020`
- Accessibility/native verification: `FCL-021`

Primary work tracking:

- `tasks/20260823-frontend-connection-lifecycle/000-main.md`