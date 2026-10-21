# Mobile Action Form and Result Usability

Correct mobile action-dialog and action-result behavior for long content,
keyboard use, and date/time entry. Ordinary action dialogs must support forms
with an arbitrary number of fields. Action results must keep long result
content and follow-up actions usable while limiting embedded forms to small
workflows and offering a separate follow-up dialog for larger forms.

## Requirements checklist

- [x] R1. Mobile action dialogs use the available safe viewport, avoid the
  software keyboard, and provide a scrollable form area so every field and the
  submit/cancel controls remain reachable for an arbitrary number of fields.
- [x] R2. Mobile action-result modals are capped to the available safe viewport,
  avoid the software keyboard, keep long markdown independently scrollable,
  and keep follow-up actions discoverable without requiring users to scroll
  through the markdown.
- [ ] R3. Embedded action-result forms remain usable for a documented small
  number of fields, including date/time entry, without allowing their fields
  or the keyboard to hide the result's follow-up actions.
- [ ] R4. The common action form schema supports a `datetime` field whose value
  can be entered with a native date/time selector on supported mobile
  platforms, cleared when optional, and edited through a text fallback where
  no selector is supported or an existing value cannot be parsed.
- [x] R5. The behavior tracked by
  `tasks/20260620-action-display-followup-dialogs.md` is completed, allowing an
  action-result follow-up button to open the same arbitrary-length action
  dialog used by ordinary session actions while preserving existing immediate
  follow-ups.
- [ ] R6. The ChatGPT usage report declares date/time inputs through the common
  schema and uses the separate follow-up-dialog path for range entry rather
  than depending on an embedded form beneath a long report.
- [ ] R7. Date-range filtering accepts selector-produced timezone-bearing
  timestamps, retains compatible manual input, treats a date-only lower bound
  as the start of the day and a date-only upper bound as the end of the day,
  and continues to reject an inverted range.
- [x] R8. UI tests use neutral fixture plugins or fixture action results and do
  not import, launch, or special-case the ChatGPT usage plugin.
- [ ] R9. Native mobile coverage exercises date/time entry and scrolling on
  both iOS and Android through production action-dialog and action-result
  components.
- [ ] R10. Current plugin author guidance explains `datetime`, the bounded
  embedded action-result form limitation, and when to use a follow-up dialog.

## Scope and constraints

- This is a single task. The existing follow-up-dialog task remains its own
  referenced handoff, but satisfying that task is required before this task can
  be marked complete.
- Arbitrary field counts are a supported requirement for ordinary action
  dialogs, including dialogs launched by action-result follow-ups.
- Embedded forms inside action results are intentionally not the arbitrary-form
  surface. They are retained for small, context-adjacent inputs only.
- Action-result title/close controls and follow-up actions remain outside the
  markdown scroll region.
- UI fixtures must describe generic actions and values such as a report,
  scheduling range, or neutral form. Plugin-specific Python tests may still
  verify the ChatGPT plugin's emitted schema and range behavior.
- Existing action dialogs, embedded display forms, and display follow-ups
  without dialogs remain backward compatible.
- Desktop behavior is in scope only where required by the referenced
  cross-platform follow-up-dialog contract. The reported layout, keyboard, and
  native selector corrections are mobile concerns.
- Portrait usability is the required mobile checkpoint. Landscape is optional
  and must not block completion of stage 1; the user explicitly permitted
  skipping it if it requires more than an easy fix.

## Requirement questions

None. The implementation may resolve local visual details without changing the
boundaries above.

## Dependencies

- Completion dependency:
  `tasks/20260620-action-display-followup-dialogs.md`.
- A React Native date/time picker compatible with the repository's current
  React Native, iOS, and Android versions must be selected and integrated.

## Established facts

- Stage 1 adds measured safe/keyboard-adjusted viewport constraints to
  `ActionResultModal`, with independent markdown and embedded-form scroll
  regions and fixed title/close/follow-up controls.
