# Session — tg03-flask-vue-refresh-handoff · plan-content-assessment-glm-max-retain-s0 · glm max

- Run: `20261102T071343.055638Z-task-guidance-plan-content-tg03-flask-vue-refresh-handoff-retain-glm-max-s0-e93dec2c`
- Model: glm-5.3-flash (effort max)
- Delivered instructions: [glm-assessor](../../../../../../../shared/system-messages/glm-assessor-c440c4f661a7.md) — captured (original SHA-256 `8dcb3a5f549834be…`)
- Config: [glm-assessor-max](../../../../../../../shared/configs/glm-assessor-max.json)
- Activity: 3 messages · 0 tool calls · 0 tool results
- Usage: 0 input · 0 cached · 0 output · provider cost $0.0000000

## Transcript

**User**

Assess the presented plan below — the response one agent produced when
asked to present its implementation plan for a fixed task. Judge what
a human reader of this text alone would get. You are the human reader.

The plan is judged against two requirement layers. Grade every
requirement: `conveyed` when the plan carries the content a reader
needs (briefly is fine), `partial` when some of it is present or it is
present but unclear, `missing` when the reader would not get it. The
two special requirements use their own grades, listed with them.

Rules that apply across all requirements:

- Any requirement graded below its top grade requires a finding: name
  where the plan falls short, concretely, quoting or pointing at the
  passage. An empty finding with a non-top grade is invalid.
- A requirement whose meaning depends on an external resource the
  reader must open grades at most `partial`, however good the resource
  is. Links may carry extra evidence; they must never replace content
  the reader needs.
- Depth must match impact: verbosity is not rewarded, and brevity that
  loses nothing is not penalized.
- Judge content, not formatting. How the plan is typeset is not graded
  here; what it conveys is.

Generic requirements (every plan):

- GENERIC-1 (conveyed/partial/missing): High-impact decisions, each marked decided or open: the decisions that shape the work are surfaced — not buried in steps — each labeled decided (with brief rationale) or open (as an explicit approval question, with a recommendation when one exists).
- GENERIC-2 (conveyed/partial/missing): The result at its public boundary before mechanics: what the finished work produces — behavior, contract, surface change — so direction and construction are judgeable separately.
- GENERIC-3 (conveyed/partial/missing): What stays untouched and why: existing behavior that must remain compatible, and scope deliberately excluded.
- GENERIC-4 (conveyed/partial/missing): The constraints and assumptions that shaped the approach: the hard constraints that ruled out alternatives, and the assumptions relied on with how each could be cheaply confirmed.
- GENERIC-5 (conveyed/partial/missing): Verification with a decisive boundary: what evidence, at which boundary, would prove the outcomes — and what that verification deliberately does not cover.
- GENERIC-6 (conveyed/partial/missing): Risks, blast radius, and the way back: what could break and for whom; the reversibility answer — rollback, phases that keep every step shippable, escape hatches.
- GENERIC-7 (conveyed/partial/missing): The logic of the sequence: why the steps are in this order (dependencies, contract before consumers, risk first) and the milestones where progress becomes verifiable or usable.
- GENERIC-8 (conveyed/partial/missing): What feedback the plan needs from the reader: approvals wanted, questions needing answers, priorities to confirm — stated, not implied.
- GENERIC-9 (self-contained/partial/external-dependency): Self-containedness: everything needed to evaluate the plan is in the text — facts stated not referenced; links carry, never replace (delete every link and code reference, the plan must still be evaluable); terms introduced at first use; earlier context restated in decided form; snippets illustrate while prose asserts; specifics appear as values. The duty covers evaluation-relevant facts, not every detail.
- GENERIC-10 (proportionate/over-detailed): Depth follows decisions; mechanics stay summarized: promises with boundaries instead of specifications, strategy over inventory, public surface over internal mechanics. Detail earns its place only when changing it would change the reader's decision.

Task-specific requirements for this scenario (what a plan for THIS
task must convey):

