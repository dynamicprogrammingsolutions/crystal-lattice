# TG-01: Eleventy archive pagination as one task

## Project

- Repository: Eleventy Base Blog
- Revision: `26b26106d7fbb30b7b40d9ef52589d10ddbcb462`
- Kind: public static website
- Existing semantic target:
  `documentation_standard/targets/33-eleventy-archive-pagination.json`

## Purpose

Verify that a cohesive, cross-template static-site change remains one task and
that an approved plan survives task creation and fresh-agent continuation.

## Natural request

> The blog archive has become difficult to browse as the number of posts
> grows. Keep `/blog/` as the first archive page, generate stable later pages
> with at most twenty posts each, and add accessible previous/next navigation.
> Preserve the home page, tags, feed, sitemap, individual-post navigation, post
> order, and static zero-JavaScript output. Plan the change and create the
> appropriate task structure, but do not implement it.

The prompt does not prescribe requirement rows, filenames, test cases, or task
decomposition.

## Approved outcomes

Use `ARCHIVE-1`–`ARCHIVE-7` from the existing target. The later-page URL
pattern and exact navigation presentation remain material decisions unless
separately approved.

## Canonical plan

1. Inspect the archive collection/template, current navigation helpers, and
   generated output configuration.
2. Present the later-page URL pattern and navigation presentation for approval
   without making them product requirements before approval.
3. Implement archive pagination while preserving newest-first exactly-once
   membership and `/blog/`.
4. Add accessible boundary-aware adjacent-page navigation.
5. Verify the production Eleventy build and inspect generated first, middle,
   and last pages.
6. Verify home, tag, feed, sitemap, individual-post navigation, and zero-script
   output remain compatible.
7. Update current documentation only if affected claims require it.

## Expected task shape

- One task file.
- No task directory.
- Requirements preserve every approved outcome without turning the URL
  recommendation, tests, documentation, or Eleventy configuration into product
  requirements.
- The plan owns implementation, generated-output evidence, documentation work,
  decisions, and remaining gaps.

## Handoff variants

### Retain plan

The task stores the canonical plan as Draft and preserves the two material
presentation/URL decisions.

### Omit plan

The task preserves verified template/configuration facts, source pointers,
ARCHIVE outcomes, protected surfaces, and unresolved decisions. It omits the
seven implementation/verification steps.

## Continuation target

A fresh agent presents a complete plan covering all seven outcomes, real build
evidence, boundary navigation, protected surfaces, and unresolved public
choices without modifying files.

## Important crossing

Production Eleventy configuration and templates must produce and expose the
expected generated public output.

## Efficiency use

Use this scenario for retained-plan versus omit-plan versus original
investigation comparison.

## Human review

- Is one task proportionate?
- Did any approved condition disappear during grouping?
- Are URL/navigation choices still approval-aware?
- Can a fresh agent plan without rediscovering the whole site structure?