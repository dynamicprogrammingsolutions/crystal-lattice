# Plugin-driven session lists

Make session-list summaries, ordering, search, filters, and rich actions plugin-driven across the HTTP API, terminal, mobile, and desktop while preserving ordinary action behavior for frontends that do not implement rich presentations.

## Requirements checklist

- [ ] HTTP and terminal session lists use one application-layer summary, presentation, and ordering pipeline.
- [ ] Pin, archive, status, enhanced main-search, and non-main filter capabilities appear only when their contributing plugins are installed and enabled; mobile and desktop retain the approved compatibility fallback search when no main-search plugin is available.
- [ ] Every enhanced session-list action remains a valid ordinary `session_list_action`; unsupported rich presentations fall back to the action's ordinary dialog behavior.
- [ ] Session filters support text, boolean, single-select, and multi-select controls with deterministic declarative matching.
- [ ] Terminal free-text search and the enhanced ordinary search are supplied by a plugin-defined main-search filter; mobile and desktop retain a shared summary-text fallback when no unambiguous plugin declaration exists.
- [ ] Pinning, archiving, and status are stored under configurable session metadata keys and are available through plugin-defined actions and filters.
- [ ] Pinning and archiving have state-aware rich toggle presentations, while status has both an ordinary form and a rich immediate-selection list presentation.
- [ ] Plugin-contributed ordering, including pinned ordering, is applied before filtering and is shared by HTTP and terminal consumers.
- [ ] No compatibility alias remains for `session_list_toggle_pinned`, pin-specific frontend registries, or top-level `SessionSummary.pinned`.
- [ ] The affected plugin contracts and examples are accurate and complete under `plugins/docs`, including previously incomplete `session_list_action` documentation.
- [ ] Every non-visual requirement has automated test coverage at the lowest useful layer plus cross-layer coverage where behavior crosses a boundary.
- [ ] Mobile and desktop are manually verified in light and dark themes for filter placement, active-filter indication, rich toggle state, and pinned status-list presentation.
  - This is the only requirement whose primary verification is manual.

## Task checklist

- [x] `tasks/20260719-plugin-session-archive-filters/010-session-list-foundation.md`
- [x] `tasks/20260719-plugin-session-archive-filters/020-plugin-driven-filters-and-search.md`
  - DEPENDS ON `tasks/20260719-plugin-session-archive-filters/010-session-list-foundation.md`
- [x] `tasks/20260719-plugin-session-archive-filters/021-search-fields-and-status-list-footer.md`
  - DEPENDS ON `tasks/20260719-plugin-session-archive-filters/020-plugin-driven-filters-and-search.md`
- [ ] `tasks/20260719-plugin-session-archive-filters/030-rich-session-list-actions.md`
  - DEPENDS ON `tasks/20260719-plugin-session-archive-filters/010-session-list-foundation.md`
  - DEPENDS ON `tasks/20260719-plugin-session-archive-filters/020-plugin-driven-filters-and-search.md`
  - DEPENDS ON `tasks/20260719-plugin-session-archive-filters/021-search-fields-and-status-list-footer.md`

## Shared contract

### Session summary context

All session-list consumers operate on the same logical summary:

```typescript
interface SessionSummary {
  session_id: string;
  modified: number;
  preview: string;
  metadata: Record<string, unknown>;
  presentation: {
    title: string;
    subtitle: string | null;
    meta: string | null;
  };

  // Fields produced by trigger: "session_list" plugin actions.
  [contributedField: string]: unknown;
}
```

Session metadata in summaries excludes heavyweight private values such as `native_messages`. Pin, archive, and status values remain under their configured `metadata.*` paths and are not projected into feature-specific top-level summary fields.

### Ordinary and rich session-list actions

Rich behavior extends, rather than replaces, an ordinary session-list action:

```python
{
    "ui_type": "session_list_action",
    "id": "stable_element_id",
    "label": "Action label",
    "icon": "icon-name",
    "order": 10,
    "action_id": "plugin_action_id",
    "fixed_params": {},
    "param_map": {
        "session_id": "$session.session_id",
    },
    "dialog": {
        "kind": "none",
    },
    "rich_ui": {
        "kind": "toggle",
        # Kind-specific rich presentation fields.
    },
}
```

The fallback rule is permanent:

1. A frontend that supports the declared `rich_ui.kind` may use the rich presentation.
2. A frontend that does not support it ignores `rich_ui` and uses `dialog`.
3. A frontend that encounters malformed rich configuration reports the problem and falls back to `dialog`; it does not discard the ordinary action.
4. Unknown future rich kinds follow the same fallback rule.

The first rich kinds are:

- `toggle`: display current boolean-like state when pinned and invoke the action immediately when selected.
- `list`: display the current option when pinned and present an immediate-selection option list when selected.

All kind-specific fields live inside the single `rich_ui` object.

### Session-list filters

Filters use a dedicated non-action element:

```typescript
interface SessionListFilterElement {
  ui_type: 'session_list_filter';
  id: string;
  label: string;
  icon?: string;
  order?: number;

  data: string | string[];
  type: 'text' | 'boolean' | 'select';
  match: 'contains' | 'equals' | 'one_of';

  case_sensitive?: boolean;
  missing_value?: unknown;
  default?: unknown;
  options?: SessionListOption[];
  multiple?: boolean;
  main_search?: boolean;
}
```

Valid initial combinations:

