# Session-list foundation

Establish the shared application-layer session-list pipeline and the ordinary-action, rich-presentation, field, filter, and ordering contracts needed by the feature tasks.

## Requirements checklist

- [x] `AgentApplication` is the single application-facing authority for session summary construction, presentation derivation, plugin-contributed fields, and ordering.
- [x] HTTP and terminal consumers receive equivalent ordered summaries without scanning session files or interpreting ordering independently.
- [x] The session-store abstraction exposes enough implementation-neutral enumeration and change-state information for session listing without leaking filesystem paths to consumers.
- [x] Session summaries contain the shared context defined by the parent task and omit heavyweight private metadata.
- [x] `trigger: "session_list"` application actions can contribute summary fields and deterministic order specifications for every application consumer.
- [x] Invalid order specifications or one failing list-trigger action cannot make the complete session list unavailable.
- [x] Modification time descending is the only non-plugin fallback order.
- [x] An ordinary `session_list_action` remains executable through `dialog` whether `rich_ui` is absent, unsupported, unknown, or malformed.
- [x] Rich presentation configuration is contained entirely under one optional `rich_ui` key and does not create another action `ui_type`.
- [x] Every runtime that interprets an overlapping part of the session-list contract follows shared normalization and evaluation semantics.
- [x] The affected sections of `plugins/docs` accurately describe runtime behavior, including `session_list_action`, all supported dialog kinds, parameter mapping, prefill, pinned actions, rich fallback, list fields, filters, and list-trigger ordering.
- [x] All requirements above have automated unit or integration coverage.

Parent Task: `tasks/20260719-plugin-session-archive-filters/000-main.md`

## Foundation contracts

### Session-list service

The public application capability must support:

```python
list_session_summaries(
    *,
    filter_values: dict[str, object] | None = None,
    apply_filter_defaults: bool = False,
    limit: int | None = None,
) -> list[dict[str, object]]
```

The exact Python signature may change during implementation review, but the observable semantics are fixed:

- enumeration, summary construction, contributed fields, presentation, and ordering happen once in the application layer;
- returned summaries include their derived `presentation`;
- optional filtering occurs after ordering;
- `limit` occurs after ordering and filtering;
- HTTP requests unfiltered summaries;
- terminal may request in-process filtering;
- exact session loading remains independent of list filters;
- cached results are isolated by application instance and session store/root;
- mutations that alter session metadata or file state invalidate or naturally bypass stale summary entries.

### Contributed list fields and ordering

A `trigger: "session_list"` action may return:

```python
{
    "session_list_fields": {
        "plugin_field": value,
    },
    "session_list_order": [
        {
            "key": "plugin_field",
            "direction": "asc",
            "fallback": 0,
            "priority": 20,
        }
    ],
}
```

Order specifications are composed by:

1. ascending `priority`;
2. application plugin configuration order;
3. declaration order within the plugin.

Missing keys require an explicit fallback. Invalid specifications are reported and ignored individually. If no valid plugin specification remains, modification time descending is used.

### Session-list fields and presentation

`session_list_field` continues to derive presentation values:

```python
{
    "ui_type": "session_list_field",
    "id": "session_title_field",
    "role": "title",
    "label": "Title",
    "data": "metadata.title",
    "template": "{{data}}",
    "order": 0,
}
```

Supported initial roles are `title`, `subtitle`, and `meta`. Fields within each role are evaluated by order. Empty/missing title and subtitle candidates fall through to the next candidate. Meta values are joined in order. The ordinary presentation fallbacks remain preview and a session-ID-derived label.

### Ordinary action fallback

`session_list_action` has the same action execution fields as other action UI elements and supports:

- `dialog.kind: "none"` for immediate execution;
- `dialog.kind: "confirm"` for confirmation without form values;
- `dialog.kind: "form"` for named inputs and OK/Cancel submission.

For form initialization, a successfully resolved `prefill_from` value takes precedence. The field's `default` is used when the prefill path is missing or resolves to no usable value. This allows a status field to show stored status while still treating a missing status as `todo`.

The optional `rich_ui` object never replaces those fields:

```python
{
    "ui_type": "session_list_action",
    "id": "example",
    "label": "Example",
    "action_id": "example_action",
    "param_map": {
        "session_id": "$session.session_id",
        "value": "$dialog.value",
    },
    "dialog": {
        "kind": "form",
        "inputs": [
            {
                "name": "value",
                "type": "string",
                "prefill_from": "$session.metadata.value",
            }
        ],
    },
    "rich_ui": {
        "kind": "future_kind",
    },
}
```

