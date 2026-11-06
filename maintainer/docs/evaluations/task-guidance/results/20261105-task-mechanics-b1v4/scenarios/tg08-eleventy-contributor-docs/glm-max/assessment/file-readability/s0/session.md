# Session — tg08-eleventy-contributor-docs · file-readability-assessment-glm-max-s0 · glm max

- Run: `20261102T112225.993008Z-task-guidance-file-readability-tg08-eleventy-contributor-docs-glm-max-s0-76233dcd`
- Model: glm-5.3-flash (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-c440c4f661a7.md) — captured (original SHA-256 `beebc670f6138d47…`)
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
  "scenario_id": "tg08-eleventy-contributor-docs",
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

# Write the contributor guide section

Write the CONTRIBUTING.md guide for adding posts: front matter, drafts, and local preview, accepted by maintainer review.

Category: kind
Task kind: documentation

Measured structure facts (per file, per top-level section):

#### tasks/20261102-contributor-post-guide.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261102-contributor-post-guide.md — Requirements checklist | 281 | 0 | 0 | 7 | 13 | 0 | 0 | 0 | 21 |
| tasks/20261102-contributor-post-guide.md — Questions and decisions | 110 | 0 | 0 | 3 | 13 | 0 | 0 | 0 | 4 |
| tasks/20261102-contributor-post-guide.md — Supporting details | 264 | 1 | 7 | 8 | 11 | 0 | 0 | 0 | 39 |
| tasks/20261102-contributor-post-guide.md — Implementation plan | 508 | 3 | 79 | 14 | 13 | 5 | 0 | 0 | 27 |

The produced task files:

### tasks/20261102-contributor-post-guide.md

````markdown
# Contributor guide: writing a blog post in `CONTRIBUTING.md`

New contributors keep asking how to add a post. Create a root `CONTRIBUTING.md`
(file does not exist yet) whose core section walks a first-time contributor
through: creating a post file, the front matter every post needs, how drafts
work, and how to preview the site locally. Documentation only — no product or
configuration behavior changes.

## Requirements checklist

- [ ] A new root `CONTRIBUTING.md` contains a writing-a-post section aimed at
  first-time contributors, covering all four requested topics: creating a post
  file, required front matter, drafts, local preview.
- [ ] Creating a post file: documents `content/posts/*.md` as the post
  location, that posts are Markdown, the resulting URL (`/posts/<slug>/`), and
  what `content/posts/posts.json` supplies automatically (the post layout and
  the `posts` collection tag).
- [ ] Front matter: documents `title` and an explicit `date` as what every post
  needs; explains `tags` (the `posts` tag comes from directory data; extra tags
  on a post produce tag pages at `/tags/<slug>/`); and treats `description`
  truthfully — no template or the feed consumes it today, so it is documented
  as unused rather than required, and any target-convention text carries a
  visible `Not implemented` marker.
- [ ] Drafts: states the current truth — the site has no draft mechanism; every
  file in `content/posts/` builds, appears in the archive, and is included in
  the feed as soon as it merges. Any description of a future draft workflow
  (e.g. `draft: true` plus `eleventyExcludeFromCollections`) carries a visible
  `Not implemented` marker.
- [ ] Local preview: documents only commands available today — `npm run build`
  (output in `_site/`, which is gitignored) and Eleventy's dev server
  (`npx @11ty/eleventy --serve`) — and adds no new scripts or configuration.
- [ ] No product behavior changes: the reviewed change touches only
  `CONTRIBUTING.md`; no template, config, `package.json`, existing content, or
  test changes.
- [ ] Every factual claim in the new section was checked against the current
  build while drafting (post URL, archive listing, feed entry, tag page, dev
  server) so all claims are true in the same change that adds them.

## Questions and decisions

- Requirement question (settles framing, not blocking): should `description` be
  presented as *recommended but currently unused* (recommended) or as a target
  convention with `Not implemented`? Requirement 3 is written so either answer
  satisfies it; the maintainer review confirms the framing.
