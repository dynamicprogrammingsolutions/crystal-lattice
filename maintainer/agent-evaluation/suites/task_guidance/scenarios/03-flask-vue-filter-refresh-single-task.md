# TG-03: Flask/Vue selected-filter refresh bug as one task

## Project

- Repository: Flask-Vue CRUD
- Revision: `be91da59a10d07384537c2f76f4505eb344d1682`
- Kind: user-facing full-stack web application

## Purpose

Verify that a bounded full-stack regression remains one cohesive task and that
the task preserves the UI, transport, server, and mutation-refresh crossing.

## Starting state

The executable fixture will derive from the pinned repository and add the
smallest deterministic pre-task state needed for this regression:

- All/Read/Unread controls and visible active state already exist;
- the Flask collection route already supports the approved read filter;
- ordinary filter selection uses the production client transport correctly;
- add, update, and delete still call an older unfiltered refresh path.

The fixture change is reviewed and fixed across baseline/candidate runs. The
task asks only for the refresh-preservation fix, not initial filter
implementation.

## Natural request

> The Books page can show All, Read, or Unread books, but after adding,
> editing, or deleting a book the refresh falls back to the unfiltered list.
> Keep the selected filter visibly active and reapply it whenever CRUD
> refreshes the collection. Preserve the existing API response shape and
> unfiltered behavior. Plan the fix and create the appropriate task structure
> without implementing it.

## Approved outcomes

- `REFRESH-1`: the selected All/Read/Unread filter remains selected after add,
  update, and delete refreshes;
- `REFRESH-2`: refresh requests use the selected filter through the production
  client transport and Flask collection endpoint;
- `REFRESH-3`: the active choice remains visibly identifiable and the table or
  empty state reflects the refreshed filtered response;
- `REFRESH-4`: existing CRUD success behavior, response shape, and unfiltered
  list behavior remain compatible.

Unknown query-value behavior, URL persistence, a state-management library, and
UI redesign are not approved outcomes.

## Canonical plan

1. Inspect filter ownership, refresh call paths after each mutation, client
   transport construction, and Flask route behavior.
2. Keep the selected filter in the existing suitable UI state boundary.
3. Route every mutation-triggered refresh through the same filter-aware fetch
   path.
4. Preserve active-state and empty-result rendering.
5. Add focused server/client evidence plus one production transport/HTTP
   crossing for representative refresh behavior.
6. Preserve existing unfiltered and CRUD behavior.

## Expected task shape

- One task file.
- No frontend/backend/test subtasks: all parts are required before the
  regression is fixed.
- Requirements contain four outcomes rather than one row per CRUD operation.

## Handoff variants

Retained-plan and omit-plan variants preserve the refresh call-path facts,
selected-state owner, public response constraints, and production crossing.
The omit variant excludes the proposed shared fetch-path implementation.

## Continuation target

A fresh agent reconstructs one cohesive plan, groups add/update/delete as
variants of one refresh outcome, and names a real client-transport-to-Flask
check.

## Important crossing

Vue selection and refresh behavior must produce the expected request through
the production transport and render the Flask response.

## Efficiency use

Use this scenario for same-agent versus fresh-agent comparison.

## Human review

- Did the agent resist splitting by frontend/backend/test phases?
- Is active-choice visibility a requirement rather than a recommendation?
- Is CRUD refresh behavior grouped without hiding any mutation path?