Assess task-guidance behavior for one fixed scenario across several producer
profiles. Use the reviewed target, not raw task count, as the authority.

Judge whether each task set preserves approved outcomes and partitions work
into coherent deliverables. A technical layer is a valid separate task only
when completion leaves an independently usable, acceptable, deferable, owned,
or reviewable result. Identify subtasks that are merely phases or layer
fragments and could merge without losing independent value. Also identify
overpacked tasks that hide several independent deliverables.

The natural user request is part of the authority. Do not label behavior
explicitly requested there or listed in approved outcomes as added scope.
A coordinating parent file such as `000-main.md` is not an implementation
deliverable: exclude it from `actual_task_count`, fragmentation ratio, and
unmatched tasks unless it contains separately assigned implementation work.
For `crossing_ownership`, apply the target's exact `important_crossings`.
Separate mocked component tests and direct route/helper tests do not prove a
required production connection. Mark the crossing complete only when the task
names at least one check through that exact connection; otherwise mark it
partial or missing and explain the gap.

Do not reward verbosity, exact filenames, or matching the target's task count
mechanically. Do not penalize an acceptable alternative partition described by
the target. Treat tests, documentation, implementation, review, and deployment
as work within a deliverable unless their result is independently required.

Assess these issue dimensions separately:

- `fragmentation`: the overall mismatch between actual tasks and coherent
  deliverables;
- `phase_only_children`: implementation, testing, documentation, deployment,
  cleanup, or review children that only complete another delivery;
- `layer_split_without_independent_value`: frontend, backend, transport,
  storage, or package children that lack independent users, ownership,
  compatibility, acceptance, or a complete product outcome;
- `evidence_reownership`: a final integration, verification, or documentation
  child re-owning evidence that belongs with outcome-delivery children;
- `unsafe_dependencies`: missing, unnecessary, or wrong dependencies that
  permit a broken intermediate state or serialize independently deliverable
  work;
- `piecewise_crossing_evidence`: separate mocks, component checks, direct
  routes, or helper tests without one decisive check through the required
  production connection.

For fragmentation use `none|low|medium|high`. For every other dimension use
`none|partial|present`. `none` means the issue is absent, `partial` means a
limited or incomplete instance, and `present` means a material instance.
List concrete occurrences separately. Do not invent numeric scores; the
evaluator derives them deterministically from these statuses.

Return JSON only with this shape:

{
  "schema_version": 2,
  "scenario_id": "tg03-flask-vue-refresh-handoff",
  "assessments": [
    {
      "producer": {"profile": "glm|gpt", "reasoning_effort": "..."},
      "outcome_coverage": "complete|partial|poor",
      "missing_outcomes": ["OUTCOME-ID"],
      "added_obligations": ["description"],
      "semantic_deliverable_count": 0,
      "actual_task_count": 0,
      "deliverable_mappings": [
        {
          "deliverable_id": "target id",
          "task_paths": ["tasks/..."],
          "coverage": "complete|partial|missing",
          "coherence": "coherent|fragmented|overpacked",
          "reason": "short evidence"
        }
      ],
      "mergeable_groups": [
        {"task_paths": ["tasks/..."], "reason": "why these are one deliverable"}
      ],
      "unmatched_tasks": ["tasks/..."],
      "overpacked_tasks": ["tasks/..."],
      "valid_layer_boundaries": ["tasks/..."],
      "automatic_layer_fragments": ["tasks/..."],
      "dependency_issues": ["description"],
      "crossing_ownership": "complete|partial|missing",
      "fragmentation_severity": "none|low|medium|high",
      "fragmentation_ratio": 0.0,
      "quality_metrics": {
        "fragmentation": {
          "status": "none|low|medium|high",
          "occurrences": [
            {
              "task_paths": ["tasks/..."],
              "description": "concrete occurrence"
            }
          ]
        },
        "phase_only_children": {
          "status": "none|partial|present",
          "occurrences": []
        },
        "layer_split_without_independent_value": {
          "status": "none|partial|present",
          "occurrences": []
        },
        "evidence_reownership": {
          "status": "none|partial|present",
          "occurrences": []
        },
        "unsafe_dependencies": {
          "status": "none|partial|present",
          "occurrences": []
        },
        "piecewise_crossing_evidence": {
          "status": "none|partial|present",
          "occurrences": []
        }
      },
      "partition_quality_score": 0,
      "handoff_quality_score": 0,
      "summary": "concise evidence-based interpretation"
    }
  ]
}

