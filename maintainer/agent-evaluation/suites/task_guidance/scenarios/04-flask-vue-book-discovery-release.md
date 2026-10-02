# TG-04: Flask/Vue book-discovery release

## Project

- Base repository: Flask-Vue CRUD
- Base revision: `be91da59a10d07384537c2f76f4505eb344d1682`
- Kind: user-facing full-stack application

## Purpose

Expose excessive layer and phase fragmentation. The approved scope is large
enough to tempt separate schema, route, query, client, state, component, test,
integration, documentation, and review tasks, but its reviewed partition is a
small set of end-to-end product capabilities.

## Derived starting state

The fixed fixture retains the existing CRUD application and adds enough books
to make discovery behavior observable. It does not contain filtering, search,
pagination, or URL-state implementation.

## Natural request

> Make the Books page practical for a larger collection. Users need to filter
> by read status, search by title or author, move through bounded pages, and
> share or restore the current discovery state through the URL. The table,
> active controls, empty state, browser navigation, and CRUD refreshes must
> stay consistent with the selected view. Preserve existing CRUD behavior and
> unfiltered API compatibility. Plan the work and create the appropriate task
> structure without implementing it.

The prompt does not mention vertical slices, task count, frontend/backend
partitioning, or delivery order.

## Approved outcomes

- `DISCOVERY-1`: Read/Unread/All filtering works end to end through the
  production client transport and Flask collection route.
- `DISCOVERY-2`: Title/author search works end to end and composes with the
  selected read filter.
- `DISCOVERY-3`: Bounded pagination, total count, boundary navigation, and
  page reset rules work end to end with filter and search.
- `DISCOVERY-4`: Filter, search, and page state are represented in the URL,
  restore on reload, and follow browser back/forward behavior.
- `DISCOVERY-5`: Active controls, results, and empty states remain clear and
  accessible.
- `DISCOVERY-6`: Add, update, and delete refresh the current discovery view.
- `DISCOVERY-7`: Existing CRUD and unparameterized collection behavior remain
  compatible.

## Reviewed coherent partition

```text
010: Deliver read-status filtering end to end
020: Add title and author search end to end
030: Add bounded pagination end to end
040: Add shareable URL state and browser restoration
```

- Each slice owns necessary Flask behavior, client transport, Vue behavior,
  focused tests, production crossing, and current documentation.
- `020` builds on the query conventions established by `010` but is a
  separately usable capability.
- `030` composes with the earlier query capabilities and owns page-reset
  behavior.
- `040` depends on the prior discovery controls and owns reload/back/forward
  integration.

## Acceptable alternatives

- Combine read filtering and search when the task still leaves search
  independently traceable and reviewable.
- Separate URL parsing from browser synchronization only if one is a reusable
  package or independently accepted contract in the fixture.
- Three to five children may be coherent; exact count is secondary to
  independent product value and manageable ownership.

## Fragmentation examples

These are mergeable when they exist only to complete one product capability:

- Flask query parsing;
- database filtering;
- route tests;
- frontend API client;
- Vue state;
- controls and rendering;
- component tests;
- integration tests;
- documentation;
- final review.

Splitting those into separate horizontal tasks can produce twelve or more
handoffs without an independently usable state.

## Overpacking example

One child containing all four capabilities, every crossing, and all
compatibility work hides independently deliverable product increments and
creates an unreviewable implementation unit.

## Important crossings

Every product slice crosses Vue state and rendering, production client
transport, Flask HTTP routing, and data selection. Separate mocked frontend and
direct route-function tests do not prove the slice.

## Semantic review questions

- How many actual subtasks map to each reviewed product capability?
- Which layer/phase children can merge without losing independent value?
- Did the partition preserve one owner for each full-stack crossing?
- Did higher effort create more handoffs rather than better deliverables?