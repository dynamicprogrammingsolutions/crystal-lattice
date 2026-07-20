# Plugin-driven session filters and search

Deliver the expanded declarative filter contract, replace hardcoded session search with a main-search plugin, and expose the same filter semantics in terminal, mobile, and desktop.

## Requirements checklist

- [x] `session_list_filter` supports text, boolean, single-select, and multi-select controls with only the valid type/match combinations defined in this task.
- [x] Filter evaluation follows the same path, missing-value, case-sensitivity, inactivity, OR-within-filter, AND-across-filters, default, Reset, Show all, and order-preservation rules in Python and TypeScript.
- [x] Zero or one effective main-search filter is valid; competing main-search declarations produce a clear schema error.
- [x] Mobile and desktop always retain a shared trivial fallback search over available session-summary text (at least session ID) when no unambiguous valid main-search declaration exists; terminal free-text search remains plugin-driven.
- [x] The built-in main-search plugin searches session ID, preview, and derived presentation title/subtitle/meta with case-insensitive `contains`.
- [x] HTTP mobile and desktop clients filter the complete loaded session collection locally without changing backend request shape or server/application order.
- [x] Terminal filtering uses the shared in-process application query path and does not duplicate filter interpretation in terminal UI code.
- [x] Terminal session selection supports default filters, main-search text, explicit non-main filter overrides, completion, and exact-ID access independent of filters.
- [x] Mobile and desktop always render a search input, use a valid main-search declaration when available, and render an adjacent filter control when plugin-declared non-main filters exist.
- [x] Boolean filters expose Any/True/False, select filters expose Any or selected options, and multi-select filters allow multiple option values.
- [x] Reset restores plugin defaults, while Show all deactivates every filter.
- [x] Filter state is scoped to the active connection and current declaration set; removed or changed declarations cannot leave stale effective values.
- [x] Empty-state and active-filter indications distinguish an empty store from a filtered result.
- [x] The filter contract and main-search plugin are documented under `plugins/docs` and in the plugin README.
- [x] All requirements above have automated unit, integration, component, or terminal-command coverage.

## Task checklist

- [x] Follow up: add a configurable Boolean pin filter to `session-pinned-app`.
- [x] Follow up: add the baseline `session-status-app` ordinary action and multi-select filter, leaving rich-list presentation to task 030.
- [x] Follow up: enable both filter providers in the maintained default configuration and verify terminal, HTTP, mobile, and desktop behavior.
- [x] Follow up: update plugin documentation, automated coverage, manual-testing guidance, and completion notes.
- [x] Manual-test regression repair: restore configured pin ordering and active-star state without restoring the removed top-level summary field.

Parent Task: `tasks/20260719-plugin-session-archive-filters/000-main.md`

Depends On: `tasks/20260719-plugin-session-archive-filters/010-session-list-foundation.md`

## Filter contract

### Common element

```python
{
    "ui_type": "session_list_filter",
    "id": "stable_filter_id",
    "label": "Filter label",
    "icon": "filter",
    "order": 10,
    "data": "metadata.some_value",
    "type": "text",
    "match": "contains",
    "default": "",
}
```

`data` may be one dotted path or an ordered list of paths. Paths are evaluated against the shared session-list evaluation context.

Options use:

```typescript
interface SessionListOption {
  value: string | boolean;
  label: string;
  icon?: string;
  tone?: 'primary' | 'warning' | 'success' | 'danger' | 'muted';
}
```

### Valid combinations

#### Text

```python
{
    "type": "text",
    "match": "contains",  # or "equals"
    "data": ["session_id", "preview"],
    "case_sensitive": False,
    "default": "",
}
```

- Runtime value is a string.
- Empty string is inactive.
- Paths inside the filter combine with OR.
- Non-string resolved values do not match text operators.

#### Boolean

