# TG-10: User-facing copy as a task

## Project

- Repository: Flask/Vue books app
- Fixture: `tg03-flask-vue-refresh` (shared project state)
- Kind: Python/Vue sample application

## Purpose

Verify that a content task keeps content-shaped sections: a brief with
audience, tone, and surface inventory, and style review as acceptance —
without inventing behavior changes or test evidence.

## Natural request

> The books app still shows placeholder texts. Create the task for writing
> the user-facing copy: the home page introduction, the empty-state texts
> for the book list and for search with no results, and the messages shown
> when loading or saving a book fails. The copy follows the existing
> concise, plain tone of the app; a maintainer reviews it against the brief
> and the style checklist in the task. No behavior changes.

The prompt does not prescribe the task file's sections, requirements
wording, or decomposition.

## Approved outcomes

Use `COPY-1`–`COPY-6` from the target. The concrete copy wording is the
author's work within the brief.

## Expected task shape

- One task file.
- Requirements carry the brief: surfaces, audience, tone constraint, and
  the review acceptance.
- Supporting details carry the style rules and the surface inventory with
  their current placeholder behavior.
- Acceptance evidence is the maintainer's brief-and-style review — not
  unit tests, not behavior changes.

## Task-kind fit

- Task kind: content.
- Applicable sections: requirements checklist, supporting details,
  execution plan (writing and review are planned work), questions and
  decisions.
- Acceptance evidence: review against brief and style checklist.
