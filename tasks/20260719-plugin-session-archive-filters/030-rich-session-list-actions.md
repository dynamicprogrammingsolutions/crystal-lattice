# Rich session-list actions

Extend ordinary session-list actions with optional toggle and list presentations, then deliver pin, archive, status, and pinned ordering as complete plugin features across the supported graphical frontends.

## Requirements checklist

- [x] A `session_list_action` with no `rich_ui`, an unknown rich kind, or invalid rich configuration retains its ordinary dialog and execution behavior.
- [x] Every rich-presentation-specific field is nested under the single `rich_ui` key.
- [x] A rich `toggle` reads current state from session-summary data, displays configured active/inactive semantics when pinned, and invokes the ordinary action immediately.
- [x] A rich `list` reads and displays the current option when pinned, marks it in the selection list, and invokes the ordinary action immediately when another option is selected.
- [x] Rich-list selection has no OK/Cancel confirmation, while its ordinary fallback remains a separate form with the current value prefilled and explicit OK/Cancel submission.
- [x] Rich action pinning remains a user preference; `default_pinned` applies only when no stored preference exists.
- [x] Unsupported or malformed rich configuration never hides an otherwise valid ordinary action.
- [x] Pinning is an ordinary session-list action with a rich toggle, a configurable metadata path, warning/muted state tones, a pin filter defaulting to Any, and no pin-specific UI type or top-level summary field.
- [x] Archiving is an ordinary session-list action with a rich toggle, a configurable metadata path, primary/muted state tones, and an archive filter defaulting to False.
- [x] Status is an ordinary session-list action with a fallback select form, a rich immediate-selection list, a configurable metadata path, and a multi-select status filter defaulting to Any.
- [x] Status options are `todo`, `in_progress`, `blocked`, and `done`; missing status behaves as `todo`.
- [x] Pin and archive are initially pinned when no user preference exists; status is not initially pinned.
- [x] Pin, archive, and status actions update sessions immutably, publish metadata-update events, report updated-session mutations, and refresh current list state.
- [x] Pinned ordering reads the configured pin metadata value from the shared summary and remains recency bucket, pin rank, then last-updated order.
- [x] Mobile and desktop produce equivalent rich-action state, invocation, and fallback behavior for the same declarations.
- [x] Unpinned rich actions remain available in the ordinary session action menu and use rich interaction when the frontend supports their kind.
- [x] The rich action, pin, archive, status, and ordering contracts are documented under `plugins/docs` and in affected plugin READMEs.
- [x] All non-visual requirements above have automated unit, integration, and component coverage.
- [ ] Filter placement, rich toggle colors/state, pinned status display, immediate list interaction, and fallback form are manually verified on mobile and desktop in light and dark themes.
  - This is the project-wide manual verification requirement declared in the parent task.

Parent Task: `tasks/20260719-plugin-session-archive-filters/000-main.md`

Depends On: `tasks/20260719-plugin-session-archive-filters/010-session-list-foundation.md`

Depends On: `tasks/20260719-plugin-session-archive-filters/020-plugin-driven-filters-and-search.md`

Depends On: `tasks/20260719-plugin-session-archive-filters/021-search-fields-and-status-list-footer.md`

## Baseline status handoff

The follow-up implementation owned by
`tasks/20260719-plugin-session-archive-filters/020-plugin-driven-filters-and-search.md`
now creates `plugins/session-status-app` with:

- the stable `set_session_status` application action;
- its ordinary `session_list_action` select form;
- the stable multi-select `session_status` filter;
- configurable metadata-key handling, immutable mutation, events,
  checkpoints, default configuration, documentation, and cross-layer tests.

Task 030 must extend that existing ordinary action with
`rich_ui.kind: "list"` and immediate selection. Do not recreate or rename the
plugin, action, filter, option values, or metadata configuration. The pin
plugin likewise already emits `pinned_state`; task 030 retains only the
ordinary rich-toggle migration for its row action. A manual-test regression
repair in task 020 also updated `session-ordering-buckets-app` to read the
configured pin key from `session_summary.metadata`. Task 030 must preserve and
verify that ordering behavior while replacing the temporary legacy row
control. Archive work remains wholly owned here.