- Decision (from "no product behavior changes"): preview is documented with the
  existing Eleventy CLI; adding an `npm run serve` script would be a config
  change and is out of scope here. If wanted, that is a separate follow-up task.
- Decision: because the repo has no draft support, the drafts section documents
  that absence rather than describing a nonexistent feature as current
  behavior, per the documentation policy in `docs/development/documentation.md`.

## Supporting details

Verified repo facts (source read on 2026-11-02):

- Posts live in `content/posts/`. Directory data file
  `content/posts/posts.json` sets `layout: layouts/post.njk` and
  `tags: ["posts"]` for every file there, so a post does not need to repeat
  either. Existing posts (`first.md`, `second.md`) use `title`, `date`
  (`YYYY-MM-DD`), and repeat `tags: [posts]` anyway.
- `description` appears in no post, no layout, and no template;
  `_includes/layouts/post.njk` renders only `title`, `author` (also unset by
  current posts, so it renders empty), and content.
- Every post lands in: the archive `content/blog.njk` (`collections.posts`),
  the home page latest list `content/index.njk` (last 3), the feed
  `content/feed.xml.njk`, and — for any additional tag — a generated page from
  `content/tag-pages.njk`. There is no state in which a merged post is hidden.
- `eleventy.config.js` contains no draft handling (no `draft` key, no
  `eleventyExcludeFromCollections`); a repo-wide search finds no draft
  mechanism. Eleventy has no built-in `draft` key either (its drafts doc pages
  return 404), so the standard pattern is `draft: true` +
  `eleventyExcludeFromCollections`, which this site does not implement.
- Scripts in `package.json` are only `build` (`eleventy`) and `test`
  (`node --test tests/*.test.js`); there is no serve/start script. Config
  input dir is `content`, output `_site` (gitignored).
- Eleventy docs (11ty.dev/docs/dates/): without a front matter `date`, the file
  creation date is used, which is unreliable on CI — supports requiring an
  explicit `date`.
- `docs/development/documentation.md` policy: documentation describes current
  supported behavior; target-only text needs a visible `Not implemented`
  marker; new public claims go in the same reviewed change that makes them
  true.
- Upstream context: compact fixture of Eleventy Base Blog (`UPSTREAM.md`);
  test suite today only checks that `/blog/index.html` exists
  (`tests/archive-output.test.js`).

## Implementation plan

Status: Draft

Single-deliverable documentation task: one new file, root `CONTRIBUTING.md`,
no other paths. The design constraint shaping the writing is truthfulness:
the section covers all four requested topics, but for `description` and
drafts the current site has no supporting behavior, so those topics are
documented as current-state facts with target text (if any) marked
`Not implemented`. This satisfies the coverage request without changing
product behavior and keeps every claim true in the reviewed change, as the
documentation policy requires.

Verification strategy: while drafting, the writer builds (`npm run build`),
inspects `_site` output to confirm each URL/architecture claim (post page,
archive entry, feed entry, tag page), runs `npx @11ty/eleventy --serve` to
confirm the documented preview command works, and finishes with a diff check
that only `CONTRIBUTING.md` changed. Acceptance is then maintainer review of
the section against the requirements checklist above — the checklist is
written to be reviewable item by item without tooling.

Risks and the way back: the main risk is documenting target behavior as
current (mitigated by the truthfulness requirements and the marker rule); a
secondary risk is scope creep into config changes like a serve script
(excluded by requirement). Blast radius is one new untracked file; rolling
back is deleting `CONTRIBUTING.md` or `git restore`/`git clean` on it. Order
is linear with one deliverable: facts are already gathered above, so draft,
verify claims, confirm clean diff, hand off for review.

### Implementation decisions and open questions

- Destination and audience are fixed by the request: root `CONTRIBUTING.md`,
  written for new contributors; no separate docs page is created.
