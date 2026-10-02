# TG-08: Contributor documentation as a task

## Project

- Repository: Eleventy Base Blog
- Fixture: `tg01-eleventy-archive` (shared project state)
- Kind: public static website

## Purpose

Verify that a documentation-only task keeps documentation-shaped sections:
content and audience requirements, a review acceptance check, and no
mechanically filled software-test sections.

## Natural request

> New contributors keep asking how to add a post. Create the task for
> writing the contributor guide section in `CONTRIBUTING.md`: creating a
> post file, the front matter every post needs (title, date, description,
> tags), how drafts work, and how to preview the site locally. A
> maintainer review against the checklist in the task is the acceptance —
> no product behavior changes.

The prompt does not prescribe the section list of the task file, its
requirements wording, or its decomposition.

## Approved outcomes

Use `DOC-1`–`DOC-5` from the target. Writing style and example post
content remain the author's choices within the review.

## Expected task shape

- One task file.
- Requirements carry the content and audience requirements and the
  review acceptance; they do not invent behavior changes.
- Supporting details carry what the guide must cover and where it lives.
- Acceptance evidence is the maintainer review checklist — not unit
  tests, not a test-suite section.

## Task-kind fit

- Task kind: documentation.
- Applicable sections: requirements checklist, supporting details,
  execution plan (documentation work is planned work), questions and
  decisions.
- Acceptance evidence: maintainer review against the content checklist.
  Testing-boundary sections do not apply; filling them mechanically is a
  `forced` fit.