```python
{
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

- Runtime value is `null`, `true`, or `false`.
- `null` means Any/inactive.
- The framework supplies an Any choice; plugins may label True and False through boolean-valued options.

#### Single select

```python
{
    "type": "select",
    "match": "equals",
    "multiple": False,
    "data": "metadata.status",
    "default": None,
    "options": [
        {"value": "todo", "label": "To do"},
        {"value": "done", "label": "Done"},
    ],
}
```

- Runtime value is `null` or one declared option value.
- `null` means Any/inactive.

#### Multiple select

```python
{
    "type": "select",
    "match": "one_of",
    "multiple": True,
    "data": "metadata.status",
    "default": [],
    "options": [
        {"value": "todo", "label": "To do"},
        {"value": "in_progress", "label": "In progress"},
        {"value": "blocked", "label": "Blocked"},
        {"value": "done", "label": "Done"},
    ],
}
```

- Runtime value is a list of declared option values.
- An empty list means Any/inactive.
- A summary matches when its resolved scalar value is one of the selected values.

### Main search

The built-in main-search plugin contributes:

```python
{
    "ui_type": "session_list_filter",
    "id": "session_search",
    "label": "Search",
    "icon": "search",
    "order": 0,
    "type": "text",
    "match": "contains",
    "data": [
        "session_id",
        "preview",
        "presentation.title",
        "presentation.subtitle",
        "presentation.meta",
    ],
    "case_sensitive": False,
    "default": "",
    "main_search": True,
}
```

`main_search` is invalid on boolean or select filters. A consumer must not silently select one declaration when multiple effective plugins mark a main search.

Mobile and desktop retain a shared frontend fallback search when there is no
unambiguous valid main-search declaration. The fallback is case-insensitive
`contains` over the available ordinary summary text, including at least
`session_id` and preserving preview/presentation search where those fields are
available. A schema conflict is still reported clearly and no competing plugin
declaration is selected. Terminal free-text search has no hardcoded fallback
and therefore requires one valid plugin-declared main search.

### Composition and state

Given active filters `A`, `B`, and `C`, a session passes only when:

```text
A(session) AND B(session) AND C(session)
```

Given paths `x`, `y`, and `z` inside one filter, that filter passes when:

```text
match(x) OR match(y) OR match(z)
```

`missing_value` is substituted only when a path cannot be resolved. It does not replace explicit `null`, false, zero, or an empty string.

Reset restores each declaration's `default`. Show all sets:

- text to `""`;
- boolean to `null`;
- single select to `null`;
- multiple select to `[]`.

## Terminal contract

The intended command behavior is:

```text
/session
/session <exact-session-id>
/session <search text>
/session --filter <filter-id>=<value> [search text]
```

Rules:

- `/session` lists sessions using plugin defaults and plugin ordering.
- An exact existing session ID switches directly even if default filters hide it.
- A non-exact argument becomes the main-search value and displays matching choices.
- `--filter` accepts stable plugin filter IDs.
- Boolean values accept `any`, `true`, and `false`.
- Single-select values accept `any` or one declared option value.
- Multi-select values accept `any` or a documented delimiter-separated set of option values.
- Text filter overrides accept a string.
- Unknown filter IDs, invalid values, or filters unsupported by their declaration produce user-facing errors.
- Completion includes filter IDs, valid boolean/select values, and matching session IDs.
- Terminal UI code parses interaction syntax but delegates matching and ordering to `TerminalApplication`/`AgentApplication`.

The exact multi-select delimiter and quoting behavior must be approved during implementation planning before command parsing is written.

## Execution plan

### Shared interpretation

Implement one focused TypeScript filter module in `packages/frontend-sdk` and one focused Python filter module used by the application listing service. Both consume the same normalized contract and conformance cases.

Validation should reject invalid type/match combinations per element while preserving other valid filters. Competing main-search declarations should put the filter schema into a clear error state so search is not silently ambiguous.

The Python application path applies defaults and terminal-supplied values. HTTP listing requests remain unfiltered. The TypeScript path applies filters to the already ordered summaries held by the session controller.

### Main-search plugin

Create a narrowly declarative built-in application plugin for the main-search element. It has no executable action and no filtering implementation. Include it in maintained default/example configurations and plugin packaging inputs.

The plugin's stable ID and project name should be reviewed before implementation, but the filter ID remains `session_search` unless review finds a collision.

### Mobile and desktop filter experience

Place reusable filter state and filter-content UI in shared frontend packages:

- pure normalization, defaults, Reset/Show-all, matching, and active-count logic in `frontend-sdk`;
- reusable text/boolean/select filter controls in `frontend-rn-components`;
- thin modal/popover wrappers and layout in mobile and desktop.

The search input is always rendered. One valid main-search declaration controls
its label and matching; otherwise the shared frontend fallback search remains
available. The filter control sits immediately to its right and is visible only
when non-main filters exist. It indicates when effective non-main filters
differ from Show all.

Desktop must reset its visible session window when effective filter values change. Both clients must scope state by connection plus effective declaration identity so plugin changes cannot retain stale IDs or values.

Before implementation, review whether desktop uses a native popover wrapper or the same modal shell as mobile. Shared filter content should not be duplicated regardless of surface choice.

### Terminal integration

Keep query construction and validation in `TerminalApplication` or a small terminal-facing helper; keep actual summary filtering in the application service.

Before implementation, approve:

- multi-select delimiter and escaping;
- how multiple matches are displayed and selected;
- whether filter overrides apply only to the current command or persist for the terminal process.

The recommended initial behavior is command-local overrides, avoiding hidden persistent terminal state.

### Documentation and scope

Document the complete filter table, inactivity rules, defaults versus Show all, path composition, main-search constraints, options, validation behavior, and client-versus-server execution in `plugins/docs/ui-elements.md`. Cross-link application-plugin and action docs where appropriate and document the main-search plugin in its README.

Do not add HTTP filter parameters, backend transport capabilities, remote pagination behavior, or message-search abstractions.

### Automated verification

Shared Python/TypeScript conformance cases must cover:

- every valid and invalid type/match combination;
- one and multiple data paths;
- case-sensitive and insensitive text;
- missing versus explicit false/null/empty values;
- inactive values;
- filter AND and path OR composition;
- defaults, Reset, and Show all;
- select option validation;
- main-search absence and conflict;
- order preservation.

Application tests must cover filtered terminal queries after plugin ordering. Terminal tests must cover syntax, exact-ID precedence, defaults, every filter control type, invalid input, completion, multiple matches, and no matches.

Mobile/desktop tests must cover plugin-driven and no-plugin fallback search,
adjacent filter control, local-only filtering, active indication, empty states,
state scoping, Reset/Show all, schema-conflict fallback with a visible warning,
and desktop window reset.

Plugin/configuration tests must cover the main-search declaration and default loading. Documentation preparation/build must pass.

### Approved completion plan

Added during task completion after explicit user approval.

1. Extend the shared language-neutral fixtures under
   `test/fixture/session-list/v1/` and add matching public-boundary Python and
   TypeScript conformance coverage for normalization, typed values, path OR,
   filter AND, missing-versus-explicit values, case handling, inactivity,
   defaults, Reset, Show all, order preservation, duplicate IDs, and
   main-search conflicts.
2. Add a focused Python filter engine under `agent_app`, install it in the
   application session-list service, expose normalized schema/value-query
   capabilities through `AgentApplication`, and retain ordering → filtering →
   limit. Structured filter diagnostics remain nonfatal to unrelated valid
   declarations.
3. Add the declarative `session-main-search-app` plugin
   (`session_main_search_app.SessionMainSearchAppPlugin`, application plugin ID
   `session_main_search`, filter ID `session_search`) with no executable
   actions. Include it in maintained default/example configurations and
   packaging discovery.
4. Keep HTTP session listing unfiltered and unchanged. Extend the existing
   FastAPI `TestClient` serialized contract and production
   `RestAgentBackend` transport tests to prove plugin defaults and frontend
   filter state never alter the HTTP request or server ordering.
5. Implement terminal query construction and typed override validation in
   `TerminalApplication` or a focused terminal-facing helper, while delegating
   matching/order to `AgentApplication`. Use command-local overrides,
   comma-separated multi-select values with CSV quoting after shell-style
   tokenization, exact-ID precedence, and numbered confirmation for every
   non-exact result set.
6. Add shared frontend filter schema/state/evaluation in `frontend-sdk`, React
   state scoped by connection plus normalized declaration identity, and shared
   React Native filter content. Mobile uses a modal; desktop uses an anchored
   in-tree dropdown/popover.
7. Mobile and desktop always keep a search box. Exactly one valid main-search
   declaration controls it; otherwise a shared case-insensitive fallback
   searches available summary text including at least session ID and preserves
   preview/presentation search. Competing declarations produce a visible
   schema warning and use the fallback without selecting a plugin declaration.
   Terminal free-text search remains plugin-driven.
8. Replace screen-local matching with shared evaluation over the complete
   loaded, server-ordered collection. Add active-filter indication, distinct
   empty-store/filtered-empty states, Reset/Show-all behavior, stale-state
   reconciliation, and desktop visible-window reset on every effective filter
   change.
9. Extend the existing production-screen mobile/desktop component tests, React
   diagnostics selector test, real-backend mobile component integration, and
   deterministic `MobileSessionListHarness`/Detox suite. Reuse production
   helpers in mocks, add stable production test IDs/accessibility labels, run
   gated tests explicitly, and execute the native session-list smoke on both
   iOS Simulator and Android Emulator.
10. Update the complete public contract in `plugins/docs`, the new plugin
    README, docs navigation, and generated default-config reference. Run
    focused and package-level Python/TypeScript/Jest verification, default
    configuration and packaging tests, mobile type checking, and docs
    preparation/build. Do not report skipped, collection-failed, teardown-
    failed, or otherwise nonzero commands as successful.

Approved human-review decisions:

- filter ID `session_search` and plugin identity described above;
- duplicate filter IDs are rejected rather than resolved by declaration order;
- competing main searches remain a clear schema error while frontend fallback
  search stays available;
- terminal multi-select uses comma-delimited CSV values and shell-style
  quoting;
- exact IDs switch immediately; non-exact matches are always displayed for
  numbered/ID selection;
- terminal overrides are command-local;
- desktop uses the existing React-tree anchored dropdown/popover rather than a
  separate native popover root.

## Completion Notes

Added during task completion.

- Added the shared, versioned filter conformance fixture under
  `test/fixture/session-list/v1/filter-cases.json`. Python and TypeScript consume
  the same valid/invalid declaration, schema-composition, typed-value,
  missing-value, path-OR, filter-AND, default, Show-all, and ordering cases.
- Added `agent_app.session_filters`, installed it as the normal
  `SessionListService` evaluator, and exposed normalized schema plus
  terminal-input coercion through `AgentApplication`. Filtering remains
  ordering → filtering → limit, and exact summary access remains unfiltered.
- Added nonfatal diagnostics for invalid declarations and runtime values,
  duplicate filter IDs, and ambiguous main searches. Individually valid
  unrelated filters remain usable. The string select value `any` is reserved
  for terminal inactivity and is rejected during normalization.
- Added the `session-main-search-app` application plugin. It contributes no
  actions and searches session ID, preview, and application-derived
  title/subtitle/meta using case-insensitive `contains`. The maintained default
  config, generated config reference, docs navigation, and runtime bundle
  selection include it.
- Reworked `/session` around the shared application query. It now applies plugin
  defaults, supports command-local `--filter id=value` overrides, parses
  multi-select values as shell-tokenized CSV, completes filter IDs/options and
  matching IDs, bypasses filters for exact IDs, and displays every non-exact
  result set for numbered/ID confirmation.
- Kept the HTTP API and `RestAgentBackend` request shape unchanged. FastAPI
  `TestClient` coverage proves an active plugin default does not filter
  `/sessions`, while mobile and desktop evaluate the complete loaded ordered
  collection locally.
- Added shared frontend schema/evaluation/default/Show-all logic, React state
  scoped by connection plus normalized declaration identity, and reusable React
  Native controls for text, Boolean, single-select, and multi-select filters.
  Plugin labels, icons, and tones are rendered; the framework supplies Any.
- Mobile now uses a filter modal and desktop uses the existing anchored
  React-tree dropdown. Both always retain a presentation-aware fallback search
  when no unambiguous plugin main search exists, display schema conflicts,
  distinguish empty storage from filtered-empty results, indicate active
  non-main filters, and expose Reset and Show all. Desktop resets its visible
  window for every effective filter/schema change.
- Extended production mobile/desktop component coverage, React diagnostics
  propagation, the production REST adapter contract, the real-backend mobile
  component integration, stable production test IDs/accessibility labels, and
  the existing deterministic native session-list harness.
- Updated `plugins/docs/ui-elements.md`,
  `plugins/docs/application-plugins.md`, the plugin README, terminal README,
  generated default-config reference, and docs-site navigation.

Verification completed:

- Foundation dependency recheck: its focused application, HTTP, terminal, and
  frontend SDK suites passed before implementation.
- Full core default suite with `ulimit -n 4096`:
  `404 passed, 26 deselected, 1 xfailed`.
- Focused application/server/terminal regression set:
  `92 passed, 13 deselected`.
- Main-search plugin tests: `2 passed`.
- Runtime bundle/packaging selection tests: `10 passed`.
- Frontend SDK: `242 passed`, including `25 passed` in the expanded
  filter-contract file.
- React bindings: `17 passed`; shared React Native package: `7 passed`.
- Mobile Jest: `80 passed`; mobile TypeScript: passed.
- Task-owned desktop `SessionsPanel` suite: `3 passed`.
- Real-backend mobile `SessionsScreen` integration: `1 passed`.
- Final rebuilt native session-list Detox suite: `4 passed` on iPhone 17 Pro
  Simulator and `4 passed` on `Medium_Phone_API_36.1`.
- Targeted Python Ruff and Black checks: passed.
- Documentation preparation and MkDocs build: passed with only pre-existing
  reference/navigation warnings.
- `git diff --check`: passed.

Two broader checks were attempted but are not counted as successful:

- `test_default_config_effective_agent_configs.py -m integration` stopped while
  loading unrelated MCP/Codex plugins because the active environment's `attr`
  package does not export `Converter`. The task-owned main-search plugin loads
  in its real `AgentApplication` integration test, and the maintained default
  config's plugin selection is independently exercised by the passing runtime
  bundle test.
- The final aggregate desktop Jest command reported all 16 suites and 94
  assertions passing, then exited nonzero because an existing
  `DependencyFlatList` timer accessed Jest after teardown. The task-owned
  `SessionsPanel` suite exits successfully on its own as recorded above.

## Follow-up plan: built-in pin and status filters

Added after task completion at the user's request. This follow-up reopens task
020 for implementation; the completed filter engine, terminal syntax, and
frontend controls remain the foundation.

### Current state and ownership split

- `plugins/session-pinned-app` already stores pin state under a configurable
  `session_pinned_metadata_key` (default `pinned`) and exposes
  `toggle_session_pinned`, but its UI contribution is still the legacy
  `session_list_toggle_pinned` and it emits no filter.
- No `session-status-app` project exists yet.
- Task 030 specifies stable pin/status filter IDs and the status option set, but
  also owns the broader rich-action framework and migration away from the
  legacy pin-specific UI type.
- Task 020 already supplies every runtime needed to interpret Boolean and
  multi-select filter declarations. Adding real plugin declarations now makes
  the feature manually testable through the personal/default configuration.

Move only the following baseline status work forward from
`tasks/20260719-plugin-session-archive-filters/030-rich-session-list-actions.md`:

- the immutable set-status application action;
- its ordinary `session_list_action` form;
- its multi-select `session_list_filter`;
- configurable metadata-path behavior, events, mutations, tests, configuration,
  and documentation.

Task 030 retains ownership of:

- `rich_ui.kind: "toggle"` and `rich_ui.kind: "list"`;
- migration of pinning away from `session_list_toggle_pinned`;
- immediate rich status selection and pinned rich-action presentation;
- archive action/filter implementation;
- pin/archive/status default-pinned preferences;
- pinned-ordering migration and removal of pin-specific frontend registries.

### Pin filter extension

Extend `SessionPinnedAppPlugin.get_ui_elements()` without changing its existing
action or legacy toggle yet. Resolve the configured metadata key from plugin
state and append:

```python
{
    "ui_type": "session_list_filter",
    "id": "pinned_state",
    "label": "Pinned",
    "icon": "star",
    "order": 10,
    "type": "boolean",
    "match": "equals",
    "data": f"metadata.{pinned_metadata_key}",
    "missing_value": False,
    "default": None,
    "options": [
        {
            "value": False,
            "label": "Not pinned",
            "icon": "star",
            "tone": "muted",
        },
        {
            "value": True,
            "label": "Pinned",
            "icon": "star",
            "tone": "warning",
        },
    ],
}
```

The plugin must derive the toggle and filter paths from the same normalized
metadata-key state. Any means inactive, so installing the plugin does not
change the default list contents. Existing sessions without the key behave as
not pinned.

Keep the current legacy pin row control and mutation behavior intact during
this follow-up. Task 030 will later replace only its UI declaration with an
ordinary rich toggle; the filter ID and semantics introduced here remain
stable.

### Baseline status plugin

Create:

- project: `plugins/session-status-app`;
- module: `session_status_app`;
- class: `SessionStatusAppPlugin`;
- application plugin ID: `session_status`;
- action and ordinary row-action ID: `set_session_status`;
- filter ID: `session_status`;
- config key: `session_status_metadata_key`, default `status`.

Define one immutable internal option table and derive both the ordinary form
and filter from it:

| Value | Label | Tone |
| --- | --- | --- |
| `todo` | To do | `muted` |
| `in_progress` | In progress | `primary` |
| `blocked` | Blocked | `danger` |
| `done` | Done | `success` |

The ordinary row action should use:

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
                "options": STATUS_OPTIONS,
                "required": True,
            }
        ],
    },
}
```

