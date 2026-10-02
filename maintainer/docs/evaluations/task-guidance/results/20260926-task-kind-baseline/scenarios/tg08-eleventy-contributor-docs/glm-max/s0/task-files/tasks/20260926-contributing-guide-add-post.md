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