# Multi-Agent Subtasks (`tasks/`)

**Trigger (required)**
- Only when the user explicitly requests subtasks, you MUST create task files for other agents to execute.

## A) Creating Task Files (Main + Subtasks)

**Directory + file layout (deterministic)**
- All task files live under `tasks/`.
- For each user request that needs subtasks, create a new subdirectory: `tasks/<kebab-case-slug>/`.
- If that directory already exists, use `tasks/<slug>-2/`, `tasks/<slug>-3/`, etc.
- Create exactly one primary task file: `tasks/<slug>/000-main.md`.
- Create one file per subtask: `tasks/<slug>/<NNN>-<subtask-slug>.md`.
- Default depth is two levels only (primary + subtasks); do not create sub-subtasks unless the user explicitly asks.

**Naming + ordering**
- Task filenames MUST start with a 3-digit number (`000`, `010`, `020`, ...) for stable reference.
- Numbering MUST respect dependencies: if task B depends on task A, then B’s number MUST be greater than A’s number.
- Use gaps in numbering to allow inserting additional tasks later without renaming existing ones.

**Cross-references (required)**
- Any time a task references another task (parent/child/dependency), it MUST use the full file path (e.g. `tasks/<slug>/020-<name>.md`), not shorthand like “task 020”.

**Parent/child + dependencies (required)**
- Every subtask file MUST declare:
  - `Parent Task: <full path to the primary task>`
  - `Depends On:` followed by either:
    - one or more full task paths, or
    - the literal text `(none)` if there are no dependencies
- The primary task MUST include:
  - a checklist enumerating every subtask file by full path
  - each subtask’s dependencies by full path
  - enough structure that execution order can be determined from the files alone

**Required content (self-contained; include concrete paths)**
- Task files must be self-contained: another agent should be able to start without chat history.
- `000-main.md` MUST include:
  - a clear goal statement (what completion means)
  - context sufficient to locate relevant code/doc areas, including concrete file and/or directory paths
  - constraints that matter for implementation (including applicable `AGENTS.md` rules for the directories in scope)
  - acceptance criteria for the overall work
  - validation guidance describing how completion should be verified
- Each subtask file MUST include:
  - `Parent Task:` (full path)
  - `Depends On:` (full paths or `(none)`)
  - a goal statement for the subtask deliverable
  - context with concrete file/directory paths the agent is expected to touch or inspect (or explicit discovery steps that produce them)
  - a checklist-driven work plan with concrete, verifiable actions
  - acceptance criteria for the subtask
  - validation guidance describing how completion should be verified

**Breakdown rules (default)**
- Subtasks do not need to be parallelizable; they may be sequential or parallel. Dependencies MUST make required ordering explicit.
- Each subtask should have a crisp boundary (single coherent deliverable), minimal overlap with other subtasks, and clear acceptance/validation.
- If key information is missing or ambiguous, create an early discovery/scope subtask whose output resolves the unknowns and updates later tasks accordingly.

**Avoid human-oriented metadata**
- Do not add fields like status, priority, owner, created, or similar tracking metadata unless the user explicitly requests them.

## B) Completing Task Files (Checklists + Updates)

**Checklists are the source of truth**
- Use Markdown checkboxes:
  - `[ ]` incomplete
  - `[x]` complete
- Do not delete checklist items. If an item becomes unnecessary, mark it `[x]` and add a brief explanation in the task file.

**Marking completion (required)**
- When a subtask is completed, the executing agent MUST:
  - mark all relevant checklist items in the subtask file as `[x]`
  - mark the corresponding subtask line in `tasks/<slug>/000-main.md` as `[x]`

**Optional implementation notes (recommended when helpful)**
- The executing agent MAY add a short `## Implementation Notes` section to the subtask file when information discovered during execution could help future maintenance or completion of dependent subtasks.
- Skip `## Implementation Notes` if the task description already contains all information needed for dependent work.

**Keeping task files accurate**
- If execution reveals missing steps, missing dependencies, or incorrect scope:
  - update the task files to reflect the new reality (including concrete paths)
  - keep dependencies consistent and referenced by full file path
  - do not introduce additional task nesting beyond the default two levels unless the user explicitly requests it