# 020 — Authoring-tool and content migration, legacy-dependency evidence gate

Move every producer to the new model — the authoring tool and both existing
posts — then record the generated-output and content evidence that shows
nothing still depends on the legacy form. This evidence is the gate that
authorizes 030. The legacy form remains accepted (but unused) at the end of
this stage.

Parent Task: tasks/20260925-author-metadata-migration/000-main.md

Depends On: tasks/20260925-author-metadata-migration/010-multi-author-model.md

## Requirements checklist

- [ ] R5 — `scripts/new-post.js` emits the structured form only.
- [ ] R6 — `content/posts/first.md` and `content/posts/second.md` migrated to
  the structured form.
- [ ] R7 (prerequisite) — Recorded evidence shows no remaining dependency on
  the legacy form in content, templates, scripts, or tests.
- [ ] R2 (still holds) — Legacy form remains accepted at the end of this stage.
- [ ] R4 — Generated output for home, archive, tags, sitemap, and the two post
  pages/feed is unchanged after migration.

## Task checklist

- [ ] Rewrite `scripts/new-post.js` `frontMatter(title, authors)` to emit the
  structured form; add unit test for the emitted front-matter contract
- [ ] Migrate `content/posts/first.md` and `second.md` front matter to `authors`
- [ ] Repo-wide scan: no template, script, or test reads the raw `author` key,
  and no content uses it (test-only legacy fixtures from 010 excluded — they
  are intentional transitional coverage until 030)
- [ ] Capture pre-migration baseline of the two post pages and the feed;
  rebuild; diff per page and feed against the baseline
- [ ] Record the evidence bundle in `## Implementation Notes` (scan summary +
  diff result) — the gate for 030
- [ ] Full `npm test` and `npm run build` green

## Verification

Decisive: build diff of the migrated posts' generated pages and feed against
the pre-migration baseline (byte-identical), plus the content scan. Supporting:
unit test of the tooling's emitted front matter; full build/test run.