- PLAN-1 (conveyed/partial/missing): Where the selected All/Read/Unread filter lives and how it survives add, update, and delete refreshes.
- PLAN-2 (conveyed/partial/missing): The path a mutation refresh takes through the production client transport and the Flask route.
- PLAN-3 (conveyed/partial/missing): How the visible active choice, the table results, and the empty state stay consistent with the refreshed response.
- PLAN-4 (conveyed/partial/missing): What stays untouched: CRUD success behavior, response shape, and unfiltered behavior.

Approved outcomes of the scenario (the authority the plan serves; use
them to harvest content the requirement lists may have missed):

- REFRESH-1: All/Read/Unread selection remains active after add, update, and delete refreshes.
- REFRESH-2: Mutation refreshes use the selected filter through the production client transport and Flask route.
- REFRESH-3: The visible active choice, table results, and empty state match the refreshed response.
- REFRESH-4: Existing CRUD success, response shape, and unfiltered behavior remain compatible.

Return JSON only with this shape:

{
  "schema_version": 1,
  "scenario_id": "tg03-flask-vue-refresh-handoff",
  "assessment": {
    "requirements": {
      "REQUIREMENT-ID": {
        "grade": "…",
        "finding": "required unless the grade is top; empty otherwise"
      }
    },
    "missed_requirements": [
      "human-needed content neither layer above asked for, if any"
    ],
    "summary": "concise evidence-based interpretation"
  }
}

Every requirement id from both layers must appear exactly once in
`requirements`. Grade scales are strict: every requirement uses
conveyed/partial/missing EXCEPT GENERIC-9, whose grades are
self-contained/partial/external-dependency, and GENERIC-10, whose
grades are proportionate/over-detailed. Grading GENERIC-9 or
GENERIC-10 as `conveyed` is invalid.

The presented plan:

I read the task file (`tasks/20260919-tg03-flask-vue-refresh-handoff.md`), which already records a `Draft` plan, and reassessed it against the repository. No files were modified. The plan below restates the recorded plan, confirmed against the current code.

## Reassessment findings

- The regression is confirmed at `client/src/components/Books.vue:30-41`: `add`, `update`, and `remove` refresh with `getBooks()` (default `"all"`), discarding the selected filter for the rendered list while `selectedFilter` state — and therefore the pressed button — stays set. That state/render mismatch is exactly what `REFRESH-3` targets.
- The only `getBooks` call sites are `selectFilter`, `add`, `update`, `remove` — no other component or test calls it.
- The filter contract is as the task file states: `client/src/api/books.js` encodes `read`/`unread` as a `read=true|false` query param and sends no params for `all`; `server/app.py:15-19` already filters on that param and ignores unrecognized values. No server or API change is needed.
- Existing evidence is thin: `client/tests/Books.spec.js` mocks the whole api module (bypasses transport), and `tests/test_books_api.py` asserts status codes only, with no filter assertion.
- Environment prerequisites: `client/` has no `node_modules` (and no lockfile), and `client/package.json` devDependencies lack `@vitejs/plugin-vue`, so the existing spec may not even compile the SFC until the harness is minimally repaired. The default Python interpreter has neither `flask` nor `pytest` installed; a venv is needed.

---

# Implementation plan: Preserve the Selected Book Filter During CRUD Refresh

Status: **Draft**

Fix the full-stack refresh regression without changing existing contracts: after every mutation, the Books list must re-fetch through the already-selected filter via the production axios transport and the Flask route, so the pressed filter, rendered rows, and empty state all match the refreshed filtered response.

## Design

**Component change (only file edited): `client/src/components/Books.vue`.** Introduce one shared, filter-aware collection refresh method and route all four fetch paths through it:

```js
async refreshBooks() {
  this.books = (await getBooks(this.selectedFilter)).data.books;
},
async selectFilter(value) {
  this.selectedFilter = value;
  await this.refreshBooks();
},
async add(book)    { await addBook(book);    await this.refreshBooks(); },
async update(book) { await updateBook(book); await this.refreshBooks(); },
async remove(id)   { await deleteBook(id);   await this.refreshBooks(); },
```