Do not add `rich_ui` in this follow-up. Task 030 will enhance this same ordinary
action with `rich_ui.kind: "list"` and immediate selection without changing its
stable IDs or mutation path.

The filter should be:

```python
{
    "ui_type": "session_list_filter",
    "id": "session_status",
    "label": "Status",
    "icon": "circle",
    "order": 20,
    "type": "select",
    "match": "one_of",
    "multiple": True,
    "data": f"metadata.{status_metadata_key}",
    "missing_value": "todo",
    "default": [],
    "options": STATUS_OPTIONS,
}
```

Missing status behaves as `todo` without writing metadata merely to display or
filter an old session. The ordinary form defaults to `todo` only when prefill
cannot resolve a usable stored value.

Implement `set_session_status` using the established immutable application
mutation pattern:

1. validate `session_id` and status against the internal option table;
2. acquire the application session lock;
3. load the exact session independently of filters;
4. replace metadata immutably at the configured key;
5. save the new `Session`;
6. publish `session_metadata_updated` with the configured key;
7. record a checkpoint best-effort;
8. return `updated_session_ids` and no unrelated UI effect.

Avoid a redundant save/event when the effective stored status already equals
the requested value; return a successful no-op result with no updated-session
mutation.

### Configuration and packaging

- Add `session-status-app` to the maintained default config near
  `session-pinned-app`; keep `session-main-search-app` enabled.
