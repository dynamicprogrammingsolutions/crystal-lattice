# Session — tg01-eleventy-archive-handoff · generated-plan · glm max

- Run: `20261029T182857.175389Z-task-guidance-generated-tg01-eleventy-archive-handoff-max-da3a3fda`
- Model: glm-5.3-flash (effort max)
- Delivered instructions: [glm-max](../../../../../shared/system-messages/glm-b2ee1cb55f52.md) — captured (original SHA-256 `a095f8255566836b…`)
- Config: [glm-max](../../../../../shared/configs/glm-max.json)
- Activity: 18 messages · 11 tool calls · 11 tool results
- Usage: 0 input · 0 cached · 0 output · provider cost $0.0000000

## Transcript

**User**

Read the task files and present the Draft implementation plan. Do not modify files or implement the task.

**Assistant** *(reasoning present)*

I'll locate the task files in the workspace.

- `Glob` {"pattern": "tasks/**/*.md"}
- `Bash` {"command": "ls -la \"<workspace>\"", "description": "List files in workspace root"}

**Tool `Glob`** — *(result omitted)*

**Tool `Bash`** — *(result omitted)*

**Assistant**

- `Read` {"file_path": "<workspace>/tasks/20261029-blog-archive-pagination.md"}
- `Read` {"file_path": "<workspace>/AGENTS.md"}

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Assistant** *(reasoning present)*

The task file contains a complete Draft plan. Before presenting it, let me verify the supporting facts still hold against the repository state.

- `Read` {"file_path": "<workspace>/content/blog.njk"}
- `Read` {"file_path": "<workspace>/_includes/postslist.njk"}
- `Read` {"file_path": "<workspace>/tests/archive-output.test.js"}
- `Read` {"file_path": "<workspace>/README.md"}

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Assistant** *(reasoning present)*

- `Bash` {"command": "ls -R \"<workspace>/content\" \"<workspace>/docs\"", "description": "List content and docs directory trees"}
- `Read` {"file_path": "<workspace>/docs/development/index.md"}
- `Read` {"file_path": "<workspace>/package.json"}

**Tool `Bash`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Assistant** *(reasoning present)*

All supporting facts in the task file verify against the current repository state (F1–F2, F5–F7, F9, F11 all accurate; the fixture has 2 posts, no `node_modules`, and the archive test is still a stub). The stored Draft plan is current. Here it is:

---

## Draft plan: Blog archive pagination

**Task file:** `tasks/20261029-blog-archive-pagination.md` (Status: **Draft** — execution waits for approval)

### Outcome

Split the `/blog/` archive into stable pages of at most 20 posts each with accessible previous/next navigation, while preserving every other generated surface (home, tags, feed, sitemap, individual posts), post order, and the static zero-JavaScript output.

### Approach

`content/blog.njk` becomes an Eleventy-paginated template and stays the single source of the archive:

- **Pagination:** over `collections.posts` with `size: 20`, `reverse: true` (whole dataset reversed before chunking, so page 1 holds the newest posts), `alias: postslist`.
- **URLs (D1):** `/blog/` for page 1 via a conditional `permalink`; `/blog/<n>/` (`/blog/2/`, `/blog/3/`, …) for later pages. Eleventy only emits later pages when posts exceed 20, so the 2-post fixture keeps a single page and `/blog/1/` is never duplicated.
- **Rendering:** the body renders the chunk directly instead of including `_includes/postslist.njk`, avoiding the double-reverse bug (the shared include already applies `| reverse` and is used by home and tag pages — those stay untouched).
- **Navigation:** a labelled `nav` landmark (`aria-label="Blog pages"`) below the list with real links only — `rel="prev"` "Newer posts" and `rel="next"` "Older posts" — plus a "Page N of M" indicator (D2). Links are omitted, never rendered disabled; no JavaScript.
- **Heading:** `Archive` on page 1, `Archive, page N` on later pages.

Nothing else changes; the sitemap picks up new archive pages automatically via `collections.all` (an accepted, documented consequence).

### Verification

Integration coverage through the real production build in `tests/archive-output.test.js` (currently an empty stub):

1. **Temp workspace with >20 generated posts** (real `eleventy.config.js`, real `_includes`): page count `ceil(n/20)`, ≤20 posts per page, `/blog/` is page 1, later pages exist, `/blog/1/` not generated, union of pages = all posts exactly once in newest-to-oldest order, correct prev/next hrefs/rel/accessible names on interior pages, first and last page lack the boundary links, and no `<script` in any emitted archive page.
2. **Committed-content build:** single archive page, no `/blog/2/`, no pagination links; home (latest 3), tag pages, feed (all posts), sitemap, and both post pages emitted unchanged.

### Documentation (same change)

- `README.md` — update the archive sentence to name the paginated archive.
- `docs/development/archive-pagination.md` (new) — concise maintainer-facing spec: URL shape, 20-post cap, order, accessible nav, sitemap note.
- `docs/development/index.md` — replace "No archive pagination specification exists." with a link to the new spec.

### Material decisions / open questions needing your answer at approval

| # | Question | Recommendation |
|---|----------|----------------|
| **D1** (material) | URL format for later archive pages | `/blog/<n>/` (e.g. `/blog/2/`) — alternative `/blog/page/2/` |
| **D2** (minor) | Nav wording | "Newer posts" / "Older posts" + "Page N of M" indicator |
| **A1** (assumption) | "Stable" = deterministic position-based URLs (new posts shift which posts sit on which page) | Accepted unless content-stable (e.g. date-based) URLs were intended — that would be a materially larger design |

### Risks / notes

- `node_modules/` is not installed here; the executor runs `npm install` before `npm test` / `npm run build`.
- Eleventy 3's pagination `reverse` semantics (dataset reversed before chunking) will be confirmed during implementation; the test order assertions pin the behavior either way.
- Small duplication of list markup in `blog.njk` is accepted to avoid changing shared-include semantics used by home and tag pages.

### Exclusions

No changes to home, tag pages, feed, sitemap template, or individual post layout; no content additions; no client-side JavaScript.

---

The plan remains stored as `Draft` in the task file — I have not modified any files. Reply with your decisions on **D1**, **D2**, and confirmation of **A1** (or simply "approved as recommended"), and execution can begin after the plan is marked `Approved`.