| Filter type | Runtime value | Supported matching |
| --- | --- | --- |
| `text` | string | `contains`, `equals` |
| `boolean` | `null`, `true`, `false` | `equals` |
| single `select` | `null` or one option value | `equals` |
| multiple `select` | zero or more option values | `one_of` |

Matching and state rules:

- Data paths inside one filter combine with OR.
- Active filters combine with AND.
- Empty text, boolean `null`, single-select `null`, and an empty multi-select are inactive.
- `contains` is case-insensitive unless `case_sensitive` is true.
- A missing data path resolves to `missing_value` before matching.
- `default` initializes filter state and is restored by Reset.
- Show all assigns each filter's inactive value rather than its plugin default.
- Filtering preserves input order.
- `main_search` is valid only for a text filter.
- Zero or one effective main-search filter is valid. Competing declarations produce a clear schema error rather than an arbitrary winner.
- Mobile and desktop retain a shared case-insensitive summary-text fallback
  search when no unambiguous main-search declaration is available. Terminal
  free-text search remains plugin-driven.

### Default built-in behavior

- Main search checks `session_id`, `preview`, the complete first non-empty user
  message, and `presentation.title`, `presentation.subtitle`, and
  `presentation.meta` using case-insensitive `contains`.
- The main-search plugin also contributes focused title/subtitle and
  first-message filters.
- Pin filtering defaults to Any.
- Archive filtering defaults to False, so archived sessions are hidden from ordinary lists.
- Status filtering defaults to Any and supports selecting multiple statuses.
- Missing pin/archive metadata means False.
- Missing status metadata means `todo`.
- Status is rendered last in session-list row metadata by default and can be
  hidden through a server setting whose fallback comes from application
  configuration.
- Built-in statuses are `todo`, `in_progress`, `blocked`, and `done`.
- Pin and archive rich actions are initially pinned when no user preference exists.
- Status is not initially pinned.
- Plugin ordering is applied before filtering.
- Without valid plugin ordering, summaries use modification time descending only.
- HTTP/mobile/desktop filtering remains client-side in this iteration.
- Terminal filtering is in-process through the shared application query service; no HTTP server-side filter API is introduced.
- An exact terminal session ID remains directly accessible even when default filters hide that session.

## Existing implementation findings

- `plugins/session-pinned-app/src/session_pinned_app/__init__.py:31-158` owns pinned metadata and the current pin-only UI element.
- `plugins/session-ordering-buckets-app/src/session_ordering_buckets_app/__init__.py:137-193` computes recency, pin, and last-updated order fields.
- `application/python/agent_terminal_app/server.py:562-832` owns an HTTP-only summary cache, metadata extraction, `session_list` trigger execution, and cached order specifications.
- `application/python/agent_terminal_app/server.py:2391-2515` implements HTTP session listing and single-summary loading.
- `application/python/agent_terminal_app/server.py:2716-2850` implements legacy and plugin-driven sorting.
- `application/python/agent_terminal_app/terminal_app.py:200-256` independently scans session JSON files and sorts by modification time.
- `application/python/agent_terminal_app/terminal.py:447-472,576-633` implements prefix completion and text-based session selection.
- `core/python/agent_app/sessions.py:12-27` has no session enumeration operation in `SessionStore`.
- `plugins/docs/ui-elements.md:252-358` documents `session_action` but omits a proper `session_list_action` contract and understates the supported dialog kinds.
- `packages/frontend-sdk/src/plugins/pluginsRegistry.ts:10-82` has a pin-specific registry collection.
- Mobile and desktop contain separate hardcoded search and pin-state rendering.

## Out of scope

- HTTP server-side filters, remote filter query serialization, or pagination-aware remote filtering.
- Generic terminal discovery and invocation of all session-list actions.
- Message/transcript search or filtering.
- Archive- or status-specific ordering beyond separately contributed order specifications.
- Provider, tool, bridge, cloud-agent, or unrelated action-system changes.
- Compatibility handling for the removed pin-only UI type.

## Execution plan

### Delivery sequence

The foundation task is completed and reviewed first. It establishes the application query boundary, summary context, ordinary-action fallback, schema-validation policy, and corrected documentation baseline.

The filter/search task follows and delivers the complete declarative filtering feature across application, terminal, mobile, and desktop.

The rich-action task then builds on both prerequisites to deliver toggle and list presentations together with pin, archive, and status plugins.

### Human review gates

Before implementation begins, review the proposed changed-file scope and the module/component extraction points in the three subtasks. In particular:

- large existing files receive thin orchestration only;
- application-owned query behavior is not left in HTTP or terminal code;
- shared filter and rich-action interpretation is not duplicated in mobile and desktop screens;
- plugin documentation remains the source of truth for the public contract;
- unrelated action surfaces are not generalized merely because they share a component.

Review the foundation boundary again before the dependent tasks start. Review terminal command syntax in the filter task and shared pinned-action layout in the rich-action task before those UI changes are implemented.

### Verification and completion evidence

Each subtask maps every hard requirement to automated unit, integration, component, or command tests in its execution plan. Cross-runtime conformance cases should be shared where practical so Python and TypeScript interpretations cannot drift.

The final verification combines:

- focused plugin, core application, HTTP, and terminal tests;
- shared frontend SDK, React bindings, and React Native component tests;
- targeted mobile and desktop tests and lint/type checks;
- documentation preparation/build validation;
- one recorded manual light/dark mobile/desktop review;
- a final changed-file scope review.
