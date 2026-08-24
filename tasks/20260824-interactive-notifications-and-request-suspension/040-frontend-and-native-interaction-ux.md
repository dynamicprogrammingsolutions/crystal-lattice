# Frontend And Native Interaction UX

Render and operate active interactions consistently across SDK, mobile, and
desktop while preserving exact connection/session ownership and explicit
navigation.

## Requirements checklist

### Functional requirements

- [ ] The owning Chat renders the complete active interaction using standard
  display, form, and action components.
- [ ] Session lists/tabs expose a compact waiting-for-input indicator without
  presenting the complete interaction outside its Chat.
- [ ] Approve, deny, forms, cancel, timeout, responded, resolved, and
  continuation states update from authoritative records/events.
- [ ] Important pending interactions can request global attention while the
  user views another session or open connection.
- [ ] View explicitly focuses/navigates to the owning connection/session.
- [ ] Interaction history remains available through the standard notification
  history surface.
- [ ] Mobile and desktop support wait-only and durable suspended flows.

### Non-functional requirements

- [ ] Active interactions cannot be dismissed through ordinary notification
  controls.
- [ ] Navigation away or temporary presentation loss cannot lose the pending
  interaction.
- [ ] Mobile and desktop share portable models/components while using their
  established navigation, window, and modal conventions.
- [ ] Stable accessibility/test identifiers cover interaction content,
  response controls, indicators, and navigation.
- [ ] Automated backend/SDK/component/native tests cover lifecycle behavior;
  manual checkpoints focus on visual and real-device validation.
- [ ] One connection/session cannot display or answer another scope's
  interaction.

Parent Task:
`tasks/20260824-interactive-notifications-and-request-suspension/000-main.md`

Depends On:

- `tasks/20260824-interactive-notifications-and-request-suspension/020-wait-only-interaction-execution.md`
- `tasks/20260824-interactive-notifications-and-request-suspension/030-durable-suspend-and-continue.md`
- `tasks/20260824-operational-notifications-and-global-attention/040-global-attention-frontend-integration.md`
- `tasks/20260823-frontend-connection-lifecycle/060-mobile-multiple-open-connections.md`
- `tasks/20260823-frontend-connection-lifecycle/070-desktop-connection-workspace-ux.md`

## Execution plan

Status: Draft

Extend SDK notification selectors/controllers with interaction-specific active
state, response mutation, compact waiting projections, and operation fallback.
Reuse shared notification/action display components while adding only
interaction response and nondismissible behavior.

Mount complete interaction hosts in the owning Chat, compact indicators in
Sessions/tabs, and eligible global attention in the established root host.
Route View through the connection lifecycle controller and responses through
the generic backend operation/action runner.

Add component and real-backend integration first, then Detox and macOS
production-root scenarios with screenshots and real interaction controls.

### Implementation decisions and open questions

- Decision: complete interaction content appears only in the owning Chat.
- Decision: compact indicators and global attention are projections of the
  same authoritative record.
- Decision: desktop modal fallback follows current notification conventions.
- Open: choose final compact indicator vocabulary during visual planning.

### Documentation

- Update SDK/shared component implementation guides.
- Document mobile and desktop interaction placement, indicators, attention,
  response, and navigation behavior.
- Update accessibility/native test guidance.

### Task checklist

- [ ] Define SDK interaction selectors/controller.
- [ ] Add response mutation and authoritative merge behavior.
- [ ] Add shared active interaction and compact indicator components.
- [ ] Integrate mobile Chat, Sessions, global attention, and navigation.
- [ ] Integrate desktop ChatPane, tabs/connection state, and attention.
- [ ] Add component and real-backend integration tests.
- [ ] Add Detox and macOS native UI scenarios.
- [ ] Complete physical-device/mobile and desktop manual checkpoints.
- [ ] Update documentation and requirement evidence.

### Requirement verification

- An interaction appears completely only in its owning Chat.
- Another session/connection shows only compact/global attention as specified.
- Response updates the active UI and backend lifecycle without ordinary
  dismissal.
- View navigates explicitly to the correct connection/session.
- Wait-only and durable continuation scenarios pass on production frontend
  hosts.

### Additional implementation verification

- Reconnect and event-cursor expiry rehydrate pending interactions.
- Cached offline state does not permit submitting against a stale revision.
- Historical replay cannot expose active response controls.