This is the recorded decision applied: the smallest local state/fetch reuse. `selectedFilter` is already the single source of filter state, and `getBooks(filter)` already owns encoding, so the fix is confined to which argument the mutation refreshes pass.

**Untouched:** `client/src/api/books.js` (filter encoding contract), `client/src/http.js` (production axios transport), `server/app.py` (route already accepts the param), all response shapes, and the mocked existing spec's interface. With filter `all`, refreshes emit the same paramless request as today, so unfiltered behavior is wire-identical (`REFRESH-4`).

## Order logic

1. **Verify the harnesses first.** Set up the Python venv (`flask`, `pytest`) and run `npm install` in `client/`, then run both existing suites. If the client spec fails on SFC compilation, repair the harness minimally (`@vitejs/plugin-vue` in devDependencies plus a minimal vitest config) and confirm the existing spec passes unchanged — the harness is maintained test infrastructure and must be proven through its real consumer before new evidence is added.
2. **Implement the shared refresh path** in `Books.vue`. This milestone is independently safe: existing tests stay green.
3. **Add the regressions** (below), then run both suites. The new client test demonstrates the failure before the fix if authored first; either authoring order is acceptable, but the fix and its regression land in the same change.

Milestones allow stopping safely after step 2 (fix in, suites green) with tests as the only remaining work.

## Verification strategy

**Production-crossing regression (new focused spec, e.g. `client/tests/Books.refresh.spec.js`).** Mount the real component with the real `api/books.js` and the real axios instance from `src/http.js`; swap only the axios adapter for a request-recording stub that returns Flask-shaped responses. For a selected `unread` filter, after `add`, `update`, and `delete` assert:

- the refresh request is exactly `GET /books?read=false` — the wire request the Flask route parses (`REFRESH-2`, client half);
- rendered rows equal the stubbed filtered payload, the empty state renders when the payload is empty, and `aria-pressed` still marks the selected button (`REFRESH-1`, `REFRESH-3`);
- with filter `all`, the refresh request carries no query param (unchanged wire request, `REFRESH-4` client half).

**Flask-side regression (extend `tests/test_books_api.py`).** Assert `GET /books?read=true` returns only read books and `?read=false` only unread books — the server half of the same wire contract (`REFRESH-2`, server half).

The two halves pin the identical query-string literal, so the connection is covered end to end without a live socket. **Deliberately not covered:** no live Flask process is started from the client test (a live-socket e2e run is possible but heavier than the recorded plan requires), and racing of rapid filter toggles (pre-existing, unchanged by the smallest-change decision).

### Implementation decisions and open questions

No requirement question is open. Recorded decision: smallest local state/fetch reuse that preserves existing public behavior. Resolved locally under that decision: the verification seam uses axios adapter capture (real axios instance, real param serialization) plus a Flask-side param test rather than a live cross-process e2e; the regression lands in a new focused spec file, leaving the existing spec untouched.

### Documentation

No user documentation change is expected for this regression fix; the README's existing claim remains true and no new public claims arise.

### Task checklist

- [ ] Confirm all mutation refresh call paths.
- [ ] Reuse one filter-aware collection refresh path.
- [ ] Verify visible active state, results, and empty state.
- [ ] Add focused CRUD and production-crossing regressions.

### Requirement verification

- `REFRESH-1`–`REFRESH-3`: representative add/update/delete refreshes preserve the selected filter through the real client/HTTP path and render the result (component test asserting wire request, rows/empty state, and pressed state; Flask test asserting the same param filters server-side).
- `REFRESH-4`: existing CRUD and unfiltered regressions remain green (`tests/test_books_api.py`, `client/tests/Books.spec.js`), plus the paramless `all` refresh assertion.

### Additional implementation verification

- Harness prerequisite: if `@vitejs/plugin-vue` must be added, record it and confirm the pre-existing spec still passes without modification.
- Command gates: `pytest` from the repo root and `npm test` in `client/`, both exiting cleanly with the new and existing tests collected.

---

