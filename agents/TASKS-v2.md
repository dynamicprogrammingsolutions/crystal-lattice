# Task Files and Subtasks (`tasks/`)

Task files are a handoff mechanism between agents. The executing agent will not have access to the conversation history, so task files must be written to stand on their own.

**Trigger (required)**
- Only create task files when the user explicitly requests a handoff via task files (with or without subtasks).

**Defining tasks in the current session**
- Capture only the requirements already defined during the current session.
- Do not make additional product/architecture decisions to “complete the spec”.
- Do only what’s necessary to make the task executable without chat history.
- If something is unknown or undecided, record it as an open question.

## Task Files (single handoff tasks)

### Where they live (required)
- Single handoff tasks live directly under `tasks/` as: `tasks/<YYYYMMDD>-<kebab-case-slug>.md`
- Create `tasks/` if it does not exist.

### Naming (required)
- `<YYYYMMDD>` MUST be the current date in `YYYYMMDD` format.
- If the resulting filename already exists, append a numeric suffix (e.g. `-2`, `-3`).
- Do not rename existing task files.

### Required content (minimal, non-negotiable)

A task file MUST include enough information for another agent to start and finish the work without chat history:

- A standalone, human-readable description as the first paragraph after the heading.
- The description MUST be clear without conversation history.
- The expected outcome if it is not obvious from the description.
- Relevant background needed to understand the task.
- Concrete file and/or directory anchors.
- Line numbers when referencing specific code locations (e.g. `path/to/file.py:123`).
- Discovery steps when exact locations are unknown.

### Optional content (use when helpful)
- Checklist.
- Dependencies, referenced by full task file paths.
- Validation guidance (commands/tests to run).
- Summary of user discussion/requirements.
- Research already performed.
- Decisions already made.
- Open questions / ambiguities that must be resolved.

---

## Subtasks (main + subtasks under `tasks/<task-dir>/`)

**Trigger (required)**
- Only when the user explicitly requests subtasks, you MUST create a main task plus subtask files.

### Directory + file layout (required)
- Create a dedicated subdirectory: `tasks/<task-dir>/`.
- `<task-dir>` can be `<kebab-case-slug>` or `<YYYYMMDD>-<kebab-case-slug>` (timestamp prefix recommended).
- If the directory already exists, append a numeric suffix.
- Do not rename existing task directories.
- Create exactly one primary task file: `tasks/<task-dir>/000-main.md`.
- Create one file per subtask: `tasks/<task-dir>/<NNN>-<subtask-slug>.md`.
- Default depth is two levels (main + subtasks).
- Do not create sub-subtasks unless the user explicitly asks.

### Naming + ordering (required)
- Subtask filenames MUST start with a 3-digit number.
- If task B depends on task A, then B’s number MUST be greater than A’s number.
- Use gaps in numbering to allow inserting additional subtasks later without renaming.

### File contents
- Every file under `tasks/<task-dir>/` MUST include all mandatory elements from “Task Files → Required content”.
- `tasks/<task-dir>/000-main.md` MUST include a list enumerating every subtask file by full path.
- Each subtask file MUST include `Parent Task: <full path to 000-main.md>`.
- Subtask files MAY include `Depends On:` (full task paths) when applicable.

### References (required when used)
- Any time a task references another task file (parent/child/dependency), it MUST use the full (relative) file path.

---

## Completing Task Files (Checklists + Updates)

### Checklists (optional, but if used they are the source of truth)
- Use Markdown checkboxes:
  - `[ ]` incomplete
  - `[x]` complete
- Keep checklists single-level (no nesting).
- Do not delete checklist items.
- If an item becomes unnecessary, mark it `[x]` and briefly note why.
- A checklist may be missing or intentionally vague at task-definition time.
- The completing agent may add or refine a simple checklist before marking completion.

### Marking completion
- For a single task file, mark the relevant checklist items `[x]`.
- For subtasks, mark completion in the subtask file.
- If `tasks/<task-dir>/000-main.md` uses a checklist, also mark the corresponding subtask line there.

### Notes added during completion (recommended when helpful)
- The completing agent may append a short section at the end of the file describing what was done, what changed, and any relevant findings.
- Make it explicit the section was added during execution after the handoff (for example, include the completion date and/or agent name).
- Skip this if the task description already contains all information needed downstream.