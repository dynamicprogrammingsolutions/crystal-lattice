# Session — tg01-eleventy-archive-handoff · file-readability-assessment-glm-max-s0 · glm max

- Run: `20261029T224820.214513Z-task-guidance-file-readability-tg01-eleventy-archive-handoff-glm-max-s0-e2ffea72`
- Model: glm-5.3-flash (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-c440c4f661a7.md) — captured (original SHA-256 `4978d488db393f43…`)
- Config: [glm-assessor-max](../../../../../../shared/configs/glm-assessor-max.json)
- Activity: 3 messages · 0 tool calls · 0 tool results
- Usage: 0 input · 0 cached · 0 output · provider cost $0.0000000

## Transcript

**User**

Assess how easily a human reader can work with the task files below.
You are that reader: a maintainer who must find, understand, and act on
what the files say. Judge every top-level section that is present; do
not invent sections that are absent, and do not grade files or sections
that do not appear.

Grade each present top-level section `readable`, `partial`, or
`unreadable`: can a reader take in that section's content with
reasonable effort — scan it, hold it, and use it? A section is
`unreadable` when a reader must re-read dense prose or wall-like list
items to extract what matters; `partial` when parts strain the reader.

Then grade the whole file's navigation `navigable`, `partial`, or
`confusing`: can a reader find the thing they are looking for — the
outcome, the constraint, the open question, the plan status — from the
file's structure alone?

Measured structure facts are provided per section; anchor on these
numbers rather than impressions. They are facts, not rules: no shape is
banned or required. Formatting elements — tables, ordered lists, code
snippets, short paragraphs — are tools among many; what is graded is
the reader's experience, never the presence of a specific element.

Every grade carries findings: concrete `{where, quote, why}` items. A
non-top grade with empty findings is invalid. Then hunt for
presentation mistakes explicitly — prose walls, list items that mix
several facts, buried load-bearing facts, headings that do not match
their content, walls of unchecked boxes — and list each as
`{where, quote, why}` in `mistakes`.

Depth must match impact: a short section is not a defect; a dense
section is not automatically one either. Verbosity is not rewarded;
brevity that loses nothing is not penalized.

Return JSON only:

{
  "schema_version": 1,
  "scenario_id": "tg01-eleventy-archive-handoff",
  "assessment": {
    "sections": {
      "SECTION TITLE": {
        "grade": "readable|partial|unreadable",
        "findings": [{"where": "...", "quote": "...", "why": "..."}]
      }
    },
    "navigation": {"grade": "navigable|partial|confusing", "findings": []},
    "mistakes": [{"where": "...", "quote": "...", "why": "..."}],
    "summary": "concise evidence-based interpretation"
  }
}

`sections` contains exactly the top-level sections listed in the
measured facts, keyed by the exact Section values of that table
(`<file path> — <section title>`), so multi-file task sets stay
addressable.

What these files are for:

# Eleventy archive pagination handoff

Preserve a reviewed cohesive archive-pagination plan in a durable task handoff.

Category: handoff

Measured structure facts (per file, per top-level section):

#### tasks/20261029-eleventy-archive-pagination.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261029-eleventy-archive-pagination.md — Requirements checklist | 218 | 0 | 0 | 12 | 23 | 0 | 0 | 0 | 6 |
| tasks/20261029-eleventy-archive-pagination.md — Open questions and decisions | 196 | 0 | 0 | 5 | 13 | 0 | 0 | 0 | 11 |
| tasks/20261029-eleventy-archive-pagination.md — Research and supporting details | 454 | 3 | 4 | 15 | 13 | 0 | 0 | 0 | 52 |
| tasks/20261029-eleventy-archive-pagination.md — Execution plan | 1147 | 5 | 67 | 54 | 16 | 7 | 0 | 0 | 78 |

The produced task files:

### tasks/20261029-eleventy-archive-pagination.md

````markdown
# Paginate the blog archive with accessible navigation