The follow-up in
`tasks/20260719-plugin-session-archive-filters/021-search-fields-and-status-list-footer.md`
also adds `session_status_label`, the ordered `session_status_meta` row field,
and its application-default/server-override visibility setting. Task 030 must
preserve that list-trigger and presentation behavior while adding the rich
status action.

## Rich action contract

### Common behavior

`rich_ui` is optional and valid only as an enhancement of `ui_type: "session_list_action"`.

Common fields:

```typescript
interface SessionListRichUiBase {
  kind: 'toggle' | 'list';
  value_path: string;
  missing_value?: unknown;
  default_pinned?: boolean;
}
```

The action's top-level `label`, `icon`, action routing, and `dialog` remain authoritative for ordinary presentation and fallback.

Frontends that support the declared kind use rich interaction whether the action is invoked from its pinned representation or selected from the ordinary action menu. Pinning controls inline visibility; it does not determine whether rich invocation is available.

### Toggle

```typescript
interface SessionListToggleRichUi extends SessionListRichUiBase {
  kind: 'toggle';
  active_value: string | number | boolean;
  appearance: {
    active: { tone: SemanticTone };
    inactive: { tone: SemanticTone };
  };
}
```

Pin example:

```python
{
    "ui_type": "session_list_action",
    "id": "toggle_session_pinned",
    "label": "Pin or unpin",
    "icon": "star",
    "order": 10,
    "action_id": "toggle_session_pinned",
    "param_map": {
        "session_id": "$session.session_id",
    },
    "dialog": {
        "kind": "none",
    },
    "rich_ui": {
        "kind": "toggle",
        "value_path": "metadata.pinned",
        "missing_value": False,
        "active_value": True,
        "default_pinned": True,
        "appearance": {
            "active": {"tone": "warning"},
            "inactive": {"tone": "muted"},
        },
    },
}
```

Archive uses the same shape with:

```python
"icon": "archive",
"rich_ui": {
    "kind": "toggle",
    "value_path": "metadata.archived",
    "missing_value": False,
    "active_value": True,
    "default_pinned": True,
    "appearance": {
        "active": {"tone": "primary"},
        "inactive": {"tone": "muted"},
    },
}
```

Basic frontends ignore `rich_ui` and immediately execute these actions because their ordinary dialog kind is `none`.

### List

```typescript
interface SessionListListRichUi extends SessionListRichUiBase {
  kind: 'list';
  input_name: string;
  options: SessionListOption[];
}
```

Status example:

```python
{
    "ui_type": "session_list_action",
    "id": "set_session_status",
    "label": "Set status",
    "icon": "circle",
    "order": 30,
    "action_id": "set_session_status",
    "param_map": {
        "session_id": "$session.session_id",
        "status": "$dialog.status",
    },
    "dialog": {
        "kind": "form",
        "title": "Set status",
        "inputs": [
            {
                "name": "status",
                "type": "select",
                "label": "Status",
                "prefill_from": "$session.metadata.status",
                "default": "todo",
                "options": [
                    {"value": "todo", "label": "To do"},
                    {"value": "in_progress", "label": "In progress"},
                    {"value": "blocked", "label": "Blocked"},
                    {"value": "done", "label": "Done"},
                ],
                "required": True,
            }
        ],
    },
    "rich_ui": {
        "kind": "list",
        "value_path": "metadata.status",
        "missing_value": "todo",
        "input_name": "status",
        "default_pinned": False,
        "options": [
            {"value": "todo", "label": "To do", "tone": "muted"},
            {
                "value": "in_progress",
                "label": "In progress",
                "tone": "primary",
            },
            {"value": "blocked", "label": "Blocked", "tone": "danger"},
            {"value": "done", "label": "Done", "tone": "success"},
        ],
    },
}
```

The fallback form and rich list are separate presentation definitions. The plugin implementation should construct them from one internal option definition so labels and values cannot drift.

The form resolves stored status through `prefill_from`; `default: "todo"` applies only when that path is missing. The currently effective status is therefore visible even for sessions created before the status plugin existed.