A consumer that does not understand `future_kind` still opens and submits the ordinary form.

## Scope references

- Application plugin protocol and action execution: `core/python/agent_app/app_plugins.py` and `core/python/agent_app/application_future.py`.
- Session store: `core/python/agent_app/sessions.py`.
- HTTP-only listing code to extract: `application/python/agent_terminal_app/server.py:562-832,2391-2515,2716-2850`.
- Terminal-only listing code to remove: `application/python/agent_terminal_app/terminal_app.py:200-256`.
- Presentation implementation: `packages/frontend-sdk/src/sessions/sessionListPresentation.ts`.
- Public plugin documentation: `plugins/docs/ui-elements.md`, `plugins/docs/actions.md`, and `plugins/docs/application-plugins.md`.

## Execution plan

### Application architecture

Create a focused application-layer module, tentatively `core/python/agent_app/session_listing.py`, containing immutable record/query types and a `SessionListService` or similarly focused class. `AgentApplication` should expose thin public delegation methods and supply callbacks for application action/UI-schema access; the existing `AgentApplication` class should not absorb the listing algorithms.

The service should own:

- summary construction and metadata projection;
- preview extraction;
- summary cache isolation and invalidation;
- `session_list` trigger discovery/execution;
- contributed-field merging;
- order-spec validation and sorting;
- presentation derivation;
- delegation to the filter interpreter delivered by the dependent task.

The HTTP server and `TerminalApplication` should only adapt inputs and outputs.

### Session-store boundary

Review whether the cleanest abstraction is:

- a `list_records` operation added to `SessionStore`; or
- a narrower optional enumeration/state protocol implemented alongside `SessionStore`.

Whichever design is selected must provide opaque session IDs, modified/change state, and session loading without requiring server or terminal consumers to know paths. Filesystem-specific stat and cache behavior remains inside `FilesystemSessionStore` or the listing service.

This boundary requires human approval before implementation because it affects future non-filesystem stores.

### Contract models and conformance

Define focused Python and TypeScript models/normalizers for the affected session-list elements. Core aggregation may continue treating plugin dictionaries as opaque, but application/frontend consumers must validate fields they interpret.

Malformed optional `rich_ui` must be separable from a valid ordinary action. Unknown rich kinds are valid for transport and ordinary fallback, even when a particular frontend cannot render them.

Use shared JSON conformance cases where practical for:

- path resolution and missing values;
- list field ordering/presentation;
- action/dialog/rich normalization;
- valid and invalid order specifications;
- unknown rich-kind fallback.

The location of shared fixtures and the malformed-element reporting policy require human review. Diagnostics should be visible without turning one bad plugin element into a list-wide failure.

### Documentation correction

Correct only the affected documentation, but make those sections complete:

- add a dedicated `session_list_action` section;
- describe action-menu and pinned-action behavior separately;
- document `none`, `confirm`, and `form` accurately;
- document `$session.*`, `$dialog.*`, fixed parameters, prefill, and submission;
- explain permanent rich-UI fallback;
- complete `session_list_field` roles, templates, formatting, and fallbacks;
- document `session_list_filter` and `session_list` trigger outputs;
- update TypeScript reference shapes and HTTP endpoint usage.

Examples should be runtime-accurate and, where practical, exercised by conformance or plugin tests. Validate with the docs preparation/build workflow.

### Human review and scope control

Before coding, approve:

- the listing service/module and store protocol boundary;
- cache ownership and invalidation;
- the exact application public method shape;
- contract fixture ownership;
- malformed plugin diagnostics;
- the touched-file list.

Do not generalize message actions, session-view actions, action-result displays, or unrelated plugin schemas as part of this prerequisite.

### Automated verification

Application/store tests must cover enumeration, malformed session files, metadata projection, previews, cache isolation/invalidation, limits, trigger failures, contributed fields, ordering composition, invalid specifications, and fallback order.

HTTP tests must compare `/sessions` and single-summary results with direct application results.

Terminal application tests must prove delegation and parity, with no independent path scan.

Python/TypeScript conformance tests must cover the shared summary, presentation, ordinary-action fallback, and order contracts.

Documentation preparation/build must complete successfully for the affected pages.

### Approved completion plan

Added during task completion after explicit user approval.

1. Extend the primary `SessionStore` boundary with implementation-neutral
   `list_records` and `get_record` operations returning opaque session IDs,
   public modification timestamps, and equality-only revision tokens.
   Filesystem paths and stat handling remain inside `FilesystemSessionStore`.
