# Session — tg03-flask-vue-refresh-handoff · plan-retain · glm max

- Run: `20260925T222307.070068Z-task-guidance-handoff-tg03-flask-vue-refresh-handoff-retain-154c0ef7`
- Model: glm-5.3-flash:cloud (effort max)
- Tools: claude_bash_tool, claude_read_tool, claude_task_stop_tool, claude_write_tool, claude_edit_tool, claude_glob_tool, claude_grep_tool, claude_web_fetch_tool, claude_web_search_tool, claude_mcp_tool
- Delivered instructions: [glm-max](../../../../../shared/system-messages/glm-152f3d9b2d0c.md) — captured (original SHA-256 `a221b96574cb1737…`)
- Config: [glm-max](../../../../../shared/configs/glm-max.json)
- Activity: 33 messages · 21 tool calls · 21 tool results
- Usage: unknown — saved session contains no provider usage metadata

## Transcript

**User**

Read the task files and present the Draft implementation plan. Do not modify files or implement the task.

**Assistant** *(reasoning present)*

I'll start by locating and reading the task files.

- `Bash` {"command": "ls -la \"<workspace>\"", "description": "List workspace root contents"}
- `Glob` {"pattern": "tasks/**/*.md"}

**Tool `Bash`** — *(result omitted)*

**Tool `Glob`** — *(result omitted)*

**Assistant**

- `Read` {"file_path": "<workspace>/tasks/20260919-tg03-flask-vue-refresh-handoff.md"}
- `Read` {"file_path": "<workspace>/AGENTS.md"}

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Assistant** *(reasoning present)*

Now let me inspect the repository state relevant to this task — the README, docs, client component, API module, Flask route, and existing tests.

- `Read` {"file_path": "<workspace>/README.md"}
- `Read` {"file_path": "<workspace>/docs/index.md"}
- `Read` {"file_path": "<workspace>/client/src/components/Books.vue"}
- `Read` {"file_path": "<workspace>/client/src/api/books.js"}

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Assistant**

- `Glob` {"pattern": "server/**/*.py"}
- `Glob` {"pattern": "tests/**/*"}
- `Glob` {"pattern": "client/src/**/*"}

**Tool `Glob`** — *(result omitted)*

**Tool `Glob`** — *(result omitted)*

**Tool `Glob`** — *(result omitted)*

**Assistant**

- `Read` {"file_path": "<workspace>/server/app.py"}
- `Read` {"file_path": "<workspace>/tests/test_books_api.py"}
- `Read` {"file_path": "<workspace>/tests/conftest.py"}
- `Read` {"file_path": "<workspace>/client/src/http.js"}

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Assistant** *(reasoning present)*

Let me check the client test infrastructure and project config to understand what test tooling is available.

- `Bash` {"command": "ls -la \"<workspace>/client\" && cat \"<workspace>/pyproject.toml\"", "description": "List client directory and read pyproject.toml"}

**Tool `Bash`** — *(result omitted)*

**Assistant**

- `Read` {"file_path": "<workspace>/client/package.json"}
- `Bash` {"command": "ls -la \"<workspace>/client/tests\"", "description": "List client tests directory"}

**Tool `Read`** — *(result omitted)*

**Tool `Bash`** — *(result omitted)*

**Assistant**

- `Read` {"file_path": "<workspace>/client/tests/Books.spec.js"}

**Tool `Read`** — *(result omitted)*

**Assistant** *(reasoning present)*

- `Bash` {"command": "ls -R \"<workspace>/docs\"", "description": "List docs directory contents"}
- `Read` {"file_path": "<workspace>/.guidance-lock.json"}

**Tool `Bash`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Assistant** *(reasoning present)*

I've read the task file (`tasks/20260919-tg03-flask-vue-refresh-handoff.md`) and inspected the relevant code. The existing Draft plan is still accurate — I confirmed the regression at `client/src/components/Books.vue:32,36,40` (all three mutations call `getBooks()` with no argument, falling back to `"all"`), the filter encoding in `client/src/api/books.js:3-6`, and the Flask route already accepting the `read` param at `server/app.py:15-19`. No files were modified.

Here is the reassessed **Draft** plan. Execution has not started and waits for your approval.

---