When a rich frontend selects an option, it supplies the selected value as the declared `input_name` in the same dialog-value context used by the standard action runner. The existing `$dialog.status` mapping therefore works for both fallback form submission and rich immediate selection.

Selecting the current value closes the list without executing a redundant mutation.

### Semantic tones

Initial supported tones are:

- `primary`
- `warning`
- `success`
- `danger`
- `muted`

Tone resolution is frontend-owned and theme-aware. Plugins do not provide raw platform color strings for these built-in presentations.

## Plugin behavior

### Pin

- Configurable metadata key, default `pinned`.
- Rich toggle shown through ordinary action pinning.
- Boolean filter:

```python
{
    "ui_type": "session_list_filter",
    "id": "pinned_state",
    "label": "Pinned",
    "icon": "star",
    "type": "boolean",
    "match": "equals",
    "data": "metadata.pinned",
    "missing_value": False,
    "default": None,
}
```

- Ordering plugin reads the configured key from `session_summary.metadata`.

### Archive

- Configurable metadata key, default `archived`.
- Rich toggle with active primary tone.
- Boolean filter:

```python
{
    "ui_type": "session_list_filter",
    "id": "archive_state",
    "label": "Archive state",
    "icon": "archive",
    "type": "boolean",
    "match": "equals",
    "data": "metadata.archived",
    "missing_value": False,
    "default": False,
    "options": [
        {"value": False, "label": "Not archived"},
        {"value": True, "label": "Archived"},
    ],
}
```

### Status

- Configurable metadata key, default `status`.
- Built-in options and tones:

| Value | Label | Tone |
| --- | --- | --- |
| `todo` | To do | `muted` |
| `in_progress` | In progress | `primary` |
| `blocked` | Blocked | `danger` |
| `done` | Done | `success` |

- Missing metadata behaves as `todo`; it need not be written merely to display the default.
- Multi-select filter:

```python
{
    "ui_type": "session_list_filter",
    "id": "session_status",
    "label": "Status",
    "icon": "circle",
    "type": "select",
    "match": "one_of",
    "multiple": True,
    "data": "metadata.status",
    "missing_value": "todo",
    "default": [],
    "options": [
        {"value": "todo", "label": "To do", "tone": "muted"},
        {"value": "in_progress", "label": "In progress", "tone": "primary"},
        {"value": "blocked", "label": "Blocked", "tone": "danger"},
        {"value": "done", "label": "Done", "tone": "success"},
    ],
}
```

## Execution plan

### Shared rich-action model

Add typed rich-action unions and normalization to the frontend SDK without splitting session-list actions into another registry category. The registry continues exposing one ordered `sessionListActions` collection.

Normalization must preserve the ordinary action even when rich configuration is unusable. Rich state evaluation should reuse shared dotted-path utilities.

Extend shared action-menu components through a focused render/invocation extension point rather than putting pin/archive/status conditionals into `ActionsMenuBar`, `SessionsScreen`, or `SessionsPanel`. The exact component boundary requires human review before implementation; likely candidates are a session-list-specific rich action host plus shared toggle/list content.

### Pinned action behavior

Derive initial pinned keys from `rich_ui.default_pinned` only when no persisted preference exists. Existing per-connection persisted user choices remain authoritative.

Pinned rendering:

- ordinary actions keep their existing icon treatment;
- rich toggles display their top-level icon with active/inactive semantic tone;
- rich lists display the current option label and tone in a compact representation;
- status labels must not crowd unrelated row controls.

Unpinned rich actions remain in the ordinary action menu. Selecting them uses rich interaction on capable frontends and ordinary dialog fallback otherwise.

Review the compact status representation, maximum width/truncation, and mobile/desktop popover/modal wrappers before implementing layout.

### Plugin implementations

Migrate `session-pinned-app` to one ordinary `session_list_action`, remove `session_list_toggle_pinned`, and emit its filter. Do not retain a top-level `pinned` summary value or pin-specific frontend collection.

Add `session-archive-app` using the immutable metadata mutation, lock, event, checkpoint, and action-result pattern proven by pinning.

Extend the existing `session-status-app` action with its rich list. Keep its
one internal option definition authoritative for the existing fallback form
and status filter plus the new rich list.