Scores are integers from 0 through 100. `fragmentation_ratio` is actual task
files divided by the semantic coherent-deliverable count, or 0 when no
deliverable exists; it is descriptive rather than decisive.

Reviewed target:

{
  "acceptable_alternatives": [
    "Add, update, and delete may be grouped as variants of one refresh outcome."
  ],
  "acceptable_partition_sizes": [
    1
  ],
  "approved_outcomes": [
    {
      "id": "REFRESH-1",
      "outcome": "All/Read/Unread selection remains active after add, update, and delete refreshes."
    },
    {
      "id": "REFRESH-2",
      "outcome": "Mutation refreshes use the selected filter through the production client transport and Flask route."
    },
    {
      "id": "REFRESH-3",
      "outcome": "The visible active choice, table results, and empty state match the refreshed response."
    },
    {
      "id": "REFRESH-4",
      "outcome": "Existing CRUD success, response shape, and unfiltered behavior remain compatible."
    }
  ],
  "category": "handoff",
  "coherent_deliverables": [
    {
      "dependencies": [],
      "id": "REFRESH-DELIVERY",
      "independent_value": "Frontend state, transport, server request, rendering, and regression evidence must all land before the bug is fixed.",
      "outcomes": [
        "REFRESH-1",
        "REFRESH-2",
        "REFRESH-3",
        "REFRESH-4"
      ],
      "title": "Fix selected-filter refresh behavior"
    }
  ],
  "fragmentation_examples": [
    "Frontend, backend, component-test, API-test, integration-test, and documentation subtasks would split one inseparable bug fix."
  ],
  "handoff": {
    "fresh_agent_plan": "A fresh agent reconstructs one cohesive cross-layer fix and groups CRUD refresh variants.",
    "omit_plan": "Preserve the observed regression, source pointers, state owner, and public response constraints without the proposed shared fetch-path solution.",
    "retain_plan": "Preserve the selected-state owner, refresh call paths, compatibility constraints, and real crossing."
  },
  "important_crossings": [
    "Vue selection and mutation refresh use the production transport and Flask HTTP route before rendering results."
  ],
  "open_questions": [],
  "overpacking_examples": [],
  "project": {
    "fixture_id": "tg03-flask-vue-refresh",
    "kind": "user-facing full-stack application",
    "name": "Flask-Vue CRUD",
    "revision": "be91da59a10d07384537c2f76f4505eb344d1682",
    "upstream": "https://github.com/testdrivenio/flask-vue-crud"
  },
  "scenario_id": "tg03-flask-vue-refresh-handoff",
  "schema_version": 1,
  "task_summary": "Keep one cross-layer regression cohesive and preserve its production transport boundary.",
  "title": "Flask/Vue selected-filter refresh handoff"
}

Natural user request:

The Books page can show All, Read, or Unread books, but after adding, editing, or deleting a book the refresh falls back to the unfiltered list. Keep the selected filter visibly active and reapply it whenever CRUD refreshes the collection. Preserve the existing API response shape and unfiltered behavior. Plan the fix and create the appropriate task structure without implementing it.

Producer records:

[
  {
    "invalid_reasons": [],
    "producer": {
      "model": "glm-5.3-flash:cloud",
      "profile": "glm",
      "reasoning_effort": "max"
    },
    "response": "Task structure created: `tasks/20260919-books-crud-filter-refresh.md` (single task file \u2014 the bug lives entirely in one layer, the Books component, so no subtask split is warranted; say the word if you'd prefer a main/subtask layout).\n\n## Root cause\n\n`client/src/components/Books.vue:32,36,40` \u2014 after `add`/`update`/`remove`, the refresh calls `getBooks()` with the default `\"all\"` filter. `selectedFilter` is never reset, so the `read`/`unread` button stays pressed while the list becomes unfiltered. `client/src/api/books.js:3-6` already supports the filter param, and the server already handles `?read=true|false` \u2014 the regression is purely the component dropping the argument.\n\n## Plan summary (Draft \u2014 execution waits for your approval)\n\n- **Outcome**: CRUD refreshes reuse the selected filter; the pressed state stays consistent with the list; API response shapes and unfiltered behavior untouched.\n- **Approach**: add a `refresh()` method to `Books.vue` that fetches with `this.selectedFilter` and route `selectFilter`/`add`/`update`/`remove` through it. No changes to `api/books.js` or `server/app.py` \u2014 preserving shapes and unfiltered behavior by not touching them.\n- **Acceptance evidence**: component tests asserting the mocked `getBooks` is last called with the selected filter after each mutation and `aria-pressed=\"true\"` survives; a small new spec pinning the filter\u2192query-param mapping (`all` \u2192 no params); existing vitest + pytest suites green with no server diffs.\n- **Judgment call to confirm**: \"visibly active\" is interpreted as the existing `aria-pressed` signal remaining correct \u2014 no new styling requested.\n- **Exclusions**: initial-load fetching, styling, server changes, CRUD error handling, new doc pages (none of the maintained docs describe filter/refresh behavior, so no documentation updates are needed).\n\nNothing has been implemented \u2014 the working tree only gains the new task file. Approval of the plan starts execution.",
    "task_files": {
      "tasks/20260919-books-crud-filter-refresh.md": "# Books CRUD refresh must reapply the selected status filter\n\nThe Books page filter (`all`/`read`/`unread`) is dropped when add, update, or\ndelete refreshes the collection: those refreshes call `getBooks()` with the\ndefault `all` filter, so the list shows unfiltered books while the filter\ncontrol still shows the previous selection as active. The fix is client-side;\nthe API contract and unfiltered behavior are preserved.\n\n## Requirements checklist\n\n- [ ] After a successful add, update, or delete, the collection refresh reuses\n  the currently selected filter (`all`/`read`/`unread`) so the displayed books\n  match the active filter. Refresh moments and component method signatures\n  (`selectFilter(value)`, `add(book)`, `update(book)`, `remove(id)`) are\n  unchanged, and refresh still happens only after the mutation succeeds.\n- [ ] The selected filter remains visibly active across CRUD refreshes: the\n  filter control's active/pressed state continues to reflect the user's\n  selection and is not reset or desynced from the refreshed list.\n- [ ] Flask API endpoints and response shapes are unchanged: `GET /books` \u2192\n  `{\"status\": \"success\", \"books\": [...]}`, `POST /books` \u2192\n  `{\"status\": \"success\", \"books\": [...]}`, `PUT/DELETE /books/<id>` \u2192\n  `{\"status\": \"success\", \"book\": ...}`. The fix is client-side only.\n- [ ] Unfiltered behavior is preserved: `all` (the default) continues to fetch\n  every book with no `read` query parameter, both when the filter is selected\n  and during CRUD refreshes while `all` is selected.\n\n## Questions and decisions\n\n- No unresolved requirement questions. Interpretation used for planning:\n  \"visibly active\" means the existing active-state signal (`aria-pressed` on\n  the filter buttons, `client/src/components/Books.vue:7`) stays correct and\n  consistent with the list; no new styling is requested. Flagged for\n  confirmation at plan approval.\n\n## Supporting facts\n\n- Regression location: `client/src/components/Books.vue:32,36,40` \u2014\n  add/update/remove refetch with `getBooks()` (default `all`), discarding the\n  selection (marked `// regression: filter lost`). `selectedFilter` is not\n  reset, so the control stays pressed while the list becomes unfiltered \u2014\n  the reported state/content mismatch.\n- Filter mechanics: buttons iterate `['all', 'read', 'unread']`\n  (`client/src/components/Books.vue:5`); `selectedFilter` defaults to `\"all\"`\n  (`client/src/components/Books.vue:24`); `selectFilter` already fetches with\n  the chosen value (`client/src/components/Books.vue:26-29`).\n- Client transport already supports filters: `getBooks(filter = \"all\")` sends\n  no params for `all` and `{ read: true|false }` otherwise\n  (`client/src/api/books.js:3-6`). No client API change is needed.\n- Server contract (`server/app.py:10-30`): GET filters via `?read=true|false`;\n  POST appends and returns `{\"status\", \"books\"}`; PUT/DELETE return\n  `{\"status\", \"book\"}`. This fix does not touch the server, which preserves\n  the response shapes.\n- There is no mounted/initial fetch; the list loads only via `selectFilter`\n  or a CRUD refresh. Initial-load behavior is out of scope.\n- Existing coverage: `client/tests/Books.spec.js` mocks the api module and\n  only checks the empty state; `tests/test_books_api.py` covers unfiltered\n  GET and the CRUD happy path. Nothing pins the CRUD-refresh filter today.\n- Rejected approach: resetting the filter to `all` after mutations, or\n  refetching without params \u2014 both reintroduce the reported inconsistency.\n  No server-side filter persistence is needed.\n\n## Execution plan\n\nStatus: Draft\n\nApproach \u2014 single-layer client fix. The capability touches no other layer\nwith an independently useful or owned result, so no per-layer split.\n\n1. `client/src/components/Books.vue`: add a `refresh()` method that sets\n   `this.books = (await getBooks(this.selectedFilter)).data.books;` and call\n   it from `selectFilter`, `add`, `update`, and `remove`. This makes the\n   selected filter the single source of truth for every refresh and keeps the\n   pressed state consistent with the list.\n2. No changes to `client/src/api/books.js` or `server/app.py`; request and\n   response handling is untouched, preserving API shapes and unfiltered\n   behavior.\n\nVerification:\n\n- Extend `client/tests/Books.spec.js`: after `selectFilter(\"read\")`, invoke\n  `add`, `update`, and `remove`, asserting the mocked `getBooks` was last\n  called with `\"read\"` after each refresh and the `read` button still has\n  `aria-pressed=\"true\"`. Add an `all`-path assertion (select `all`, then\n  `add` \u2192 last call `\"all\"`). Keep the existing empty-state test passing.\n  Tests must call methods via `wrapper.vm` because the fixture wires no CRUD\n  controls to these methods.\n- New `client/tests/api-books.spec.js` (mock `../src/http`): pin the\n  `getBooks` mapping \u2014 `all` \u2192 `GET /books` with `{ params: {} }`, `read` \u2192\n  `{ params: { read: true } }`, `unread` \u2192 `{ params: { read: false } }`.\n- Run `npm test` in `client/` and `pytest` at the repo root; existing server\n  tests must pass untouched (no diffs under `server/` or `client/src/api/`).\n\nRisks / notes:\n\n- Component tests assert the api-client seam with a mock; they do not catch\n  param-mapping regressions in `api/books.js` \u2014 mitigated by the new api spec.\n- If a mutation rejects, no refresh occurs (unchanged behavior; no new error\n  handling is introduced).\n- No e2e layer exists in this fixture; component + api unit tests are the\n  proportionate evidence.\n\nExclusions: initial-load fetching, filter control styling, server changes,\nCRUD error handling, new documentation pages.\n\n### Implementation decisions and open questions\n\n- Decision (local, resolved): extract `refresh()` rather than repeating\n  `getBooks(this.selectedFilter)` in three methods \u2014 removes the duplication\n  that caused the regression and keeps `selectedFilter` authoritative.\n- Open questions: none. The \"visibly active\" interpretation above is the only\n  judgment call; confirm it at approval.\n\n### Documentation\n\nNone required. No maintained documentation describes the filter or refresh\nbehavior (`README.md:3` is generic; `docs/development/index.md:3` records that\nno book-discovery specification exists). The change restores intended behavior\nwithout introducing new public claims, so no pages are added or edited. If\nmaintained docs describing refresh behavior are discovered during execution,\nupdate them in the same change.\n\n### Task checklist\n\n- [ ] Add `refresh()` to `Books.vue` and route `selectFilter`/`add`/`update`/\n  `remove` through it; remove the stale `// regression: filter lost` markers.\n- [ ] Extend `client/tests/Books.spec.js` with CRUD-refresh filter and\n  `aria-pressed` coverage (read path and all path).\n- [ ] Add `client/tests/api-books.spec.js` pinning the filter\u2192params mapping.\n- [ ] Run the client vitest suite and root pytest suite; confirm green and no\n  server/api diffs.\n\n### Requirement verification\n\n- Filter reused on CRUD refresh \u2192 component test: mocked `getBooks` last\n  called with the selected filter after each of add/update/remove (boundary:\n  component\u2192api-client seam; the mock records the argument the fix controls\n  rather than bypassing the behavior under test).\n- Filter stays visibly active \u2192 component test: `aria-pressed=\"true\"` on the\n  selected button after each CRUD refresh (boundary: rendered component DOM).\n- API response shapes preserved \u2192 no diff to `server/app.py` or\n  `client/src/api/books.js` handling; existing `tests/test_books_api.py`\n  passes unmodified (boundary: Flask test client).\n- Unfiltered behavior preserved \u2192 api spec asserts `all` \u2192 `GET /books` with\n  empty params; the existing unfiltered server test passes; the component\n  `all`-path assertion (boundary: client request contract + Flask test\n  client).\n\n### Additional implementation verification\n\n- Optional, cheap server pin: extend `tests/test_books_api.py` with a\n  `GET /books?read=true` assertion returning only read books. That behavior\n  is pre-existing and unchanged by this fix; include it only if desired when\n  executing."
    },
    "task_tree": {
      "all_dependencies_resolve": true,
      "all_parent_links_resolve": true,
      "dependencies": [],
      "files": [
        {
          "dependencies": [],
          "has_execution_plan": true,
          "parent_task": null,
          "path": "tasks/20260919-books-crud-filter-refresh.md",
          "phase_terms": [],
          "plan_status": "Draft",
          "requirement_count": 4,
          "title": "Books CRUD refresh must reapply the selected status filter"
        }
      ],
      "parent_links": [],
      "phase_named_files": [],
      "task_directory_count": 0,
      "task_file_count": 1
    },
    "tool_metrics": {
      "list": 0,
      "mutation": 1,
      "other": 1,
      "read": 15,
      "search": 1,
      "shell": 5,
      "total": 22
    },
    "valid": true
  },
  {
    "invalid_reasons": [],
    "producer": {
      "model": "gpt-5.6-luna",
      "profile": "gpt",
      "reasoning_effort": "high"
    },
    "response": "Created the Draft single-task plan:\n\n[20260919-preserve-book-filter-after-crud.md](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T200517.144897Z-task-guidance-tg03-flask-vue-refresh-handoff-high-fb7445ee/workspace/tasks/20260919-preserve-book-filter-after-crud.md)\n\nIt covers:\n\n- Preserving `selectedFilter` across add, update, and delete refreshes.\n- Keeping the active filter visibly represented through `aria-pressed`.\n- Retaining the existing `All`/unfiltered behavior.\n- Preserving the Flask/API response shapes.\n- Component regression tests for `Read`, `Unread`, and `All`.\n- API response-key verification if current tests do not already prove it.\n- Documentation scope and verification steps.\n\nNo implementation or tests were run; execution remains intentionally unstarted because the plan is `Draft`. `git diff --check` passes.",
    "task_files": {
      "tasks/20260919-preserve-book-filter-after-crud.md": "# Preserve the selected book filter across CRUD refreshes\n\nThe Books page must keep its selected `All`, `Read`, or `Unread` filter active\nafter adding, editing, or deleting a book, and must refresh the collection\nusing that same filter.\n\n## Requirements checklist\n\n- [ ] After an add, update, or delete completes, the Books page refreshes the\n  collection with the currently selected filter.\n- [ ] The selected filter remains visibly active after each CRUD refresh,\n  including the `aria-pressed` state used by the filter controls.\n- [ ] The existing `All`/unfiltered behavior is preserved, including the\n  default collection and the client request behavior for the `all` filter.\n- [ ] The existing API response shape and Flask API contract remain unchanged.\n- [ ] Component-level regression coverage proves filtered refreshes for CRUD\n  operations and the preserved unfiltered path.\n\n## Scope and ownership\n\nThis is one cohesive client-side task owned by `client/src/components/Books.vue`\nand its component tests. The Flask routes and the `getBooks` response\ntransformation are existing boundaries to preserve, not separate workstreams:\nthe defect is that the three CRUD handlers omit the component's\n`selectedFilter` when calling `getBooks`.\n\n## Requirement questions and decisions\n\n- No unresolved requirement questions.\n- Decision: use a single task file rather than subtasks because the required\n  behavior is a localized state-and-refresh interaction whose useful result\n  cannot be split into independently complete UI and API changes.\n- Decision: keep the fix at the component refresh boundary and do not change\n  query encoding, server filtering, or response payloads.\n\n## Research and supporting facts\n\n- `Books.vue` stores the current filter in `selectedFilter` and passes a\n  selected value to `getBooks` from `selectFilter`.\n- `add`, `update`, and `remove` currently call `getBooks()` without an\n  argument, which defaults to the unfiltered `all` request.\n- The filter buttons already derive `aria-pressed` from `selectedFilter`, so\n  preserving that state does not require a new visual-state mechanism.\n- `client/src/api/books.js` maps `all` to an empty query object and maps\n  `read`/`unread` to the existing `read` query parameter.\n- The Flask API returns collection responses under `books` and mutation\n  responses under `book`; no response-shape change is needed.\n- There is no `docs/index.md`, and the existing development documentation says\n  no book-discovery specification exists. No maintained user or developer page\n  currently documents this interaction.\n\n## Execution plan\n\nStatus: Draft\n\nImplement the refresh behavior in the Books component by ensuring every CRUD\ncompletion reloads through the current `selectedFilter`. Prefer one small\ncomponent-level refresh path if that keeps the three handlers consistent; it\nmust continue to consume `getBooks(...).data.books` without changing the API\nadapter or Flask routes.\n\nExtend `client/tests/Books.spec.js` with deterministic mocked collection\nresponses and assertions that:\n\n1. selecting `read` or `unread` keeps the corresponding filter control\n   pressed and causes each of add, update, and delete to refresh with that\n   filter;\n2. the refreshed rows reflect the returned filtered collection;\n3. selecting or retaining `all` causes CRUD refreshes to use the existing\n   unfiltered path; and\n4. the filter remains active after the asynchronous refresh completes.\n\nRun the client test command from `client/package.json`. If the test harness\nrequires a small setup adjustment to exercise the component methods, keep that\nadjustment test-only and preserve the real component/API boundary. Inspect the\ndiff and existing Flask/API tests to confirm no server contract or response\nshape was altered; if the current API tests do not assert the response keys,\nadd focused assertions without changing the route implementation.\n\n### Implementation decisions and open questions\n\n- Use the existing `selectedFilter` value as the single source of truth for\n  both the visible control state and post-mutation collection refreshes.\n- Keep `getBooks`'s existing default and query mapping intact so `all` remains\n  unfiltered and the API response shape remains untouched.\n- No open requirement questions remain. A local implementation choice between\n  a shared refresh method and direct argument passing may be resolved by the\n  executor based on the smallest clear diff; it must satisfy the same tests.\n\n### Documentation\n\nNo documentation update is planned because the repository has no maintained\npage describing Books filter interactions, and creating a placeholder page\nwould add no useful audience-facing guidance. If an existing maintained Books\nguide is discovered during execution, update it in the same change to describe\nthat CRUD refreshes retain the selected filter.\n\n### Task checklist\n\n- [ ] Update the Books component so add, update, and delete refresh with\n  `selectedFilter`.\n- [ ] Add regression tests for `read` and `unread` CRUD refreshes and visible\n  filter state.\n- [ ] Add or retain coverage for the `all`/unfiltered CRUD refresh path.\n- [ ] Run the client test suite and verify the API/server boundary, adding\n  focused response-key assertions only if existing tests do not already prove\n  the unchanged shape.\n- [ ] Record implementation and completion notes after execution begins and\n  the evidence is available.\n\n### Requirement verification\n\n- Selected-filter refresh: the Vue component test selects a non-`all` filter,\n  executes each CRUD handler with mocked successful mutations, waits for the\n  refresh, and asserts `getBooks` received the selected filter and the\n  resulting rows come from that filtered response.\n- Visible active filter: the same component test asserts the selected\n  button's `aria-pressed` value remains `true` and the other filter buttons\n  remain inactive after each asynchronous CRUD refresh.\n- Preserved unfiltered behavior: a component regression test exercises CRUD\n  while `all` is selected and verifies the refresh uses the existing `all`\n  path; the unchanged API adapter mapping preserves an empty query for that\n  path.\n- API contract: inspect the diff and run the Flask API tests, asserting that\n  collection responses still expose `status` and `books`, mutation responses\n  still expose `status` and `book`, and no route or payload implementation has\n  changed."
    },
    "task_tree": {
      "all_dependencies_resolve": true,
      "all_parent_links_resolve": true,
      "coordinating_files": [],
      "dependencies": [],
      "files": [
        {
          "dependencies": [],
          "has_execution_plan": true,
          "parent_task": null,
          "path": "tasks/20260919-preserve-book-filter-after-crud.md",
          "phase_terms": [],
          "plan_status": "Draft",
          "requirement_count": 5,
          "title": "Preserve the selected book filter across CRUD refreshes"
        }
      ],
      "implementation_task_count": 1,
      "parent_links": [],
      "phase_named_files": [],
      "task_directory_count": 0,
      "task_file_count": 1
    },
    "tool_metrics": {
      "list": 0,
      "mutation": 2,
      "other": 2,
      "read": 0,
      "search": 0,
      "shell": 9,
      "total": 11
    },
    "valid": true
  }
]