2. Add a focused `core/python/agent_app/session_listing.py` service. It owns
   base-summary construction, private metadata projection, preview extraction,
   per-application caching, `session_list` trigger execution, contributed
   fields, presentation derivation, order validation/application, structured
   nonfatal diagnostics, and the ordering/filter/limit query sequence.
3. Keep `AgentApplication` thin: construct the service, expose
   `list_session_summaries`, exact `get_session_summary`, and diagnostic
   delegation, and invalidate affected cache entries after application-owned
   saves and deletes.
4. Remove HTTP-owned filesystem access, caching, trigger execution, and
   ordering from `server.py`; make the list and single-summary routes direct
   application adapters. Replace terminal filesystem scanning with delegation
   to the same application query.
5. Establish language-neutral conformance fixtures under
   `test/fixture/session-list/v1/` and focused frontend SDK normalizers for paths,
   list fields/order declarations, ordinary `session_list_action` dialogs, and
   optional `rich_ui`. Preserve ordinary actions when rich configuration is
   absent, unknown, unsupported, or malformed.
6. Prefer application-derived summary presentation in frontend consumers while
   retaining the existing field evaluator as a compatibility/conformance
   fallback. Extract dialog-prefill initialization into shared pure logic and
   enforce resolved-prefill-before-default semantics.
7. Correct only the affected sections of
   `plugins/docs/ui-elements.md`, `plugins/docs/actions.md`, and
   `plugins/docs/application-plugins.md`.
8. Verify store/application behavior, HTTP and terminal parity, shared
   Python/TypeScript conformance, ordinary rich fallback, prefill behavior,
   relevant default suites, targeted lint/type checks, and docs preparation
   plus MkDocs build.

Scope control for this completion:

- task 020 retains ownership of declarative filter evaluation and terminal /
  mobile / desktop filter integration;
- task 030 retains ownership of concrete rich `toggle` / `list` renderers and
  pin, archive, status, and pinned-ordering plugin conversion;
- no HTTP filter query API, message-action generalization, session-view action
  generalization, or action-result display changes are included here.

## Follow-up coverage plan

Added after completion review with explicit user approval.

- [x] Add FastAPI `TestClient` coverage for the serialized `/sessions` and
  `/sessions/{id}/summary` contracts, including ordering, limits, metadata
  projection, exact-summary parity, and missing-session handling.
- [x] Add mobile `SessionsScreen` component coverage for application-derived
  presentation, server ordering, ordinary-action fallback, and dialog prefill.
- [x] Exercise the real frontend SDK dialog-initialization helper from the
  React Native component regression test instead of duplicating that helper in
  the Jest mock.
- [x] Add a deterministic mobile session-list harness and Detox smoke suite for
  iOS Simulator and Android Emulator, covering native row presentation,
  ordering, ordinary-action fallback, and prefill behavior.
- [x] Add focused frontend SDK transport, action-path edge-case, and React
  diagnostics propagation tests.
- [x] Add a real-backend mobile session-list component integration test.
- [x] Add generic desktop `SessionsPanel` component coverage for
  application-derived presentation and server ordering.
- [ ] Add mobile, desktop, and macOS native UI coverage for the concrete rich
  actions in
  `tasks/20260719-plugin-session-archive-filters/030-rich-session-list-actions.md`.
- [ ] Add configured pin/archive/status state tests with the concrete rich
  action work in
  `tasks/20260719-plugin-session-archive-filters/030-rich-session-list-actions.md`.

All foundation-owned follow-ups are complete. The remaining items are
explicitly deferred to task 030 because they require the concrete rich-action
implementations and configured pin/archive/status plugins.

## Completion Notes

Added during task completion.

- Added `SessionStoreRecord`, `SessionStore.list_records`, and
  `SessionStore.get_record`. `FilesystemSessionStore` now supplies opaque
  revision tokens and modification timestamps without exposing paths.
- Added the focused `agent_app.session_listing.SessionListService` and thin
  `AgentApplication` delegation for list queries, exact summaries, diagnostics,
  filter-evaluator installation, and mutation invalidation.
- Moved summary construction, metadata projection, previews, per-application
  caching, list-trigger execution, contributed fields, deterministic
  mixed-direction ordering, presentation derivation, and query sequencing out
  of the HTTP server.
- Replaced HTTP and terminal filesystem scans with shared application calls.
  The server's private session-root lookup, global summary cache, special
  trigger dispatcher, pinned fallback sorting, and order interpreter were
  removed.