Retain the existing `session-ordering-buckets-app` resolution of the configured
pin metadata key from `session_summary.metadata`, and keep its
recency/pin/last-updated priority semantics covered while migrating the pin UI.

Plugin project names, stable IDs shown in this task, and the touched default/example configurations should receive a final scope review before files are added.

### Frontend integration

Mobile and desktop should:

- consume ordinary `sessionListActions`;
- pass rich actions through the shared host;
- render persisted pinned actions in declared order;
- reload the list from ordinary action mutation effects;
- update visible state from refreshed summaries;
- fall back to `ApplicationActionDialog` for unsupported/invalid rich descriptors;
- use shared filter declarations delivered by the prerequisite task.

The status rich list uses immediate selection with no OK/Cancel. The fallback form remains independently testable by rendering the same action with rich support disabled or with an unsupported kind.

Do not add generic terminal action discovery in this task. Terminal receives pin/archive/status filters and plugin ordering through the prerequisite work, but status mutation remains available on frontends that already expose session-list actions.

### Documentation and scope

Extend the corrected `session_list_action` documentation with complete `toggle` and `list` schemas, fallback rules, pin preference behavior, semantic tones, value paths, immediate-selection semantics, and examples from all three plugins.

Update pin, ordering, archive, and status plugin READMEs and generated built-in/default-configuration documentation.

Do not generalize rich presentations to `session_action`, `message_action`, composer actions, or unrelated action-result displays in this task.

### Automated verification

Contract/SDK tests must cover:

- no rich descriptor;
- valid toggle and list descriptors;
- unknown and malformed kinds;
- fallback preservation;
- value/missing resolution;
- semantic tone selection;
- default versus persisted pinning;
- immediate list selection and no-op current selection.

Plugin tests must cover default/custom metadata keys, immutable mutation, locking, event/checkpoint publication, action results, all UI declarations, default values, and status option consistency.

Ordering tests must cover configured metadata lookup, recent/old and pinned/unpinned combinations, order specifications, and absence of any top-level pin dependency.

Shared component and mobile/desktop tests must cover pinned and unpinned invocation, toggle rendering, status rendering, rich list selection, fallback form submission, action failure, list reload, row-event propagation, stored pin preferences, and filter integration.

Configuration tests and documentation preparation/build must pass.

### Manual verification

After automated tests pass, verify mobile and desktop in light and dark themes:

- search and adjacent filter control placement;
- active-filter indication;
- inactive and active pin/archive tones;
- default-pinned behavior;
- compact pinned status label/tone;
- current-status marker;
- one-click status change without OK/Cancel;
- fallback form with prefilled current status and OK/Cancel;
- row layout with several pinned actions.

Record the devices/simulators, themes, and concise results in completion notes.

### Approved completion plan

Added during task completion after explicit user approval on July 21, 2026.

1. Extend the frontend SDK with discriminated `toggle` and `list` rich-action
   contracts, strict kind-specific normalization, pure value/current-option
   evaluation, semantic-tone selection, immediate dialog-value construction,
   current-value no-op handling, and declaration-ordered default-pin
   derivation. Preserve every valid ordinary action when `rich_ui` is absent,
   malformed, or unsupported.
2. Retire the temporary pin compatibility surface: remove
   `session_list_toggle_pinned`, `sessionListPinnedToggles`, and the
   deprecated top-level `SessionSummary.pinned`. Keep one ordered
   `sessionListActions` collection.
3. Make shared and mobile pin-preference persistence distinguish absent
   storage from a stored empty/custom preference. Apply `default_pinned` only
   while no persisted preference exists, including when application UI schema
   declarations arrive or refresh after initial render.
4. Add a session-list-specific rich-action host and shared toggle/list content
   in the React Native component package. Extend the generic action menu only
   with presentation render hooks; it must not contain pin/archive/status
   conditionals. Use theme semantic tones and stable accessibility identifiers.
5. Migrate the pin plugin to its ordinary rich-toggle action, create
   `session-archive-app` with stable IDs `session_archive`,
   `toggle_session_archived`, `archive_state`, and
   `session_archived_metadata_key`, and add rich-list metadata to the existing
   stable status action. Enable archive in the maintained default
   configuration. Preserve status's existing `session_status_label`,
   `session_status_meta`, and server-scoped footer visibility setting.