- `session-pinned-app` is already selected by that config, so its new filter
  should appear automatically after restart.
- Add the status project descriptor, packaging metadata, README, docs-site
  navigation entry, generated default-config reference, and runtime bundle
  selection assertion.
- Update personal/manual guidance to state that the filter button should now
  appear without a temporary fixture plugin.
- Do not add HTTP filter parameters or server-side filtering.

### Automated verification

Pin plugin tests must prove through the public plugin/application boundary:

- default and custom pin metadata keys produce the matching filter `data` path;
- the filter has stable ID `pinned_state`, `missing_value: false`, and default
  Any (`null`);
- existing toggle mutations immediately affect subsequent filtered application
  queries;
- `true`, `false`, and inactive values distinguish pinned, unpinned, and all
  sessions, including sessions missing metadata;
- the existing action/event/checkpoint behavior and legacy row control remain
  regression-safe until task 030 migrates them.

Status plugin tests must prove:

- default/custom metadata keys are used consistently by action prefill,
  mutation, event fields, and filter paths;
- one internal option definition keeps form and filter values/labels aligned;
- missing metadata evaluates as `todo`;
- the ordinary form preloads stored status and falls back to `todo`;
- valid mutations are immutable, locked, persisted, evented, checkpointed, and
  reported through `updated_session_ids`;
