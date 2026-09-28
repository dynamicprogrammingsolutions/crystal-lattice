# Reviewed target — tg04-flask-vue-discovery-decomposition

**Flask/Vue book discovery decomposition** — Partition a large full-stack release into a few end-to-end product capabilities rather than technical phases.

Category: decomposition · Project: `Flask-Vue CRUD discovery fixture` · Acceptable partition sizes: 3, 4, 5

**Approved outcomes**

- DISCOVERY-1: Read-status filtering works end to end.
- DISCOVERY-2: Title and author search works end to end and composes with filtering.
- DISCOVERY-3: Bounded pagination and total count compose with filter and search.
- DISCOVERY-4: Discovery state is shareable in the URL and restores across reload and browser navigation.
- DISCOVERY-5: Controls, active state, results, and empty states remain clear and accessible.
- DISCOVERY-6: CRUD refreshes retain the current discovery view.
- DISCOVERY-7: Existing CRUD and unparameterized API behavior remain compatible.

**Coherent deliverables**

- **DISCOVERY-D1** — Deliver read-status filtering end to end
  Users gain a complete usable filter through the real client/server path.
  - Outcomes: DISCOVERY-1, DISCOVERY-5, DISCOVERY-6, DISCOVERY-7
- **DISCOVERY-D2** — Add title and author search end to end (depends on DISCOVERY-D1)
  Search is independently useful and composes with the established filter query conventions.
  - Outcomes: DISCOVERY-2, DISCOVERY-5, DISCOVERY-6, DISCOVERY-7
- **DISCOVERY-D3** — Add bounded pagination end to end (depends on DISCOVERY-D1)
  Pagination is a complete independently reviewable scale capability.
  - Outcomes: DISCOVERY-3, DISCOVERY-5, DISCOVERY-6, DISCOVERY-7
- **DISCOVERY-D4** — Add shareable URL state and browser restoration (depends on DISCOVERY-D1, DISCOVERY-D2, DISCOVERY-D3)
  URL persistence is a separately useful workflow enhancement over the working controls.
  - Outcomes: DISCOVERY-4, DISCOVERY-5, DISCOVERY-6

**Important crossings**

- Each product capability crosses Vue state/rendering, production transport, Flask HTTP routing, and data selection.

**Acceptable alternatives**

- Read filtering and search may be combined if both remain independently traceable and the slice stays reviewable.
- URL parsing may be separate only when it is an independently maintained reusable contract.

**Fragmentation examples**

- Flask query parsing as a separate task.
- Database filtering as a separate task.
- Frontend API client as a separate task.
- Vue state and controls as separate tasks.
- Component tests, integration tests, documentation, and final review as horizontal tasks.

**Overpacking examples**

- One child containing all discovery capabilities and every crossing hides independently useful releases.

**Open questions**

- Exact query encoding and URL parameter names remain material contract decisions.

**Handoff expectations**

- retain plan: Preserve the reviewed vertical delivery rationale and dependency graph.
- omit plan: Preserve approved outcomes, project facts, cross-layer constraints, and public questions without the four-slice implementation direction.
- fresh agent plan: A fresh agent reconstructs a small vertical partition and does not expand layers or test types into separate phases.

**Plan content requirements**

- PLAN-1: The discovery state contract between client and server: what read-status filtering, title/author search, bounded pagination, and total count are exchanged. (from DISCOVERY-1, DISCOVERY-2, DISCOVERY-3)
- PLAN-2: The composability rules and bounds: how search composes with filtering and pagination, and where the bounds are. (from DISCOVERY-2, DISCOVERY-3)
- PLAN-3: The URL shareability design: which discovery state encodes in the URL and how it restores across reload and browser navigation. (from DISCOVERY-4)
- PLAN-4: How CRUD refreshes retain the current discovery view instead of resetting it. (from DISCOVERY-6)
- PLAN-5: How existing CRUD and unparameterized API behavior remain compatible. (from DISCOVERY-7)
- PLAN-6: The adoption sequence across the Vue state/rendering, production transport, Flask routing, and data selection crossings — with the state contract settled before the surfaces that consume it.
