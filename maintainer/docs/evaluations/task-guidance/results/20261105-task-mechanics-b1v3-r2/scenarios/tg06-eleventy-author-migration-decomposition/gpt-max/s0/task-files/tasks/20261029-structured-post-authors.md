# Migrate Posts to Structured Authors

Replace the single-name post author field with a structured multi-author model while keeping existing content and generated pages working through the migration.

## Requirements checklist

- [ ] Posts support the approved structured representation of one or more authors.
- [ ] Existing posts and generated public pages remain compatible while content and consumers transition.
- [ ] Templates, archive output, feeds, and the new-post authoring tool consume the structured model.
- [ ] Existing post content is migrated without losing author information.
- [ ] The legacy author form is rejected only after generated-output and content evidence confirms no supported path still depends on it.

## Unresolved questions

- What exact structured author schema is required (for example, strings in an `authors` list versus objects with name and optional metadata)?
- What public output should represent multiple authors in post pages, archives, and feed entries, and in what order/format?

## Supporting details

- **Fact:** `content/posts/first.md` and `content/posts/second.md` currently use a single `author` string.
- **Fact:** `_includes/layouts/post.njk` renders `author`; `content/feed.xml.njk` emits `post.data.author`. The shared archive list currently renders titles only.
- **Fact:** `scripts/new-post.js` generates the legacy front matter.
- **Fact:** The test files are currently comment-only; `tests/author-output.test.js` describes generated-output coverage but contains no executable assertions.
- **Fact:** `package.json` provides `npm run build` and `npm test`; `eleventy.config.js` uses the production content tree and writes `_site`.
- **Constraint:** Keep migration evidence with this capability; test through the actual production build/output path, not only template mocks.
- **Assumption:** Preserve all names from existing content and avoid changing unrelated page content or URLs.

## Execution plan

Status: Draft

### Design

Treat this as one end-to-end migration because source front matter, authoring, templates, and generated output jointly define the author contract and do not have independent acceptance boundaries in this compact site. First settle the structured schema and public rendering contract. Then add temporary compatibility so legacy content and new structured content both produce correct pages while the content and authoring tool move. Migrate the existing posts, verify the rendered post pages, archive surfaces, and feed from a production build, and only then remove legacy handling and enforce the structured form. The legacy rejection gate must use both a content-tree check and generated-output evidence; a unit-level check alone is not sufficient.

### Ordered steps

1. Resolve and record the structured schema and output conventions before implementation.
2. Add dual-form handling to relevant templates and authoring paths so old and new content can coexist.
3. Migrate existing posts and update the new-post tool to emit the approved structured form.
4. Add production-build assertions for post pages, archive output where authors are displayed, and feed entries; verify both legacy and structured fixtures during the transition.
5. Inspect all supported content for legacy fields and generated output for remaining legacy-dependent results.
6. Remove legacy support and add a guard that rejects the old form only after those checks pass.
7. Run the focused author-output tests, full test suite, and production build; update maintained user/developer guidance for the supported format.

### Implementation decisions and open questions

- Schema and public author formatting are unresolved requirement questions above; do not encode a guessed schema or output contract before approval.
- Keep the transition tolerant until migrated-content and generated-output evidence supports the final rejection gate.
- Do not split authoring, content, templates, tests, or documentation into separate tasks: each only completes this shared migration.

### Documentation

- Update the maintained project guidance (likely `README.md`, subject to audience fit) to describe the approved current authoring format and transition completion.
- Do not publish target-only behavior as current guidance before implementation; if guidance is added earlier, mark it as not implemented.

### Task checklist

- [ ] Confirm structured schema and rendered author conventions.
- [ ] Implement and verify temporary compatibility.
- [ ] Migrate existing post front matter and authoring tool.
- [ ] Verify generated pages, archive surfaces, and feed through production build.
- [ ] Establish content and output evidence before rejecting legacy form.
- [ ] Remove legacy support, run checks, and update guidance.

### Requirement verification

- Structured author support and authoring tool: exercise the new-post generator and build generated posts using the approved structured form; verify rendered names and ordering in production output.
- Transition compatibility: build with both legacy and structured post fixtures and assert expected author output on post pages and feed before removing compatibility.
- Content migration: inspect every post under `content/posts` for retained legacy-only metadata and verify migrated names against rendered output.
- Archive behavior: assert author output in every archive surface where the approved design displays authors; the current shared archive list only shows titles, so preserve that behavior unless the resolved output contract says otherwise.
- Legacy rejection: run the production build and content scan after migration, then verify a legacy-only post is rejected by the supported validation path. The gate must not be enabled until the content and generated-output checks pass.

### Additional implementation verification

- Run `npm test` and `npm run build` after focused production-output assertions pass.
- Confirm generated output has no missing or malformed author fields and no unintended URL/content changes.