- invalid status values fail clearly;
- setting the already effective status is a successful no-op;
- multi-select filtering supports one and multiple statuses while preserving
  application order.

Cross-layer coverage should include:

- terminal `/session --filter pinned_state=...` and
  `--filter session_status=todo,blocked`, including completion, command-local
  overrides, invalid values, and exact-ID bypass;
- FastAPI `TestClient` proof that installing filters still leaves `/sessions`
  unfiltered;
- production `RestAgentBackend` request-shape regression;
- mobile and desktop component scenarios using the real pin/status
  declarations for Boolean labels/icons/tones, multi-select status choices,
  active indication, Show all, Reset, and filtered-empty messaging;
- real-backend mobile integration that toggles pin, sets status through the
  ordinary form, refreshes summaries, and filters the resulting collection;
- default-config loading, plugin-bundle selection, docs preparation/build, and
  the relevant package/full regression suites.

Reuse the shared filter evaluator, React state hook, production controls,
stable test IDs, existing real-backend harness, and existing native
session-list harness. Do not duplicate filter matching in either plugin or a
test mock.

### Manual acceptance

With `~/.crystal/config.json` refreshed from or aligned with the maintained
default plugin list:

1. restart the server and confirm `pinned_state`, `session_status`, and
   `session_search` through `/application/ui-schema`;