- Stage 1 makes ordinary `ApplicationActionDialog` reuse
  `ApplicationActionForm`, with a bounded scroll body and fixed title and
  Cancel/OK controls.
- The mobile action-field renderer currently specializes select and boolean
  fields. Unknown field types fall back to a text input.
- The ChatGPT usage report currently emits `from` and `to` as string fields in
  an embedded action-result form.
- Shared form submission currently preserves explicit empty values only for
  string and multiline fields, so an optional `datetime` needs corresponding
  clear semantics.
- The report parser accepts date-only, naive date/time, and ISO timestamps.
  Its current inclusive comparison interprets a date-only upper bound as
  midnight at the start of that date.
- Stage 1 adds neutral native scenarios that exercise actual scrolling,
  keyboard presentation, last-field reachability, and typed submission.
- The first slice supplied the mobile field-renderer registry to global
  action-result forms and added follow-up dialogs. Those paths are available
  for the next layout slice.

## Execution plan

Status: Approved

The first implementation slice is complete. Stage 1 is approved for execution,
including its tests and documentation. Stop after stage 1 for the user's manual
checkpoint and report improvements and existing plugin entry points. Stages 2
and 3 remain planned and require approval after that checkpoint.

Use one common form contract and two intentionally different mobile
presentations.

An ordinary action dialog is the unrestricted form surface. Its modal should
occupy the available safe viewport when needed, with a fixed title area, one
scrollable form body, and fixed submit/cancel controls. Keyboard avoidance
shrinks the form body instead of moving fields or controls outside the
viewport. This presentation is used by ordinary session actions and by
action-result follow-ups that declare a dialog.

An action result is a content surface, not an unrestricted form surface. Its
modal remains bounded to the safe viewport, with a fixed header and fixed
follow-up action area. Markdown owns a bounded scroll region. A small embedded
form may appear outside that markdown region, but plugins must not depend on
that arrangement for arbitrary field counts. Workflows needing larger forms
place a simple follow-up button on the result and open an ordinary action
dialog through the protocol in
`tasks/20260620-action-display-followup-dialogs.md`.

The generic form schema gains `datetime`. Form state continues to transport
strings so existing `$dialog.*` and `$form.*` mappings remain compatible.
Native mobile selectors display device-local values and submit an ISO-8601
timestamp with an explicit timezone. Optional fields expose a clear operation.
Unsupported platforms and unparseable existing values retain the ordinary text
fallback, preventing data loss and preserving desktop compatibility.

The ChatGPT usage report becomes a consumer of these generic capabilities, not
their UI test fixture. Its result keeps report markdown and simple follow-up
buttons. Selecting the range opens a `datetime` action dialog, and applying it
re-runs the report. Python tests verify the plugin-specific schema, parameter
mapping, timezone handling, date-only compatibility, and filtering behavior.

### Stage ownership and completion checkpoints

These stages are execution slices within the existing task files, not new
subtasks. The proposed earlier report migration in stage 2 remains a sequencing
recommendation for the later plan; it does not change the approved requirements.

| Stage | Owning task | Requirement coverage |
| --- | --- | --- |
| 0. Follow-up-dialog foundation, completed | `tasks/20260620-action-display-followup-dialogs.md`, incorporated by this task's completed first slice | R5 protocol dependency; R8 fixture constraint |
| 1. Mobile layout and keyboard handling | `tasks/20261004-mobile-action-form-and-result-usability.md` | R1, R2, layout portion of R3, remaining presentation portion of R5, scrolling portion of R9, embedded-form guidance portion of R10 |
| 2. Real usage report adopts a text follow-up dialog and correct range boundaries | `tasks/20261004-mobile-action-form-and-result-usability.md` | Follow-up-dialog portion of R6; manual-input, date-only, timezone-bearing input, and inverted-range portions of R7 |
| 3. Common datetime controls and real report adoption | `tasks/20261004-mobile-action-form-and-result-usability.md` | R4, datetime portions of R3 and R6, selector-to-filter verification for R7, remaining R9 and R10 |

