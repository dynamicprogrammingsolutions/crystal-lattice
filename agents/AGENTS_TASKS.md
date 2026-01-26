## 7. Task Files (`tasks/`)

**Trigger (required)**
- Only when the user explicitly requests a task handoff via task files, you MUST create the task file(s).

**A) Creating Task Files**

**Location**
- Task files live under `tasks/`. Create `tasks/` if it does not exist.

**Naming (required)**
- A single handoff task MUST be a single Markdown file at: `tasks/<NNN>-<kebab-case-slug>.md`.
- `<NNN>` MUST be a 3-digit number used for stable referencing.
- Choose `<NNN>` deterministically based on existing task files.

**Cross-references (required)**
- Any reference to another task file (e.g. dependencies) MUST use the full file path (e.g. `tasks/<NNN>-<name>.md`).

**Required content (self-contained; include concrete paths)**
- Task files must be self-contained: another agent should not need chat history.
- Do not add human-oriented tracking metadata (e.g. status, priority, owner, created) unless the user explicitly requests it.
- The task file MUST include:
  - an H1 title
  - `Depends On:` followed by either full task paths or the literal `(none)`
  - a goal statement (what completion means)
  - context sufficient to locate relevant code/doc areas, including concrete file and/or directory paths (or explicit discovery steps that produce them)
  - constraints that matter for implementation (including applicable `AGENTS.md` rules for the directories in scope)
  - a checklist-driven work plan with concrete, verifiable actions
  - acceptance criteria
  - validation guidance describing how completion should be verified

**B) Completing Task Files (Checklists + Updates)**

**Checklists are the source of truth**
- Use Markdown checkboxes:
  - `[ ]` incomplete
  - `[x]` complete
- Do not delete checklist items. If an item becomes unnecessary, mark it `[x]` and add a brief explanation in the task file.

**Optional implementation notes (recommended when helpful)**
- The executing agent MAY add a short `## Implementation Notes` section when information discovered during execution could help future maintenance or dependent work.
- Skip `## Implementation Notes` if the task description already contains all information needed downstream.

**Keeping task files accurate**
- If execution reveals missing steps, missing dependencies, incorrect scope, or newly discovered concrete paths:
  - update the task file to reflect the new reality
  - keep all dependencies and references expressed as full file paths

---

## 8. Subtasks (Main + Subtasks under `tasks/<slug>/`)

**Trigger (required)**
- Only when the user explicitly requests subtasks, you MUST create a main task plus subtask files.

**A) Creating Main + Subtasks**

**Directory + file layout (required)**
- Create a dedicated subdirectory: `tasks/<kebab-case-slug>/`.
- If that directory already exists, use `tasks/<slug>-2/`, `tasks/<slug>-3/`, etc.
- Create exactly one primary task file: `tasks/<slug>/000-main.md`.
- Create one file per subtask: `tasks/<slug>/<NNN>-<subtask-slug>.md`.
- Default depth is two levels only (primary + subtasks); do not create sub-subtasks unless the user explicitly asks.

**Naming + ordering (required)**
- Subtask filenames MUST start with a 3-digit number.
- Numbering MUST respect dependencies: if task B depends on task A, then B’s number MUST be greater than A’s number.
- Use gaps in numbering to allow inserting additional tasks later without renaming existing ones.

**Parent/child + dependencies (required)**
- Every subtask file MUST declare:
  - `Parent Task: <full path to the primary task>`
  - `Depends On:` followed by either full task paths or the literal `(none)`
- The primary task (`000-main.md`) MUST include:
  - a checklist enumerating every subtask file by full path
  - each subtask’s dependencies by full path
  - enough structure that execution order can be determined from the files alone

**Breakdown rules (default)**
- Subtasks do not need to be parallelizable; they may be sequential or parallel. Dependencies MUST make required ordering explicit.
- Each subtask should have a crisp boundary (single coherent deliverable), minimal overlap with other subtasks, and clear acceptance/validation.
- If key information is missing or ambiguous, include an early discovery/scope subtask whose output resolves the unknowns and updates later tasks accordingly.

**B) Completing Subtasks (Additional completion requirements)**

**Marking completion (required)**
- When a subtask is completed, the executing agent MUST:
  - mark all relevant checklist items in the subtask file as `[x]`
  - mark the corresponding subtask line in `tasks/<slug>/000-main.md` as `[x]`