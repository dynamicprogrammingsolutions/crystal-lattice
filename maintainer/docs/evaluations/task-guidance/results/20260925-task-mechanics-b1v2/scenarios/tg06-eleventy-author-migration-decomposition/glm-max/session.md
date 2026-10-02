# Session — tg06-eleventy-author-migration-decomposition · task-creation · glm max

- Run: `20260925T202507.497578Z-task-guidance-tg06-eleventy-author-migration-decomposition-max-a4fd26ce`
- Model: glm-5.3-flash:cloud (effort max)
- Tools: claude_bash_tool, claude_read_tool, claude_task_stop_tool, claude_write_tool, claude_edit_tool, claude_glob_tool, claude_grep_tool, claude_web_fetch_tool, claude_web_search_tool, claude_mcp_tool
- Delivered instructions: [glm-max](../../../shared/system-messages/glm-a7bfadce849d.md) — captured (original SHA-256 `322b89bf639f9f49…`)
- Config: [glm-max](../../../shared/configs/glm-max.json)
- Activity: 46 messages · 30 tool calls · 30 tool results
- Usage: unknown — saved session contains no provider usage metadata

## Transcript

**User**

Migrate post author metadata from the current single-name field to a structured multi-author form without breaking existing content or generated pages during the transition. Templates, archives, feeds, and authoring tools must move to the new model, existing posts must be migrated safely, and the legacy form may be rejected only after generated-output and content evidence show that nothing still depends on it. Plan the work and create the appropriate task structure without implementing it.

**Assistant** *(reasoning present)*

I'll start by exploring the repository structure and understanding the current author metadata model.

- `Bash` {"command": "ls -la <workspace>", "description": "List workspace root contents"}
- `Glob` {"pattern": "**/*.{js,json,toml,yaml,yml,md}"}

**Tool `Bash`** — *(result omitted)*

**Tool `Glob`** — *(result omitted)*

**Assistant**

- `Read` {"file_path": "<workspace>/AGENTS.md"}
- `Read` {"file_path": "<workspace>/README.md"}
- `Read` {"file_path": "<workspace>/package.json"}
- `Read` {"file_path": "<workspace>/eleventy.config.js"}

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Assistant**

- `Read` {"file_path": "<workspace>/content/posts/first.md"}
- `Read` {"file_path": "<workspace>/content/posts/second.md"}
- `Read` {"file_path": "<workspace>/content/posts/posts.json"}
- `Read` {"file_path": "<workspace>/scripts/new-post.js"}

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Assistant**