R8 applies to every stage. All proposed work has an existing owner. The former
stage 4, final integration/regression/documentation, is removed: its checks and
documentation belong to the stage that introduces the affected behavior.

- **Stage 0:** completed with SDK, public-backend, mobile/desktop coverage and
  protocol documentation. Manual demonstration is available through the
  neutral plugin's `Show follow-up dialog`; the real usage report has not
  adopted this capability yet.
- **Stage 1:** implement the detailed mobile layout slice below. Complete its
  neutral component and native iOS/Android tests, relevant existing
  public-backend regressions, and mobile/plugin-author layout guidance in the
  same stage. Manually test the existing ChatGPT report's long markdown and
  embedded From/To text fields with the keyboard open. Existing ordinary
  plugin dialogs provide an additional real consumer without plugin changes.
- **Stage 2:** remove the real report's embedded range form and put its current
  optional string fields in a follow-up dialog with `$dialog.*` mappings.
  Preserve applied values, clearing, close/refresh behavior, and correction
  dialogs on error results. Normalize date-only lower/upper bounds to the
  start/end of the server-local day while preserving exact timestamps and
  rejecting inverted ranges. Include plugin schema/usage-journal regression
  tests, the existing neutral production-UI/public-backend checks, and the
  plugin README describing the implemented text-dialog and range semantics.
  Manual checks cover open/cancel/apply/reopen/clear, same-day inclusion, and
  invalid/inverted ranges against existing journal history. R6 remains
  incomplete until stage 3 upgrades the fields to datetime.
- **Stage 3:** define `datetime` and consistent shared initialization,
  validation, clearing, and submission; integrate a compatible native picker
  and its fallback; upgrade the real report's two dialog fields to datetime.
  Add shared/component and public-backend coverage, extend the neutral native
  harness on both platforms for selectors in ordinary/follow-up dialogs and
  small embedded forms, and verify emitted timezone-bearing values against
  the report parser. Include native builds, relevant desktop fallback
  regressions, current datetime authoring guidance, and the plugin README
  update. Manual checks use native selection, optional clearing, retained
  values, supported text fallback, and phone/server timezone differences on
  the real report.

### First implementation slice: action-result follow-up dialogs

This completed slice established the follow-up-dialog path needed to move the
ChatGPT report's range fields out of its result. Its verification and remaining
boundaries are recorded under Implementation Notes.

The SDK owns the protocol shape and one structural adapter; frontends own
presentation state:

1. Extend `ActionDisplayRunActionAction` with the common optional `dialog`
   contract while preserving all existing fields and immediate-action
   behavior. Keep the existing public action-dialog types/exports compatible.
2. Add an SDK helper that converts a display `run_action` plus its originating
   display form into an `ActionUiElement`. It must carry `dialog`,
   `fixed_params`, `param_map`, `action_owner`, and the embedded `form`, so a
   submitted follow-up can resolve `$dialog.*` and `$form.*` together. Replace
   the hand-built follow-up elements in frontend handlers with this helper.
3. Extend the neutral dummy action-display fixture plugin with a second flow:
   an ordinary result containing a `run_action` with a generic form dialog,
   followed by an echo result that proves the mapped values reached the real
   backend. Keep the existing embedded-form fixture unchanged for regression
   coverage.
4. In mobile session chat and session list, route a dialog-bearing follow-up
   through the existing `usePluginActionDialog` and
   `ApplicationActionDialog`. Store the originating display entry and any
   embedded `formValues` in the dialog context. A dialog cancel leaves the
   originating display unchanged; submit closes the dialog and executes the
   same action with `dialogValues`, `formValues`, and the original
   session/message/connection context.
5. Add the same capability to `GlobalDisplayLayer` so connection and session
   notifications plus globally presented direct action results do not bypass
   follow-up dialogs. The provider owns one pending dialog and renders it at
   the global layer, independent of which `MobileDisplayHost` exposed the
   action.
