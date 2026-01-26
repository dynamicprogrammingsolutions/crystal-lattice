# Task Files and Subtasks (`tasks/`)

Task files are a handoff mechanism between agents. The executing agent will not have access to the conversation history, so task files must be written to stand on their own.

**Trigger (required)**
- Only create task files when the user explicitly requests a handoff via task files (with or without subtasks).

**Defining tasks in the current session**
- Capture only the hard (or elastic) requirements already defined during the current session.
- Do not make additional product/architecture decisions to “complete the spec”; leave decisions to the executing agent.
- Avoid extensive additional research just to write the task file. Do only what’s necessary to define the task clearly enough for another agent to continue where the current session left off.
- If something is unknown or undecided, record it as an open question instead of deciding it.

## Task Files (single handoff tasks)

### Where they live (required)
- Single handoff tasks live directly under `tasks/` as: `tasks/<NNN>-<kebab-case-slug>.md`
- Create `tasks/` if it does not exist.

### Naming (required)
- `<NNN>` MUST be a 3-digit number used for stable reference.
- Choose numbers deterministically based on existing files under `tasks/` (avoid renaming existing task files).

### Required content (minimal, non-negotiable)

A task file MUST include enough information for another agent to start and finish the work without chat history:

- Immediately after any optional title/heading, include a standalone, human-readable description of the task. This must be clear without conversation history; include brief context inline if needed.
- This description should make it clear what needs to be done and what outcome is expected; deeper goals/context/details can follow elsewhere in the file.
- Context that makes the task executable without chat history, including:
  - a descriptive explanation of relevant background (can be short or extensive depending on how much research/analysis has already been done)
  - concrete file and/or directory paths that anchor the description
  - when referring to specific code locations, include line numbers (e.g. `path/to/file.py:123`)
  - if exact locations are unknown, include discovery steps whose output is the concrete paths/line numbers needed

### Optional content (use when helpful)
- A simple checklist (may be vague or omitted; the completing agent may add/refine it after further research).
- Dependencies (only when applicable), referenced by full task file paths.
- Summary of relevant discussion/requirements from the user (so the executing agent doesn’t need chat history).
- Research already performed (what was inspected, what was learned, what was ruled out).
- Decisions already made (chosen approach, tradeoffs, assumptions).
- Open questions / ambiguities that must be resolved (and what to ask/confirm).
- Definition of done (when applicable).

---

## Subtasks (main + subtasks under `tasks/<slug>/`)

**Trigger (required)**
- Only when the user explicitly requests subtasks, you MUST create a main task plus subtask files.

### Directory + file layout (required)
- Create a dedicated subdirectory: `tasks/<kebab-case-slug>/` (subdirectories are for subtasks).
- Create exactly one primary task file: `tasks/<slug>/000-main.md`.
- Create one file per subtask: `tasks/<slug>/<NNN>-<subtask-slug>.md`.
- Default depth is two levels only (main + subtasks). Do not create sub-subtasks unless the user explicitly asks.

### Naming + ordering (required)
- Subtask filenames MUST start with a 3-digit number.
- Numbering MUST respect dependencies: if task B depends on task A, then B’s number MUST be greater than A’s number.
- Use gaps in numbering to allow inserting additional subtasks later without renaming.

### References (required when used)
- Any time a task references another task file (parent/child/dependency), it MUST use the full file path.

### Main task file (`000-main.md`) requirements

`tasks/<slug>/000-main.md` MUST include:

- Immediately after any optional title/heading, include a standalone, human-readable description of the overall work. This must be clear without conversation history; include brief context inline if needed. Additional goals/context/details can follow elsewhere in the file.
- The overall goal/outcome (what “done” means), if it is not already clear from the description.
- Context with descriptive explanation plus concrete anchors (paths + line numbers where relevant).
- A list enumerating every subtask file by full path (a checklist is optional and may be added/refined by the completing agent).

Optional in `000-main.md`:

- Dependencies/ordering notes between subtasks (full paths).
- Summary of user discussion, research performed, decisions made, open questions, constraints, validation guidance.

### Subtask file requirements

Each subtask file MUST include:

- `Parent Task: <full path to 000-main.md>`
- Immediately after any optional title/heading, include a standalone, human-readable description of the subtask work. This must be clear without conversation history; include brief context inline if needed. Additional goals/context/details can follow elsewhere in the file.
- The subtask goal/outcome (what “done” means), if it is not already clear from the description.
- Context with descriptive explanation plus concrete anchors (paths + line numbers where relevant), or discovery steps that produce them.

Optional in subtask files:

- `Depends On:` only when applicable; use full task paths.
- A simple checklist (may be vague or omitted; the completing agent may add/refine it after further research).
- Summary of discussion/research/decisions/open questions, constraints, validation guidance.

---

## Completing Task Files (Checklists + Updates)

### Checklists (optional, but if used they are the source of truth)
- Use Markdown checkboxes:
  - `[ ]` incomplete
  - `[x]` complete
- Keep checklists simple: single-level; avoid nested/multi-level checklists.
- Do not delete checklist items. If an item becomes unnecessary, mark it `[x]` and briefly note why.
- A checklist may be missing or intentionally vague at task-definition time; the completing agent may add or refine a simple checklist before marking completion.

### Marking completion
- For a single task file: if a checklist exists, mark the relevant items `[x]`.
- For subtasks:
  - mark completion in the subtask file (if a checklist exists)
  - also mark the corresponding subtask line in `tasks/<slug>/000-main.md` if it uses a checklist

### Optional implementation notes (recommended when helpful)
- The executing agent MAY add a short `## Implementation Notes` section when information discovered during execution could help future maintenance or completion of dependent tasks.
- Skip `## Implementation Notes` if the task description already contains all information needed downstream.