- `Bash` {"command": "ls -R <workspace>/_includes <workspace>/content <workspace>/tests <workspace>/docs <workspace>/scripts", "description": "List all subdirectories re…

**Tool `Bash`** — *(result omitted)*

**Assistant**

- `Read` {"file_path": "<workspace>/_includes/layouts/post.njk"}
- `Read` {"file_path": "<workspace>/_includes/postslist.njk"}
- `Read` {"file_path": "<workspace>/content/blog.njk"}
- `Read` {"file_path": "<workspace>/content/feed.xml.njk"}

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Assistant**

- `Read` {"file_path": "<workspace>/content/index.njk"}
- `Read` {"file_path": "<workspace>/content/tag-pages.njk"}
- `Read` {"file_path": "<workspace>/content/sitemap.xml.njk"}
- `Read` {"file_path": "<workspace>/tests/author-output.test.js"}

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Assistant** *(reasoning present)*

- `Read` {"file_path": "<workspace>/tests/archive-output.test.js"}
- `Read` {"file_path": "<workspace>/docs/development/documentation.md"}
- `Read` {"file_path": "<workspace>/docs/development/index.md"}
- `Bash` {"command": "cat .gitignore UPSTREAM.md .guidance-lock.json && git status --short && git log --oneline -5 2>/dev/null | head -20", "description": "Show gitignor…

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Read`** — *(result omitted)*

**Tool `Bash`** — *(result omitted)*

**Assistant** *(reasoning present)*

Now I have the full picture. Let me verify there are no other author-data consumers I might have missed.

- `Grep` {"-i": true, "-n": true, "output_mode": "content", "pattern": "author"}
- `Bash` {"command": "ls node_modules 2>/dev/null | head -3; echo \"---\"; ls _site 2>/dev/null | head -5", "description": "Check for node_modules and built output"}

**Tool `Grep`** — *(result omitted)*

**Tool `Bash`** — *(result omitted)*

**Assistant** *(reasoning present)*

The inventory is complete and confirmed. The current single-name model touches exactly: front matter (2 posts), two templates (post layout byline, feed entries), one authoring tool, and two stub test files with no assertions. Archives/tags/home/sitemap don't render author data. Now I'll create the task structure.

- `Bash` {"command": "mkdir -p tasks/20260925-author-metadata-migration", "description": "Create task directory"}

**Tool `Bash`** — *(result omitted)*

**Assistant**

- `Write` {"content": "# Migrate post author metadata to a structured multi-author model\n\nStaged migration of the single-name `author` front-matter field to a structure…

**Tool `Write`** — *(result omitted)*

**Assistant**

- `Write` {"content": "# 010 — Multi-author model with legacy-compatible rendering\n\nAdd the canonical structured `authors` model and its normalizer, move the\npost-layo…

**Tool `Write`** — *(result omitted)*

**Assistant**

- `Write` {"content": "# 020 — Authoring-tool and content migration, legacy-dependency evidence gate\n\nMove every producer to the new model — the authoring tool and both…

**Tool `Write`** — *(result omitted)*

**Assistant**

- `Write` {"content": "# 030 — Reject the legacy single-author form (evidence-gated)\n\nRemove support for the legacy single-name `author` field so the production\nbuild …

**Tool `Write`** — *(result omitted)*

**Assistant** *(reasoning present)*

Task structure created under `tasks/20260925-author-metadata-migration/` — no code touched. Here's the plan for review.

**Outcome.** Posts support a structured multi-author `authors` list; byline and feed render all authors through it; `scripts/new-post.js` and both existing posts move to the new form; the legacy `author` string is rejected at build time only after recorded evidence proves nothing depends on it.

**Approach — three gated stages**, each leaving the build green and public output stable:

1. **010 — Model + rendering** (`010-multi-author-model.md`): canonical normalizer that is the *only* code reading the raw `author` key; post layout and feed consume only canonical `authors`; legacy form stays accepted and byte-identical. Adds the missing real coverage: production-build integration tests (the two existing test files are comment-only stubs).
2. **020 — Producers + evidence gate** (`020-authoring-and-content-migration.md`): migrate the authoring tool and both posts, then record the evidence bundle — repo-wide scan for legacy readers/usage plus a before/after build diff of post pages and feed.
3. **030 — Gated rejection** (`030-legacy-rejection.md`): normalizer throws on legacy input → build failure; blocked until 020's evidence is recorded, and abandoned with a report if evidence shows a straggler.

**Material decisions needing your approval** (execution waits on these):
- **Q1 — `authors` item shape** (data + feed contract): plain name strings vs. objects with required `name`. Recommendation: objects with `name`.
- **Q2 — scope**: no new per-author archive/profile pages; "archives" is continuity of existing archive output (they render no author data today — verified).
- Minor: multi-author byline join format (recommendation: comma-joined), and no new missing-author validation.

**Evidence at the public boundary**: integration tests drive the real Eleventy build and assert generated HTML/XML — byline and feed entries for multi-author and legacy posts, archive/tag/home/sitemap continuity, build-failure on legacy after rejection, plus a unit test for the tooling contract. One key constraint: multi-author rendering can't be proven with a permanent test post (it would change public output), so the test builds a temporary fixture through the same production config/templates.

**Risks**: the exact Eleventy mechanism for the canonical read path (filter vs. computed data) is left to the executor to avoid a self-reference gotcha in computed data; single-author output byte-equality is the regression anchor throughout.

**One flag**: since planning the work was the requested deliverable, I retained the full plan as `Status: Draft` in `000-main.md` rather than a requirements-only handoff — say the word if you'd prefer the plan stripped out. Nothing is approved for execution yet: approve Q1/Q2 and the plan, and 010 can start.