The blog archive (`/blog/`) currently renders every post on a single page and
will not scale as posts accumulate. Convert it to stable paginated archive
pages with accessible Previous/Next navigation while preserving the home page,
tags, feed, sitemap, individual-post navigation, post order, and the static
zero-JavaScript output. Plan and task structure only — implementation is not
authorized yet.

## Requirements checklist

- [ ] `/blog/` remains the first archive page at the same URL, listing at most the 20 newest posts, newest first.
- [ ] Later archive pages are generated at stable URLs, each containing at most 20 posts.
- [ ] Archive pages provide accessible Previous/Next navigation (nav landmark, links only when a target page exists, current-page context, no JavaScript).
- [ ] Home page (`/`) is preserved unchanged, including its newest-three post list.
- [ ] Tag pages (`/tags/<slug>/`) are preserved unchanged, listing every post for the tag.
- [ ] Feed (`/feed/feed.xml`) is preserved unchanged, listing all posts.
- [ ] Sitemap is preserved: all currently produced entries remain, and the sitemap mechanism itself is unchanged.
- [ ] Individual-post navigation is preserved: post permalinks do not change, and links to individual posts from the home, tag, and archive listings keep working.
- [ ] Post order remains newest → oldest, flowing from `/blog/` through the later archive pages and within each page.
- [ ] Build output remains static HTML with zero client-side JavaScript.
- [ ] Production-build test evidence covers the new pagination behavior and the preserved surfaces.
- [ ] Maintained documentation describes the paginated archive (README claim stays true; the archive pagination spec in `docs/development/index.md` replaces the "no specification exists" note).

## Open questions and decisions

- **Decision — later-page URL scheme (material, user-visible).**
  Recommendation: `/blog/2/`, `/blog/3/`, … (first page stays `/blog/`).
  Alternative: `/blog/page/2/`. Resolved by approving this plan; easy to change
  before execution.
- **Decision — page 1 holds the newest posts.** Current `/blog/` shows all
  posts newest-first (postslist reverses `collections.posts`). Preserving that
  order means page 1 must hold the newest 20 and later pages go progressively
  older. Not treated as open; it follows from "preserve post order".
- **Decision — "individual-post navigation" interpretation.** The post layout
  (`_includes/layouts/post.njk`) has no in-post prev/next today, so there is
  nothing of that kind to preserve. Read as: stable post permalinks plus
  working links to posts from home/tags/archive. If in-post prev/next was
  intended, that is a scope addition to approve.
- **Decision — sitemap and new archive pages.** Keep the sitemap template
  untouched and accept what `collections.all` naturally contains, verifying the
  outcome and documenting it. See fact-to-verify F1. Not adding
  `pagination.addAllPagesToCollections` unless verification shows later archive
  pages are missing from `collections.all` and the user wants them present,
  because that option's interaction with the `posts` collection used by the
  feed, tags, and home pages is unverified in this fixture.
- No other requirement questions are open.

## Research and supporting details

Facts (verified by inspection):

- F0. Eleventy `^3.0.0` (ESM config, `eleventy.config.js`); input `content/`,
  includes `_includes/`, output `_site/` (gitignored). Dependencies are not
  installed; the executor must run `npm install` before any build or test.
- F1 (fact-to-verify during execution). `content/sitemap.xml.njk` iterates
  `collections.all`. Whether Eleventy pagination pages beyond the first land in
  `collections.all` by default is not verified for this fixture; the first
  production build will settle it and the test should assert the actual
  outcome the user approves.
- F2. Current archive: `content/blog.njk` (permalink `/blog/`) includes
  `_includes/postslist.njk` with `postslist = collections.posts`; the include
  renders `postslist | reverse`, i.e. newest first. `collections.posts` itself
  is date-ascending.
- F3. Home: `content/index.njk` uses the `head(-3)` filter (defined in
  `eleventy.config.js`) to show the newest three posts via the same include.
  Tags: `content/tag-pages.njk` paginates `collections` (`size: 1`,
  `filter: [all, posts]`, alias `tag`) to `/tags/<slug>/` and shows all posts
  of the tag. Feed: `content/feed.xml.njk` lists all posts at
  `/feed/feed.xml`. Sitemap: `content/sitemap.xml.njk` lists `collections.all`.
