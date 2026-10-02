# Session — tg03-flask-vue-refresh-handoff · plan-omit · glm max

- Run: `20260919T224000.396486Z-task-guidance-handoff-tg03-flask-vue-refresh-handoff-omit-36ec60c0`
- Model: glm-5.3-flash:cloud (effort max)
- Tools: claude_bash_tool, claude_read_tool, claude_task_stop_tool, claude_write_tool, claude_edit_tool, claude_glob_tool, claude_grep_tool, claude_web_fetch_tool, claude_web_search_tool, claude_mcp_tool
- Delivered instructions: [glm-max](../../../../shared/system-messages/glm-f7acbd8a2b1b.md) — captured (original SHA-256 `0962b70fdf0ce773…`)
- Config: [glm-max](../../../../shared/configs/glm-max.json)
- Activity: 30 messages · 19 tool calls · 19 tool results
- Usage: unknown — saved session contains no provider usage metadata

## Transcript

**User**

Read the task files and present the Draft implementation plan. Do not modify files or implement the task.

**Assistant** *(reasoning present)*

I'll start by exploring the workspace to find the task files.

- `Bash` {"command": "ls -la <workspace>", "description": "List files in workspace directory"}
- `Glob` {"pattern": "tasks/**/*"}

**Tool `Bash`** — *(result omitted)*

**Tool `Glob`** — *(result omitted)*

**Assistant**

- `Read` {"file_path": "<workspace>/tasks/20260919-tg03-flask-vue-refresh-handoff.md"}
- `Read` {"file_path": "<workspace>/AGENTS.md"}

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Assistant** *(reasoning present)*

The task file has requirements but no execution plan (this handoff omitted the plan). I'll inspect the repository state needed to formulate the plan, without modifying anything.

- `Read` {"file_path": "<workspace>/README.md"}
- `Glob` {"pattern": "**/*"}

**Tool `Read`** — *(result omitted)*

**Tool `Glob`** — *(result omitted)*

**Assistant**

- `Read` {"file_path": "<workspace>/client/src/components/Books.vue"}
- `Read` {"file_path": "<workspace>/client/src/api/books.js"}
- `Read` {"file_path": "<workspace>/client/src/http.js"}

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Assistant** *(reasoning present)*

- `Read` {"file_path": "<workspace>/server/app.py"}
- `Read` {"file_path": "<workspace>/tests/test_books_api.py"}
- `Read` {"file_path": "<workspace>/tests/conftest.py"}
- `Read` {"file_path": "<workspace>/client/tests/Books.spec.js"}

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Assistant** *(reasoning present)*

- `Read` {"file_path": "<workspace>/client/package.json"}
- `Read` {"file_path": "<workspace>/pyproject.toml"}
- `Read` {"file_path": "<workspace>/UPSTREAM.md"}
- `Read` {"file_path": "<workspace>/docs/development/index.md"}

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Assistant** *(reasoning present)*

- `Read` {"file_path": "<workspace>/docs/development/documentation.md"}

**Tool `Read`** — *(result omitted)*

**Assistant** *(reasoning present)*

I have the full picture now. Let me quickly check the remaining config file, then present the plan.

- `Read` {"file_path": "<workspace>/.guidance-lock.json"}

**Tool `Read`** — *(result omitted)*

**Assistant** *(reasoning present)*

I've read the task file (`tasks/20260919-tg03-flask-vue-refresh-handoff.md`) and the code it references. No files have been modified — the plan below is presented here only (the task file stays untouched until you approve, and I can write it in as `## Execution plan` at that point if you want it tracked).

**Key findings from inspection:**
- Root cause confirmed: `client/src/components/Books.vue:32,36,40` — `add`, `update`, and `remove` call `getBooks()` with no argument, falling back to the `"all"` default and discarding `selectedFilter`. Filter selection itself (`Books.vue:26-29`) works.
- `client/src/api/books.js:3-4` encodes the filter (`read=true|false` param, none for `all`); `server/app.py:15-19` already filters on it. Neither needs changes.
- `client/tests/Books.spec.js` currently mocks the entire `api/books` module, which bypasses both the real filter encoding and the transport — insufficient evidence for `REFRESH-2`.

---

## Execution plan

Status: Draft

### Approach

Root cause is client-side only: the three mutation methods in `Books.vue` refresh via `getBooks()` without the selected filter, so every add/update/delete resets the visible list to the unfiltered response while the button state still claims the old filter. The fix restores the already-supported filtered refresh by passing the selected filter through the existing production path — component → `getBooks(selectedFilter)` → axios transport (`client/src/http.js`) → `GET /books?read=...` → existing Flask filtering. No contracts change: request/response shapes, route behavior, and the `getBooks(filter = "all")` signature stay as they are; unfiltered behavior (default `"all"`, no `read` param) is preserved because `selectedFilter` always holds a valid value.

### Scope