2. pin one session and leave another unpinned, then verify Any, Not pinned, and
   Pinned on mobile, desktop, and terminal;
3. assign different statuses through the ordinary status form, verify stored
   prefill on reopen, and filter one or multiple statuses;
4. verify old sessions without status appear under To do;
5. verify Show all clears both filters and Reset restores their Any defaults;
6. verify active indication, filtered-empty versus empty-store messaging, and
   order preservation in light and dark themes;
7. verify exact terminal ID access even when pin/status filters would hide the
   target.

Record the exact devices, themes, terminal commands, and outcomes in the
follow-up completion notes. After implementation, mark the four follow-up
items in the task checklist complete and restore task 020's parent checklist
entry to complete.

## Follow-up completion notes

Added during completion of the built-in pin/status filter follow-up.

### Implementation

- `session-pinned-app` now emits stable Boolean filter `pinned_state` from the
  same configurable metadata key used by `toggle_session_pinned`. Its default
  is Any, missing values behave as false, and its Not pinned/Pinned choices
  carry the declared star icon and muted/warning tones.
- The existing pin action and `session_list_toggle_pinned` row contribution
  remain for compatibility. The legacy row contribution now declares the same
  configured metadata path and missing value as the filter so graphical
  clients can render current state without a top-level summary field. Task 030
  still owns migration to an ordinary rich toggle.