6. In desktop chat and sessions, route dialog-bearing follow-ups through the
   existing `usePluginActionDialog` and native macOS action-dialog presenter.
   Preserve the originating display context until cancel or submit. Before
   editing `ChatPane.tsx`, inspect and preserve the unrelated in-progress
   transcript-scroll changes already present in the worktree.
7. In `DesktopGlobalDisplayLayer`, retain the backend/envelope context while a
   dialog is open and use the existing action-dialog coordinator. A follow-up
   launched from the detached action-display window uses a dedicated action
   dialog window rather than an unanchored popover; ordinary chat/session
   follow-ups retain their current configured presentation.
8. Preserve lifecycle semantics: opening or cancelling a dialog never removes
   the source display; after submit, the frontend applies the same
   `preserve_display` and result-presentation policy that its immediate
   follow-ups use today. Follow-ups without a dialog continue executing
   immediately with no extra modal state.

Decisive verification for this slice:

- SDK unit tests prove the adapter carries both dialog and embedded-form
  contracts, and `runApplicationAction` maps mixed `$dialog.*`/`$form.*`
  values, including explicit empty values.
- The existing local-backend action-display integration suite uses the neutral
  fixture plugin to execute show-result → inspect follow-up dialog → submit
  dialog values → observe the echoed result through `FetchTransport`,
  `RestAgentBackend`, and the public action endpoint.
- Mobile component coverage presses a neutral result follow-up in production
  session-list/chat handling, verifies that the existing production dialog
  opens, cancels without executing, then submits and observes the mapped
  values. Separate `GlobalDisplayLayer` coverage proves the global
  notification/direct-display route.
- Desktop component coverage proves chat/session handlers publish the dialog
  through the existing coordinator and that submission resumes action
  execution. `DesktopGlobalDisplayLayer` plus `ActionDisplayWindow` coverage
  proves the detached-window route opens a dialog window and retains its
  connection/session backend context.
- Regression cases cover immediate follow-ups, embedded-only forms,
  `preserve_display` true and false, dialog cancellation, action failure, and
  returned replacement displays.
- Focused commands are the frontend SDK unit suite and local
  `integration:action-display-forms`, frontend SDK React hook tests, mobile
  Jest plus the focused real-backend component integration, and affected
  desktop Jest/type checks. Native iOS/Android UI runs begin with the later
  layout/datetime slice, where they can prove keyboard and selector behavior.
- Update `plugins/docs/actions.md` in the same slice with the follow-up-dialog
  shape, `$dialog.*` mapping, coexistence with `$form.*`, cancellation and
  `preserve_display` behavior, and a neutral example.

### Next implementation slice: mobile modal layout and keyboard handling

Status: Approved

Deliver the usable mobile form surface before adding native datetime controls.
This slice addresses R1, R2, the layout portion of R3, and the remaining
arbitrary-field presentation portion of R5. It does not introduce the datetime
schema, a picker dependency, ChatGPT report migration, or date-range parsing
changes.

Ordinary action dialogs:

- Give the mobile dialog a stable header, one scrollable form body, and fixed
  Cancel/OK controls. Expand the card to the available safe viewport for forms
  that need it; small confirmations remain compact.
- Derive the height constraint from the actual presentation container, safe
  area, and keyboard-adjusted space. Native dialogs and overlays inside result
  or settings modals use the same layout; do not subtract keyboard height
  twice.
- Retain iOS keyboard avoidance and verify Android's existing `adjustResize`
  behavior. Ensure focusing the final field scrolls it into view and tapping
  submit works with the keyboard open.
- Use the same field/form implementation for ordinary actions and follow-ups.
  Preserve initialization, validation, clearing, field renderer callbacks,
  and the existing macOS Return/focus behavior.

Action-result modals:

- Cap the card to the available safe viewport and add keyboard avoidance.
  Keep title/close and follow-up controls outside the markdown scroll region.