- F4. Content is two posts (`first.md` 2026-01-01, `second.md` 2026-01-02),
  so the real site produces a single archive page until 21 posts exist. Tests
  must synthesize more posts to exercise later pages and nav boundaries.
- F5. `tests/archive-output.test.js` contains only a placeholder comment; there
  is no real test yet. `npm test` runs `node --test tests/*.test.js`.
- F6. Eleventy pagination supports `size`, `alias`, permalink interpolation on
  `pagination.pageNumber`, `pagination.href.previous/next`,
  `pagination.pages`, and (since v2, so available on v3) `pagination.before`
  to reorder the full data set before chunking. Fallback if `before` misbehaves:
  register a custom collection via `addCollection` returning date-descending
  posts and paginate over it.
- F7. `content/posts/posts.json` sets the `posts` tag and post layout for all
  posts; post permalinks follow the default slug pattern.
- F8. `docs/development/index.md` currently states "No archive pagination
  specification exists." — the anticipated home for the new spec.
  `docs/development/documentation.md` was read per AGENTS.md before planning
  documentation changes.

Constraints:

- C1. Zero client-side JavaScript is a build-output property; pagination must
  be produced entirely at build time (it is — pagination is a static-site
  feature).
- C2. `_includes/postslist.njk` is shared by home, tags, and archive. Keep it
  behaviorally unchanged so the shared surfaces stay identical.

Risks:

- R1. `pagination.before` template-string syntax may differ from expectation
  in v3 → use the fallback custom collection (F6). Low impact; covered by the
  ordering assertions.