- Added `plugins/session-status-app` with stable plugin ID `session_status`,
  action/UI ID `set_session_status`, filter ID `session_status`, and
  configurable `session_status_metadata_key`.
- The status plugin derives its ordinary select form and multi-select filter
  from one option table: `todo`, `in_progress`, `blocked`, and `done`. Missing
  status behaves as `todo`; setting an already-effective value is a successful
  no-op with no save, event, checkpoint, or updated-session mutation.
- Non-no-op status changes validate input, acquire the application session
  lock, replace the immutable `Session`, publish `session_metadata_updated`,
  record a checkpoint, and report the updated session.
- Enabled `session-status-app` in the maintained default configuration, bundle
  selection, generated default-config reference, and docs navigation.
- Updated terminal guidance and plugin docs/READMEs. Task 030 now has an
  explicit handoff telling its executor to enrich the existing status action
  rather than recreate it.
- Mobile, desktop, real-backend, and native harness scenarios now use the
  actual built-in pin/status IDs, options, missing values, defaults, labels,
  icons, and tones.
- The user's current `~/.crystal/config.json` was inspected read-only at the end
  of verification and already contains `session-main-search-app`,
  `session-pinned-app`, and `session-status-app`; no personal config write was
  needed.

### Verification

- Pin plugin: 5 passed.
- Status plugin: 4 passed.
- Combined plugin/main-search/terminal/HTTP/bundle slice: 28 passed.
- Shared Python filter/listing boundary: 13 passed.
- Terminal real-plugin commands: 5 passed in the terminal filter suite,
  including Boolean and multi-select coercion/completion.