- **Change:** `client/src/components/Books.vue` — pass `this.selectedFilter` to `getBooks` in `add`, `update`, and `remove`.
- **Test changes:** `client/tests/Books.spec.js` — replace the api-module mock with a mocked `../src/http` transport so the real `getBooks` encoding is exercised; add filter-retention cases for add/update/remove, the active-choice/`aria-pressed` state, and the filtered empty state. `tests/test_books_api.py` — add route filtering assertions for `read=true` / `read=false` / unfiltered, plus light response-shape assertions.
- **Unchanged:** `client/src/api/books.js`, `client/src/http.js`, `server/app.py`, existing contracts (`REFRESH-4`).

The Flask route already accepts the filter and the client encoding already works for manual selection, so both sides of the HTTP seam are established production behavior; the only new behavior is which filter value the mutation refreshes send.

### Risks

- The test-file mocking strategy changes from `../src/api/books` to `../src/http`; the existing empty-state test must keep passing under the new setup.
- axios param serialization (`params: { read: false }` → `?read=false`) is not covered by the component test because the transport is mocked at the instance boundary; this seam is already proven by the working manual filter selection, and the server-side half is covered by pytest.
- If the single-test end-to-end option below is declined, evidence for `REFRESH-2` is compositional (client-side request shape + server-side route filtering) rather than one live crossing.

### Implementation decisions and open questions

- **Decision (local, reversible):** Fix is the minimal three-line change in `Books.vue` (`getBooks(this.selectedFilter)`), not a refactor into a shared `refresh()` helper and not client-side list filtering, which would bypass the required client-to-server crossing.
- **Decision (local, reversible):** Swap the component-test mock from the api module to the `../src/http` transport so the real `getBooks` filter encoding stays in the exercised path; keep the existing empty-state test.
- **Open question (needs your decision):** Should evidence for `REFRESH-2` include a true end-to-end integration test — a vitest test that spawns the Flask server as a subprocess and issues real axios calls against `GET /books?read=...`? That gives decisive single-boundary evidence for the transport+route crossing but introduces a new cross-language test harness (subprocess lifecycle, port polling, cleanup) disproportionate to this fixture. **Recommendation:** rely on the compositional evidence (transport-level request assertions in vitest + route filtering in pytest), since the seam itself is already production-proven; add the E2E test only if you want the decisive live crossing.

### Documentation

None planned. This is a bug fix restoring already-supported filtered-refresh behavior; it introduces no new public claims, and the fixture's `README.md` and `docs/development/index.md` (which states no book-discovery specification exists) remain accurate. Per the smallest-structure guidance, no documentation pages are created.

### Task checklist

- [ ] Fix `add`, `update`, and `remove` in `client/src/components/Books.vue` to refresh via `getBooks(this.selectedFilter)`.
- [ ] Rework `client/tests/Books.spec.js` to mock `../src/http` (real api module) and add tests: selection retained with `aria-pressed` after add/update/delete; refreshed rows match the filtered response; filtered empty state shows "No books found." with the choice still active.
- [ ] Add pytest coverage in `tests/test_books_api.py` for `GET /books?read=true`, `?read=false`, and unfiltered (shape + membership), plus response-shape assertions for the existing mutation flow.
- [ ] Run `pytest` (root) and `client` vitest suite; record results as requirement evidence.

### Requirement verification

- **`REFRESH-1`** — Component test: after selecting `read`/`unread` and performing add/update/delete, `selectedFilter` remains active and the corresponding button keeps `aria-pressed="true"`. Boundary: mounted component with real api module.
- **`REFRESH-2`** — Client: component test asserts each mutation refresh calls the production `getBooks(selectedFilter)` and issues `http.get("/books", { params: { read: <bool> } })` with the real encoding. Server: pytest asserts the Flask route returns only matching books for `read=true`/`read=false` and all books unfiltered. Compositional; upgradeable to a decisive live crossing via the open-question E2E test if approved.
- **`REFRESH-3`** — Component test: rendered rows (or the "No books found." empty state) exactly match the mocked filtered response for the selected filter after each mutation, while the active choice stays pressed.
- **`REFRESH-4`** — Existing pytest CRUD tests keep passing unchanged status expectations; new pytest assertions pin response shapes; `getBooks` default (`"all"`, no `read` param) and server route behavior are unmodified, and the unfiltered-refresh path is covered by the component test for the `"all"` case.

### Additional implementation verification

- Full-suite runs (`pytest` at root, `vitest run` in `client/`) to confirm no regression in the untouched empty-state test and existing CRUD tests.
- Review the final diff to confirm only `Books.vue` plus the two test files changed and no server/api contract was touched.

---

**Summary for approval:** the outcome is a full-stack-consistent bug fix — after add/update/delete, the Books page keeps the chosen All/Read/Unread filter and re-queries the Flask API through the real transport so results, empty state, and active button agree. Scope is one production file (`Books.vue`) plus the two test files. Acceptance evidence comes from component tests (filter retention, matching results/empty state) and pytest route tests (filtering, shapes, compatibility). No documentation changes, no contract changes. The one open question is whether to add a live vitest↔Flask E2E test for `REFRESH-2` (recommended: no). Execution waits for your explicit approval.