- Open (review-time framing): `description` as recommended-but-unused versus
  target convention with marker — see Questions and decisions.

### Documentation

- Audience: first-time contributors adding their first post.
- Destination: new root `CONTRIBUTING.md`, reviewed in the same change.
- Related maintained docs: `README.md` (stays as is), `AGENTS.md` /
  `docs/development/documentation.md` (policy followed, not modified).

### Task checklist

- [ ] Draft the writing-a-post section in root `CONTRIBUTING.md` covering the
  four topics using the verified facts in Supporting details.
- [ ] Verify every claim: `npm run build`, inspect `_site` for the post URL,
  archive entry, feed entry, and a tag page; run `npx @11ty/eleventy --serve`
  and confirm it serves the site.
- [ ] Confirm the diff touches only `CONTRIBUTING.md` (`git status`).
- [ ] Hand off to a maintainer for review against the Requirements checklist.

### Requirement verification

- Coverage of the four topics (requirements 1–5): decisive evidence is the
  maintainer review of the `CONTRIBUTING.md` section against the checklist —
  the review reads the published section itself, which is the outcome of a
  documentation task. The executor's build/serve checks support claim
  accuracy but do not replace the review.
- No behavior changes (requirement 6): `git status`/diff showing
  `CONTRIBUTING.md` as the only change; `npm test` still passes untouched.
- Claim accuracy (requirement 7): executor's build inspection recorded in
  implementation notes; final acceptance remains the maintainer review.
- Deliberately not covered: no test additions (documentation-only change);
  review judges factual accuracy and coverage, not prose style beyond
  contributor readability.

### Additional implementation verification

- Run `npm test` after drafting to confirm the existing archive test is
  unaffected (cheap guard against incidental edits).
````


**Assistant** *(reasoning present)*