- Replace the modal's fixed 420px body ceiling with available-space sizing.
  The compact inline card remains a separate presentation.
- Proposed layout: give markdown and the optional embedded form separate,
  bounded scroll regions within the middle area. Small embedded forms use
  their natural height; cap overflow so fields cannot consume all the space
  reserved for markdown. When both regions overflow, prefer roughly two
  thirds of the middle area for markdown and one third for the form.
  In short viewports, reserve a readable markdown line and enough form space
  for a single-line input where the available height permits; use a compact
  title/variant row to reduce fixed chrome.
- Document embedded forms as small, context-adjacent input. Large or
  keyboard-heavy forms should use the now-supported follow-up dialog. Do not
  impose an arbitrary field-count rejection or automatically rewrite plugin
  actions.
- Preserve the source result beneath follow-up dialogs, accessibility
  isolation, cancel/submit behavior, and hardware Back routing from the first
  slice.

Implementation sequence:

1. Establish viewport and safe-area constraints at mobile presentation
   boundaries. Add only the layout/focus plumbing needed by the production
   form renderer; keep desktop layout opt-in behavior compatible.
2. Refactor the mobile action-dialog layout into fixed header/footer and a
   scrollable body. Reuse `ApplicationActionForm` where practical so field
   rendering and submission do not diverge between dialogs and results.
3. Add keyboard-aware result sizing and the independent content/form scroll
   regions. Keep loading, dismissibility, and follow-up actions unchanged.
4. Add a neutral deterministic native harness that mounts production
   `ApplicationActionDialog` and `ActionResultModal`. Wire it through the
   actual iOS and Android launch paths and `index.js`, following existing
   Detox harness conventions.
5. Extend component tests and add the focused native scenarios, then update
   current mobile and plugin-author documentation.

Decisive acceptance evidence:

- Native tests on both platforms cover a compact confirmation, the screenshot
  equivalent three-field form, and a generated many-field form containing
  mixed single-line and multiline fields. Scroll to and edit the last field
  with the software keyboard open, then submit all values through the
  production form. Repeat through a result follow-up dialog.
- Native result tests use long neutral markdown, no form, a small embedded
  form, and an oversized embedded-form stress fixture. Scroll content and form
  independently and prove the follow-up controls stay reachable while the
  keyboard is open; the stress fixture tests viewport containment, not a new
  arbitrary-form support promise for embedded results.
- Cover portrait, including the reduced height with the keyboard open, and the
  existing larger typography preset. Landscape verification is optional.
  Verify native frames/visibility rather than merely
  asserting that a `ScrollView` exists. Exercise both supported markdown
  renderers because selectable native text may affect scroll gestures.
- Preserve the first slice's component and real-backend tests. Run mobile
  Jest/TypeScript, shared RN tests, and focused desktop dialog regressions.
- After building each platform, run the focused suite from the mobile package:
  `npx detox test -c ios.sim.release e2e/actionForms.e2e.test.ts --cleanup`
  and, after the existing emulator preparation script,
  `npx detox test -c android.emu.e2e e2e/actionForms.e2e.test.ts --cleanup`.
  Missing platforms or skipped scenarios remain unverified.

Documentation describes the implemented modal behavior and the small embedded
form limitation in `plugins/docs/actions.md`, with native harness commands in
the mobile README/development guidance. Main risks are duplicate keyboard
insets in overlay presentations, multiline/selectable text gesture handling,
and shared-layout changes affecting the desktop presenter. Stage 3 adds native
datetime fields to these same fixtures.

### Implementation decisions and open questions

- Approved stage-1 decision: cap an action result's embedded form in its
  own scroll region while reserving space for markdown and keeping follow-up
  controls fixed. The approximate two-to-one allocation is a layout
  recommendation for overflow, not a field-count limit.
- Decision: ordinary action dialogs, including follow-up dialogs, support
  arbitrary field counts; embedded action-result forms explicitly do not make
  that guarantee.
