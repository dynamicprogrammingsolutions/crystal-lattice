# Session — tg08-eleventy-contributor-docs · file-readability-assessment-glm-max-s0 · glm max

- Run: `20261029T235235.900097Z-task-guidance-file-readability-tg08-eleventy-contributor-docs-glm-max-s0-0337ace7`
- Model: glm-5.3-flash (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-c440c4f661a7.md) — captured (original SHA-256 `6ec0e2a17759b0de…`)
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

#### tasks/20261029-contributing-post-authoring-guide.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261029-contributing-post-authoring-guide.md — Requirements checklist | 286 | 0 | 0 | 8 | 12 | 0 | 0 | 0 | 15 |
| tasks/20261029-contributing-post-authoring-guide.md — Scope | 60 | 0 | 0 | 2 | 12 | 0 | 0 | 0 | 4 |
| tasks/20261029-contributing-post-authoring-guide.md — Requirement questions and decisions | 63 | 0 | 0 | 1 | 11 | 0 | 0 | 0 | 1 |
| tasks/20261029-contributing-post-authoring-guide.md — Supporting facts (verified by reading the repo) | 199 | 0 | 0 | 8 | 12 | 0 | 0 | 0 | 35 |
| tasks/20261029-contributing-post-authoring-guide.md — Execution plan | 655 | 3 | 62 | 23 | 15 | 6 | 0 | 0 | 38 |

The produced task files:

### tasks/20261029-contributing-post-authoring-guide.md

````markdown
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
````


**Assistant** *(reasoning present)*