6. Integrate the shared host into mobile and desktop session lists. Mobile
   presents rich lists in its modal surface; desktop directly reuses the
   completed generic native `NSPopover` coordinator. Unsupported rich
   descriptors continue to use the existing ordinary action dialogs.
7. Extend the existing mobile and desktop production session-list harnesses
   and native desktop popover harness rather than creating parallel test-only
   interfaces. Cover mutations, summary refresh, status-footer refresh and
   visibility, default/persisted pins, fallback forms, filters, and configured
   ordering.
8. Update plugin and public contract documentation, run focused and
   cross-layer automated verification, then perform the required mobile and
   desktop light/dark manual visual pass. Record verified environments,
   outcomes, known environment blockers if any, and completion details in this
   task file and the parent checklist.

## Completion Notes

Added during task completion on July 21, 2026.

Implemented the rich `session_list_action` contract end-to-end:

- The frontend SDK now normalizes `rich_ui.kind` `toggle` and `list`
  descriptors, preserves ordinary actions for absent, malformed, and future
  descriptors, derives rich state from configured summary paths, builds typed
  immediate-list inputs, and derives declaration-ordered default pins.
- The compatibility-only pin UI type, pin-specific frontend registry, and
  deprecated top-level pin summary field are removed. Pin is now an ordinary
  rich-toggle action. A new `session-archive-app` provides the configured
  archive action and default-false archive filter. The stable status action
  retains its ordinary form and adds the rich immediate-selection list.
- Shared React Native controls render rich pinned actions, preserve ordinary
  dialog fallback, and keep generic menu infrastructure plugin-agnostic.
  Mobile uses a modal rich list; desktop uses the existing native popover
  coordinator. Mobile waits for its action-menu modal to dismiss before
  presenting a rich list and gives that list a non-zero modal height; both
  defects were exposed and corrected by the iOS native suite.
- Pin preferences now distinguish absent storage from a stored empty/custom
  preference, so defaults can arrive with late plugin schema while stored
  choices remain authoritative. Pinned rendering follows declaration order.
- Updated plugin and contract documentation, default configuration reference,
  built-in-plugin docs navigation, configuration tests, fixtures, and
  production mobile/desktop test harnesses.

Automated verification completed:

- SDK: `npm --workspace @crystal-lattice/frontend-sdk test -- --run src/sessions/sessionListContracts.test.ts src/plugins/pluginsRegistry.test.ts` — 36 passed.
- React SDK and shared RN components: focused suites passed (5 and 7 tests).
- Mobile unit/component suites: 13 passed; mobile real-backend component
  integration passed.
- Python plugin/configuration/HTTP/ordering suite: 31 passed.
- Documentation preparation and `mkdocs build -f docs_site/mkdocs.yml` passed.
- iOS native: rebuilt and ran
  `npm run detox:test:session-list:ios` on iPhone 17 Pro / iOS 26.1 — 6 passed.
- Android native: rebuilt and ran
  `npm run detox:test:session-list:android` on Medium_Phone_API_36.1 — 6 passed.
- Desktop Jest `SessionsPanel` suite passed (3 tests). The macOS XCUITest
  target compiled, but its runner failed before test execution because macOS
  timed out while enabling UI automation. This is an environment/permission
  blocker, not an assertion or build failure.

Manual visual verification remains pending. This environment cannot inspect
the simulator or desktop UI visually, and the macOS XCUITest automation
failure prevents a substitute native desktop pass. The remaining requirement
is to inspect mobile and desktop in light and dark themes for the exact
checklist in **Manual verification** above, especially rich toggle colors,
compact status/current marker, immediate selection, fallback form, and
multi-pinned row layout. Do not mark this task or its parent checklist complete
until that review is recorded.

### Placement and highlight follow-up completion notes

Added during task completion on July 21, 2026.

Implemented the approved generic placement and yellow-pin follow-up:

- `rich_ui.placements` is an optional ordered array. Known placements are
  `actions_bar`, `header_leading`, and `header_trailing`; absence defaults to
  `actions_bar`. Unknown strings remain transportable, while invalid and
  duplicate entries are discarded with diagnostics.
- Frontends choose the first declared supported rich action for each header
  slot and independently render an action-bar placement. This prevents
  duplicate controls in a single slot while allowing one declaration to
  request multiple locations. The ordinary action menu remains available for
  all actions and retains dialog fallback.
- Added the generic semantic `highlight` tone and a shared yellow theme token
  (`#FFCC00` light, `#FFD60A` dark). The action-menu pin star now also uses
  that token. Pin action/filter active state migrated from `warning` to
  `highlight`.
- The pin plugin now declares `["header_trailing", "actions_bar"]`, restoring
  its trailing title-corner control while leaving actions-bar visibility under
  the existing user preference.

Verification for this placement-only follow-up:

- SDK placement/filter/registry suites: 64 passed.
- Shared RN component suite: 7 passed.
- Mobile component suites: 15 passed; includes header-only exclusion and
  dual-placement single-render assertions.
- Desktop `SessionsPanel` suite: 4 passed; includes first-declared header-slot
  conflict resolution plus separate actions-bar placement.
- Python filter, pin plugin, default-config, and HTTP coverage: 13 passed.
- Documentation preparation and MkDocs build passed.
- The focused desktop TypeScript check has only the pre-existing missing
  `react-native-vector-icons/Feather` declaration errors.

At the user's direction, native Detox/XCUITest was not rerun for this
placement-only change. A fresh iOS build succeeded; the subsequent Detox run
was canceled during its final filter test, so it is not counted as a passing
run. The original task's earlier full iOS and Android native results remain
recorded above.

### Detox cleanup follow-up notes

Added during task completion on July 21, 2026.

At the user's direction, reduced the session-list Detox suite from six
assertion-focused scenarios to one native component smoke scenario. It retains
the native session-row ordering check and the action-menu → rich-list modal →
immediate action-submission path. The removed fallback-form, detailed
presentation, pin/archive visibility, main-search, and filter/Reset assertions
are covered by the existing component, SDK, and real-backend component
integration tiers. Added a shared-component archive action assertion so the
removed native archive-visibility check retains direct coverage. The separate
transcript Detox suite remains unchanged because its physical swipe,
inverted-list virtualization, and variable-height scroll behavior require a
native host.

### Native smoke verification update

Added during task completion on July 21, 2026.

The consolidated iOS session-list Detox smoke was rerun after the cleanup and
passed: 1 suite, 1 test. It verified the real native session-row ordering and
the action-menu → rich-status modal → immediate action-submission flow.

### Approved follow-up plan

Added during task completion after explicit user approval on July 21, 2026.

1. Extend the rich-action contract with a strictly normalized ordered
   `rich_ui.placements` array. Its supported values are `actions_bar`,
   `header_leading`, and `header_trailing`; absent placement retains the
   existing `actions_bar` behavior. Invalid entries are discarded without
   losing the ordinary action, and frontend support is evaluated per
   placement so an unsupported preferred slot can fall through to a later
   declared one without duplicate UI declarations.
2. Add the generic semantic `highlight` tone, mapped to the existing yellow
   theme token. Migrate the active pin appearance from `warning` to
   `highlight`; archive and status tones remain unchanged.
3. Make the shared session-list host expose each rich action at every
   supported declared placement. Header slots are independently
   deterministic: the lowest declaration order wins each slot, while the
   action bar keeps its existing pinned-preference semantics. The ordinary
   action menu and dialog fallback always remain available.
4. Update mobile and desktop session rows to render generic leading/trailing
   header slots and keep the actions-bar path intact. Pin will declare
   `header_trailing` plus `actions_bar`, restoring its prior title-corner
   presence while retaining a user-configurable action-bar placement.
5. Extend SDK, shared/mobile/desktop, plugin, native-harness, documentation,
   and light/dark verification coverage for placements, conflict ordering,
   unknown-slot fallback, yellow pin tone, and ordinary-menu preservation.

