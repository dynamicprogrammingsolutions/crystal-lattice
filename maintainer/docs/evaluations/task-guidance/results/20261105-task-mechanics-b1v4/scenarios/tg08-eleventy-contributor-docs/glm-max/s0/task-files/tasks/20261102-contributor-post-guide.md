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
