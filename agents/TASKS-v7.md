# Task Files and Subtasks (`tasks/`)

Task files are a handoff mechanism between agents. A new agent executing a task will not have access to the current conversation, so each task file should stand on its own and make the current state of research easy to pick up.

## Terms

- A **requirement** is a verifiable outcome or constraint that the completed work must satisfy.
- A **task** is a concrete unit of work performed while executing a plan.
- An **execution plan** records the decided approach, boundaries, tasks, verification, documentation, risks, and dependencies needed for another agent to continue without repeating decisions.
- **Supporting details** are facts and rationale needed to interpret requirements without being separate completion outcomes.
- An **open question** is a **requirement question** when its answer changes a required outcome or constraint, and a **design decision** when the requirements stay the same but the implementation direction changes.
- A **material design decision** affects user-visible behavior, interfaces or contracts, ownership or module boundaries, compatibility or persisted data, security or privacy, or a significant operational or maintenance tradeoff.

## Creating task files (handoff author)

Create or modify a task file only when the user requests task-file tracking or names a task file to work from.

When you are asked to create task files:
1. Confirm which format the user wants: a single task file, or a main task with subtasks.
2. Review relevant work already done and write a concise, standalone handoff containing what is known, decided, unresolved, and left to do.
3. Follow the structure and status rules below plus any user instructions.
4. Record task relations only when explicitly requested.

Start each task with a title, short description, and `## Requirements checklist`. Requirements are concise, verifiable outcomes or constraints, not work steps.

Keep the human-review section near the top: after requirements and any brief scope/workstream summary, list unresolved requirement questions and material design decisions. Put detailed research and supporting facts after that and before any execution plan.

Keep task files short without losing handoff-critical information. Omit investigation chronology, repeated requirement restatements, exhaustive file inventories, and speculative implementation detail. Prefer concise findings and references. Supporting details may clarify requirements but must not add hidden completion conditions.

When a task file follows planning, follow the user's requested handoff:
- If asked to retain the plan, preserve the common handoff content and put the plan in a separate `## Execution plan`; use `Draft` unless execution was already approved.
- If asked to omit the plan, preserve the requirements, factual research, supporting details, decided directions, and classified open questions, but do not include or relabel execution-plan content.
- If the user does not say whether to retain the plan, ask.

Creating a task file does not itself authorize execution.

### Status tracking

- Do not change requirements without user-approved scope changes.
- Mark a requirement complete only when supported by evidence such as a test, build, inspection, or human confirmation.
- Identify requirements needing human verification and leave them incomplete until that verification is confirmed.
- Update execution tasks throughout completion, not only at the end.

### Questions and decisions

- Ask before resolving a requirement question or changing the requirements checklist. After the answer, update the affected requirements and reconsider any existing plan.
- Present material design decisions with a recommendation and relevant tradeoffs. Local, reversible implementation choices may be made without separate approval.

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

### Main task subtasks

- In `tasks/<task-dir>/000-main.md`, include `## Subtasks` and list every subtask file as a checkbox item using its full relative path.
- If the user explicitly asks to record task relations, add the relation under the relevant item using a clear keyword such as `SUPERSEDED BY`, `SPLIT INTO`, `COMPLETED VIA`, or `OVERLAP`.
- You do not need to inspect other task files just to use these labels.

### Required links / references (subtasks)
- In each subtask file, include `Parent Task: tasks/<task-dir>/000-main.md`.
- When referencing another task file (parent/child/dependency), use the full relative path.
- In subtask files, add `Depends On:` with full task paths when applicable.

### When working with task files

- Read only the current task, its parent, declared dependencies, explicitly referenced task files, and same-directory tasks needed to confirm scope ownership or avoid overlap. Do not inspect unrelated task files or list other task directories unless the user asks.

---

## Execution plans

Use `## Execution plan`, followed immediately by `Status: Draft` or `Status: Approved`. Keep `### Requirement verification`, `### Documentation`, and `### Task checklist` separate.

Requirement verification maps each requirement, or coherent requirement group, to concise acceptance evidence at a user-relevant or public boundary. Put implementation-specific robustness checks in an optional `### Additional implementation verification` section or the task checklist.

Do not add implementation or completion notes during planning. Add `## Implementation Notes` only after execution starts and immutable `## Completion Notes` only after completion.

- `Draft` records planning but does not authorize execution.
- `Approved` means the user has approved execution of that plan.
- Material changes before execution return the plan to `Draft` until approved again.

### Presenting an execution plan

Before requesting approval, write the complete plan into the task file as `Draft`, then give the user a concise, self-contained summary covering:

- outcome, scope, approach, and material decisions;
- acceptance evidence by requirement or requirement group;
- documentation audience and what the documentation will make understandable;
- material risks, exclusions, open questions, and recommended choices.

Describe conceptual boundaries rather than file inventories unless a location is itself a material decision. Apply requested changes to the draft, then ask for approval and state that execution begins only after approval.

## Completing task files (handoff executor)

1. Read the allowed task files and inspect the relevant repository state.
2. Write the complete execution plan as `Draft`. If one exists from an earlier session, reassess it and present it again.
3. Present the plan as described above and obtain explicit approval.
4. Mark the plan `Approved`, then execute and continuously update its task checklist.
5. Keep requirement evidence and parent status current. Record discoveries and plan changes in `## Implementation Notes`; ask about high-impact ambiguities or material changes. Clear, safe, in-scope fixes may be made and then reported.
6. Append immutable `## Completion Notes` covering the outcome, requirement evidence, verification performed or blocked, plan deviations and findings, and unresolved or deferred scope.
7. Put later corrections under `## Post-completion follow-up`. Ask before reopening or materially extending the task, or creating another task.

Approval authorizes execution only when the original request includes execution or completion and the agent explicitly said execution would begin after approval. Steps 2–4 do not require duplicate approval when the user has already approved the plan, asked execution to start, and asks for a task file only to track that execution.