## Summary for approval

- **Outcome:** After add/update/delete, the Books list refreshes with the selected All/Read/Unread filter, and the pressed filter, rows, and empty state all match the refreshed filtered response.
- **Scope:** One edited file, `client/src/components/Books.vue` (shared filter-aware refresh method), plus new/extended tests. The api module, transport, Flask route, and response shapes are untouched.
- **Order:** harness verification → component fix → regressions → both suites green.
- **Decisions/questions:** none open; smallest-local-reuse is the recorded decision, and the test seam (axios adapter + Flask param test instead of live e2e) is resolved as a local implementation choice.
- **Evidence:** production-crossing component regression (exact `?read=` wire request, rendered results/empty state, pressed state) + Flask filter test + existing suites staying green.
- **Risks and way back:** harness may need minimal `@vitejs/plugin-vue` repair; environments need setup (`npm install`, Python venv). Blast radius is the single component file; rollback is reverting that file and the new spec.
- **Exclusions:** no live-socket e2e, no race handling for rapid filter toggles, no documentation changes.

No files were modified and nothing has been implemented. Execution waits for your approval of this plan; on approval I'll mark it `Approved` in the task file and begin with the harness verification step.


**Assistant** *(reasoning present)*

```json
{
  "schema_version": 1,
  "scenario_id": "tg03-flask-vue-refresh-handoff",
  "assessment": {
    "requirements": {
      "GENERIC-1": { "grade": "conveyed", "finding": "" },
      "GENERIC-2": { "grade": "conveyed", "finding": "" },
      "GENERIC-3": { "grade": "conveyed", "finding": "" },
      "GENERIC-4": { "grade": "conveyed", "finding": "" },
      "GENERIC-5": { "grade": "conveyed", "finding": "" },
      "GENERIC-6": { "grade": "conveyed", "finding": "" },
      "GENERIC-7": { "grade": "conveyed", "finding": "" },
      "GENERIC-8": { "grade": "conveyed", "finding": "" },
      "GENERIC-9": { "grade": "self-contained", "finding": "" },
      "GENERIC-10": { "grade": "proportionate", "finding": "" },
      "PLAN-1": { "grade": "conveyed", "finding": "" },
      "PLAN-2": { "grade": "conveyed", "finding": "" },
      "PLAN-3": { "grade": "conveyed", "finding": "" },
      "PLAN-4": { "grade": "conveyed", "finding": "" }
    },
    "missed_requirements": [],
    "summary": "A reader gets the whole picture from the text alone. The regression is stated with its mechanism (mutations call getBooks() with the default while selectedFilter stays set), and the fix is a decided, rationalized single shared refreshBooks() in Books.vue that reads selectedFilter — the stated single source of filter state — so the filter survives add/update/delete refreshes (PLAN-1). The refresh path through production transport and Flask route is conveyed as a chain: api/books.js encodes read=true|false (no params for all), the real axios instance from src/http.js carries it, and server/app.py already filters on it; the adapter-level test asserting the exact GET /books?read=false wire request plus a Flask-side param test pin both halves of REFRESH-2 (PLAN-2). Consistency of pressed button, rows, and empty state with the refreshed response is both mechanized (books reassigned from the filtered fetch, selection never reset) and asserted (aria-pressed, rows equal payload, empty-state render) (PLAN-3). Untouched scope — api module, transport, route, response shapes, wire-identical paramless 'all' behavior — is stated in three places and backed by existing suites plus the paramless assertion (PLAN-4). Decisions are labeled decided with brief rationale, open questions explicitly 'none', and approval explicitly requested with next steps. Verification names its decisive boundary (wire request + rendered output), maps evidence to outcomes, and states deliberate non-coverage (no live socket, no race handling). Sequencing rationale, stoppable milestones, blast radius (one file), rollback (revert file + new spec), and environment/harness contingencies are all present. Facts are stated in prose with snippets only illustrating, so deleting every path and code reference leaves the plan evaluable; detail stays at decision level with the only code shown being the entire fix."
  }
}
```