- FastAPI session-list contract: 2 passed; `/sessions` remains complete and
  unfiltered while in-process pin/status queries filter.
- Cloud/runtime bundle selection: 10 passed.
- Frontend SDK: 242 passed.
- React bindings: 17 passed.
- Shared React Native package: 7 passed.
- Mobile Jest: 21 suites, 81 tests passed.
- Desktop task-owned `SessionsPanel`: 3 passed.
- Real-backend mobile integration: 1 passed. It loads the real plugin schemas,
  toggles pin through the application action, sets status through the ordinary
  form, refreshes the summary, and applies both filters in the production
  frontend adapter.
- Mobile TypeScript: passed.
- Rebuilt iOS Detox on iPhone 17 Pro: 4 passed.
- Rebuilt Android Detox on `Medium_Phone_API_36.1`: 4 passed.
- MkDocs preparation/build, focused Black, focused Ruff, JSON validation,
  generated-config semantic comparison, and `git diff --check`: passed.

### Broader checks not counted as successful

- The full application test collection stops on the unrelated optional
  `mcp_shared` package not being installed. The separately attempted
  default-config integration still stops before task assertions because the
  active unrelated `attr` package does not expose `Converter` for MCP/Codex
  imports. Focused application, HTTP, terminal, real plugin, and bundle tests
  pass.
- The aggregate desktop Jest command reports all 16 suites and 94 assertions
  passing, then exits nonzero because the existing `DependencyFlatList` timer
  accesses Jest after teardown. The task-owned desktop suite exits cleanly.
- A broad desktop `tsc --noEmit` remains blocked by existing unrelated Feather
  declaration, ChatPane optional-string, and theme `shadow` errors. This
  follow-up's focused desktop component suite passes without introducing
  another reported TypeScript error.

### Manual acceptance handoff

The rebuilt deterministic native harness verified the light-theme production
controls on iPhone 17 Pro and `Medium_Phone_API_36.1`. Human visual checks of
the personal backend on mobile/desktop, especially dark-theme appearance and
desktop popover placement, remain appropriate using the seven steps above.

## Pin-state regression repair

Added after manual testing exposed an incomplete task-010 summary-contract
migration.

- Confirmed pin mutations and `pinned_state` filtering were correct, but the
  ordering plugin and mobile/desktop star controls still read the removed
  top-level `summary.pinned` value.
- `session-pinned-app` now publishes `data` and `missing_value` on its temporary
  legacy row control from `session_pinned_metadata_key`.
- Mobile and desktop resolve that declared path against shared summary
  metadata, expose selected-state accessibility semantics, and use the active
  yellow star only when the resolved Boolean value is true.
- `session-ordering-buckets-app` now reads the same configured metadata key
  from `session_summary.metadata`, while preserving recency bucket, pin rank,
  and last-updated ordering priorities.
- Regression coverage uses summaries with no top-level `pinned` field,
  exercises a custom metadata key, toggles through the real pin action, proves
  public HTTP ordering with a newer unpinned peer, and checks active-star state
  in mobile, desktop, and real-backend component scenarios.

Regression verification:

- Pin and ordering plugin suites: 9 passed.
- FastAPI session-list contract: 3 passed.
- Mobile Jest: 21 suites and 81 tests passed.
- Mobile production TypeScript check: passed.
- Mobile real-backend component integration: 1 passed.
- Desktop `SessionsPanel`: 3 passed.
- Focused Ruff and Black checks: passed.
- MkDocs prepare/build: passed with the repository's pre-existing warnings.
- The explicitly enabled default-config integration reached plugin loading but
  remains blocked before its assertions by the pre-existing `attr.Converter`
  import failures in MCP Runtime and Codex tools.
- Broad desktop `tsc --noEmit` still reports only the previously recorded
  Feather declarations, ChatPane optional-string, and theme `shadow` errors.
