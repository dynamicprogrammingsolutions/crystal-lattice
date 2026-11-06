# Contributor guide: adding a post (`CONTRIBUTING.md`)

Write the contributor guide section that answers "how do I add a post?" in a
new root-level `CONTRIBUTING.md`, aimed at new contributors. Coverage is fixed
by the user request: creating a post file, required front matter (title, date,
description, tags), how drafts work, and local preview. Documentation only —
no product behavior changes. **Acceptance is a maintainer review against the
requirements checklist below**, supported by the writer's recorded command
runs.

## Requirements checklist

- [ ] `CONTRIBUTING.md` exists at the repository root and contains one
      contributor-facing guide section covering adding a post. No other files
      are created for this guide (smallest structure that serves the audience).
- [ ] The section documents creating a post file: Markdown files live in
      `content/posts/` and accurately describes what the site provides
      automatically versus what the author supplies (see supporting facts on
      `posts.json` directory data).
- [ ] The section documents the front matter every post needs — `title`,
      `date`, `description`, `tags` — with a working example. Claims match
      current behavior: nothing may be asserted to display or be published
      that the current templates/config do not do.
- [ ] The section documents how drafts work in this site, matching actual
      behavior. There is no draft mechanism implemented today; the text must
      say so plainly and give the practical consequence (a file committed to
      `content/posts/` is built and published). Any target-state draft
      workflow (e.g. upstream's `draft: true`) may appear only with a visible
      `Not implemented` marker.
- [ ] The section documents how to preview the site locally using commands
      that exist and were run successfully by the writer: `npm run build`
      (output to `_site/`) and the Eleventy dev server. It must not reference
      an `npm run serve`-style script, because none exists.
- [ ] Every factual claim in the section was verified during this task, by
      running the documented commands and/or building a scratch post with the
      documented front matter and inspecting the output.
- [ ] The guide follows repo documentation rules
      (`docs/development/documentation.md` read before writing; current
      supported behavior only; no placeholder content).
- [ ] Final diff touches only `CONTRIBUTING.md`; scratch posts and build
      output used for verification are removed.

## Scope

- In scope: one new file `CONTRIBUTING.md` (repo root), one guide section,
  verification runs recorded in this file's Implementation Notes.
- Out of scope: code, templates, config, `package.json` scripts, existing
  posts, tests, CI, and any draft-mechanism implementation. Adding fields
  other than the four required ones to posts (e.g. `author`, which
  `post.njk` renders but no post sets) is out of scope.

## Requirement questions and decisions

- Decision (recorded, derived from "no product behavior changes" + current
  state): "how drafts work" is documented as the truthful current state —
  no draft flag or exclusion mechanism exists, so anything in
  `content/posts/` publishes on build. If the maintainer intended a real
  draft workflow, that is a product change and a separate task; raise it in
  review rather than implementing it here.

## Supporting facts (verified by reading the repo)

- Eleventy 3 (`@11ty/eleventy ^3.0.0`). Config (`eleventy.config.js`): input
  `content/`, includes `../_includes`, output `_site/`, plus `head` filter and
  `public` passthrough.
- `content/posts/posts.json` directory data applies to every file in
  `content/posts/`: `layout: layouts/post.njk` and `tags: ["posts"]`.
- Existing posts (`first.md`, `second.md`) set `title` and `date` and repeat
  `tags: [posts]`; none sets `description`. The guide's front matter example
  must not contradict the directory data.
- No template consumes `description` today (`post.njk` renders `title`,
  `author`, content; `postslist.njk` renders `title` + `url`). Document
  `description` as the required convention without claiming it is rendered.
- No draft mechanism: no `draft:` handling, `eleventyExcludeFromCollections`,
  or permalink override anywhere in the fixture. Upstream Eleventy Base Blog
  (`UPSTREAM.md`) has draft support, but this compact fixture does not.
- `package.json` scripts: `build` = `eleventy`, `test` = `node --test
  tests/*.test.js`. No serve/start script; the dev server is
  `npx @11ty/eleventy --serve`.
- `tests/archive-output.test.js` currently contains only a comment (collects
  no tests), so documentation changes have no automated coverage; acceptance
  is the maintainer review plus the writer's recorded runs.
- `README.md` claims pages (feed, sitemap, tag pages) whose templates are not
  present in this fixture. Do not repeat or extend those claims in the guide;
  stick to post-authoring facts observed in this task.

## Execution plan

Status: Draft

### Approach

Create `CONTRIBUTING.md` at the repo root (standard location for the
contributor audience; the file does not exist yet) with a single guide
section, structured as: create the post file → required front matter (with a
copyable example) → drafts → preview locally. Tone and length: minimal,
example-driven, no scaffolding prose.

Component/content design:

- *Creating a post file*: state the directory (`content/posts/`), the file
  format (Markdown with YAML front matter), and that `layout` and the
  `posts` tag are supplied by `content/posts/posts.json`, so a new post does
  not need to set them.
- *Front matter*: one fenced example showing `title`, `date` (YYYY-MM-DD),
  `description`, `tags`; prose for each field explaining its purpose.
  Because nothing renders `description` today, describe it as the convention
  for a short summary, not as displayed output.
- *Drafts*: plain statement that there is no draft flag in this site; a file
  saved in `content/posts/` is included in the next build and published.
  Practical guidance: keep unpublished writing outside `content/posts/`.
  Optionally one sentence about upstream's `draft: true` with a
  `Not implemented` marker, per repo documentation rules.
- *Preview locally*: `npm run build` (inspect `_site/`) and
  `npx @11ty/eleventy --serve` for the local dev server, using the exact
  behavior observed when running them. No invented scripts or URLs.

Verification strategy: after drafting, run `npm run build` (expect a clean
exit); add a temporary scratch post in `content/posts/` using exactly the
documented front matter, rebuild/serve, confirm it renders and appears in
listings; run `npx @11ty/eleventy --serve` and confirm the documented preview
experience; then delete the scratch post and confirm the final diff contains
only `CONTRIBUTING.md`. Record command results in Implementation Notes.

### Implementation decisions and open questions

- File location: repo root `CONTRIBUTING.md` (audience is contributors;
  matches repository convention). Decided.
- Drafts content: truthful "no mechanism" statement, optional marked
  target-state note. Decided (see Requirement questions and decisions).
- Whether to include a short "checks before you push" line (`npm run build`,
  `npm test`) at the end of the section: writer's call during execution; keep
  only if both commands were run successfully as part of this task.
- Open question for maintainer review (not blocking): if a real draft
  workflow is wanted, it requires product/config changes and a new task.

### Documentation

- Deliverable: `CONTRIBUTING.md` (new), audience: new contributors.
- Per repo rules, this is user/developer documentation describing current
  supported behavior; any target-only text carries `Not implemented`.
- No other maintained documentation is affected by a docs-only change;
  `docs/development/documentation.md` must be read before writing (required
  by repo guidance and restated in the checklist).

### Task checklist

- [ ] Read `docs/development/documentation.md` and `README.md`.
- [ ] Draft `CONTRIBUTING.md` with the single guide section per the approach.
- [ ] Run `npm run build`; record result in Implementation Notes.
- [ ] Add scratch post with the documented front matter; build and confirm
      rendering/listing; run `npx @11ty/eleventy --serve` and confirm the
      preview instructions match observed behavior.
- [ ] Remove the scratch post and any build output; verify final diff is
      `CONTRIBUTING.md` only.
- [ ] Tick requirement checkboxes as evidence lands; leave the maintainer
      review item outcomes to the reviewer.
- [ ] Present the diff to the maintainer for review against the requirements
      checklist (this is the acceptance gate).

### Requirement verification

- Checklist items 1–5 and 7 (content, accuracy, structure): evidence is the
  maintainer review of `CONTRIBUTING.md` against this checklist — the
  designated acceptance — supported by the writer's Implementation Notes.
- Checklist item 6 (claims verified): evidence is the recorded build/serve
  runs and scratch-post inspection in Implementation Notes.
- Checklist item 8 (diff hygiene): evidence is `git status` / `git diff`
  showing only `CONTRIBUTING.md`.
- No automated test covers documentation content in this fixture
  (`tests/archive-output.test.js` collects no tests), so no test gate applies
  to this task; the existing suite is not a meaningful signal either way.

### Additional implementation verification

- None planned beyond the runs above. If the build or serve command exposes
  behavior that contradicts a supporting fact above, stop, record the
  finding, and reconcile the guide text before review.