```json
{
  "schema_version": 1,
  "scenario_id": "tg08-eleventy-contributor-docs",
  "assessment": {
    "sections": {
      "tasks/20261029-contributing-post-authoring-guide.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "Requirements checklist, item 4 (drafts)",
            "quote": "There is no draft mechanism implemented today; the text must say so plainly and give the practical consequence (a file committed to `content/posts/` is built and published). Any target-state draft workflow (e.g. upstream's `draft: true`) may appear only with a visible `Not implemented` marker.",
            "why": "One checkbox item packs the current-state claim, the required phrasing, the practical consequence, and the marker rule — roughly double the load of its sibling items. Still parseable, but it is the one item a reviewer must slow down for."
          },
          {
            "where": "Requirements checklist, item 2",
            "quote": "The section documents creating a post file: Markdown files live in `content/posts/` and accurately describes what the site provides automatically versus what the author supplies",
            "why": "The colon promises a specification, then the sentence pivots to a second verb phrase (\"and accurately describes\"), so the requirement needs a second read to parse cleanly."
          }
        ]
      },
      "tasks/20261029-contributing-post-authoring-guide.md — Scope": {
        "grade": "readable",
        "findings": [
          {
            "where": "Scope, out-of-scope item",
            "quote": "Out of scope: code, templates, config, `package.json` scripts, existing posts, tests, CI, and any draft-mechanism implementation. Adding fields other than the four required ones to posts (e.g. `author`, which `post.njk` renders but no post sets) is out of scope.",
            "why": "A seven-item exclusion list plus a second, more specific exclusion with a parenthetical rationale share one bullet, and \"out of scope\" is stated twice. At 60 words the section absorbs this, but the second sentence partially repeats the first instead of extending it."
          }
        ]
      },
      "tasks/20261029-contributing-post-authoring-guide.md — Requirement questions and decisions": {
        "grade": "readable",
        "findings": [
          {
            "where": "Requirement questions and decisions, single item",
            "quote": "Decision (recorded, derived from \"no product behavior changes\" + current state): \"how drafts work\" is documented as the truthful current state — no draft flag or exclusion mechanism exists, so anything in `content/posts/` publishes on build.",
            "why": "The entire section is one ~70-word bullet carrying the decision, its derivation, its content consequence, and the escalation path. Nothing exceeds a reader's hold at this size, but there is no internal structure to scan."
          }
        ]
      },
      "tasks/20261029-contributing-post-authoring-guide.md — Supporting facts (verified by reading the repo)": {
        "grade": "readable",
        "findings": [
          {
            "where": "Supporting facts, item 1",
            "quote": "Eleventy 3 (`@11ty/eleventy ^3.0.0`). Config (`eleventy.config.js`): input `content/`, includes `../_includes`, output `_site/`, plus `head` filter and `public` passthrough.",
            "why": "Six distinct facts (version plus five config settings) share one bullet — the densest line of the section. The code spans keep it lookup-friendly for a developer, but it is a fact pile rather than a statement."
          },
          {
            "where": "Supporting facts, items 3, 4 and 8",
            "quote": "Document `description` as the required convention without claiming it is rendered.",
            "why": "Several bullets mix an observed fact with a writing directive (\"must not contradict\", \"Do not repeat or extend those claims\"), so a reader skimming for facts versus rules must separate two registers within the same list."
          }
        ]
      },
      "tasks/20261029-contributing-post-authoring-guide.md — Execution plan": {
        "grade": "partial",
        "findings": [
          {
            "where": "Execution plan → Approach, verification strategy paragraph",
            "quote": "Verification strategy: after drafting, run `npm run build` (expect a clean exit); add a temporary scratch post in `content/posts/` using exactly the documented front matter, rebuild/serve, confirm it renders and appears in listings; run `npx @11ty/eleventy --serve` and confirm the documented preview experience; then delete the scratch post and confirm the final diff contains only `CONTRIBUTING.md`.",
            "why": "Five ordered steps are chained with semicolons inside one ~62-word sentence (the measured longest paragraph), so extracting the sequence takes a re-read. The identical steps reappear as the Task checklist below, forcing the reader to diff two versions to learn which is authoritative."
          },
          {
            "where": "Execution plan → Approach, drafts bullet",
            "quote": "*Drafts*: plain statement that there is no draft flag in this site; a file saved in `content/posts/` is included in the next build and published.",
            "why": "The drafts guidance is specified here, in Requirements checklist item 4, and in Requirement questions and decisions, each with slightly different wording; the reader must cross-check all three to confirm they agree before acting on any one."
          },
          {
            "where": "Execution plan → Implementation decisions and open questions",
            "quote": "Whether to include a short \"checks before you push\" line (`npm run build`, `npm test`) at the end of the section: writer's call during execution; keep only if both commands were run successfully as part of this task.",
            "why": "An undecided item sits between two items explicitly marked \"Decided\"; the labels carry the distinction, but a reader scanning for the decisions must read each item to its tail to learn its status."
          }
        ]
      }
    },
    "navigation": {
      "grade": "navigable",
      "findings": [
        {
          "where": "Overall file structure",
          "quote": "Status: Draft",
          "why": "Headings are specific and match their content, the acceptance gate is bolded in the intro, and plan status sits directly under the Execution plan heading — outcome, constraints, facts, and status are each reachable from structure alone."
        },
        {
          "where": "Requirement questions and decisions heading",
          "quote": "## Requirement questions and decisions",
          "why": "The heading promises questions, but the section holds only a recorded decision; the file's actual open question lives one level deeper under Execution plan → \"Implementation decisions and open questions\", so a reader hunting open questions must visit two headings."
        }
      ]
    },
    "mistakes": [
      {
        "where": "Execution plan → Approach, verification strategy paragraph",
        "quote": "Verification strategy: after drafting, run `npm run build` (expect a clean exit); add a temporary scratch post in `content/posts/` using exactly the documented front matter, rebuild/serve, confirm it renders and appears in listings; ...",
        "why": "Prose step-chain: a five-step ordered procedure compressed into one sentence with semicolons, then duplicated nearly verbatim as the Task checklist — the reader pays twice, once to parse it and once to reconcile it."
      },
      {
        "where": "Requirements checklist item 4 / Requirement questions and decisions / Execution plan → Approach drafts bullet",
        "quote": "Any target-state draft workflow (e.g. upstream's `draft: true`) may appear only with a visible `Not implemented` marker.",
        "why": "The drafts rule — current state, consequence, and marker requirement — is stated in three sections with shifting wording; triplication invites divergence and makes the reader cross-check rather than trust any single statement."
      },
      {
        "where": "Requirements checklist, item 2",
        "quote": "The section documents creating a post file: Markdown files live in `content/posts/` and accurately describes what the site provides automatically versus what the author supplies",
        "why": "Broken parallelism after the colon makes a load-bearing accuracy requirement hard to parse on first read."
      },
      {
        "where": "Supporting facts, item 1",
        "quote": "Config (`eleventy.config.js`): input `content/`, includes `../_includes`, output `_site/`, plus `head` filter and `public` passthrough.",
        "why": "List item mixing several facts: six independent repo facts in one bullet, with no separation between what matters for the guide (output dir, input dir) and incidental detail (head filter, passthrough)."
      },
      {
        "where": "Requirement questions and decisions heading vs Execution plan → Implementation decisions and open questions",
        "quote": "Open question for maintainer review (not blocking): if a real draft workflow is wanted, it requires product/config changes and a new task.",
        "why": "Heading-content mismatch by omission: the section titled for questions contains only a decision, so the file's one genuinely open question is filed under the Execution plan where a reader scanning for open questions may not look."
      },
      {
        "where": "Supporting facts, items 3, 4 and 8",
        "quote": "Do not repeat or extend those claims in the guide; stick to post-authoring facts observed in this task.",
        "why": "Buried load-bearing rules: prohibitions and writing directives that shape the deliverable are embedded in a list the reader reads as reference facts, rather than surfaced in the requirements checklist where obligations live."
      }
    ],
    "summary": "The file is a competently structured task doc whose smaller sections — Requirements checklist, Scope, Requirement questions and decisions, Supporting facts — are all readable at their measured sizes: short bullets, code spans that aid lookup, and headings that match content. The strain concentrates in the Execution plan (655 words): the verification-strategy paragraph chains five ordered steps through one 62-word sentence and then repeats them as the Task checklist, and the drafts guidance is triplicated across three sections with shifting wording, so the reader must reconcile versions instead of trusting any one. Navigation stays navigable because every kind of content has an accurately labeled home; the only structural detour is that the file's open question sits under the Execution plan rather than in the section titled for questions."
  }
}
```