- Added shared language-neutral contract cases under
  `test/fixture/session-list/v1/` and matching Python/TypeScript coverage for path
  resolution, missing values, presentation, deterministic datetime formatting,
  ordinary action normalization, rich fallback, prefill, and order
  normalization.
- Added frontend SDK normalization and nonfatal diagnostics for session-list
  actions and fields. Unknown rich kinds remain transportable; malformed rich
  configuration is removed without losing a valid ordinary action.
- Extracted action-dialog initialization into shared pure logic. Resolved
  `prefill_from` values now take precedence over nonempty defaults in both
  shared React Native dialog implementations.
- Corrected the affected public contract documentation in
  `plugins/docs/ui-elements.md`, `plugins/docs/actions.md`, and
  `plugins/docs/application-plugins.md`.

Verification completed:

- Full default core suite with an adequate process file-descriptor limit:
  `401 passed, 26 deselected, 1 xfailed`.
- Session-list foundation tests: `10 passed`.
- HTTP server tests: `50 passed, 11 deselected`.
- Terminal application tests: `36 passed, 2 deselected`.
- Shared server/terminal event tests: `2 passed`.
- Frontend SDK: `211 passed`; React bindings: `15 passed`; shared React Native
  components: `7 passed`.
- Mobile action-dialog regression tests: `4 passed`.

Follow-up coverage execution:

- Added FastAPI `TestClient` coverage for serialized list and exact-summary
  responses, modification-time fallback ordering, post-order limit behavior,
  metadata projection, malformed-record isolation, and HTTP 404 handling.
- Added mobile `SessionsScreen` component tests proving that application-derived
  presentation wins over local fields, server order is preserved, malformed
  rich configuration retains the ordinary form, and stored metadata supplies
  dialog prefill.
- Removed the duplicate dialog-initialization implementation from the mobile
  component test so it now exercises the real frontend SDK helper.
- Added stable session-row, action-menu, action-item, and dialog-control test
  identifiers at the production component boundaries.
- Added a deterministic `MobileSessionListHarness`, native launch routing,
  dedicated package scripts, and a two-scenario Detox suite.
- Verified the Detox suite on both iPhone 17 Pro Simulator and
  `Medium_Phone_API_36.1`: `2 passed` on each platform.
- Broader follow-up verification: `62 passed` across the focused Python
  application/server suites; `73 passed` in the complete mobile Jest suite;
  frontend SDK `211 passed`; React bindings `15 passed`; shared React Native
  components `7 passed`; mobile TypeScript passed.
- Targeted ESLint was not run because the mobile package currently has no
  discoverable ESLint configuration; its existing `lint` script fails before
  analyzing source files for the same reason.
- Added frontend SDK transport coverage for list and exact-summary responses,
  plus action-path coverage for arrays, explicit `null`, false, zero, empty
  strings, and genuinely missing values.
- Added React selector coverage proving session-list diagnostics propagate
  through `useApplicationPlugins`.
- Added a real-backend mobile integration that uses the actual
  `session-title-app` and message-count plugin, verifies HTTP summaries, opens
  the real list action, checks stored prefill, submits a title mutation, and
  observes the refreshed screen.
- Restored the missing `StartedBridge` interface declaration in the shared
  integration harness; this had prevented every mobile real-backend component
  test from collecting. All six mobile real-backend integration tests now
  pass.
- Added desktop `SessionsPanel` component coverage for application-derived
  presentation, server ordering, and open-tab presentation propagation.
- Added the standard desktop React Native Jest bridge bootstrap and a public
  API mock for the macOS-only text host component, allowing `App.test.tsx` and
  all 14 desktop suites to execute. All 82 desktop assertions pass; the
  combined Jest command still exits nonzero after completion because an
  existing `DependencyFlatList` timer accesses the Jest environment after
  teardown. The `DependencyFlatList` suite and the new `SessionsPanel` suite
  both pass independently.
- Updated frontend verification totals: frontend SDK `215 passed`; React
  bindings `16 passed`; shared React Native components `7 passed`.
- Mobile TypeScript check: passed.
- Targeted Python Ruff and Black checks: passed.
- Documentation preparation and MkDocs build: passed with only pre-existing
  navigation/reference warnings.

The complete application test directory was also attempted, but collection is
gated by unrelated optional plugin dependencies absent from the active
environment (`mcp_shared` and `openai`). All application files directly
affected by this task were run successfully as listed above.
