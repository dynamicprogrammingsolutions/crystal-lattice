# Task Files and Subtasks (`tasks/`)

Task files are a handoff mechanism between agents. A new agent executing a task will not have access to the current conversation, so each task file should stand on its own and make the current state of research easy to pick up.

## Terms

- A **requirement** is a verifiable outcome or constraint that the completed work must satisfy.
- A **task** is a concrete unit of work performed while executing a plan.
- An **execution plan** records the approach, important decisions and rationale, affected boundaries, ordered tasks, requirement verification, documentation work, risks, and dependencies. It preserves enough direction for another agent to continue without making new important decisions, while omitting redundant detail.

## Creating task files (handoff author)

Create or modify a task file only when the user requests task-file tracking or names a task file to work from.

When you are asked to create task files:
1. Confirm which format the user wants: a single task file, or a main task with subtasks.
2. Review the work/research you already did related to the task (what you inspected, what you learned, what you ruled out).
3. Assemble a clear handoff package: what's known, what's been tried, what remains, and where to look next.
4. Write the task file(s) so a new agent can continue without access to the current conversation.
5. Add the required structure and status tracking described below.
6. If the user explicitly asks to record task relations, add brief relation notes under the relevant items in the main file's `## Subtasks`, using clear keywords and full relative task paths.
7. If the user provides additional instructions for task file structure/content, follow those instructions.

At the start of each task file:
- Include a title, a short human-readable description, and then a `## Requirements checklist`.
- Put verifiable outcomes in the requirements checklist, not ordered work steps.
- After the requirements, include any useful research, constraints, references, or design details in any appropriate format, before any execution plan.
- Include enough prior findings that the completing agent does not need to rediscover them.

Creating or updating a task file does not request or approve a plan or execution. For an ordinary task-creation request, include requirements and handoff details but stop before `## Execution plan`; prior discussion does not authorize storing its plan. Add a plan only when the current user request explicitly says to include, save, preserve, or track it. Record preserved preliminary planning as `Draft`; use `Approved` only when the user already approved execution and asks for a task file to track it.

### Status tracking

- Do not change requirements without user-approved scope changes.
- Mark a requirement complete only when supported by evidence such as a test, build, inspection, or human confirmation.
- Identify requirements needing human verification and leave them incomplete until that verification is confirmed.
- Update execution tasks throughout completion, not only at the end.

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

Example:
```md
## Subtasks

- [x] `tasks/example-task/010-first-step.md`
  - COMPLETED VIA `tasks/example-task/050-combined-implementation.md`
- [ ] `tasks/example-task/020-follow-up.md`
```

### Required links / references (subtasks)
- In each subtask file, include `Parent Task: tasks/<task-dir>/000-main.md`.
- When referencing another task file (parent/child/dependency), use the full relative path.
- In subtask files, add `Depends On:` with full task paths when applicable.

### When working with task files

- Read only the current task, its parent, declared dependencies, explicitly referenced task files, and same-directory tasks needed to confirm scope ownership or avoid overlap. Do not inspect unrelated task files or list other task directories unless the user asks.

---

## Execution plans

Use `## Execution plan`, followed immediately by `Status: Draft` or `Status: Approved`, and keep `### Requirement verification`, `### Documentation`, and `### Task checklist` as separate parts. During planning, do not add implementation- or completion-notes sections at any heading level; add `## Implementation Notes` only after execution starts and `## Completion Notes` only after completion.

- `Draft` records planning but does not authorize execution.
- `Approved` means the user has approved execution of that plan.
- Material changes before execution return the plan to `Draft` until approved again.

### Presenting an execution plan

Before requesting approval, write the complete plan into the task file as `Draft`. Then present a concise, self-contained summary that the user can review without reading the repository or full plan:

- Explain the outcome, scope by affected area, approach, and decisions about user-visible behavior, interfaces, contracts, ownership, or extraction boundaries.
- **Requirement verification:** For each requirement or coherent requirement group, identify the planned evidence, including the test type and boundary where tests apply. Do not burden the summary with tests of internal implementation details unless they affect an important risk or decision.
- **Documentation:** Explain the intended audience, what documentation will be added or changed, and what usage, behavior, or interface it will make understandable without reading source code or unrelated examples. State when no documentation change is planned.
- Present every material decision requiring user confirmation and name the recommended choice explicitly rather than generalizing it; also include material risks, exclusions, and open questions.

Describe conceptual changes rather than a file inventory unless a location is itself an important decision. Apply requested changes to the draft. End the response by explicitly asking the user to approve the plan and stating that execution will begin only after approval.

## Completing task files (handoff executor)

1. Read the allowed task files and inspect the relevant repository state.
2. Write the complete execution plan as `Draft`. If one exists from an earlier session, reassess it and present it again.
3. Present the plan as described above and obtain explicit approval.
4. Mark the plan `Approved`, then execute and continuously update its task checklist.
5. Keep requirement evidence and parent status current. Record discoveries and plan changes in `## Implementation Notes`; ask about high-impact ambiguities or material changes. Clear, safe, in-scope fixes may be made and then reported.
6. Append immutable `## Completion Notes` covering the outcome, requirement evidence, verification performed or blocked, plan deviations and findings, and unresolved or deferred scope.
7. Put later corrections under `## Post-completion follow-up`. Ask before reopening or materially extending the task, or creating another task.

Approval authorizes execution only when the original request includes execution or completion and the agent explicitly said execution would begin after approval. Steps 2–4 do not require duplicate approval when the user has already approved the plan, asked execution to start, and asks for a task file only to track that execution.