- Decision: action-result markdown and follow-up controls are not placed in one
  shared scroll view. This prevents long markdown from hiding actions.
- Decision: the ChatGPT report uses a follow-up dialog because its long
  markdown makes embedded input undesirable even though it currently has only
  two fields.
- Decision: UI behavior tests use neutral fixtures. ChatGPT-specific coverage
  remains at the plugin/schema and backend range-calculation boundaries.
- Decision: `datetime` values remain strings and use timezone-bearing ISO-8601
  output from native selectors. This preserves the existing action mapping and
  backend input model.
- Decision: an optional datetime field has an explicit Clear control and
  honors `submit_empty`, including clearing a previously supplied default.
- Decision: an unparseable existing datetime value is shown through the text
  fallback rather than replaced or silently normalized.
- Decision: native verification covers both iOS and Android because selector
  behavior differs materially between the platforms.
- Open implementation choice: select the maintained datetime-picker package
  version compatible with React Native 0.82 during execution and record any
  required native configuration in implementation notes.

### Documentation

- Update `plugins/docs/actions.md` with the `datetime` field contract, selector
  fallback, serialized value shape, clearing behavior, and a neutral example.
- Update action-display guidance to state that embedded forms are for small
  context-adjacent input and that arbitrary or keyboard-heavy forms belong in
  a follow-up dialog.
- Document display follow-up dialogs and `$dialog.*` mapping as required by
  `tasks/20260620-action-display-followup-dialogs.md`, cross-referencing
  embedded forms as the bounded alternative.
- Update `plugins/chatgpt-auth-app/README.md` to describe the report's
  date-range follow-up dialog and timezone/date-only behavior.
- Update mobile development guidance only if the resulting modal layout or
  native test harness establishes a reusable convention not already captured.

### Task checklist

- [x] Complete the protocol, SDK, mobile, desktop, tests, and documentation
  required by `tasks/20260620-action-display-followup-dialogs.md`.
- [x] Stage 1: complete mobile ordinary-dialog and result-modal layout,
  keyboard/focus handling, and host integration, with neutral component/native
  tests, relevant backend/desktop regressions, required layout/embedded-form
  documentation, and manual checkpoint instructions.
  - [x] Implement shared form reuse, bounded mobile dialog/result layout,
    focus reveal, overlay keyboard ownership, and orientation support.
  - [x] Add and run component regressions, relevant public-backend checks,
    shared package tests, and desktop dialog/TypeScript regressions.
  - [x] Update plugin author guidance and mobile/shared documentation, including
    existing-plugin manual checkpoint instructions.
  - [x] Complete native iOS and Android portrait scrolling/keyboard verification.
- [ ] User reviews the manual checkpoint after stage 1 before stage 2 begins.
- [ ] Stage 2: migrate the real usage report to a text follow-up dialog and
  correct range normalization, with plugin/schema/journal tests, neutral
  frontend regressions, the plugin README update, and manual checkpoint
  instructions.
- [ ] Stage 3: implement common datetime semantics and native selectors,
  upgrade the real report, and complete shared/component/backend/native and
  desktop-fallback verification, required datetime documentation, and
  manual checkpoint instructions.

### Requirement verification

- R1: Passed in stage 1 through `e2e/actionForms.e2e.test.ts` on iOS and
  Android. A neutral native action-dialog scenario renders a
  fixture with enough mixed fields to exceed the viewport, scrolls from the
  first field to the last, focuses fields with the keyboard open, changes the
  last field, and submits all values through the production dialog.
- R2: Passed in stage 1 through `e2e/actionForms.e2e.test.ts` on iOS and
  Android, with both markdown renderers. A neutral native action-result scenario renders long
  markdown with fixed follow-up actions, scrolls the markdown independently,
  and confirms the actions remain visible and operable before and after
  keyboard presentation.
- R3: The neutral action-result scenario includes a supported small embedded
  form with a datetime field, opens the selector, submits the value, and keeps
  the follow-up controls reachable. Documentation inspection confirms the
  small-form limitation and directs larger forms to follow-up dialogs.
