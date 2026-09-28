# Reviewed target — tg03-flask-vue-refresh-handoff

**Flask/Vue selected-filter refresh handoff** — Keep one cross-layer regression cohesive and preserve its production transport boundary.

Category: handoff · Project: `Flask-Vue CRUD` · Acceptable partition sizes: 1

**Approved outcomes**

- REFRESH-1: All/Read/Unread selection remains active after add, update, and delete refreshes.
- REFRESH-2: Mutation refreshes use the selected filter through the production client transport and Flask route.
- REFRESH-3: The visible active choice, table results, and empty state match the refreshed response.
- REFRESH-4: Existing CRUD success, response shape, and unfiltered behavior remain compatible.

**Coherent deliverables**

- **REFRESH-DELIVERY** — Fix selected-filter refresh behavior
  Frontend state, transport, server request, rendering, and regression evidence must all land before the bug is fixed.
  - Outcomes: REFRESH-1, REFRESH-2, REFRESH-3, REFRESH-4

**Important crossings**

- Vue selection and mutation refresh use the production transport and Flask HTTP route before rendering results.

**Acceptable alternatives**

- Add, update, and delete may be grouped as variants of one refresh outcome.

**Fragmentation examples**

- Frontend, backend, component-test, API-test, integration-test, and documentation subtasks would split one inseparable bug fix.

**Handoff expectations**

- retain plan: Preserve the selected-state owner, refresh call paths, compatibility constraints, and real crossing.
- omit plan: Preserve the observed regression, source pointers, state owner, and public response constraints without the proposed shared fetch-path solution.
- fresh agent plan: A fresh agent reconstructs one cohesive cross-layer fix and groups CRUD refresh variants.

**Plan content requirements**

- PLAN-1: Where the selected All/Read/Unread filter lives and how it survives add, update, and delete refreshes. (from REFRESH-1)
- PLAN-2: The path a mutation refresh takes through the production client transport and the Flask route. (from REFRESH-2)
- PLAN-3: How the visible active choice, the table results, and the empty state stay consistent with the refreshed response. (from REFRESH-3)
- PLAN-4: What stays untouched: CRUD success behavior, response shape, and unfiltered behavior. (from REFRESH-4)
