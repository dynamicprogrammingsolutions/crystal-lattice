# Migrate existing posts and update the authoring tool

Convert all existing post sources to the canonical multi-author front matter
and update `scripts/new-post.js` so new posts are authored in that model. This
task owns the source-content inventory and the authoring-helper-to-production
path.

Parent Task: tasks/20260926-author-metadata-migration/000-main.md
Depends On: tasks/20260926-author-metadata-migration/010-schema-compatibility.md

## Requirements checklist

- [ ] Migrate every existing post under the content input to the canonical
  author field without losing names or their order.
- [ ] Update the authoring helper API and serialization to emit the canonical
  single- and multi-author forms safely.
- [ ] Ensure generated front matter does not reintroduce the legacy `author`
  key.
- [ ] Prove that front matter emitted by the authoring helper can enter the
  real Eleventy content pipeline and produce correct post and feed output.
- [ ] Record a source-content inventory and clean scan that the retirement
  task can use as evidence.

## Requirement questions and decisions

- **Question:** Confirm the authoring helper’s final input API once the
  canonical entry shape is approved (an array, records, or another explicit
  collection interface).
- **Question:** Confirm whether a one-author convenience input remains
  supported by the helper while always serializing the canonical collection.
- **Recommendation:** Keep the helper’s output deterministic and use a real
  YAML serializer or equivalent escaping strategy rather than interpolating
  unescaped names into front matter.

## Research and supporting facts

- `content/posts/first.md` and `content/posts/second.md` are the current
  source posts and both use scalar `author` front matter.
- `scripts/new-post.js` exports `frontMatter(title, author)` and directly
  interpolates both values into YAML.
- There is no current executable test proving the helper output is valid
  front matter or that it reaches a built page.
- The build consumes `content/` directly, so a generated fixture can exercise
  the helper and production Eleventy path without mocking page data.

## Execution plan
Status: Draft

Inventory all post source files before editing and record each legacy value and
its intended order. Apply the canonical field to every existing post, review
the diff for title/body/tag/permalink changes, and run a source scan that
targets front-matter keys rather than incidental prose mentions.

Update `frontMatter` to accept the approved author collection and serialize it
as valid, escaped front matter. Cover both the convenience single-author case
and multiple authors if the API decision permits the convenience form. Keep
the function’s output free of the legacy key so newly authored content cannot
extend the transition accidentally.

For the decisive integration check, invoke the helper to create front matter
for a temporary or dedicated test post, place that post through the same
Eleventy input pipeline used by production, run the real build, and assert the
post and feed output. Clean up temporary/generated fixtures according to the
test harness so `_site/` and the committed content set remain controlled.

### Implementation decisions and open questions

- The helper API depends on the canonical author entry shape from subtask 010.
- The migration should preserve source order and values; it should not
  normalize names by sorting or rewriting them without approval.
- Whether a committed fixture or an isolated integration fixture is best can
  be decided locally, provided the check crosses the real content/build
  boundary.

### Documentation

Update the maintained development authoring guidance with the canonical
front-matter example, helper input contract, and one/many-author examples.
State the transition fallback or final rejection only after the retirement
gate establishes that state.

### Task checklist

- [ ] Inventory every post source and capture legacy values/order.
- [ ] Resolve the helper API and serialization decisions.
- [ ] Migrate all existing post front matter.
- [ ] Update helper coverage for valid singleton and multi-author output.
- [ ] Run the helper-to-Eleventy integration check and inspect post/feed
  output.
- [ ] Run the clean content scan and hand its evidence to the retirement
  task.

### Requirement verification

- Scan the complete content input for legacy front-matter keys and confirm
  every post has the canonical field with the expected names/order.
- Invoke the authoring helper, use its emitted front matter as real Eleventy
  input, run the production build, and assert the resulting post and feed.
  This is the decisive check for the authoring tool.
- Verify special characters and multiple names remain valid and intact after
  serialization and rendering.

### Additional implementation verification

- Review the migration diff for accidental changes to title, body, tags,
  permalink, or layout data.
- Check that helper output cannot create malformed YAML from quotes, colons,
  or newline characters.
- Check that temporary integration content cannot be mistaken for committed
  production content.