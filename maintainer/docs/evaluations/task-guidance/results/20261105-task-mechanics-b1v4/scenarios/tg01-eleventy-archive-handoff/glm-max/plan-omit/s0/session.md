# Session — tg01-eleventy-archive-handoff · plan-omit · glm max

- Run: `20261102T004609.618265Z-task-guidance-handoff-tg01-eleventy-archive-handoff-omit-1febd87a`
- Model: glm-5.3-flash (effort max)
- Tools: claude_bash_tool, claude_read_tool, claude_task_stop_tool, claude_write_tool, claude_edit_tool, claude_glob_tool, claude_grep_tool, claude_web_fetch_tool, claude_web_search_tool, claude_mcp_tool
- Delivered instructions: [glm-max](../../../../../shared/system-messages/glm-8b4fac5728ee.md) — captured (original SHA-256 `4299a0e598c15191…`)
- Config: [glm-max](../../../../../shared/configs/glm-max.json)
- Activity: 31 messages · 22 tool calls · 22 tool results
- Usage: 0 input · 0 cached · 0 output · provider cost $0.0000000

## Transcript

**User**

Read the task files and present the Draft implementation plan. Do not modify files or implement the task.

**Assistant** *(reasoning present)*

- `Glob` {"pattern": "tasks/**/*"}
- `Bash` {"command": "ls -la", "description": "List files in workspace root"}

**Tool `Glob`** — *(result omitted)*

**Tool `Bash`** — *(result omitted)*

**Assistant** *(reasoning present)*

- `Read` {"file_path": "<workspace>/tasks/20260919-tg01-eleventy-archive-handoff.md"}
- `Read` {"file_path": "<workspace>/AGENTS.md"}
- `Read` {"file_path": "<workspace>/README.md"}

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Assistant** *(reasoning present)*

The task file has requirements but no plan yet, and notes two unresolved public decisions (later-page URL pattern, navigation presentation). Let me inspect the relevant repository state before drafting.

- `Read` {"file_path": "<workspace>/content/blog.njk"}
- `Read` {"file_path": "<workspace>/_includes/postslist.njk"}
- `Read` {"file_path": "<workspace>/tests/archive-output.test.js"}
- `Read` {"file_path": "<workspace>/eleventy.config.js"}
- `Read` {"file_path": "<workspace>/package.json"}

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Assistant** *(reasoning present)*

- `Bash` {"command": "find content _includes tests docs -type f | sort", "description": "List all content, template, test, and docs files"}

**Tool `Bash`** — *(result omitted)*

**Assistant**

- `Read` {"file_path": "<workspace>/content/index.njk"}
- `Read` {"file_path": "<workspace>/content/tag-pages.njk"}
- `Read` {"file_path": "<workspace>/content/feed.xml.njk"}
- `Read` {"file_path": "<workspace>/content/sitemap.xml.njk"}
- `Read` {"file_path": "<workspace>/content/posts/posts.json"}
- `Read` {"file_path": "<workspace>/content/posts/first.md"}
- `Read` {"file_path": "<workspace>/content/posts/second.md"}
- `Read` {"file_path": "<workspace>/docs/development/documentation.md"}

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Assistant** *(reasoning present)*

