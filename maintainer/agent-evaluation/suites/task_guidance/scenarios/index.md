# Task-guidance scenario contracts

These approved contracts are executable fixtures and real-model prompts.
[Stage B0 — Current-guidance baseline](../../../../docs/evaluations/task-guidance/test-plan.md#stage-b0--current-guidance-baseline)
has exercised all planned model/effort cells. One GPT same-agent continuity
chain is explicitly invalid because its task-creation turn produced no task
file.

The suite uses three bounded cases for task handoff and three substantially
larger cases for decomposition quality. The larger cases use reviewed derived
project states rather than reusing the small requirement-quality tasks.

| ID | Project | Role | Primary boundary |
|---|---|---|---|
| [Scenario TG-01 — Eleventy archive pagination as one task](01-eleventy-archive-single-task.md) | Eleventy Base Blog | Bounded handoff | Approved plan preservation and generated-site crossing |
| [Scenario TG-02 — FastAPI notes pagination as one task](02-fastapi-pagination-single-task.md) | FastAPI CRUD Async | Bounded handoff | Public API plan and HTTP/storage evidence |
| [Scenario TG-03 — Flask/Vue selected-filter refresh regression](03-flask-vue-filter-refresh-single-task.md) | Flask-Vue CRUD | Bounded handoff | Full-stack bug handoff and selected-filter preservation |
| [Scenario TG-04 — Flask/Vue book-discovery decomposition](04-flask-vue-book-discovery-release.md) | Derived Flask-Vue CRUD fixture | Complex vertical decomposition | Four end-to-end product capabilities crossing client/server layers |
| [Scenario TG-05 — FastAPI service, client, and CLI query capability](05-fastapi-multi-consumer-query-capability.md) | Derived FastAPI monorepo fixture | Complex component decomposition | Public API, reusable SDK, and first-party consumer boundaries |
| [Scenario TG-06 — Eleventy author-metadata compatibility migration](06-eleventy-author-metadata-migration.md) | Derived Eleventy Base Blog fixture | Complex migration decomposition | Four compatibility-preserving content/build states |

The bounded handoff contracts support:

- canonical independent task-creation input;
- retained-plan and omit-plan handoffs;
- fresh-agent plan presentation;
- focused same-agent continuation;

The complex decomposition contracts support:

- a reviewed partition of approximately four coherent deliverables;
- acceptable alternative partitions;
- actual-subtask-to-deliverable mapping;
- mergeable-fragment and overpacked-slice assessment;
- valid versus automatic technical-layer classification;
- descriptive fragmentation ratio;

Every contract supports:

- semantic task/topology assessment;
- quality-gated investigation-efficiency evidence where designated.

Prompts stay natural. Approved outcomes and canonical plans remain hidden
evaluator targets.

## Common stage prompts

The scenario-specific natural request supplies the task scope. Later stage
prompts remain short because standing guidance owns task-file rules.

### Retain-plan task creation

> Create the task file or task directory for the approved plan. Preserve the
> plan as Draft. Do not implement the change.

### Omit-plan task creation

> Create the task file or task directory with the approved requirements,
> verified facts, decisions, unresolved questions, and useful source pointers,
> but omit the execution plan. Do not implement the change.

### Fresh-agent planning

> Read the task files and present the Draft implementation plan. Do not modify
> files or implement the task.

### Same-agent planning

> Continue by presenting the Draft implementation plan for the task you just
> created. Do not implement the task.

The evaluator supplies the exact task path when needed. Prompts do not restate
requirement, testing, decomposition, or section-format rules.