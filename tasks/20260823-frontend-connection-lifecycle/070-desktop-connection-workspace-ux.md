# Desktop connection and workspace UX

Adopt the shared lifecycle controller across the desktop Connections,
Sessions, tabs, Chat status, and native connection editor while preserving
several open manual runtimes and cached offline workspaces.

## Requirements checklist

- [ ] Desktop rows expose authoritative Open, Cancel, Close, Retry,
  Unavailable, and Error state, and late completion cannot reopen or replace a
  closed/superseded connection.
- [ ] Several manual runtimes remain independently open and relevant later
  request failure converges row, Sessions, and Chat to one runtime state.
- [ ] Follow-active-tab enabled focuses the active tab's connection/session;
  disabled preserves an independently focused Sessions panel.
- [ ] New/Edit connection submission has explicit Save/Open semantics and
  validates candidates without destroying a usable old runtime.
- [ ] Cached Sessions and Chat tabs remain available offline with honest
  server freshness independent from local draft/preference updates.
- [ ] Close tab, Close runtime, cache clear, Delete, and Clear all communicate
  distinct tabs/cache/draft effects.
- [ ] Accessible production selectors plus Jest and macOS tests cover
  connection, editor, focus/tab, concurrent-open, failure, and offline paths.

Parent Task: `tasks/20260823-frontend-connection-lifecycle/000-main.md`

Depends On:

- `tasks/20260823-frontend-connection-lifecycle/017-desktop-connection-host-specification.md`
- `tasks/20260823-frontend-connection-lifecycle/020-shared-connection-lifecycle-controller.md`

## Supporting details

- Normative requirements: `FCL-002`–`FCL-006`, `FCL-009`–`FCL-015`,
  `FCL-020`–`FCL-022`; `DCL-001`–`DCL-008`, `DCL-012`–`DCL-016`.
- Task 020 migrates the manual runtime hook as a limited real consumer but
  intentionally preserves current desktop presentation.
- Desktop already supports multiple direct runtimes, focused cached Sessions,
  persistent cross-connection tabs, and connection-labeled global displays.
- Complete offline draft/composer behavior belongs to task 080.
- Bridge/cloud/Bonjour desktop connection kinds remain outside this task.

## Execution plan
Status: Draft

Replace remaining panel-level assumptions with shared lifecycle snapshot and
commands. Expose Cancel during Opening and normalized errors/status per row.
Report relevant runtime failures so Connections, Sessions, and Chat converge.

Implement an explicit focus/tab coordinator satisfying `FCL-022`, including
the follow setting and stale scroll/select guard. Preserve independent panel
behavior when disabled.

Refine native connection-editor submission into explicit Save/Open semantics
and shared candidate promotion. Separate server freshness from local cache
preference/draft update time. Clarify destructive actions and add production
selectors/native scenarios.

### Implementation decisions and open questions

- **Decision:** Initial desktop connection-kind scope remains manual direct
  HTTP.
- **Decision:** Several manual runtimes remain open until explicit Close.
- **Decision:** Follow enabled focuses the active tab's connection; follow
  disabled preserves independent Sessions focus.
- **Recommendation for approval:** Provide both Save and Save & Open where
  native window layout remains clear. If one combined action is retained,
  label it Save & Open.
- **Question for plan approval:** When an edited candidate fails, should its
  configuration still be saved offline? Recommendation: plain Save may do so;
  Save & Open commits only under the explicitly selected policy while
  preserving the old runtime.

### Documentation

- Update desktop user docs for delivered row states, focus/tab behavior,
  editor actions, and offline/cache semantics.
- Update desktop development docs for shared-controller host, failure
  reporting, focus coordinator, editor events, and macOS tests.
- Update root/package requirement evidence.
- Do not claim bridge/cloud/Bonjour desktop support.

### Task checklist

- [ ] Expose controller runtime/attempt/error state to ConnectionsPanel.
- [ ] Add Cancel during Opening and late-completion regression behavior.
- [ ] Report relevant runtime failure and converge all owning surfaces.
- [ ] Implement follow-enabled/disabled focus-tab coordinator.
- [ ] Implement authoritative native editor Save/Open candidate flow.
- [ ] Separate message server freshness from local draft/preference writes.
- [ ] Clarify Close tab/runtime and delete/clear scopes/copy.
- [ ] Remove or implement placeholder tab actions.
- [ ] Add stable accessible connection/editor/tab/offline selectors.
- [ ] Add Jest/component tests and focused production macOS UI scenarios.
- [ ] Run desktop/shared/backend integration and documentation checks.
- [ ] Update current docs and `FCL-*`/`DCL-*` evidence.

### Requirement verification

- `FCL-003`–`FCL-006`, `DCL-002`, `DCL-005`: deferred open/close/failure tests
  prove status and late-result behavior across row/Sessions/Chat.
- `FCL-012`, `DCL-004`: two manual runtimes remain open and independent.
- `FCL-022`, `DCL-003`: component/native tests cover both follow modes across
  connections.
- `FCL-005`, `DCL-006`, `DCL-013`: cancelled/stale editor and candidate
  failure preserve the old runtime and cannot commit late.
- `FCL-015`, `DCL-008`: local draft/preference activity cannot advance server
  freshness; failed refresh retains cache.
- `FCL-020`–`FCL-021`, `DCL-012`, `DCL-015`: destructive actions and
  selectors expose exact scope and accessible meaning.

### Additional implementation verification

- Restored tabs do not force automatic opening.
- Active Chat B remains visible while Sessions intentionally focuses A with
  follow disabled.
- Closing A does not remove A tabs or affect B runtime/displays.
- Connection-editor window close prevents a later saved event.
- Existing transcript, notification, native popover, and cache tests remain
  passing.