Rerun attempt on July 21, 2026: the focused macOS suite entered UI automation
and launched the production popover harness, but both XCTest cases were
blocked by a host-level `Force Quit Applications` dialog from `loginwindow`.
The rich status action existed in the native popover; its click failed only
because that system dialog covered it. Dismiss the host dialog, then rerun
`npm run test:macos-ui:session-filters` before recording desktop visual
verification.

## Archive ordering follow-up

### Requirements checklist

- [x] Sessions archived within the approved age window sort below
  non-archived sessions in the shared application session-list order.
- [x] Archive-derived ordering does not affect sessions older than the
  approved two-month boundary; those sessions retain the existing recency,
  pin-rank, and last-updated ordering behavior.
- [x] Archive ordering reads the same configurable
  `application.session_archived_metadata_key` as `session-archive-app`, with
  missing or non-`true` metadata treated as not archived.
- [x] HTTP, terminal, mobile, and desktop receive the same order through the
  existing application listing pipeline; client-side filtering preserves it.
- [x] The ordering contract and plugin documentation describe archive rank,
  its age exemption, and its configured metadata key.
- [x] Automated coverage proves rank calculation, exact age-boundary
  behavior, configured-key handling, composed ordering, and the public
  application/HTTP result.

### Supporting details and recommended decisions

`session-ordering-buckets-app` is the sole ordering contributor. It currently
computes `updated_24h_rank`, `pinned_rank`, and
`last_updated_sort_key`; the shared application listing service applies those
specifications before filters, and frontends preserve the returned sequence.
`session-archive-app` already owns `application.session_archived_metadata_key`
and defaults its archive filter to false, so the new rank is observable when
the archive filter is set to Any or Archived.

Recommended semantics, requiring approval with this draft:

- Treat “two months” as a rolling fixed 60-day (`60 * 24 * 60 * 60`) window,
  not calendar-month arithmetic. This is deterministic for epoch timestamps
  and matches the ordering plugin's existing seconds-based 24-hour window.
- Reuse the plugin's existing effective last-updated timestamp:
  `session_updated_at` when `session_order_use_updated_at` is enabled and
  valid, otherwise `modified`; an unusable timestamp remains the existing
  neutral `0` and is therefore age-exempt.
- A summary whose age is exactly 60 days remains in the archive-ordering
  window. Only an age greater than 60 days is exempt.
- Add `recent_archived_rank`: `1` only for archived summaries in that window,
  otherwise `0`. Emit it at priority 5, before the existing recency (10),
  pin (20), and last-updated (30) ranks. This is the recommended reading of
  “sorted lower than other sessions”: a recent archived session is below every
  non-archived session, not merely below one inside its current recency
  bucket. An older archived session receives `0` and is ordered solely by the
  existing ranks.
- Do not add a new user setting or frontend-specific ordering. The two-month
  policy is fixed for this feature; the existing shared archive metadata-key
  setting remains the only configuration surface.

## Execution plan

Status: Approved

### Component and module boundaries

Extend only `plugins/session-ordering-buckets-app`:

1. Declare and resolve `session_archived_metadata_key` with the same
   normalization/default as `session-archive-app`, alongside the existing
   configured pin key.
2. Compute `recent_archived_rank` from the resolved archive metadata and
   effective last-updated timestamp, then emit it as the first contributed
   order specification.
3. Leave `core/python/agent_app/session_listing.py`, the HTTP route, terminal,
   frontend SDK, and graphical frontends unchanged. They already compose and
   preserve contributed ordering before filtering.

This avoids duplicating archive-state interpretation in clients and preserves
the archive plugin as the owner of mutation/filter declarations while the
ordering plugin remains the owner of rank calculation.

### Implementation approach

1. Update the ordering plugin's module documentation, schema, initialized
   state, and action description to describe archive-aware ranking.
2. Reuse the current effective-update computation and strict `is True`
   metadata interpretation to derive the new rank. Preserve all existing
   order fields and priorities after inserting the archive rank at priority 5.
