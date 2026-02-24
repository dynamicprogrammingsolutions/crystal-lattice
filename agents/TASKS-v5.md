# Task Files and Subtasks (`tasks/`)

Task files are a handoff mechanism between agents. A new agent executing a task will not have access to the current conversation, so each task file should stand on its own and make the current state of research easy to pick up.

## Creating task files (handoff author)

When you are asked to create task files:
1. Confirm which format the user wants: a single task file, or a main task with subtasks.
2. Review the work/research you already did related to the task (what you inspected, what you learned, what you ruled out).
3. Assemble a clear handoff package: what’s known, what’s been tried, what remains, and where to look next.
4. Write the task file(s) so a new agent can continue without access to the current conversation.
5. If the user provides additional instructions for task file structure/content, follow those instructions.

At the start of each task file:
- Include a title.
- Include a short, easy-to-understand description of the task targeted to humans (the rest of the file can be as simple or as detailed as needed).

To save work for the completing agent:
- Include information from your existing research (explanations, code snippets, and references with line numbers/ranges) so they don’t need to rediscover the current state.

### Single task (no subtasks): placement + naming
- Put the task directly under `tasks/` (create it if missing) as `tasks/<YYYYMMDD>-<kebab-case-slug>.md`.
- Use the current date for `<YYYYMMDD>`.
- If the filename already exists, append a numeric suffix (e.g. `...-2.md`).

### Task with subtasks: directory + file layout
- Create a dedicated subdirectory: `tasks/<task-dir>/`.
- Use `<task-dir>` as `<kebab-case-slug>` or `<YYYYMMDD>-<kebab-case-slug>` (timestamp prefix recommended).
- If the directory already exists, append a numeric suffix.
- Create one main file: `tasks/<task-dir>/000-main.md`.
- Create one file per subtask: `tasks/<task-dir>/<NNN>-<subtask-slug>.md`.
- Keep default depth to two levels (main + subtasks).

### Subtask naming + ordering
- Start subtask filenames with a 3-digit number.
- Use numbering to reflect dependencies (dependent subtasks get larger numbers).
- Leave gaps between subtask numbers so additional subtasks can be inserted later without renaming existing files (for example, `010-...`, `020-...`, `030-...`, not `001-...`, `002-...`, `003-...`).

### Required links / references (subtasks)
- In `tasks/<task-dir>/000-main.md`, include a list enumerating every subtask file by full path.
- In each subtask file, include `Parent Task: tasks/<task-dir>/000-main.md`.
- When referencing another task file (parent/child/dependency), use the full relative path.
- In subtask files, add `Depends On:` with full task paths when applicable.

---

## Completing task files (handoff executor)

When you are asked to complete a task from task files:
1. Read the task file(s) and any relevant code referenced by the task (or discovered while scoping).
2. Draft an execution plan and choose an execution approach (single pass vs staged checkpoints) based on task size/risk and expected testing/iteration.
3. Share the plan and approach with the user.
4. After the user approves, append the plan to the task file (make it clear it was added during completion).
5. Only implement changes when the user explicitly requests implementation.
6. After implementing, append completion notes at the bottom (what was done, what changed, and any relevant findings), and make it clear these notes were added during completion.