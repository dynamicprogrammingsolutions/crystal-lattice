# Task Files and Subtasks (`tasks/`)

Task files are a handoff mechanism between agents. The executing agent will not have access to the conversation history, so task files must be written to stand on their own.

**Create task files only on request**
- Only create task files when the user explicitly requests a handoff via task files (with or without subtasks).

**When defining tasks**
- Capture requirements already defined in the current session.
- Don’t make new product/architecture decisions just to “complete the spec”.
- Avoid extra research just to write the task file.
- Record unknown/undecided items as open questions.

## Task Files (single handoff tasks)

### Location + naming
- Put single tasks directly under `tasks/` (create it if missing) as `tasks/<YYYYMMDD>-<kebab-case-slug>.md`.
- Use the current date for `<YYYYMMDD>`.
- If the filename already exists, append a numeric suffix (e.g. `...-2.md`).

### Required content (minimal)
- Start with a standalone description as the first paragraph after the heading (include brief context inline if needed).
- The description MUST be clear without conversation history.
- State the expected outcome if it isn’t obvious.
- Include enough context to execute: relevant background plus concrete file/directory anchors.
- When referencing specific code, include line numbers (e.g. `path/to/file.py:123`).
- If exact locations are unknown, include discovery steps whose output is the needed paths/line numbers.

### Optional content (use when helpful)
- Checklist.
- Dependencies (full task file paths).
- Validation guidance (commands/tests to run).
- Summary of requirements, research performed, decisions made, and open questions.

---

## Subtasks (main + subtasks under `tasks/<task-dir>/`)

**When to use**
- Only create subtasks when the user explicitly requests them.

### Directory + file layout
- Create a dedicated subdirectory: `tasks/<task-dir>/`.
- Use `<task-dir>` as `<kebab-case-slug>` or `<YYYYMMDD>-<kebab-case-slug>` (timestamp prefix recommended).
- If the directory already exists, append a numeric suffix.
- Create one main file: `tasks/<task-dir>/000-main.md`.
- Create one file per subtask: `tasks/<task-dir>/<NNN>-<subtask-slug>.md`.
- Keep default depth to two levels (main + subtasks).

### Ordering
- Start subtask filenames with a 3-digit number.
- Assign numbers to reflect dependencies (dependent tasks get larger numbers).
- Leave gaps to allow inserting additional subtasks later.

### File contents
- In every file under `tasks/<task-dir>/`, include the required content from “Task Files → Required content”.
- Add any relevant items from “Task Files → Optional content” when helpful.
- In `tasks/<task-dir>/000-main.md`, list every subtask file by full path.
- In each subtask file, include `Parent Task: <full path to 000-main.md>`.
- Add `Depends On:` with full task paths when a subtask depends on another.

### References
- When referencing another task file (parent/child/dependency), use the full relative path.

---

## Completing Task Files (Checklists + Updates)

### Checklists
- Use Markdown checkboxes: `[ ]` incomplete, `[x]` complete.
- Keep checklists single-level.
- Don’t delete checklist items; if something becomes unnecessary, mark it `[x]` and note why.
- It’s fine to start with no checklist; the completing agent can add/refine one before marking completion.

### Marking completion
- For single tasks, mark the relevant checklist items `[x]` (if a checklist exists).
- For subtasks, mark completion in the subtask file and (if used) in `tasks/<task-dir>/000-main.md`.

### Notes added during completion (optional)
- The completing agent may append a short section at the end describing what was done, what changed, and any relevant findings.
- Make it explicit that this was added during completion (for example, include a completion date and/or agent name).