## Draft execution plan — Preserve the Selected Book Filter During CRUD Refresh

### Approach

**Fix (single component, no contract changes).** Add one filter-aware refresh method to `Books.vue`, e.g. `async refreshBooks() { this.books = (await getBooks(this.selectedFilter)).data.books; }`, and route `selectFilter` plus all three mutations (`add`, `update`, `remove`) through it. `selectFilter` sets `this.selectedFilter` before refreshing, so it keeps its current semantics; mutations now refresh with the retained filter. When the filter is `"all"`, the encoded request is identical to today's unfiltered call (no `read` param), so `REFRESH-4` compatibility holds by construction. `api/books.js` and `server/app.py` are untouched.

**Verification design (this is the main decision to approve).** `REFRESH-2` requires the refresh to cross the *production* client transport and the Flask route, so a component test with the API module mocked cannot be decisive. The plan adds:

1. **Full-stack spec** (`client/tests/Books.fullstack.spec.js`) — mounts `Books` with the **real** `api/books.js` + `http.js` axios instance, against a **real Flask server** on `localhost:5000` (the hardcoded `baseURL`). A new `client/vitest.config.js` + `globalSetup` spawns the server (`python3 -c "from server.app import app; app.run(port=5000)"` from the repo root, readiness-polled, killed on teardown). One sequential spec drives select filter → add → update → delete, using unique ids and asserting on its own added titles, so Flask's shared in-process `BOOKS` state can't break assertions. This single automated test traverses component → API module → axios → Flask route → rendered result, satisfying the "one named decisive check through the actual production path" rule.
2. **Component tests** (`client/tests/Books.spec.js`, API module mocked) — cheap supporting evidence at the component boundary: active filter retention (`REFRESH-1`), rendered results/empty state matching the refreshed response (`REFRESH-3`), and `"all"`-selected compatibility (`REFRESH-4` client side). These are supporting evidence only, not the REFRESH-2 check.
3. **Server-side regressions** (`tests/test_books_api.py`) — filter-param behavior (`read=true`, `read=false`, no param) plus response-shape assertions, guarding `REFRESH-4`'s route compatibility.

### Task checklist

- [ ] Confirm all mutation refresh call paths (done during planning: three, all in `Books.vue`)
- [ ] Add shared `refreshBooks()` and route `selectFilter` + `add`/`update`/`remove` through it
- [ ] Add component tests: filter retention, rendered results/empty state, `"all"` compatibility
- [ ] Add full-stack spec + vitest config/globalSetup spawning Flask on :5000
- [ ] Extend Flask tests: filter-param and response-shape regressions
- [ ] Run client vitest suite, full-stack spec, and pytest suite; all green

### Requirement verification

| Requirement | Evidence |
|---|---|
| `REFRESH-1` | Component test: `aria-pressed` stays on the selected filter after add/update/delete refreshes |
| `REFRESH-2` | Full-stack spec: mutation refreshes carry the filter through real axios transport to the live Flask route |
| `REFRESH-3` | Full-stack spec + component tests: rendered rows and empty state match the refreshed filtered response |
| `REFRESH-4` | Existing + extended pytest suite green; existing client empty-state test green; `"all"` path unchanged in component tests |

### Implementation decisions and open questions

No requirement questions are open. Resolved locally: the shared-refresh shape above (internal to the component). Decision needing your approval: the **full-stack harness** (new `client/vitest.config.js` + globalSetup spawning Flask) as the decisive REFRESH-2 check — it's the honest production path but adds a small piece of test infrastructure.

### Documentation

None. This is a regression fix with no new public claims; `README.md` and the fixture docs remain accurate. No audience or doc change expected.

### Risks

- Port 5000 availability / Flask not installed in the environment → globalSetup fails fast with a clear message; readiness poll with timeout.
- Flask's in-process `BOOKS` is shared across requests → E2E assertions scoped to unique ids/titles it adds itself; one sequential full-stack spec avoids concurrent hammering.

### Exclusions

No changes to `api/books.js`, `server/app.py`, or any contracts; no new runtime dependencies; no documentation updates.

---

**Approval requested for the plan as summarized (notably the full-stack test harness).** If you approve, I'll mark the plan `Approved` in the task file and begin execution, updating the checklist as I go. Execution waits.