- R2. The reversal chain (descending pagination data → per-chunk display via
  the include's `reverse`) is easy to get backwards; ordering assertions on
  first/last titles per page are the guard.
- R3. Pagination pages shifting content as new posts arrive is inherent to
  date-based pagination; "stable" here means the deterministic `/blog/<n>/`
  scheme, not immutable page contents. Recorded so approval is informed.
- R4. `node --test` with async builds: builds must be awaited and temp
  fixtures cleaned up in `t.after`/`finally`.

## Execution plan

Status: Draft

### Design

**Outcome.** `/blog/` stays the archive entry page showing the 20 newest
posts. Additional pages `/blog/2/`, `/blog/3/`, … (D1) carry at most 20 older
posts each, in the same newest-first order flowing page by page (D2). Each
page gets a build-time, zero-JS Previous/Next nav. Home, tags, feed, and the
sitemap mechanism are untouched; post permalinks and listing links are
untouched; the shared include stays byte-identical in behavior (C2).

**Component responsibilities and data flow.**

- `content/blog.njk` becomes the paginated archive template:
  - frontmatter pagination over `collections.posts` with `size: 20`,
    alias (e.g. `posts`), and `pagination.before` reversing the full set to
    date-descending before chunking (F6; fallback: custom descending
    collection registered in `eleventy.config.js`).
  - permalink: `/blog/` for page 0; `/blog/{{ pagination.pageNumber + 1 }}/`
    for later pages — first page keeps the exact current URL.
  - body: set `postslist = posts | reverse` (restores ascending order inside
    the chunk so the shared include's own `reverse` renders newest-first) and
    include `postslist.njk` unchanged; append the navigation below the list.
    Add a brief comment explaining the reversal chain (R2).
- Navigation markup (inline in `blog.njk`; no other page reuses it, so no new
  include is warranted):
  - `<nav>` landmark with `aria-label` (e.g. "Blog archive pages");
  - "Page X of Y" text for current-page context;
  - "Previous" / "Next" anchors with `rel="prev"` / `rel="next"` rendered only
    when `pagination.href.previous` / `pagination.href.next` exist; inert
    placeholder text (`<span aria-disabled="true">`) otherwise;
  - omitted entirely when there is only one page (current two-post site).
- `_includes/postslist.njk`, `content/index.njk`, `content/tag-pages.njk`,
  `content/feed.xml.njk`, `content/posts/**`: unchanged (C2, F3, F7).
- `content/sitemap.xml.njk`: unchanged; the outcome for later archive pages is
  verified and documented (F1, D-sitemap).

**Compatibility states.** With ≤ 20 posts the site output is identical to
today except possibly the nav (omitted for single page) and sitemap contents
(F1). With > 20 posts the new pages appear. No persisted data, APIs, or
client-side behavior changes.

**Verification strategy.** The decisive check is a real production Eleventy
build whose output files are asserted on disk (integration test through the
actual engine, permalinks, pagination math, and template rendering — no
mocked slicing). `tests/archive-output.test.js` is replaced with:

1. A synthesized temp-site fixture (copy config + includes; generate 41 posts
   with distinct ascending dates in a temp directory; build via the Eleventy
   Node API into a temp output dir, cleaned up afterwards; F5, F4, R4).
   Assertions:
   - pages exist for `/blog/`, `/blog/2/`, `/blog/3/`; no `/blog/4/`;
   - item counts per page are 20/20/1 (cap and remainder);
   - order: page 1 starts at the newest post, ends at post 22; page 2 spans
     posts 21→2; page 3 holds post 1 (newest → oldest across and within
     pages; R2 guard);
   - navigation: page 1 has Next and no Previous anchor, middle page has
     both, last page has Previous and no Next; nav landmark and
     `aria-disabled` placeholders present where applicable; correct
     `href`s between consecutive pages; no `<script>` anywhere;
   - preserved surfaces: home lists exactly the newest three posts with the
     newest first; `/tags/posts/` lists all 41; feed lists all 41; sitemap
     contains home, post pages, tag page, feed, `/blog/` — and its treatment
     of `/blog/2/`+ is asserted per the approved decision and recorded
     (F1, D-sitemap);
   - individual-post navigation: archive/home/tag links point at the stable
     expected post URLs, and a sampled post page exists on disk.
2. A real-content build (the two committed posts): `_site/blog/index.html`
   exists, no `/blog/2/`, no archive nav rendered (F5 keeps its original
   intent).

Run `npm test` (node --test) and `npm run build`; inspect `_site` for the
real-content case.

### Ordered steps

1. `npm install` (F0).
2. Implement pagination in `content/blog.njk` per the design (D1, D2, F6,
   fallback if `before` misbehaves).
3. Add the accessible Previous/Next nav to `content/blog.njk`.
4. Replace `tests/archive-output.test.js` with the build-output tests above.
5. Update `README.md` (archive is paginated, ≤ 20 posts per page, prev/next
   links) and replace the note in `docs/development/index.md` with a concise
   archive pagination specification: URL scheme, page size cap, ordering,
   navigation and accessibility behavior, single-page behavior, and the
   verified sitemap treatment of later pages.
6. Run `npm test` and `npm run build`; fix failures; record evidence.
7. Update this task's checklist and completion notes.

### Implementation decisions and open questions

- D1: later-page URLs `/blog/2/`, `/blog/3/`, … — needs approval (material,
  user-visible URL scheme).
- D2: page 1 = newest 20, later pages older — follows from preserving the
  current newest-first archive order.
- D3: interpretation of "individual-post navigation" as stable post URLs plus
  listing links; no in-post prev/next exists today — flag if that was
  intended (would be a scope addition).
- D4: sitemap keeps its mechanism untouched; acceptance of later archive
  pages follows what verification shows `collections.all` contains, recorded
  in docs — flag if later archive pages must be explicitly included or
  excluded.
- No other open questions.

### Documentation

- `README.md`: one clause so the existing public claim stays true and current
  (audience: site users/adopters).
- `docs/development/index.md`: concise archive pagination spec replacing the
  "No archive pagination specification exists." line (audience: maintainers).
  No new files or directories — smallest structure that serves the reader.

### Task checklist

- [ ] Install dependencies (`npm install`).
- [ ] Implement archive pagination in `content/blog.njk` (stable later-page URLs, ≤ 20 posts/page, newest-first order).
- [ ] Add accessible Previous/Next navigation to `content/blog.njk`.
- [ ] Replace `tests/archive-output.test.js` with real-build pagination and preservation tests.
- [ ] Update `README.md` and write the archive pagination spec in `docs/development/index.md`.
- [ ] Run `npm test` and `npm run build`; record results and the verified sitemap outcome (F1).
- [ ] Update requirement evidence and write completion notes.

### Requirement verification

- `/blog/` first page, newest-first, ≤ 20 posts → test 1 page-existence and
  ordering assertions on `/blog/index.html` (real build output).
- Stable later pages, ≤ 20 posts each → test 1 assertions on `/blog/2/`,
  `/blog/3/`, absence of `/blog/4/`, per-page item counts 20/20/1.
- Accessible prev/next nav → test 1 nav assertions (landmark, anchors present
  only with a target page, placeholders, hrefs, no `<script>`).
- Home preserved → test 1 home assertions (newest three, newest first).
- Tags preserved → test 1 assertion that `/tags/posts/` lists all posts
  (shared include untouched).
- Feed preserved → test 1 feed assertion (all posts listed).
- Sitemap preserved → test 1 sitemap assertions (existing entries present;
  later-page treatment asserted per approved decision and recorded).
- Individual-post navigation preserved → test 1 assertions that listing links
  match expected stable post URLs and a sampled post page exists.
- Post order → test 1 ordering assertions across and within pages (R2 guard).
- Zero-JavaScript static output → test 1 "no `<script>`" assertion across all
  generated HTML; pagination is build-time only.
- Test evidence added → `npm test` run with the new tests collecting and
  exiting cleanly.
- Documentation updated → files inspected in review; README/spec claims
  checked against build output.

### Additional implementation verification

- Build the real two-post content and confirm `_site/blog/index.html` is the
  only archive page with no nav rendered (regression guard for the ≤ 20 case).
- Grep the generated `_site` for `<script` as a whole-output check, not just
  sampled pages.
````


**Assistant** *(reasoning present)*

```json
{
  "schema_version": 1,
  "scenario_id": "tg01-eleventy-archive-handoff",
  "assessment": {
    "sections": {
      "tasks/20261029-eleventy-archive-pagination.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "checklist item 3",
            "quote": "Archive pages provide accessible Previous/Next navigation (nav landmark, links only when a target page exists, current-page context, no JavaScript).",
            "why": "One checkbox packs four distinct navigation conditions into a single parenthetical; at ~20 words it stays scannable, but it is the densest item in an otherwise one-requirement-per-box list."
          },
          {
            "where": "checklist item 12",
            "quote": "Maintained documentation describes the paginated archive (README claim stays true; the archive pagination spec in `docs/development/index.md` replaces the \"no specification exists\" note)",
            "why": "Two documentation targets share one checkbox; minor since the parenthetical names both files, but the item carries two deliverables where the other eleven carry one."
          }
        ]
      },
      "tasks/20261029-eleventy-archive-pagination.md — Open questions and decisions": {
        "grade": "partial",
        "findings": [
          {
            "where": "4th bullet, sitemap decision",
            "quote": "Not adding `pagination.addAllPagesToCollections` unless verification shows later archive pages are missing from `collections.all` and the user wants them present, because that option's interaction with the `posts` collection used by the feed, tags, and home pages is unverified in this fixture.",
            "why": "A nested conditional (not-X-unless-A-and-B, because C) in one sentence buries the actual decision — leave the sitemap template untouched and document what verification shows; this item must be re-read to extract it."
          },
          {
            "where": "2nd bullet, under the bold header 'Decision — page 1 holds the newest posts.'",
            "quote": "Not treated as open; it follows from \"preserve post order\".",
            "why": "An item filed under a 'Decision' label states it is not actually open, so the reader must double-check whether any approval is being requested here before moving on."
          }
        ]
      },
      "tasks/20261029-eleventy-archive-pagination.md — Research and supporting details": {
        "grade": "partial",
        "findings": [
          {
            "where": "fact F3, a single list item",
            "quote": "F3. Home: `content/index.njk` uses the `head(-3)` filter (defined in `eleventy.config.js`) to show the newest three posts via the same include. Tags: `content/tag-pages.njk` paginates `collections` (`size: 1`, `filter: [all, posts]`, alias `tag`) to `/tags/<slug>/` and shows all posts of the tag. Feed: `content/feed.xml.njk` lists all posts at `/feed/feed.xml`. Sitemap: `content/sitemap.xml.njk` lists `collections.all`.",
            "why": "One list item bundles four distinct preserved surfaces (home, tags, feed, sitemap); a reader checking a single surface must parse the whole item, and the internal labels only partly offset the density."
          },
          {
            "where": "fact F6",
            "quote": "Eleventy pagination supports `size`, `alias`, permalink interpolation on `pagination.pageNumber`, `pagination.href.previous/next`, `pagination.pages`, and (since v2, so available on v3) `pagination.before` to reorder the full data set before chunking. Fallback if `before` misbehaves: register a custom collection via `addCollection` returning date-descending posts and paginate over it.",
            "why": "A six-element API inventory and the actionable contingency plan share one item; the fallback — the part an executor would act on — is appended after the feature list."
          },
          {
            "where": "whole section (Facts/Constraints/Risks items)",
            "quote": "52 code spans across 454 words, e.g. \"`content/blog.njk` (permalink `/blog/`) includes `_includes/postslist.njk` with `postslist = collections.posts`\"",
            "why": "Nearly every clause carries inline code, so even the shorter F-items scan slowly; precision is high, but reading effort exceeds what the information density alone requires."
          }
        ]
      },
      "tasks/20261029-eleventy-archive-pagination.md — Execution plan": {
        "grade": "partial",
        "findings": [
          {
            "where": "Design — Verification strategy, test 1 assertion bullet on ordering",
            "quote": "order: page 1 starts at the newest post, ends at post 22; page 2 spans posts 21→2; page 3 holds post 1 (newest → oldest across and within pages; R2 guard);",
            "why": "Three separate ordering assertions plus a cross-reference ride in one bullet on semicolons; extracting any single check means re-reading the whole chain."
          },
          {
            "where": "Ordered steps vs Task checklist (same section)",
            "quote": "4. Replace `tests/archive-output.test.js` with the build-output tests above." ,
            "why": "This step is restated almost verbatim as checklist item \"- [ ] Replace `tests/archive-output.test.js` with real-build pagination and preservation tests.\": two seven-item lists cover the same work with different wording, and nothing marks which one tracks execution status."
          },
          {
            "where": "Implementation decisions and open questions",
            "quote": "D1: later-page URLs `/blog/2/`, `/blog/3/`, … — needs approval (material, user-visible URL scheme).",
            "why": "Restates the top-level 'Open questions and decisions' section under a second numbering scheme with different detail; a reader must reconcile two lists to know what genuinely needs approval."
          },
          {
            "where": "Design — Component responsibilities, sitemap bullet",
            "quote": "`content/sitemap.xml.njk`: unchanged; the outcome for later archive pages is verified and documented (F1, D-sitemap).",
            "why": "The cross-reference label `D-sitemap` is never defined — the sitemap decision is numbered D4 — so following the reference dead-ends for a reader tracking labels."
          }
        ]
      }
    },
    "navigation": {
      "grade": "partial",
      "findings": [
        {
          "where": "top-level 'Open questions and decisions' vs 'Execution plan — Implementation decisions and open questions'",
          "quote": "**Decision — later-page URL scheme (material, user-visible).** Recommendation: `/blog/2/`, `/blog/3/`, …",
          "why": "The file's open questions live in two differently numbered, differently detailed lists; a reader looking up 'what is still open' finds both and must merge them to get one answer."
        },
        {
          "where": "Execution plan, '### Ordered steps' and '### Task checklist'",
          "quote": "1. `npm install` (F0)." ,
          "why": "A numbered step list and a checkbox list mirror each other (both seven items starting with the install); structure alone does not say which list is the live tracker."
        },
        {
          "where": "Execution plan — Design and Verification strategy",
          "quote": "(F1, D-sitemap)",
          "why": "One of the file's systematic cross-reference labels does not resolve (D4 is the sitemap decision), undermining an otherwise consistent F/C/R/D reference scheme that a reader relies on to trace claims."
        }
      ]
    },
    "mistakes": [
      {
        "where": "Open questions and decisions, 4th bullet",
        "quote": "Not adding `pagination.addAllPagesToCollections` unless verification shows later archive pages are missing from `collections.all` and the user wants them present, because that option's interaction with the `posts` collection used by the feed, tags, and home pages is unverified in this fixture.",
        "why": "Prose run-on mixing the decision, its trigger conditions, and the rationale; the load-bearing outcome is buried mid-sentence behind a double conditional."
      },
      {
        "where": "Research and supporting details, fact F3",
        "quote": "Home: `content/index.njk` … Tags: `content/tag-pages.njk` … Feed: `content/feed.xml.njk` … Sitemap: `content/sitemap.xml.njk` …",
        "why": "A list item that mixes four facts; each preserved surface deserves its own item so it can be found and checked off independently."
      },
      {
        "where": "Research and supporting details, fact F6",
        "quote": "Fallback if `before` misbehaves: register a custom collection via `addCollection` returning date-descending posts and paginate over it.",
        "why": "A contingency plan appended to a feature inventory; the fallback is buried behind six enumerated API features."
      },
      {
        "where": "Open questions and decisions, 2nd bullet",
        "quote": "**Decision — page 1 holds the newest posts.**",
        "why": "Heading does not match its content: the item announces a decision then states 'Not treated as open', a label/content mismatch that costs the reader a re-check."
      },
      {
        "where": "Execution plan — Implementation decisions and open questions (vs. the top-level section of the same subject)",
        "quote": "D2: page 1 = newest 20, later pages older — follows from preserving the current newest-first archive order.",
        "why": "Duplicate statement of decisions already made in 'Open questions and decisions'; two sources of truth for approvals in one handoff file."
      },
      {
        "where": "Execution plan — Ordered steps vs Task checklist",
        "quote": "5. Update `README.md` (archive is paginated, ≤ 20 posts per page, prev/next links) … — [ ] Update `README.md` and write the archive pagination spec in `docs/development/index.md`.",
        "why": "Two parallel work lists with different wording for the same work; a maintainer cannot tell from structure which one reflects or tracks actual progress."
      },
      {
        "where": "Execution plan — Design, sitemap bullet and Verification strategy",
        "quote": "(F1, D-sitemap)",
        "why": "Dangling cross-reference: `D-sitemap` matches no defined label (the decision is D4), so the systematic F/C/R/D referencing breaks exactly where the reader follows it."
      },
      {
        "where": "Execution plan — Design — Verification strategy, test 1 assertion bullets",
        "quote": "navigation: page 1 has Next and no Previous anchor, middle page has both, last page has Previous and no Next; nav landmark and `aria-disabled` placeholders present where applicable; correct `href`s between consecutive pages; no `<script>` anywhere;",
        "why": "Five-plus distinct assertions chained with semicolons in one bullet; the individual checks blend into a wall-like item despite the surrounding list structure."
      }
    ],
    "summary": "This is a systematically labeled, mostly well-partitioned handoff: the Requirements checklist is genuinely scannable (one requirement per box), section names let a reader locate the outcome, constraints, open questions, and Draft status, and the F/C/R/D reference scheme makes claims traceable. The strains are localized, not pervasive: a handful of items bundle several facts into one unit (F3 packs four preserved surfaces, F6 appends a fallback to a feature list, the sitemap decision hides its outcome behind a double conditional, and verification assertions chain three-plus checks per semicolon). The Execution plan's 1147 words are split across seven subsections so nothing is a true wall, but it duplicates content against itself — decisions appear in two differently numbered lists and the work appears in both Ordered steps and a Task checklist — leaving the reader to reconcile which list is authoritative, and one cross-reference ('D-sitemap') resolves to nothing. Net effect: every section is usable with reasonable effort, but the duplication and the multi-fact items force re-reading at the exact points a maintainer would consult most."
  }
}
```
