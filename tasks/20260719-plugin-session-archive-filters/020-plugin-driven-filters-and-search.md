# Plugin-driven session filters and search

Deliver the expanded declarative filter contract, replace hardcoded session search with a main-search plugin, and expose the same filter semantics in terminal, mobile, and desktop.

## Requirements checklist

- [ ] `session_list_filter` supports text, boolean, single-select, and multi-select controls with only the valid type/match combinations defined in this task.
- [ ] Filter evaluation follows the same path, missing-value, case-sensitivity, inactivity, OR-within-filter, AND-across-filters, default, Reset, Show all, and order-preservation rules in Python and TypeScript.
- [ ] Zero or one effective main-search filter is valid; competing main-search declarations produce a clear schema error.
- [ ] Main search is absent when no valid main-search declaration exists; no hardcoded fallback search remains.
- [ ] The built-in main-search plugin searches session ID, preview, and derived presentation title/subtitle/meta with case-insensitive `contains`.
- [ ] HTTP mobile and desktop clients filter the complete loaded session collection locally without changing backend request shape or server/application order.
- [ ] Terminal filtering uses the shared in-process application query path and does not duplicate filter interpretation in terminal UI code.
- [ ] Terminal session selection supports default filters, main-search text, explicit non-main filter overrides, completion, and exact-ID access independent of filters.
- [ ] Mobile and desktop render the main-search input and an adjacent filter control from plugin declarations.
- [ ] Boolean filters expose Any/True/False, select filters expose Any or selected options, and multi-select filters allow multiple option values.
- [ ] Reset restores plugin defaults, while Show all deactivates every filter.
- [ ] Filter state is scoped to the active connection and current declaration set; removed or changed declarations cannot leave stale effective values.
- [ ] Empty-state and active-filter indications distinguish an empty store from a filtered result.
- [ ] The filter contract and main-search plugin are documented under `plugins/docs` and in the plugin README.
- [ ] All requirements above have automated unit, integration, component, or terminal-command coverage.

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

The main-search input is rendered only from the valid main-search declaration. The filter control sits immediately to its right and is visible only when non-main filters exist. It indicates when effective non-main filters differ from Show all.

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

Mobile/desktop tests must cover declaration-driven search visibility, adjacent filter control, local-only filtering, active indication, empty states, state scoping, Reset/Show all, and desktop window reset.

Plugin/configuration tests must cover the main-search declaration and default loading. Documentation preparation/build must pass.
