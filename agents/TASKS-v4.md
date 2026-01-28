# Task Files and Subtasks (`tasks/`)

When you are asked to create task files:
1. Confirm which format the user wants: a single task file, or a main task with subtasks.
2. Review the work/research you already did related to the task (what you inspected, what you learned, what you ruled out).
3. Assemble a clear handoff package: what’s known, what’s been tried, what remains, and where to look next.
4. Write the task file(s) so a new agent can continue without access to the current conversation.

A new agent executing the task will not have access to the current conversation. Each task file is a standalone handoff; it should make it easy to understand what was already researched and what to do next.

At the start of each task file:
- Include a title.
- Include a short, easy-to-understand description of the task targeted to humans (the rest of the file can be as simple or as detailed as needed).

To save work for the completing agent:
- Include information from your existing research (explanations, code snippets, and references with line numbers/ranges) so they don’t need to rediscover the current state.

If the user provides additional instructions for task file structure/content, follow those instructions.

---

## Single task (no subtasks)

### Placement + naming
- Put the task directly under `tasks/` (create it if missing) as `tasks/<YYYYMMDD>-<kebab-case-slug>.md`.
- Use the current date for `<YYYYMMDD>`.
- If the filename already exists, append a numeric suffix (e.g. `...-2.md`).

---

## Task with subtasks (main + subtasks)

### Directory + file layout
- Create a dedicated subdirectory: `tasks/<task-dir>/`.
- Use `<task-dir>` as `<kebab-case-slug>` or `<YYYYMMDD>-<kebab-case-slug>` (timestamp prefix recommended).
- If the directory already exists, append a numeric suffix.
- Create one main file: `tasks/<task-dir>/000-main.md`.
- Create one file per subtask: `tasks/<task-dir>/<NNN>-<subtask-slug>.md`.
- Keep default depth to two levels (main + subtasks).

### Naming + ordering
- Start subtask filenames with a 3-digit number.
- Use numbering to reflect dependencies (dependent subtasks get larger numbers).
- Leave gaps between subtask numbers so additional subtasks can be inserted later without renaming existing files (for example, `010-...`, `020-...`, `030-...`, not `001-...`, `002-...`, `003-...`).

### Required links / references
- In `tasks/<task-dir>/000-main.md`, include a list enumerating every subtask file by full path.
- In each subtask file, include `Parent Task: tasks/<task-dir>/000-main.md`.
- When referencing another task file (parent/child/dependency), use the full relative path.
- In subtask files, add `Depends On:` with full task paths when applicable.

---

## Notes added during completion (optional)
- The completing agent may append notes at the end describing what was done and any relevant findings for future work.
- Make it explicit that the notes were added during completion (for example, include a completion date and/or agent name).