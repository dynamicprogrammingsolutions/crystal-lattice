# Session — tg08-eleventy-contributor-docs · file-readability-assessment-glm-max-s0 · glm max

- Run: `20260928T214648.703654Z-task-guidance-file-readability-tg08-eleventy-contributor-docs-glm-max-s0-c4c2b983`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `b11a662234a3edff…`)
- Config: [glm-assessor-max](../../../../../../shared/configs/glm-assessor-max.json)
- Activity: 3 messages · 0 tool calls · 0 tool results
- Usage: unknown — saved session contains no provider usage metadata

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

#### tasks/20260926-contributing-guide-add-post.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-contributing-guide-add-post.md — Requirements checklist | 334 | 1 | 20 | 8 | 11 | 0 | 0 | 0 | 27 |
| tasks/20260926-contributing-guide-add-post.md — Open requirement questions | 114 | 0 | 0 | 3 | 13 | 0 | 0 | 0 | 6 |
| tasks/20260926-contributing-guide-add-post.md — Supporting details | 438 | 5 | 31 | 17 | 15 | 0 | 0 | 0 | 60 |
| tasks/20260926-contributing-guide-add-post.md — Execution plan | 577 | 2 | 120 | 21 | 15 | 5 | 0 | 0 | 38 |

The produced task files:

### tasks/20260926-contributing-guide-add-post.md

````markdown
# Write contributor guide section in CONTRIBUTING.md

Create `CONTRIBUTING.md` (new file) with a contributor-facing section teaching
new contributors how to add a blog post: creating the post file, the front
matter every post needs, how drafts work, and local preview. Docs-only change;
no product behavior changes. Acceptance is a maintainer review against the
requirements checklist below.

## Requirements checklist

Each item is a maintainer-review checklist line: check it against the finished
diff using the verified facts in this task.

- [ ] `CONTRIBUTING.md` exists as a new file with a single contributor-facing
      section on adding a blog post, aimed at new contributors.
- [ ] The section states that posts are Markdown files in `content/posts/`,
      that `layout` and the base `posts` tag are provided by
      `content/posts/posts.json` so contributors do not re-declare them, and
      that additional custom tags are allowed and create `/tags/<slug>/`
      pages.
- [ ] The section documents the required front matter — `title`, `date`,
      `description`, `tags` — with semantics matching verified behavior:
      `title` renders in the post heading and in archive/tag lists; `date`
      controls archive and feed ordering; `description` is required by
      convention but the guide makes no claim about it rendering anywhere
      (no template consumes it today); `tags` inherits `posts` from the
      directory data file.
- [ ] The section documents how drafts work per verified current behavior
      (framing per the open question below): there is no built-in draft
      support; unfinished posts are kept outside `content/posts/` until
      publication; it states plainly what that does and does not hide
      (absent from archive, feed, and tag pages, but still built to a public
      URL and listed in the sitemap); it presents no unsupported mechanism
      (`draft: true`, future dates, `permalink: false`) as working.
- [ ] The section documents local preview: `npm install` prerequisite,
      `npm run build` producing `_site/`, and `npx @11ty/eleventy --serve`
      for a watched dev server, with the URLs a contributor can check
      (`/blog/` archive, `/posts/<slug>/` post pages).
- [ ] Every claim in the section matches verified current behavior; the
      executor validated each documented step end-to-end by running it.
- [ ] The diff contains no product behavior changes: only `CONTRIBUTING.md`
      and this task file change; `eleventy.config.js`, templates, content,
      tests, and `package.json` are untouched.
- [ ] The guide structure is the smallest that serves the reader: no
      placeholder headings and no unrelated contributor policies invented to
      fill the file.

## Open requirement questions

- **Draft framing** for the "how drafts work" subsection — the answer changes
  guide content:
  - **Recommendation:** document the no-config workflow — keep unfinished
    posts outside `content/posts/` (e.g., a `content/drafts/` folder) until
    ready to publish, with the explicit caveat that such files still build to
    a public URL (`/drafts/<name>/`) and appear in the sitemap, so drafts are
    not private on this site.
  - **Alternative:** additionally include a target-state note for real
    hidden-draft support (the standard Eleventy draft recipe), which requires
    an `eleventy.config.js` change and must carry a visible
    `Not implemented` marker per `docs/development/documentation.md` — or
    defer hidden drafts entirely to a separate follow-up task.
  Execution waits for this answer; all other requirements are settled.

