# Migrate Post Author Metadata

Plan a staged migration from the current single-name post `author` field to structured multi-author metadata while preserving existing content and generated output until the migration is proven complete.

## Requirements checklist

- [ ] Posts support structured metadata for multiple authors.
- [ ] Existing content and generated pages remain compatible during the transition.
- [ ] Templates, archives, feeds, and authoring tools use the new model.
- [ ] Existing posts are migrated safely.
- [ ] The legacy form is rejected only after generated-output and content evidence shows nothing depends on it.

## Scope

The migration includes post pages, shared post lists and archive/tag pages, the feed, post front matter, `scripts/new-post.js`, build-time validation, and maintained authoring guidance. It does not change unrelated site content or metadata.

## Unresolved questions

- What exact front matter key and record shape define the structured author model (for example, an `authors` list of objects with a display name, optionally accompanied by stable identity fields)?
- What author representation must generated post pages, archive entries, and feed entries expose, and what legacy output details must remain byte-for-byte or semantically stable during transition?
- Should the new-post helper accept one or multiple authors, and what interface should its caller use?

## Supporting details

- Verified current uses: `author` appears in the post layout, feed, post front matter, new-post helper, and author-output test stub. The shared post-list include renders titles and links; blog and tag archives use it.
- Verified production path: Eleventy reads `content`, uses `_includes`, and writes `_site`; `package.json` exposes `npm run build` and `npm test`.
- Existing author-output and archive-output tests are placeholders, not passing evidence of generated behavior.
- No task directory existed at planning time.

## Execution plan
Status: Draft

### Design and sequencing

Use an additive compatibility stage before changing source data. Rendering and feed code should consume the structured model while continuing to render legacy-only posts with equivalent existing output. Once that compatibility path is exercised through a real Eleventy build, migrate the post-authoring helper and all existing post records, then update maintained authoring guidance. Retire the legacy form only in a final stage that verifies all source content uses the new model, checks the generated production output, and makes build validation reject the old form.

Do not settle the public author schema, helper signature, or output representation without answering the open questions above. Keep the legacy-to-new adaptation in the production data/rendering path rather than hiding it in test-only helpers. The decisive integration evidence must build mixed legacy and structured posts through Eleventy and inspect post pages, the blog archive, tag archives, and feed; final retirement evidence must inspect the complete content set and generated output before exercising rejection of a legacy record.

### Ordered work

1. Add structured-author consumption with a compatibility path for legacy-only posts; update post page, shared archive rendering as required by the approved output, and feed.
2. Add generated-output regression coverage through the Eleventy production build for both metadata forms and for all affected page/feed surfaces.
3. Update the new-post tool and migrate every existing post; verify generated or authored front matter matches the approved schema and retains all existing author names.
4. Update `README.md` with the supported authoring form in the same change that makes it current.
5. Audit all source content and the production build output for legacy dependencies; only then add validation that rejects legacy metadata and test its failure on a legacy fixture.
6. Run the focused production-build and test checks, then the full available test suite.

### Implementation decisions and open questions

- Schema, author identity fields, helper input interface, and generated author presentation remain open requirement questions; obtain answers before marking this plan Approved.
- Local implementation details such as where to place the adapter can be resolved during execution, provided the production compatibility boundary remains intact.
- Retirement is a gated later step, not an unconditional cleanup: if source or generated-output evidence still depends on the legacy form, preserve compatibility and leave rejection incomplete.

### Documentation

Update `README.md` for current post-authoring guidance after the structured format is implemented. Do not create a standalone specification or placeholder documentation page for this compact site.

### Task checklist

- [ ] [Add transitional rendering and generated-output coverage](tasks/20261029-post-author-migration/010-transitional-rendering.md)
- [ ] [Migrate authoring tool and existing posts](tasks/20261029-post-author-migration/020-authoring-content-migration.md)
- [ ] [Retire legacy metadata after evidence](tasks/20261029-post-author-migration/030-legacy-retirement.md)

### Requirement verification

- Structured multiple-author support: build structured-author posts through the production Eleventy build and inspect rendered post and listing/archive output, after the model and presentation questions are answered.
- Transition compatibility: build a corpus containing legacy-only and structured-author posts; assert existing legacy author presentation remains in post pages, relevant archives, and feed, while structured values appear on the same surfaces.
- Templates, archives, feeds, and tools use the new model: exercise generated post front matter from the actual authoring helper and confirm via the production build that its authors render through post pages, blog/tag archives, and feed.
- Safe migration of existing posts: inspect the complete `content/posts` set for the approved structure and build it; assert all former author names remain represented.
- Evidence-gated rejection: retain source-content and generated-output audit results showing no legacy dependency, then build a deliberately legacy-form post and verify the production validation rejects it. Do not claim completion based only on a schema/unit test.

### Additional implementation verification

Run `npm test` and `npm run build` after focused production-output checks; report each command’s actual result.