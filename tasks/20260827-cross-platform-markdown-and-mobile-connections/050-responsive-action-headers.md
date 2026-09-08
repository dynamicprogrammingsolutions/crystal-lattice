# Responsive mobile action headers

Correct long action-menu titles and make the Sessions and Messages headers
remain usable with long titles or many pinned actions.

Parent Task: `tasks/20260827-cross-platform-markdown-and-mobile-connections/000-main.md`

## Requirements checklist

### Functional requirements

- [x] A long mobile actions-menu title stays inside its modal, uses no more
  than two lines, and does not overlap its close control.
- [x] Mobile connection action menus use the same compact close icon as the
  Sessions and Messages action menus.
- [x] The Sessions view title shows the active connection name, falls back to
  `Sessions` when no matching record is available, and truncates on one line
  when space is constrained.
- [x] Sessions and Messages header titles shrink before their action areas
  overflow.
- [x] The triple-dot action-menu trigger remains visible and clickable when
  more actions are pinned than can fit in the header.
- [x] The compact bar renders as many complete pinned actions as fit within a
  window-width-derived limit; additional pinned actions remain pinned and
  available in the triple-dot menu.

### Non-functional requirements

- [x] A pure React Native flex structure independently reserves a
  non-shrinking overflow-trigger slot outside a shrinkable pinned-action
  viewport.
- [x] The visible-pin limit is an explicit shared option and its mobile value
  derives from current window width and maintained layout metrics rather than
  a fixed low count.
- [x] Responsive tests derive expectations from the maintained layout helper
  and relative native geometry, without copying typography preset values.
- [x] Existing pin persistence, action ordering, disabled-state behavior,
  modal behavior, and desktop popover behavior remain unchanged.

## Execution plan
Status: Approved

Harden the shared actions modal by making its title consume only the remaining
header width, limiting it to two lines, and keeping a non-shrinking close
control aligned inside the modal. Give the title and panel stable identifiers
for native geometry checks. Mobile Connections will supply the existing
Feather `x` renderer already used by Sessions and Messages.

Refactor `ActionsMenuBar` into a shrinkable pinned-action viewport followed by
a fixed overflow-trigger slot. The viewport may clip as the final pure-layout
safety mechanism, but the trigger cannot shrink or enter the clipped region.
Add an optional `maxPinnedActionsForBar` input that limits only compact
rendering; the complete pinned set continues to drive persistence and menu
star state.

Add a pure mobile layout helper that computes the compact pin limit from
`useWindowDimensions().width`, the shared action-button slot size, the outer
screen gutter, the overflow slot, and a minimum useful title reservation.
Use it for the Sessions and Messages screen headers. Narrow phones therefore
show fewer complete pinned buttons while wider phones and tablets retain more;
the flex safety invariant still protects the trigger if measured content
differs from the estimate.

Derive the active connection name in `ConnectedRoot` and pass it explicitly to
`SessionsScreen`. The title uses one-line tail truncation and the same
shrinkable title-versus-actions structure as Messages.

### Implementation decisions and open questions

- Decision: additional pins are hidden only from the compact bar; they remain
  pinned, marked in the menu, and executable from the triple-dot menu.
- Decision: use a width-derived complete-button limit plus flex clipping,
  rather than a horizontally scrolling header or `onLayout` measurement.
- Decision: apply the responsive limit to Sessions and Messages headers. Other
  action bars gain the shared flex safety behavior without adopting a
  caller-specific limit.
- No open requirement questions remain.

### Documentation

- Update shared action-component development guidance with the fixed overflow
  slot and optional compact-pin limit.
- Update mobile development guidance with connection-name title ownership and
  width-derived header capacity.

### Task checklist

- [x] Constrain the shared actions modal header and expose geometry IDs.
- [x] Add the shared compact-pin option and fixed overflow-trigger flex
  structure.
- [x] Add and test the mobile width-derived pin-capacity helper.
- [x] Show the active connection name in the responsive Sessions header.
- [x] Apply responsive capacity to Sessions and Messages headers.
- [x] Add component and native geometry regression coverage.
- [x] Run shared and mobile verification and update owning documentation.

### Requirement verification

- Shared model tests prove the compact limit affects only bar rendering and
  leaves the full action/pinned model available to the menu.
- Mobile component tests verify active-name/fallback title selection, title
  truncation styles, modal close-icon wiring, and responsive limit use.
- The production mobile harness uses a long connection name and excess pinned
  actions; Detox verifies that the title and triple-dot trigger do not overlap,
  the trigger stays inside the header and opens the complete menu, and the
  long modal title and close control remain inside the modal.

### Additional implementation verification

- Run the shared component test suite and type check.
- Run complete mobile Jest and TypeScript checks.
- Build and run the focused native scenario on iOS and Android.

## Implementation Notes

- `ActionsMenuBar` now keeps compact pins in a shrinkable clipped viewport and
  its overflow trigger in a fixed 44-point sibling slot.
- `maxPinnedActionsForBar` limits only rendered compact pins.
  `limitPinnedActionsForBar` leaves the full model and persisted pin array
  unchanged.
- Mobile derives the Sessions/Messages compact limit from current window
  width after reserving the outer gutter, a useful title width, and the fixed
  overflow slot. The shared flex structure remains the fallback if custom
  content exceeds the estimate.
- `ConnectedRoot` resolves the active saved-connection name and Sessions uses
  it as a one-line shrinking title with a `Sessions` fallback.
- Connection action menus use the existing Feather `x`; shared menu titles
  shrink, wrap to at most two lines, and stay before the fixed close control.
- The native session-list harness publishes three application actions through
  the production UI-schema path and seeds all six header actions as pinned.
  Its long connection name exercises the compact limit and fixed trigger.

## Completion Notes

- Shared tests pass 44 cases and the shared TypeScript check passes using the
  mobile workspace compiler.
- Complete mobile Jest passes 33 suites and 142 tests; mobile TypeScript
  passes.
- Complete desktop Jest passes 23 suites and 120 tests, covering the shared
  action-bar consumer boundary.
- Fresh iOS and Android Detox builds pass.
- The focused session-list Detox scenario passes two tests on each platform,
  including six pinned header actions, long-title containment, fixed-trigger
  reachability, complete-menu access, and existing default/largest typography
  geometry.
- The focused Connections/Settings Detox scenario passes on each platform,
  including long modal-title and close-control geometry.
- Initial native runs showed that the deterministic backend exposed
  executable actions without matching `application_action` UI declarations.
  The harness was corrected to use the realistic public UI-schema path before
  the final successful runs.
- `git diff --check` passes. Existing React test `act(...)` warnings and
  Android Detox process-probe noise remain non-failing baseline output.