3. Extend the ordering plugin unit tests with frozen time for recent active,
   recent archived, exactly-60-day archived, older archived, missing archive
   metadata, custom archive metadata key, and the
   `session_updated_at`/`modified` fallback path. Put rank/priority assertions
   in `plugins/session-ordering-buckets-app/tests/test_session_ordering_buckets_app_bucket_logic.py`
   and configuration/initialized-state assertions in
   `plugins/session-ordering-buckets-app/tests/test_session_ordering_buckets_app_plugin_unit.py`,
   alongside the existing ordering tests.
4. Extend application/HTTP session-list coverage with both archive and
   ordering plugins installed. Verify the complete unfiltered/Any archive
   sequence, confirm the default archive filter remains unchanged, and use a
   custom archive metadata key so the archive action/filter/order consumers
   cannot drift. Add this to
   `application/python/tests/test_session_list_http_contract.py` next to
   `test_session_list_http_contract_orders_configured_pinned_metadata`.
5. Update the ordering and archive plugin READMEs and the relevant
   contributed-ordering documentation to state the rank priority and
   two-month exemption. No bundled default configuration change is planned
   because the existing archive metadata-key default is sufficient.

### Requirement verification

- Rank and boundary semantics:
  `plugins/session-ordering-buckets-app/tests/test_session_ordering_buckets_app_bucket_logic.py`
  with `time.time` fixed at a deterministic epoch.
- Plugin configuration and configured-key state:
  `plugins/session-ordering-buckets-app/tests/test_session_ordering_buckets_app_plugin_unit.py`.
- Shared ordering behavior: application/HTTP integration coverage exercising
  the public `/sessions` response and direct application query with archive
  filtering disabled in
  `application/python/tests/test_session_list_http_contract.py`.
- Configured metadata key: integration fixture sets
  `session_archived_metadata_key` to a non-default key and verifies the
  archive action/filter/order use it consistently.
- Consumer parity: existing shared listing architecture is retained; the
  integration test proves the HTTP boundary and existing terminal/frontend
  tests establish that consumers delegate to and preserve application order.
  No UI-specific test is needed because no UI code or local sort is changed.

### Documentation

Update the ordering plugin README for users configuring archive and pin
metadata keys, the archive plugin README to explain its ordering interaction,
and the plugin action/order documentation for plugin authors. The docs will
make clear that archive ordering applies only to recently updated summaries
and does not alter the default archive filter.

### Task checklist

- [x] Confirm the recommended 60-day, effective-update, global-priority, and
  exact-boundary semantics through plan approval.
- [x] Implement archive rank and shared archive metadata-key resolution in the
  ordering plugin.
- [x] Add unit and application/HTTP regression tests.
- [x] Update documentation and run the focused plugin, application/HTTP, and
  documentation-build verification.
- [x] Record evidence and any relevant manual observation in completion notes.

### Archive ordering follow-up completion notes

Completed on July 21, 2026.

- `session-ordering-buckets-app` now emits `recent_archived_rank` at priority
  5. It is `1` only for a literal `True` archive value whose effective
  last-updated timestamp is at most 60 days old; it is `0` for active,
  missing/non-boolean, and older archived summaries. The existing 24-hour,
  pin, and last-updated ranks follow unchanged.
- The ordering plugin now resolves
  `application.session_archived_metadata_key` using the same default and
  normalization as `session-archive-app`. No client, terminal, HTTP route, or
  default configuration change was needed because all list consumers already
  delegate to the shared application ordering pipeline.
- Added direct ordering-plugin coverage for the new field/order priority,
  exact 60-day boundary, one-second age exemption, `modified` fallback,
  custom key, and non-boolean archive data. Added an HTTP/application
  integration fixture that toggles archive through the configured custom key,
  checks the complete public `/sessions` order, and proves the default archive
  filter still hides both archived sessions.
- Updated the ordering and archive plugin READMEs plus the contributed-order
  documentation.

Verification:

- `pytest plugins/session-ordering-buckets-app/tests plugins/session-archive-app/tests application/python/tests/test_session_list_http_contract.py core/python/tests/test_application_session_listing.py -q` — 21 passed.
- Focused Black and Ruff checks passed.
- `python docs_site/scripts/prepare_mkdocs_site.py && mkdocs build -f docs_site/mkdocs.yml` passed, with the repository's existing Material, Pydantic, nav, and Griffe warnings.
- `git diff --check` passed.
