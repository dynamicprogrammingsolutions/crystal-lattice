# Write user-facing copy for the Books app

This task defines and reviews concise, plain-language copy for the Books app's
primary user-facing states. It is a content task only: the task must not add
or change UI behavior, state transitions, API calls, persistence, or error
handling.

## Requirements checklist

- [ ] Provide a short introduction for the home page that explains the
  purpose of the Books app in plain language without inventing unsupported
  features.
- [ ] Provide the empty-state text shown when the book list contains no
  books.
- [ ] Provide a distinct empty-state text for a search that returns no
  results, making clear that the query had no matches.
- [ ] Provide a concise message for a failed book-list load.
- [ ] Provide a concise message for a failed book save.
- [ ] Keep all copy consistent with the app's existing concise, plain tone.
- [ ] Have a maintainer review the final copy against this brief and the style
  checklist below.
- [ ] Make no behavior changes as part of this task.

## Scope and copy brief

The final deliverable is the reviewed wording for five content contexts. The
wording is intentionally left for the copy author and maintainer to decide;
the contexts and user intent below are the acceptance boundary.

| Context | User intent the copy must support | Current status |
| --- | --- | --- |
| Home page introduction | Orient a first-time user and state what the app is for. | Not implemented |
| Book list with no books | Explain that there are no books in the current list. Do not imply that a search was performed. | Not implemented |
| Search with no results | Explain that the active search found no matching books. Keep this distinct from an empty library. | Not implemented |
| Loading a book list fails | Tell the user that the books could not be loaded. Do not promise a retry, recovery, or other action unless that action already exists. | Not implemented |
| Saving a book fails | Tell the user that the book could not be saved. Do not imply that the save succeeded or prescribe unsupported recovery steps. | Not implemented |

The component currently contains the placeholder `No books found.` for its
general empty state. The search and load/save failure contexts are not
represented in the current component, so this task records their target copy
without introducing those states or wiring them up.

## Style checklist

The maintainer should review every proposed string against all of the
following:

- [ ] Use everyday words and a direct sentence structure.
- [ ] Be concise enough to scan quickly in the relevant UI state.
- [ ] Name the relevant subject plainly (`books` or `book`) instead of using
  vague phrases such as “something went wrong.”
- [ ] Match the app's neutral, helpful tone; avoid marketing language,
  enthusiasm, blame, and unnecessary apology.
- [ ] Describe the current state truthfully and avoid claiming an action,
  result, or recovery path that the app does not provide.
- [ ] Keep the empty library and no-search-results meanings distinct.
- [ ] Use consistent capitalization, punctuation, and terminology across all
  strings.
- [ ] Avoid technical implementation terms, internal error details, and
  placeholder wording.
- [ ] Check that the text remains understandable when shown without
  additional context.

## Requirement questions and decisions

There are no unresolved requirement questions. The request specifies the
content contexts, tone, review gate, and copy-only boundary; exact wording is
the maintainer-approved design outcome.

Decisions:

- Treat the unfiltered empty list and a search with no matches as separate
  messages.
- Keep failure messages factual and non-committal about recovery because no
  retry or recovery interaction is in scope.
- Do not add a new copy system, localization layer, component, or interaction
  solely to hold these strings.

## Supporting facts

- `README.md` describes a Vue Books page backed by a Flask JSON API.
- `client/src/components/Books.vue` currently renders the general empty-state
  placeholder and has book filtering, but no search, loading-failure, or
  save-failure copy.
- `docs/development/index.md` states that no book-discovery specification
  exists.
- No maintained user or developer documentation needs updating for this
  copy-only task; the task itself is the reviewed content brief.

## Execution plan

Status: Draft

Draft the five strings as a small, labeled copy set, preserving the contexts
and intent in the brief. Review the draft as a complete set so terminology,
punctuation, and tone remain consistent. A maintainer then checks every
string against the brief and style checklist, records approval or requested
edits, and confirms that the resulting change contains copy planning only.

The copy should be written so it can later replace the relevant placeholders
or be supplied to the owner of any future search and failure-state surfaces.
That later integration is outside this task unless separately authorized; no
component logic, rendering conditions, API transport, or error behavior is to
be changed here.

### Implementation decisions and open questions

The task remains Draft until execution is explicitly approved. Exact strings
are intentionally not prescribed in advance. The maintainer's review is
required because the acceptance criteria are primarily linguistic and
user-facing rather than behavioral.

### Documentation

No documentation update is planned. This task does not change supported
behavior or a documented interface. If the approved copy is later integrated
into a user guide, that guide should be updated in the separate integration
change.

### Task checklist

- [ ] Draft one candidate string for each of the five contexts.
- [ ] Check the candidates against the copy brief.
- [ ] Check the candidates against every item in the style checklist.
- [ ] Revise any wording that is ambiguous, repetitive, or unsupported.
- [ ] Obtain maintainer review and record the accepted copy.
- [ ] Confirm that no source, test, API, or behavior changes were included.

### Requirement verification

- Home introduction, both empty states, and both failure messages: maintainer
  review of the labeled five-string copy set against the brief and style
  checklist.
- Concise, plain tone and consistent terminology: the same maintainer review,
  with each style-checklist item explicitly checked.
- No behavior changes: review the final diff and confirm it is limited to the
  copy task artifact.

All listed requirements require human maintainer verification and remain
incomplete until that review is recorded.