Two more files to complete the picture — the post layout (for ARCHIVE-5's "individual-post navigation") and the docs index — plus checking the installed toolchain state.

- `Read` {"file_path": "<workspace>/_includes/layouts/post.njk"}
- `Read` {"file_path": "<workspace>/docs/development/index.md"}
- `Bash` {"command": "ls node_modules/@11ty 2>/dev/null; node --version", "description": "Check installed Eleventy and Node version"}

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Bash`** — *(result omitted)*

**Assistant** *(reasoning present)*

I've read the task file and all relevant repository state. Key findings before the plan:

- **Current archive**: `content/blog.njk` renders the entire `collections.posts` (2 posts) through the shared `_includes/postslist.njk`, which reverses for newest-first order. That same include also serves home (`content/index.njk`, newest 3 via `head(-3)`) and tag pages (`content/tag-pages.njk`, full per-tag list) — so it must not be restructured.
- **Unchanged surfaces**: feed (`content/feed.xml.njk`) lists all posts newest-first; sitemap (`content/sitemap.xml.njk`) enumerates `collections.all`; the post layout has no prev/next nav.
- **Tests**: `tests/archive-output.test.js` contains only a comment — no tests exist today. Eleventy is not installed (`node_modules` absent), Node v20 available; execution will need `npm install`.
- **Open public decisions** (per the task file): the later-page URL pattern and the navigation presentation.

Per your instruction I have not modified any files — the plan is presented here only.

---

## Implementation plan

Status: Draft

### Decided design

Pagination is implemented entirely in `content/blog.njk` using Eleventy's native pagination; no shared template, config, or dependency changes.

- **Data flow**: `pagination.data: collections.posts`, `size: 20`, `reverse: true` (so page 1 holds the 20 *newest* posts, satisfying ARCHIVE-1 and ARCHIVE-3), and no alias — the page reads `pagination.items`.
- **Ordering subtlety**: `postslist.njk` internally applies `| reverse`, and home/tag callers depend on that behavior. `blog.njk` therefore passes `pagination.items | reverse` so the include's reverse restores newest-first display. `_includes/postslist.njk` stays byte-for-byte unchanged, eliminating risk to ARCHIVE-5 surfaces.
- **URLs**: page 1 stays `/blog/` (permalink unchanged); later pages follow the pattern chosen in the open questions below — recommended `/blog/{{ pagination.pageNumber + 1 }}/`.
- **Navigation**: inside a `<nav aria-label="Blog archive pages">`, links to `pagination.href.previous` ("Newer posts") and `pagination.href.next` ("Older posts") with `rel="prev"`/`rel="next"`, each rendered only when the href is truthy. Plain anchors, zero client-side JavaScript (ARCHIVE-4, ARCHIVE-6).

### Ordered steps and order logic

1. Apply the approved URL pattern and nav presentation in `content/blog.njk` (single-file, single-commit change).
2. Run `npm install`, then `npm run build` on the real content and inspect `_site/blog/index.html` and `_site/sitemap.xml` manually as a sanity gate before writing tests.
3. Rewrite `tests/archive-output.test.js` (currently comment-only) with production-build integration tests: each test copies the project (excluding `node_modules`, `.git`, tests) to a temp sandbox, symlinks `node_modules`, generates ~45 synthetic posts, runs the real `eleventy` production command in the sandbox, asserts on `_site` output, and cleans up. A second case builds the real 2-post content unchanged.
4. Run `npm test` and `npm run build`; both must collect and exit cleanly.
5. Update `README.md`'s archive sentence to state the bounded pagination behavior (one sentence, contingent on the URL decision).
6. Update the task file: requirement evidence and completion entry.

Steps 1–2 stop safely at any point: the change is one template file reverted by restoring its original six lines. Steps are ordered implementation → build sanity → evidence because the test asserts the approved pattern, which step 1 fixes.

### Risks and the way back

- **`pagination.reverse` semantics**: if the installed Eleventy version chunked before reversing (not its documented behavior), ordering breaks; the order assertions catch it. Fallback: reverse via a `pagination.before` filter registered in `eleventy.config.js`.
- **Double-reverse mistake** would show oldest-first; caught by ARCHIVE-3 ordering assertions.
- **Sitemap content grows**: `sitemap.xml.njk` enumerates `collections.all`, so new archive pages will legitimately appear. The generating rule is unchanged; see open question 3 if exclusions are wanted instead.
- **Blast radius / rollback**: one template file + one test file + one README sentence. No dependency, config, include, home, tag, feed, or post-layout changes. Rollback = restore `content/blog.njk`.

### Implementation decisions and open questions

These are the unresolved public decisions the task file names; approval of the plan should include a choice on each.

1. **Later-page URL pattern** (required for ARCHIVE-1). Recommended: `/blog/2/`, `/blog/3/`, … (`pageNumber + 1`, Eleventy convention). Alternative: `/blog/page/2/`. (`/blog/1/` as the first page would violate ARCHIVE-1.)
2. **Navigation presentation** (required for ARCHIVE-4). Recommended: "Newer posts" / "Older posts" anchors with `rel="prev"`/`rel="next"` in `<nav aria-label="Blog archive pages">`. Alternatives: "Previous"/"Next" wording, or numbered page links.
3. **Sitemap inclusion of new archive pages**. Recommended: accept — the sitemap rule (enumerate all pages) is unchanged and the pages are public. Excluding them would be a new rule and needs explicit approval.

### Documentation

Audience: site README readers. `README.md`'s one-line archive claim gets a minimal accuracy update (bounded 20-post pages, later-page pattern) in the same change as the behavior. No new pages or directories; `docs/development/index.md` is untouched. `documentation.md` guidance was read; no structural documentation change is warranted.

### Task checklist

- [ ] Implement pagination in `content/blog.njk` with approved URL pattern and nav markup
- [ ] Verify real-content build sanity (`/blog/` single page, no nav, sitemap output)
- [ ] Replace `tests/archive-output.test.js` with production-build tests (sandbox >20 posts; real 2-post case)
- [ ] `npm test` and `npm run build` pass cleanly
- [ ] Update `README.md` archive description
- [ ] Record requirement evidence and completion entry in the task file

### Requirement verification

- **ARCHIVE-1** — Real build output contains `_site/blog/index.html`; later pages exist at the approved pattern (`_site/blog/2/index.html`, …).
- **ARCHIVE-2** — In the >20-post sandbox build, each archive page's list contains ≤ 20 post links (pages sized 20/20/remainder).
- **ARCHIVE-3** — Union of post links across all archive pages equals the full post set with no duplicates; each page lists posts newest-first by date.
- **ARCHIVE-4** — First page has only "Older", last page only "Newer", middle pages both; every nav href resolves to an existing page. Real 2-post build renders no nav.
- **ARCHIVE-5** — In the sandbox build: home shows only the 3 newest posts; `/tags/posts/` lists all posts; feed contains all posts newest-first; sitemap still enumerates all pages; individual-post links unchanged. Proves the shared include and untouched surfaces kept their behavior.
- **ARCHIVE-6** — Archive pages contain no `<script` elements and are static build output; no new runtime dependencies added.

Deliberately not covered: browser or screen-reader accessibility tooling (accessibility rests on semantic `nav`/labeled links), and pagination is exercised at sandbox post counts (45) rather than production-scale volumes.

### Additional implementation verification

None beyond the above; the sandbox build through the real `eleventy` command already covers the material risk (pagination semantics of the installed version).

---

**Summary for approval**

- **Outcome**: `/blog/` becomes a bounded, paginated archive (≤ 20 posts per page, newest-first, each post exactly once) with prev/next navigation rendered only when the destination exists, all static with zero client-side JS.
- **Scope**: one template (`content/blog.njk`), one test file, one README sentence. The shared include, home, tags, feed, sitemap, and post templates are untouched.
- **Approach/order**: Eleventy native pagination with `reverse: true` and a compensating reverse into the existing include; implement → real-build sanity check → production-build tests → docs → task-file bookkeeping. Every prefix of that order is a safe stopping point.
- **Material decisions awaiting you**: (1) later-page URL pattern — recommended `/blog/2/`; (2) nav presentation — recommended "Newer posts"/"Older posts" with `rel` attributes in a labeled `<nav>`; (3) whether new archive pages may appear in the sitemap — recommended yes.
- **Acceptance evidence**: real production builds (sandbox with ~45 posts and the real 2-post content) asserting page bounds, global uniqueness/order, nav presence rules, and preservation of home/tag/feed/sitemap behavior.
- **Risks/way back**: ordering semantics of `pagination.reverse` (caught by assertions; fallback via `pagination.before`); revert is a one-file template restore. Note the sitemap will grow to include new archive pages under the unchanged enumeration rule.
- **Exclusions**: no accessibility-tooling runs, no production-scale data tests, no new dependencies.

Execution has **not** started and nothing has been written to the task file, per your instruction. Tell me your choices on the three decisions (or accept the recommendations), and confirm whether on approval I should write the plan into `tasks/20260919-tg01-eleventy-archive-handoff.md` and begin execution — execution waits until then.
