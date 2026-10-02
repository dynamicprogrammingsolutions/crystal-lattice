# 030 — Reject the legacy single-author form (evidence-gated)

Remove support for the legacy single-name `author` field so the production
build fails on content using it. May execute only after 020's recorded evidence
shows no remaining dependency on the legacy form in content, templates,
scripts, or tests.

Parent Task: tasks/20260925-author-metadata-migration/000-main.md

Depends On: tasks/20260925-author-metadata-migration/020-authoring-and-content-migration.md

## Requirements checklist

- [ ] R7 — Legacy form rejected at build time, executed only after 020's
  recorded evidence; rejection is abandoned with a report if the evidence shows
  a straggler.
- [ ] R8 — README transitional note removed; rejection behavior and migration
  path documented.
- [ ] R2 (retired) — Post-rejection state is fully on the new model; the
  transitional compatibility branch is gone.

## Task checklist

- [ ] Confirm 020's evidence is recorded and clean; if missing or showing a
  straggler, stop and report instead of proceeding
- [ ] Make the canonical normalizer reject the legacy `author` key with an
  actionable error that fails the production build
- [ ] Update 010's legacy-compat test to assert rejection (replaces the
  transitional coverage)
- [ ] README: remove the transitional note; document the rejection error and
  the migration path from legacy content
- [ ] Full build and tests green; verify all generated pages present (home,
  archive, tag pages, feed, sitemap, both post pages)

## Verification

Decisive: test asserting the production build fails on legacy-form content with
the documented error, plus a final green full build with all generated pages
present through the real pipeline.