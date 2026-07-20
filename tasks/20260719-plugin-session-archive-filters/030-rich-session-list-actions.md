# Rich session-list actions

Extend ordinary session-list actions with optional toggle and list presentations, then deliver pin, archive, status, and pinned ordering as complete plugin features across the supported graphical frontends.

## Requirements checklist

- [ ] A `session_list_action` with no `rich_ui`, an unknown rich kind, or invalid rich configuration retains its ordinary dialog and execution behavior.
- [ ] Every rich-presentation-specific field is nested under the single `rich_ui` key.
- [ ] A rich `toggle` reads current state from session-summary data, displays configured active/inactive semantics when pinned, and invokes the ordinary action immediately.
- [ ] A rich `list` reads and displays the current option when pinned, marks it in the selection list, and invokes the ordinary action immediately when another option is selected.
- [ ] Rich-list selection has no OK/Cancel confirmation, while its ordinary fallback remains a separate form with the current value prefilled and explicit OK/Cancel submission.
- [ ] Rich action pinning remains a user preference; `default_pinned` applies only when no stored preference exists.
- [ ] Unsupported or malformed rich configuration never hides an otherwise valid ordinary action.
- [ ] Pinning is an ordinary session-list action with a rich toggle, a configurable metadata path, warning/muted state tones, a pin filter defaulting to Any, and no pin-specific UI type or top-level summary field.
- [ ] Archiving is an ordinary session-list action with a rich toggle, a configurable metadata path, primary/muted state tones, and an archive filter defaulting to False.
- [ ] Status is an ordinary session-list action with a fallback select form, a rich immediate-selection list, a configurable metadata path, and a multi-select status filter defaulting to Any.
- [ ] Status options are `todo`, `in_progress`, `blocked`, and `done`; missing status behaves as `todo`.
- [ ] Pin and archive are initially pinned when no user preference exists; status is not initially pinned.
- [ ] Pin, archive, and status actions update sessions immutably, publish metadata-update events, report updated-session mutations, and refresh current list state.
- [ ] Pinned ordering reads the configured pin metadata value from the shared summary and remains recency bucket, pin rank, then last-updated order.
- [ ] Mobile and desktop produce equivalent rich-action state, invocation, and fallback behavior for the same declarations.
- [ ] Unpinned rich actions remain available in the ordinary session action menu and use rich interaction when the frontend supports their kind.
- [ ] The rich action, pin, archive, status, and ordering contracts are documented under `plugins/docs` and in affected plugin READMEs.
- [ ] All non-visual requirements above have automated unit, integration, and component coverage.
- [ ] Filter placement, rich toggle colors/state, pinned status display, immediate list interaction, and fallback form are manually verified on mobile and desktop in light and dark themes.
  - This is the project-wide manual verification requirement declared in the parent task.

Parent Task: `tasks/20260719-plugin-session-archive-filters/000-main.md`

Depends On: `tasks/20260719-plugin-session-archive-filters/010-session-list-foundation.md`

Depends On: `tasks/20260719-plugin-session-archive-filters/020-plugin-driven-filters-and-search.md`

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
