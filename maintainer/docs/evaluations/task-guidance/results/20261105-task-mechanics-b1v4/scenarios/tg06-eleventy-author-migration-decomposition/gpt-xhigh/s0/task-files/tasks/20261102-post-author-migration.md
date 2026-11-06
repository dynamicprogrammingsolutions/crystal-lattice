# Post Author Metadata Migration

Plan a compatibility-safe migration from the single `author` field to a structured form that supports multiple authors across post content and generated output.

## Requirements checklist

- [ ] Post metadata uses an agreed structured multi-author form, and the authoring tool emits that form.
- [ ] Post templates, archives, and feeds consume the new model and represent authors according to the approved rendering policy.
- [ ] Existing posts are migrated without losing their titles, bodies, or author names; legacy content remains buildable during the transition.
- [ ] Legacy `author` input is not rejected until generated-output and content evidence both show that repository content and output no longer depend on it.

## Scope

Keep this as one end-to-end task. The content schema, authoring tool, templates, archives, feed, and compatibility gate share one contract; separate tasks could leave a partially migrated site that cannot be accepted independently.

## Questions and decisions

- **Requirement question — metadata shape:** Should the canonical field be `authors: [{ name: "Ada Example" }]` or `authors: ["Ada Example"]`? Recommendation: use author objects, which make each author an explicitly structured record and leave room for later author attributes without changing the list shape.
- **Requirement question — archive output:** Should blog, tag, and home archive rows newly display every author, or should they remain title-only while being verified to work with the new metadata? Recommendation: display every author because archives are explicitly in scope.
- **Requirement question — legacy rejection:** After both evidence gates pass, should the build actively reject a legacy `author` field, or merely stop consuming it? Recommendation: reject it so future posts cannot silently regress to the old form.
- **Design decision:** Use a temporary compatibility normalization boundary so old and new post records can coexist while templates move to one canonical author list. Finalize the exact field and rendered markup only after the requirement questions are answered.

## Supporting details

- Two Markdown posts currently contain scalar `author` front matter; both use the same post layout.
- `scripts/new-post.js` emits scalar `author` front matter. No in-repository caller of its exported function was found.
- `_includes/layouts/post.njk` renders the scalar author. The feed emits it once per entry. `_includes/postslist.njk`, used by the blog, tag, and home views, currently renders titles only.
- `tests/author-output.test.js` and `tests/archive-output.test.js` contain comments but no assertions, so they do not currently verify generated output.
- `npm run build` invokes Eleventy and writes `_site`; `npm test` runs Node's test runner. The repository has no `docs/index.md` or authoring guide. `README.md` is the only package-level user documentation.
- The working tree was clean when this plan was drafted.

## Implementation plan

Status: Draft

### Design

Use a canonical plural author field in post front matter, with the precise value shape left open for the requirement decision above. While legacy posts may still exist, normalize both forms at one Eleventy boundary into a canonical iterable list; templates should not each implement their own legacy fallback. Update the post layout, shared listing template, and feed to consume that list. The authoring helper should emit only the approved new form. Convert existing post front matter while preserving all unrelated metadata and Markdown bodies.

During migration, keep the old field readable so mixed old/new content remains buildable. Add actual generated-output coverage for the post layout, archive paths, and feed, including a multi-author record processed by Eleventy with the project's templates. Add content checks over the repository's post front matter and record the evidence before removing compatibility or enabling rejection. The archive's visible author treatment and the final rejection behavior depend on the unresolved requirement decisions.

### Order and milestones

1. Resolve the metadata shape, archive rendering, and legacy rejection decisions. These define the persisted contract and visible output, so no content or template migration should precede them.
2. Add the shared compatibility normalization and move the post layout, archive listing, and feed to the canonical list. Keep old records accepted at this milestone; a build should still handle a mixed corpus.
3. Change the authoring helper to generate the new form and migrate the existing Markdown records, preserving titles, bodies, and names.
4. Add focused tests that exercise generated output through Eleventy and verify all migrated source front matter. Run a production build and inspect/assert post pages, archive output, and feed output before treating the evidence gate as passed.
5. Only after both generated-output and content checks pass, remove legacy handling and, if approved, add legacy-field rejection. Run the full build and tests again with that final policy active.
6. Update the README with the supported front-matter form and authoring contract once the schema and behavior are settled.

The safe stopping point after step 2 is a mixed-format build with old content still accepted. If migration or output checks fail, retain the compatibility path and correct the conversion or rendering before proceeding to the rejection gate.

### Risks and way back

- Front-matter conversion could lose a name or alter unrelated post content. Limit conversion to the author field and verify each migrated record's names, title, and body.
- Nunjucks escaping or multi-author formatting could change visible pages or produce incorrect feed XML. Assert real generated files for all affected output paths, including a multi-author case.
- Removing compatibility too early could break remaining or externally supplied legacy records. Make the source-content check and the generated-output check prerequisites to the removal; if either fails, keep or restore the compatibility boundary.
- The migration changes metadata only, not URLs or post bodies, so reverting the schema, templates, helper, and front matter together restores the prior behavior without data loss.

### Implementation decisions and open questions

The metadata shape, whether archive rows display authors, and whether legacy metadata is actively rejected remain unresolved requirement questions above. Execution must wait for those answers and approval of this plan. The compatibility boundary and staged order are the planned approach; adjust them only if the approved schema requires a different implementation.

### Documentation

Update `README.md` rather than create a new documentation structure. Document the final supported post-author front matter and the authoring helper's contract after the open schema and rendering decisions are resolved. Do not describe the temporary fallback as permanent supported authoring guidance.

### Task checklist

- [ ] Resolve the schema, archive-output, and legacy-rejection questions.
- [ ] Add shared compatibility handling and update every affected template.
- [ ] Update author generation and migrate all existing post metadata.
- [ ] Add generated-output and content evidence for the migration.
- [ ] Remove legacy support or enable rejection only after both evidence gates pass.
- [ ] Update the README and run final build and test checks.

### Requirement verification

- **Structured form and authoring output:** Test the helper's generated front matter and inspect every post's parsed front matter to confirm it uses the approved plural form; exercise a multi-author record through Eleventy to ensure the real templates receive multiple authors.
- **Templates, archives, and feed:** Run the production build and assert the generated post pages, blog/tag/home archive outputs, and feed contain the approved author representation without losing existing single-author names. If archives remain title-only by decision, verify their generated paths and contents still build correctly from posts carrying the new field.
- **Safe content migration and transition:** Check all post front matter for the new form and absence of legacy `author` keys, review that the conversion preserves post titles and bodies, and build a mixed legacy/new corpus before compatibility is removed. This does not establish that unknown external repositories have migrated.
- **Legacy rejection gate:** Require both the generated-output assertions and the complete post-content check to pass before enabling a legacy-field rejection rule. Verify the final production build and test suite with that rule active; if rejection is not approved, verify instead that old metadata is no longer consumed and document the retained policy.

### Additional implementation verification

Run `npm test` and `npm run build` after the final gate change. These are routine quality checks; they supplement but do not replace the generated-output and source-content evidence above.
