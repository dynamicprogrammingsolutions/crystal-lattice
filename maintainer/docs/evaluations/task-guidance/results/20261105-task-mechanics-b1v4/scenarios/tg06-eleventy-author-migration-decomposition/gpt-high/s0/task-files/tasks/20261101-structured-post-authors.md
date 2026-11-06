# Structured post author migration

Move posts from one author-name string to structured multi-author metadata while keeping the production site and existing content working through a staged transition.

## Requirements checklist

- [ ] Posts use a structured author representation capable of identifying multiple authors.
- [ ] Existing post content and generated pages remain supported while content, templates, and authoring tools transition to the new representation.
- [ ] Post templates, archive output, feeds, and authoring tools consume the new author representation without losing existing author information.
- [ ] Existing posts are migrated without changing who is credited.
- [ ] The legacy single-name form is rejected only after repository content and production-generated output provide evidence that nothing still relies on it.

## Questions and decisions

- **Question — schema:** What is the exact structured author shape and required author fields? Recommendation: an ordered list of author records with a required display name; defer any identity, URL, or affiliation fields unless needed.
- **Question — archive presentation:** Should archive entries begin displaying author names, or should archives only be updated and checked for compatibility if they currently render author data? Existing post lists render titles only, so adding visible bylines would be a new user-facing behavior.

## Supporting details

- **Fact:** The Eleventy production build consumes Markdown under `content/posts/`, using `content/posts/posts.json` to apply the post layout and `posts` collection tag.
- **Fact:** Current post metadata is `author: "..."`; the post layout renders it, and the Atom feed copies it into each entry's `<author>` element.
- **Fact:** The shared post list powers the blog archive, home-page listing, and tag pages, but currently renders titles and URLs only.
- **Fact:** `scripts/new-post.js` generates the legacy single-name front matter. `tests/author-output.test.js` and `tests/archive-output.test.js` currently contain comments but no assertions.
- **Fact:** `npm run build` invokes Eleventy, and `npm test` runs Node's test runner over `tests/*.test.js`.
- **Fact:** No authoring guide exists; `README.md` is the only current user-facing site documentation.

## Implementation plan
Status: Draft

Treat this as one end-to-end content migration because the author schema is shared by Markdown, the post layout, the generated feed, the authoring helper, and the archive collection path. Keep a compatibility reader while both metadata forms exist; migrate the authored posts and the generator before making the new representation authoritative. The old form remains accepted during that overlap. After every consumer and source post uses the new form, verify the actual Eleventy build output and scan source content and templates for legacy dependencies. Only then add a rejection guard for legacy metadata and prove it through focused tests. The exact field shape and whether archive bylines become visible remain open until approved.

Execution order is intentional: establish output-level regression coverage and compatibility first; then update consumers and authoring; migrate source content; finally use build and repository evidence as the gate for rejecting the old form. This allows work to stop safely with both forms accepted if migration or generated-output checks expose a problem. The migration's blast radius is limited to post metadata and its presentation; rollback is to restore legacy content/consumer behavior while keeping the tests that reveal regressions.

### Implementation decisions and open questions

- Preserve author ordering and credited names through migration; do not infer identities or add author fields beyond the approved schema.
- Resolve the structured metadata contract before implementation. The recommendation is an ordered list of records with a required display name.
- Resolve whether archive entries gain bylines before implementation; do not silently change visible archive behavior.
- Transitional readers must tolerate both forms until the content and generated-output gate passes. Do not make rejection conditional on a test harness convenience.

### Documentation

- Update `README.md` with the supported author front matter and authoring guidance after the schema is approved and implemented.
- Keep documentation changes in the same implementation change as the behavior they describe; do not document target behavior as already supported during the transition.

### Task checklist

- [ ] Add meaningful generated-output tests that exercise a real Eleventy production build for post bylines and feed author elements, including multiple authors.
- [ ] Implement transitional reading/rendering for legacy and structured metadata across post pages, archive/collection surfaces, and feeds.
- [ ] Update the new-post authoring helper to generate only the approved structured form and test its generated front matter.
- [ ] Migrate all existing posts while preserving their credited names and author ordering.
- [ ] Build the site and inspect generated pages, archives, tags, and feed; scan repository content and consumer code for legacy-form use.
- [ ] Only after those checks pass, reject legacy metadata and add regression coverage for that rejection.
- [ ] Update maintained authoring documentation and run `npm test` and `npm run build`.

### Requirement verification

- **Structured author representation and authoring tools:** Test generated front matter from `scripts/new-post.js` against the approved schema. This does not by itself prove production rendering.
- **Transition compatibility and final post/feed output:** Build with Eleventy using representative legacy and structured posts during transition, then assert the rendered post page and Atom feed preserve each credited author. Do not use mocked template rendering as the decisive check.
- **Archive compatibility:** Assert actual generated blog, home, and tag archive outputs remain valid and render authors if visible archive bylines are approved. The current archive output has no bylines, so absent that approval this check proves no archive regression, not author display.
- **Safe content migration and legacy rejection gate:** Inspect every post's source front matter and assert production-generated output includes all migrated credits; scan the complete content/templates/tooling source for legacy-form dependencies before enabling the rejection test. The scan alone does not prove generated output, and the build alone does not prove no dormant source dependency remains.
- **Documentation:** Review the maintained authoring guidance against the implemented schema and generator behavior.

### Additional implementation verification

- Run `npm test` and `npm run build` after the focused migration checks to catch unrelated production-surface regressions; these checks do not replace the generated-output and source-content gate above.