- R4: Shared component tests cover initial datetime values, native selection,
  timezone-bearing submission, required validation, optional clearing,
  `submit_empty`, and unparseable-value fallback. The tests exercise both the
  ordinary dialog and embedded action-result form using neutral fixtures.
- R5: The completed protocol slice plus stage-1 native ordinary/follow-up
  many-field scenarios provide the required evidence. The decisive SDK/backend
  integration uses a neutral fixture plugin that
  returns a display follow-up with a dialog, opens it through the production
  frontend path, submits `$dialog.*` values, and observes the mapped values at
  the real public backend. Mobile and desktop presentation tests cover their
  respective production dialog paths.
- R6: ChatGPT plugin unit tests assert that the usage report returns a simple
  follow-up action carrying the common datetime dialog and correct parameter
  mappings; no mobile UI test depends on that plugin.
- R7: ChatGPT usage-journal/plugin tests cover timezone-bearing selector
  values, start-of-day lower bounds, end-of-day upper bounds, exact
  date/time bounds, clearing, and inverted-range errors.
- R8: Inspection of mobile component, integration, and native UI fixtures
  confirms that they use neutral action records or neutral fixture plugins and
  contain no ChatGPT usage plugin dependency.
- R9: Focused Detox scenarios pass on both iOS and Android with the native
  selector and keyboard enabled; a skipped platform run is reported as not
  verified rather than success.
- R10: Documentation inspection confirms the maintained action authoring guide
  covers datetime semantics, embedded-form limits, and follow-up-dialog
  selection guidance, and the ChatGPT plugin README describes its implemented
  behavior.

### Additional implementation verification

- Run shared frontend SDK and React Native component package tests.
- Run mobile Jest, TypeScript, and focused real-backend component integration
  suites.
- Run focused desktop tests affected by the follow-up-dialog protocol.
- Run non-manual ChatGPT auth plugin tests and the relevant usage-journal tests.
- Verify iOS CocoaPods and Android autolinking/build configuration after adding
  the native datetime dependency.
- Check that action dialogs without datetime fields, embedded display forms
  without datetime fields, and immediate display follow-ups retain their
  existing behavior.

## Implementation Notes

- Stage 1 execution is approved. The user requires a manual checkpoint after
  this stage, with a report of the improvements and existing plugin workflows
  where they can be tested. Stages 2 and 3 will not execute before that
  checkpoint is reviewed.

- Execution of the first slice began after explicit user approval.
- Existing unrelated changes in the shared worktree, including desktop chat
  and action-menu work, are preserved.
- The first slice is complete. `ActionDisplayRunActionAction` now accepts the
  common `dialog`, `buildDisplayFollowupActionElement` carries both dialog and
  embedded-form contracts, and `useDisplayFollowupDialog` retains the source
  context until cancellation or submission.
- Mobile session chat, session list, global displays, session settings, and
  embedded provider settings use the production dialog path. Mobile result
  modals render the follow-up dialog as an overlay inside the existing native
  modal instead of nesting another native modal. Accessibility hides the
  source controls while the follow-up is open; hardware Back cancels the
  follow-up first.
- Desktop chat uses the configured native presenter. Desktop sessions normally
  forward results to the global display layer; the decisive session test
  therefore traverses that production path. Global displays and detached
  result windows use a dedicated dialog window with the originating backend.
  Inactive presenter instances no longer close a different owner's dialog.
- A neutral desktop test exposed lexicographic selection of modal IDs hiding a
  newly returned result. Global desktop modal selection now follows
  presentation order, and the replacement-display assertion passes.
- The fixture plugin's new `Show follow-up dialog` flow and shared
  `test/fixture/displayFollowupDialog.ts` are the source of all new generic UI
  results. The ChatGPT usage plugin was not imported or launched by these
  tests. Its report has not yet been migrated.