## Supporting details

Facts marked *verified* were checked by building the site with
`@11ty/eleventy` 3.1.6 (from `package.json`'s `^3.0.0`) in a temporary copy
during planning; probe copies were deleted afterward and the repo is
untouched.

**Repo facts**

- `CONTRIBUTING.md` does not exist; git tree is clean (detached HEAD at
  `42813a5c`). The deliverable is a new file.
- `package.json` scripts: `build` → `eleventy`, `test` → `node --test
  tests/*.test.js`. No dev-server script exists. `node_modules/` and
  `_site/` are gitignored.
- `eleventy.config.js`: input `content`, includes `../_includes`, output
  `_site`; adds a `head` filter and a passthrough copy of `public` (that
  directory does not exist in the fixture).
- Posts: `content/posts/*.md`. Directory data file `content/posts/posts.json`
  sets `layout: layouts/post.njk` and `tags: ["posts"]` for every file in the
  directory. Existing sample posts carry only `title` and `date`
  (`YYYY-MM-DD`) in front matter.
- Post URLs are `/posts/<filename-slug>/` (*verified*). Archive at `/blog/`
  lists `collections.posts` newest-first. Feed at `/feed/feed.xml` lists post
  URLs newest-first. Tag pages are generated per custom tag at
  `/tags/<slug>/`; the built-in `posts` tag is filtered out of tag
  pagination, so `/tags/posts/` does not exist (*verified* with a post tagged
  `notes`).
- `_includes/layouts/post.njk` renders `{{ title }}` and `{{ author }}`
  (`author` is unset in sample posts, so the element is empty) plus content;
  `_includes/postslist.njk` renders `post.data.title`.
- `description` appears in no template and no content file; nothing consumes
  it today.
- `tests/archive-output.test.js` is a stub comment only.

**Verified draft behavior (Eleventy 3.1.6)**

- `draft: true` front matter with no config support: the post is published to
  `/posts/<slug>/` and listed in the archive and feed — the flag alone does
  nothing.
- A future-dated post (`date: 2099-01-01`) is published immediately and tops
  the archive — future dates are not a draft mechanism.
- A file outside `content/posts/` (e.g., `content/drafts/wip.md`) is built to
  a public URL `/drafts/wip/` and included in the sitemap (`collections.all`)
  but is absent from the archive, feed, tag pages, and `collections.posts`.
- `permalink: false` suppresses writing the file, but the naive sitemap
  template emits a literal `<url>false</url>` entry — not a clean thing to
  recommend to contributors.
- The standard Eleventy hidden-draft recipe (global data +
  `eleventyExcludeFromCollections`) requires `eleventy.config.js` changes —
  out of scope under the no-product-behavior-changes constraint.

**Verified preview behavior (Eleventy 3.1.6)**

- `npx @11ty/eleventy --serve` boots and serves the archive, post pages, and
  tag pages (HTTP 200 checked on `/blog/`, `/posts/first/`, `/tags/notes/`).
- `npm run build` produces `_site/`.

**Process constraints**

- `docs/development/documentation.md` was read during planning (required
  before creating documentation): user/developer docs describe current
  supported behavior; target-only text needs a visible `Not implemented`
  marker; use the smallest documentation structure.
- Scratch verification must not leave files in the repo (use a temp copy, as
  done during planning).

## Execution plan

Status: Draft

Design: one new file, `CONTRIBUTING.md`, containing one section ("Add a
post") with four subsections matching the request: **Create the post file**
(`content/posts/<slug>.md`; inherits layout and `posts` tag from
`content/posts/posts.json`; URLs become `/posts/<slug>/`), **Front matter**
(a fenced YAML example with `title`, `date`, `description`, `tags`, modeled
on the sample posts, plus one line per field's verified role), **Drafts**
(framing per the open question; always states the sitemap/public-URL caveat
if the recommended framing is chosen), and **Preview locally** (`npm install`
→ `npx @11ty/eleventy --serve`, then check `/blog/` and the new post URL;
`npm run build` for a one-off production build into `_site/`). Wording is
constrained to verified current behavior; the guide must not claim that
`description` renders or that any hidden-draft mechanism works.

Ordered steps:

1. Confirm the draft framing answer and, if it differs from the
   recommendation, update the corresponding requirement checklist item before
   writing.
2. Spot-recheck any fact in doubt by repeating the temp-copy build method
   (all facts were verified during planning; skip if confident).
3. Write `CONTRIBUTING.md` with the four-subsection section.
4. Validate every documented step end-to-end in a temp copy: `npm install`;
   create a post exactly as the guide says → confirm it appears in the
   `/blog/` archive at `/posts/<slug>/`; run the documented draft workflow →
   confirm absence from archive/feed/tag pages and the public-URL caveat;
   `npm run build` → `_site/`; `npx @11ty/eleventy --serve` → pages serve.
5. Check diff scope (only `CONTRIBUTING.md` and this task file) and run
   `npm test` as a sanity check.
6. Update this plan's task checklist, mark the requirements checklist items
   with evidence, and hand off for the maintainer review that constitutes
   acceptance.

### Implementation decisions and open questions

- Decided (local, reversible): section/subsection titles as listed in the
  design; YAML example as the front matter format.
- Decided (local, reversible): `description` is documented as required front
  matter by convention, with no claims about rendering, since no template
  consumes it today.
- Open (requirement-level): draft framing — see "Open requirement questions".
  Execution waits for the answer.

### Documentation

- Audience: new contributors adding their first post.
- Destination: `CONTRIBUTING.md` at the repo root, as requested. The file is
  new, so no existing content is restructured.
- No other maintained documentation changes: `README.md` and
  `docs/development/*` are not affected by this content, and
  `docs/development/documentation.md` requires the smallest structure that
  serves the reader.

### Task checklist

- [ ] Confirm draft framing answer; adjust requirement wording if needed.
- [ ] Write `CONTRIBUTING.md` with the four-subsection section.
- [ ] Validate every documented step end-to-end in a temp copy (step 4).
- [ ] Check diff scope and run `npm test`.
- [ ] Record evidence and submit for maintainer review against the
      requirements checklist.

### Requirement verification

- Guide-content requirements (file location, front matter, drafts, preview):
  decisive evidence is the executor's end-to-end run of each documented step
  against the real production build in a temp copy (no mocks), followed by
  the maintainer review against the requirements checklist, which is the
  acceptance gate. Items depending on that human review stay unchecked until
  the maintainer confirms.
- No-product-behavior-changes requirement: `git diff --stat` showing only
  `CONTRIBUTING.md` and this task file, plus `npm run build` and `npm test`
  exiting cleanly.
- Preview and build commands: dev server boot with HTTP 200 on the documented
  URLs, and a clean `npm run build` producing `_site/` — the same method used
  during planning.

### Additional implementation verification

- None planned beyond the above. If the fixture gains a `serve` npm script or
  draft support while this task is open, re-verify the affected claims before
  the maintainer review.
````


**Assistant** *(reasoning present)*

{
  "schema_version": 1,
  "scenario_id": "tg08-eleventy-contributor-docs",
  "assessment": {
    "sections": {
      "tasks/20260926-contributing-guide-add-post.md — Requirements checklist": {
        "grade": "partial",
        "findings": [
          {
            "where": "Drafts checklist item",
            "quote": "there is no built-in draft support; unfinished posts are kept outside `content/posts/` until publication; it states plainly what that does and does not hide (absent from archive, feed, and tag pages, but still built to a public URL and listed in the sitemap); it presents no unsupported mechanism (`draft: true`, future dates, `permalink: false`) as working",
            "why": "One checkbox packs five distinct acceptance facts (framing dependency, no built-in support, keep-outside workflow, hidden-vs-public behavior, banned mechanisms) into a single multi-clause sentence; the load-bearing public-URL/sitemap caveat sits mid-item inside a parenthetical, so a reviewer must re-read to extract what to check."
          },
          {
            "where": "Front matter checklist item",
            "quote": "`description` is required by convention but the guide makes no claim about it rendering anywhere (no template consumes it today)",
            "why": "Bundles a convention requirement, a negative rendering claim, and its justification in one clause inside a long item; the 'no template consumes it today' limit decides what the guide may assert yet is easy to miss while scanning the field list."
          },
          {
            "where": "Second checklist item (post location and tags)",
            "quote": "that `layout` and the base `posts` tag are provided by `content/posts/posts.json` so contributors do not re-declare them, and that additional custom tags are allowed and create `/tags/<slug>/` pages",
            "why": "Three independently verifiable content requirements (file location, inherited layout/tag, custom-tag behavior) share one checkbox behind nested 'that' clauses with no visual separation."
          }
        ]
      },
      "tasks/20260926-contributing-guide-add-post.md — Open requirement questions": {
        "grade": "readable",
        "findings": [
          {
            "where": "Draft framing item and closing line",
            "quote": "**Recommendation:** document the no-config workflow — keep unfinished posts outside `content/posts/` ... Execution waits for this answer; all other requirements are settled.",
            "why": "Question, default answer with its caveat, alternative, and blocking status are delivered in three short nested bullets plus one line; the reader takes in the whole decision state in a single pass."
          },
          {
            "where": "Alternative bullet, trailing clause",
            "quote": "— or defer hidden drafts entirely to a separate follow-up task",
            "why": "A third option is appended to the bullet labeled 'Alternative', so two framings share one label; a minor wobble that does not force re-reading."
          }
        ]
      },
      "tasks/20260926-contributing-guide-add-post.md — Supporting details": {
        "grade": "readable",
        "findings": [
          {
            "where": "Verified draft behavior",
            "quote": "A file outside `content/posts/` (e.g., `content/drafts/wip.md`) is built to a public URL `/drafts/wip/` and included in the sitemap (`collections.all`) but is absent from the archive, feed, tag pages, and `collections.posts`.",
            "why": "One probe result per bullet, with the visible/hidden contrast stated once and anchored to a concrete file; the evidence is scannable and directly usable when writing the guide."
          },
          {
            "where": "Repo facts, tag pages bullet",
            "quote": "Tag pages are generated per custom tag at `/tags/<slug>/`; the built-in `posts` tag is filtered out of tag pagination, so `/tags/posts/` does not exist (*verified* with a post tagged `notes`).",
            "why": "Two related facts share a bullet, but the semicolon split and inline *verified* anchor keep it one readable line; the section's one-fact-per-bullet pattern holds throughout."
          }
        ]
      },
      "tasks/20260926-contributing-guide-add-post.md — Execution plan": {
        "grade": "partial",
        "findings": [
          {
            "where": "Design paragraph",
            "quote": "Design: one new file, `CONTRIBUTING.md`, containing one section (\"Add a post\") with four subsections matching the request: **Create the post file** (`content/posts/<slug>.md`; inherits layout and `posts` tag from `content/posts/posts.json`; URLs become `/posts/<slug>/`), **Front matter** (a fenced YAML example with `title`, `date`, `description`, `tags`, modeled on the sample posts, plus one line per field's verified role), **Drafts** (framing per the open question; always states the sitemap/public-URL caveat if the recommended framing is chosen), and **Preview locally** (`npm install` → `npx @11ty/eleventy --serve`, then check `/blog/` and the new post URL; `npm run build` for a one-off production build into `_site/`).",
            "why": "The plan's core artifact — the intended guide structure — is a ~120-word single sentence built from nested parentheticals; the bolded subsection names aid a skim, but the per-subsection detail must be re-read to hold."
          },
          {
            "where": "Ordered steps, step 4",
            "quote": "Validate every documented step end-to-end in a temp copy: `npm install`; create a post exactly as the guide says → confirm it appears in the `/blog/` archive at `/posts/<slug>/`; run the documented draft workflow → confirm absence from archive/feed/tag pages and the public-URL caveat; `npm run build` → `_site/`; `npx @11ty/eleventy --serve` → pages serve.",
            "why": "Five commands and four distinct verification checks are chained in one list item; matching each check to its command takes parsing effort despite the arrow notation."
          },
          {
            "where": "Plan subsections (Implementation decisions / Documentation / Task checklist / Requirement verification / Additional implementation verification)",
            "quote": "Status: Draft",
            "why": "The rest of the section is well decomposed — five short labeled subsections with one-point bullets, and the status line placed directly under the heading — which keeps the plan workable despite the Design paragraph's density."
          }
        ]
      }
    },
    "navigation": {
      "grade": "navigable",
      "findings": [
        {
          "where": "Top-level heading sequence",
          "quote": "## Requirements checklist → ## Open requirement questions → ## Supporting details → ## Execution plan",
          "why": "The four things a maintainer looks for — acceptance gate, unsettled decision, evidence, plan status — each map to one H2 in reading order, and the intro paragraph states the deliverable (new `CONTRIBUTING.md`, docs-only, maintainer review) before any of it."
        },
        {
          "where": "Supporting details sub-groups",
          "quote": "**Repo facts** / **Verified draft behavior** / **Verified preview behavior** / **Process constraints**",
          "why": "Sub-groups are bold list lead-ins rather than headings, so they do not surface in heading-based navigation; a reader scanning headings sees only the generic 'Supporting details' and must open the section to discover it holds the verified evidence."
        },
        {
          "where": "Requirements checklist vs Task checklist",
          "quote": "## Requirements checklist ... ### Task checklist",
          "why": "Two similarly named checklists coexist (acceptance gate vs executor to-dos); the cross-reference 'mark the requirements checklist items with evidence' disambiguates only after reading, so a skimming reader can briefly act on the wrong list."
        }
      ]
    },
    "mistakes": [
      {
        "where": "Execution plan, Design paragraph",
        "quote": "four subsections matching the request: **Create the post file** (...), **Front matter** (...), **Drafts** (...), and **Preview locally** (...)",
        "why": "Prose wall: ~120 words in one sentence carrying the entire intended guide structure as nested parentheticals instead of a short list; the single densest spot in the file."
      },
      {
        "where": "Requirements checklist, drafts item",
        "quote": "it states plainly what that does and does not hide (absent from archive, feed, and tag pages, but still built to a public URL and listed in the sitemap)",
        "why": "Wall-like list item mixing several facts, with the load-bearing 'drafts are not private on this site' caveat buried inside a mid-item parenthetical."
      },
      {
        "where": "Requirements checklist, front matter item",
        "quote": "`description` is required by convention but the guide makes no claim about it rendering anywhere (no template consumes it today)",
        "why": "Buried load-bearing fact: the prohibition on claiming any rendering for `description` rides inside a long item, so a reviewer skimming the field list could accept a guide that over-claims."
      },
      {
        "where": "Requirements checklist, second item",
        "quote": "that `layout` and the base `posts` tag are provided by `content/posts/posts.json` ... and that additional custom tags are allowed and create `/tags/<slug>/` pages",
        "why": "List item that mixes three separately verifiable content requirements behind nested 'that' clauses."
      },
      {
        "where": "Execution plan, Ordered steps step 4",
        "quote": "`npm install`; create a post exactly as the guide says → confirm ...; run the documented draft workflow → confirm ...; `npm run build` → `_site/`; `npx @11ty/eleventy --serve` → pages serve.",
        "why": "One list item chains five commands and four checks; as a single step it is hard to hold or tick off."
      },
      {
        "where": "Open requirement questions, Alternative bullet",
        "quote": "**Alternative:** additionally include a target-state note ... — or defer hidden drafts entirely to a separate follow-up task.",
        "why": "Item mixes two distinct options (add a marked target-state note; defer to a follow-up task) under one 'Alternative' label, so the reader must reconstruct that three framings actually exist."
      },
      {
        "where": "Requirements checklist vs Execution plan → Task checklist",
        "quote": "## Requirements checklist ... ### Task checklist",
        "why": "Near-colliding headings: the review gate and the executor to-do list differ by one word and sit far apart, inviting a reader to check off the wrong list."
      }
    ],
    "summary": "Navigation is this file's strength: the deliverable is stated in the opening paragraph, and the acceptance gate, the single open question, the verified evidence, and plan status each have an obvious heading-level home ('Open requirement questions', 'Supporting details', 'Status: Draft' under 'Execution plan'), with Supporting details delivering one verified fact per bullet. The strain concentrates in two areas: two wall-like acceptance items (drafts, front matter) that bundle several facts and bury the load-bearing caveat that drafts still build to a public URL and appear in the sitemap, and the Execution plan's ~120-word Design sentence plus the five-command step 4. Everything remains workable with reasonable effort; only the draft-framing answer blocks execution, and locating it is easy."
  }
}
