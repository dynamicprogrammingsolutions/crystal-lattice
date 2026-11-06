# Migrate Post Author Metadata

Safely move post author metadata from one legacy name to a structured form that supports multiple authors, preserving generated output during transition.

## Requirements checklist

- [ ] Posts support the approved structured multi-author metadata form.
- [ ] Existing post metadata is migrated without losing author names.
- [ ] Templates, archives, feeds, and post-authoring tools consume the new form while preserving intended generated author information.
- [ ] Legacy metadata is rejected only after repository content and production-generated output provide evidence that no dependency remains.

## Questions and decisions

- **Question — schema:** What is the structured author contract (for example, an ordered `authors` array of objects containing `name`, with any additional identity fields)? Recommendation: use an ordered array so multiple authors and their display order are explicit; settle object fields before implementation.
- **Question — output:** Should the public post byline and feed expose names only, or should the schema’s additional identity fields appear in generated output? Existing output uses a name on post pages and feed entries.
- **Decision needed — transition behavior:** Preserve legacy input as a compatibility fallback while migrating consumers, then reject it only after source and production-output checks pass. Confirm the intended enforcement boundary for rejection (authoring tool/schema validation versus build-time validation).

## Supporting details

- **Fact:** `content/posts/first.md` and `content/posts/second.md` currently provide one `author` string each.
- **Fact:** `_includes/layouts/post.njk` renders the `author` value; `content/feed.xml.njk` emits it in feed entries.
- **Fact:** `content/blog.njk` and `content/index.njk` share `_includes/postslist.njk`; that list currently renders titles and links, not author names.
- **Fact:** `scripts/new-post.js` generates front matter with a single `author` string.
- **Fact:** `tests/author-output.test.js` and `tests/archive-output.test.js` currently contain comments only; neither provides generated-output assertions.
- **Fact:** The production build is `npm run build`, and tests run through `npm test`.
- **Fact:** `README.md` is the only root-level user-facing project guide; there is no `docs/index.md`.

## Implementation plan

Status: Draft

Keep the migration as one end-to-end task: the metadata contract is shared by content, Eleventy templates, the feed, and the post-creation helper, so splitting these into independently executable children would permit incompatible intermediate states. The content moves to the approved structured contract, while templates and the feed adapt to that contract and the authoring helper generates it. During the transition, preserve legacy reads so old content can still build; only tighten validation after all source posts use the new form and a real production build demonstrates the intended generated author data.

Generated pages and feeds are the decisive compatibility boundary. Add build-backed assertions covering post bylines and feed entries, and check archive/index output for preservation of existing archive behavior and any approved author display. Inspect every generated output for stale/missing legacy author data before enabling rejection. Do not infer archive byline requirements: current archive lists show titles only, so archive author display depends on the schema/output decision above.

Sequence the work so the contract is decided first, then migration and consumer changes land together with build-backed regression coverage, and legacy rejection is last. This order avoids breaking production builds midway through content migration and makes the removal gate evidence-based. The blast radius is limited to post metadata, generated author rendering, feed entries, and authoring output. The way back is to restore the legacy compatibility read and revert the content migration together; do not reject legacy input before rollback is no longer needed.

### Implementation decisions and open questions

Resolve the author object fields, the public rendering of those fields, archive author display expectations, and the legacy-rejection enforcement boundary before execution. Keep authors ordered and support multiple entries; avoid adding identity fields or public output not approved by the user.

### Documentation

Update `README.md` only if its authoring guidance is expanded or the supported content contract changes what authors must do. Keep migration-only/internal transition details in this task rather than introducing a standalone documentation page.

### Task checklist

- [ ] Agree the structured author contract and output behavior.
- [ ] Add or update production-build coverage for post, archive, and feed output.
- [ ] Migrate existing posts and update templates and authoring output.
- [ ] Build and inspect generated author output for legacy dependencies.
- [ ] Reject legacy metadata after the evidence gate passes.
- [ ] Update maintained authoring guidance if applicable.

### Requirement verification

- Structured metadata and migrated content: inspect all post front matter and run the production build with build-backed checks confirming each author name is retained and multiple author entries render in approved order. This does not establish authoring-tool ergonomics by itself.
- Templates, archives, feeds, and authoring tools: invoke `scripts/new-post.js` in its focused test and run `npm run build`; assert post bylines and feed authors, and verify archive/index output against the approved display contract. This does not cover external consumers of the feed.
- Legacy rejection gate: with legacy compatibility still available, inspect repository post front matter and built `_site` output for legacy-only reads or missing author data; only then run the gated build validation that rejects legacy input. This deliberately does not claim compatibility with untracked external content.

### Additional implementation verification

Run `npm test` and `npm run build` after the focused checks. If a realistic legacy fixture is needed to verify the compatibility interval, keep it test-scoped and ensure the final rejection check separately demonstrates the configured failure for legacy metadata.