- Verification: frontend SDK 374 tests; frontend SDK React 25 tests; shared
  React Native components 76 tests; mobile 300 tests; desktop 216 tests all
  passed. Both application TypeScript checks and the frontend SDK React
  TypeScript check passed.
- Decisive backend checks passed: SDK
  `integration:action-display-forms` (2 tests), mobile
  `ActionDisplayForm.realBackend.integration.test.tsx` (2 tests), desktop
  `DesktopGlobalDisplay.realBackend.integration.test.tsx` (3 tests). Mobile
  and desktop tests enter and submit values in production dialogs and use
  `FetchTransport`/`RestAgentBackend` with public backend actions.
- The additional standalone frontend SDK TypeScript check reports 58 existing
  diagnostics in unrelated tests/integration files. A compiler comparison
  replacing this slice's SDK changes with their HEAD versions produced the
  identical 58 diagnostics; no new diagnostic was introduced. This broad
  check is not counted as passed.
- After the first slice, R5's protocol dependency was completed through
  `tasks/20260620-action-display-followup-dialogs.md`; its remaining
  arbitrary-length layout evidence is supplied by stage 1 below.

### Stage 1 checkpoint

- Stage 1 is complete and execution stops for the requested manual review.
  R1, R2, and R5 are verified. R3's layout portion is implemented, while its
  datetime portion and R4/R6/R7/R9/R10's remaining work belong to later stages.
- Ordinary mobile dialogs reuse the common form with a measured, scrollable
  body and fixed title/Cancel/OK controls. Native focus reveal uses the
  actual scroll viewport after layout/keyboard changes; form inputs remain
  mounted during resizing.
- Result modals have safe/keyboard-aware sizing, independent markdown/form
  scroll regions, fixed follow-up controls, and reduced padding in short
  viewports. The source keyboard is dismissed on dialog transitions, and
  Android inputs disable fullscreen IME editing.
- Native verification passed with the current code: 7 portrait scenarios on
  iPhone 17 Pro / iOS 26.1 and 7 on the Android API 35 AOSP emulator. The
  optional landscape scenario is intentionally skipped by the default
  commands and is not included in those counts. A separate
  `CLC_TEST_ACTION_FORM_LANDSCAPE=1` Android run passed its one focused
  landscape scenario. Landscape is optional per the user's scope correction.
- Commands: `npm run detox:build:ios`,
  `npm run detox:test:action-forms:ios`, `npm run detox:build:android`, and
  `DETOX_ANDROID_AVD=CLC_HTTP_Bridge_AOSP35_20261010 npm run detox:test:action-forms:android`.
  Both builds and requested portrait suites exited successfully. The default
  API 36.1 emulator initially showed a System UI ANR; that interrupted attempt
  is not counted as verification.
- Final checks passed: mobile Jest 321 tests, shared RN 76 tests, focused
  desktop dialog regressions 3 tests, and the public-backend mobile
  action-display integration 2 tests. Mobile and desktop TypeScript checks
  passed. The desktop chat regression submits through Return/Enter.
- Native checks exposed and fixed portrait-only iOS modal orientation causing
  clipping during rotation and Android fullscreen keyboard editing covering
  controls. Android bundling now tracks shared frontend/fixture directories,
  so workspace component changes invalidate the production bundle inputs.
- Current author guidance is updated in `plugins/docs/actions.md`; shared
  form API notes are in `packages/frontend-rn-components/README.md`.
  Mobile implementation, native commands, and manual instructions are in
  `mobile/crystal-lattice-control-rn/docs/development/action-forms-and-results.md`.
- Manual review is pending human confirmation. Use the existing
  **Show ChatGPT usage report** action in a supported session to check
  independent report/From/To scrolling and reachable Apply/Close controls
  with the keyboard open. Use **Reset cost tracking** to inspect an ordinary
  Bucket form, then cancel, and **Show cost report** for another real markdown
  result. The backend/plugin schemas are unchanged for this stage; From/To
  remain text fields. Stages 2 and 3 have not started.