```json
{
  "schema_version": 1,
  "scenario_id": "tg08-eleventy-contributor-docs",
  "assessment": {
    "sections": {
      "tasks/20261102-contributor-post-guide.md — Requirements checklist": {
        "grade": "partial",
        "findings": [
          {
            "where": "Checklist item 3 (Front matter)",
            "quote": "treats `description` truthfully — no template or the feed consumes it today, so it is documented as unused rather than required, and any target-convention text carries a visible `Not implemented` marker.",
            "why": "One checkbox chains three separately reviewable claims (title/date, tags, description) plus the marker rule, with a parenthetical nested inside another parenthesis earlier in the same item ('explains `tags` (the `posts` tag comes from directory data; extra tags...)'). A maintainer ticking it must hold several conditions at once, and a partially met item cannot be recorded."
          },
          {
            "where": "Checklist item 2 (Creating a post file)",
            "quote": "documents `content/posts/*.md` as the post location, that posts are Markdown, the resulting URL (`/posts/<slug>/`), and what `content/posts/posts.json` supplies automatically (the post layout and the `posts` collection tag).",
            "why": "Four distinct facts ride in a single ~40-word checkbox; the topic label ('Creating a post file:') keeps it findable, but the multi-claim bundling strains the review-by-item flow the file itself promises ('reviewable item by item without tooling')."
          },
          {
            "where": "Whole section",
            "quote": "- [ ] A new root `CONTRIBUTING.md` contains a writing-a-post section... - [ ] Creating a post file:... - [ ] Front matter:... - [ ] Drafts:... - [ ] Local preview:...",
            "why": "The colon lead-ins map cleanly onto the four requested topics, so the 7-item, 281-word checklist remains scannable at the heading level; the strain is inside items 2-4, not in the section's shape."
          }
        ]
      },
      "tasks/20261102-contributor-post-guide.md — Questions and decisions": {
        "grade": "readable",
        "findings": [
          {
            "where": "First bullet",
            "quote": "Requirement question (settles framing, not blocking): should `description` be presented as *recommended but currently unused* (recommended) or as a target convention with `Not implemented`? Requirement 3 is written so either answer satisfies it",
            "why": "The question, both options, and its non-blocking status sit in one ~40-word sentence, but the lead-in label and the explicit cross-reference to Requirement 3 let a reader resolve it in a single pass."
          },
          {
            "where": "Whole section",
            "quote": "Decision (from \"no product behavior changes\"): preview is documented with the existing Eleventy CLI; adding an `npm run serve` script would be a config change and is out of scope here.",
            "why": "Three bullets, each anchored by a label ('Requirement question', 'Decision', 'Decision'), give the open question and the two scope decisions in 110 words with nothing buried."
          }
        ]
      },
      "tasks/20261102-contributor-post-guide.md — Supporting details": {
        "grade": "readable",
        "findings": [
          {
            "where": "Drafts bullet",
            "quote": "Eleventy has no built-in `draft` key either (its drafts doc pages return 404), so the standard pattern is `draft: true` + `eleventyExcludeFromCollections`, which this site does not implement.",
            "why": "This is the densest of the eight bullets, stacking the repo-search result, upstream doc status, the standard pattern, and the site's non-implementation into one sentence; it still parses in one pass because each clause advances the same point."
          },
          {
            "where": "Third bullet (post surfaces)",
            "quote": "There is no state in which a merged post is hidden.",
            "why": "The bullet's load-bearing conclusion arrives only after a four-item enumeration of surfaces ('the archive `content/blog.njk`..., the home page latest list..., the feed..., and — for any additional tag — a generated page'), so a skim for the conclusion can miss it."
          },
          {
            "where": "Whole section",
            "quote": "Posts live in `content/posts/`. Directory data file `content/posts/posts.json` sets `layout: layouts/post.njk` and `tags: [\"posts\"]`...",
            "why": "One fact-cluster per bullet with dated provenance ('source read on 2026-11-02') makes this a reference list a maintainer can quote from directly; the 39 code spans aid precision rather than hurt scanning."
          }
        ]
      },
      "tasks/20261102-contributor-post-guide.md — Implementation plan": {
        "grade": "partial",
        "findings": [
          {
            "where": "'Risks and the way back' paragraph",
            "quote": "the main risk is documenting target behavior as current (mitigated by the truthfulness requirements and the marker rule); a secondary risk is scope creep into config changes like a serve script (excluded by requirement). Blast radius is one new untracked file; rolling back is deleting `CONTRIBUTING.md` or `git restore`/`git clean` on it.",
            "why": "Five distinct facts (primary risk, its mitigation, secondary risk, blast radius, rollback path) are compressed into a semicolon-chained prose paragraph; the reader must re-read to separate risk from mitigation from rollback, the clearest prose wall in the file."
          },
          {
            "where": "Verification strategy paragraph vs. Task checklist vs. Requirement verification",
            "quote": "runs `npx @11ty/eleventy --serve` to confirm the documented preview command works, and finishes with a diff check that only `CONTRIBUTING.md` changed",
            "why": "The same build/serve/diff verification is spelled out three times in near-identical wording (strategy paragraph, the 'Verify every claim' checkbox, and the 'Claim accuracy' bullet under Requirement verification); the reader must reconcile duplicates to find the authoritative steps, and none of the three adds what the others lack."
          },
          {
            "where": "Opening paragraph",
            "quote": "the design constraint shaping the writing is truthfulness: the section covers all four requested topics, but for `description` and drafts the current site has no supporting behavior, so those topics are documented as current-state facts with target text (if any) marked `Not implemented`.",
            "why": "This 79-word paragraph restates what Requirements 3-4 and Questions and decisions already establish, spending the section's densest prose on framing rather than new information; the two shorter paragraphs that follow (status line excluded) carry similar per-sentence loads."
          },
          {
            "where": "'Additional implementation verification' subsection",
            "quote": "Run `npm test` after drafting to confirm the existing archive test is unaffected (cheap guard against incidental edits).",
            "why": "A dedicated five-word subsection heading introduces a single footnote-sized item that overlaps the verification content above it, costing the reader a scan for one sentence that could live in the strategy paragraph."
          }
        ]
      }
    },
    "navigation": {
      "grade": "navigable",
      "findings": [
        {
          "where": "Section headings",
          "quote": "## Requirements checklist / ## Questions and decisions / ## Supporting details / ## Implementation plan",
          "why": "Each reader goal has an obvious host heading: the outcome in the title and intro ('Create a root `CONTRIBUTING.md`'), the constraints under Requirements checklist, the open question under Questions and decisions, and plan status in the literal 'Status: Draft' first line of Implementation plan."
        },
        {
          "where": "Implementation plan, 'Implementation decisions and open questions' subsection",
          "quote": "Open (review-time framing): `description` as recommended-but-unused versus target convention with marker — see Questions and decisions.",
          "why": "The one open question is cross-referenced rather than re-argued, so a reader landing in the plan is pointed back to the authoritative section instead of finding two competing statements."
        }
      ]
    },
    "mistakes": [
      {
        "where": "Requirements checklist, item 3 (Front matter)",
        "quote": "documents `title` and an explicit `date` as what every post needs; explains `tags` (...); and treats `description` truthfully — ... and any target-convention text carries a visible `Not implemented` marker.",
        "why": "List item mixing several facts: a semicolon chain makes one checkbox responsible for three independent reviewable claims, so the checklist cannot express partial compliance."
      },
      {
        "where": "Implementation plan, 'Risks and the way back' paragraph",
        "quote": "Blast radius is one new untracked file; rolling back is deleting `CONTRIBUTING.md` or `git restore`/`git clean` on it. Order is linear with one deliverable: facts are already gathered above, so draft, verify claims, confirm clean diff, hand off for review.",
        "why": "Prose wall: rollback, execution order, and blast radius are packed into consecutive semicolon-heavy sentences with no list structure, forcing a re-read to extract the actual way back."
      },
      {
        "where": "Implementation plan (Verification strategy, Task checklist, Requirement verification)",
        "quote": "inspect `_site` for the post URL, archive entry, feed entry, and a tag page; run `npx @11ty/eleventy --serve` and confirm it serves the site",
        "why": "Buried/duplicated load-bearing content: the authoritative verification steps appear three times in slightly different words, so no single location is clearly the checklist a maintainer executes."
      },
      {
        "where": "Implementation plan, 'Additional implementation verification' subsection",
        "quote": "Run `npm test` after drafting to confirm the existing archive test is unaffected (cheap guard against incidental edits).",
        "why": "Heading does not match its weight: a standalone subsection heading delivers one sentence that duplicates verification content already stated twice above it."
      },
      {
        "where": "Supporting details, third bullet",
        "quote": "There is no state in which a merged post is hidden.",
        "why": "Buried load-bearing fact: the bullet's conclusion (no merged post can be hidden) follows a four-surface enumeration instead of leading it."
      }
    ],
    "summary": "One file with four conventional sections whose headings match their content; a maintainer can reach the outcome, the constraints, the open question, and the plan status from structure alone, so navigation is clean. Effort concentrates where items are overloaded: three of the seven requirement checkboxes each bundle several verifiable claims into a single tick (front matter alone chains title/date, tags, and description with nested parentheticals), and the Implementation plan is the heaviest section at 508 words, with a 79-word opening paragraph restating settled framing, a five-fact 'Risks and the way back' prose paragraph, and the build/serve/diff verification steps stated three times in near-identical wording. Supporting details is the strongest section — one dated fact-cluster per bullet, directly quotable — and Questions and decisions needs nothing. Splitting the bundled checkboxes and collapsing the duplicated verification text into one authoritative list would lift both partial sections to readable."
  }
}
```
