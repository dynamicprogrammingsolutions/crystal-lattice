# Task Files and Subtasks (`tasks/`)

Task files are standalone handoffs for agents without the current conversation.

## Terms

- A **requirement** is a necessary, approved completed-state outcome or constraint. Implementation, tests, documentation, and verification belong in the plan unless their outcome is independently required.
- A **task** is a concrete unit of work performed while executing a plan.
- An **execution plan** records the decided approach, boundaries, tasks, verification, documentation, risks, and dependencies needed for another agent to continue without repeating decisions.
- **Supporting details** are facts and rationale needed to interpret requirements without being separate completion outcomes.
- An **open question** is a **requirement question** when its answer changes a required outcome or constraint, and a **design decision** when the requirements stay the same but the implementation direction changes.
- A **material design decision** affects user-visible behavior, interfaces or contracts, ownership or module boundaries, compatibility or persisted data, security or privacy, or a significant operational or maintenance tradeoff.

## Creating task files (handoff author)

Create or modify a task file only when the user requests task-file tracking or names a task file to work from.

When you are asked to create task files:
1. Confirm which format the user wants: a single task file, or a main task with subtasks.
2. Review prior work and record what is known, decided, unresolved, and left.
3. Follow the structure and status rules below plus any user instructions.
4. Record task relations only when explicitly requested.

Start each task with a title, short description, and `## Requirements checklist`. Derive the minimum approved outcomes and constraints needed for completion. A requirement must trace to the request, an explicitly preserved contract, a necessary consequence, or an approved policy or decision. Group variants, operations, boundaries, and examples without hiding an approved condition, unless separate acceptance, ownership, or status adds value. Keep implementation, testing, documentation, refactoring, and verification work in the plan unless its outcome is independently required.

Near the top, after requirements and optional scope/workstreams, list unresolved requirement questions and decisions changing scope or outcomes. Put research and supporting facts before any execution plan.

Optimize for continuation, not length. Keep human-review sections concise. Supporting details preserve durable facts, constraints, references, and failed approaches needed to avoid rediscovery; omit chronology, raw output, duplication, replaceable inventories, and unselected speculation. Label uncertain content as fact, assumption, decision, recommendation, or question. Supporting details must not add hidden requirements.

When a task file follows planning, follow the user's requested handoff:
- If asked to retain the plan, preserve the common handoff content and put the plan in a separate `## Execution plan`; use `Draft` unless execution was already approved.
- If asked to omit the plan, preserve requirements, facts, supporting details, and requirement questions; omit implementation direction, decisions or questions, planned documentation, tasks, verification, and risks unless the user requests a specific item.
- If the user does not say whether to retain the plan, ask.

Creating a task file does not itself authorize execution.

### Status tracking

- Do not change requirements without user-approved scope changes.
- Mark a requirement complete only when supported by evidence such as a test, build, inspection, or human confirmation.
- Identify requirements needing human verification and leave them incomplete until that verification is confirmed.
- Update execution tasks throughout completion, not only at the end.
- Task creation is planning, not implementation. Inspect only what is needed to write the plan; do not install dependencies or create scratch implementations in the repository. Use a temporary location for diagnostics that must write files, and remove incidental changes before handoff. Leave only the requested task-file changes.

### Questions and decisions

- Ask before resolving a requirement question or changing the requirements checklist. After the answer, update the affected requirements and reconsider any existing plan.
- In a retained plan, collect material decisions and questions immediately before documentation and give unresolved decisions a recommendation and tradeoffs. Resolve local, reversible implementation choices. Public APIs, persisted data, compatibility, security, privacy, and user-visible behavior are material; ask unless the user or approved task authorized that decision. Do not invent fallback or error behavior for unspecified inputs merely to complete the plan.

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

Use `## Execution plan`, followed immediately by `Status: Draft` or `Status: Approved`, then a substantive free-form body with the approach and details another agent needs. Structure it as the task requires.

End every plan with these H3 sections exactly once and in this order: `### Implementation decisions and open questions`, `### Documentation`, `### Task checklist`, `### Requirement verification`, then optional `### Additional implementation verification`. Do not use these headings earlier in the plan. Execution tasks use checkboxes.

Requirement verification maps each requirement or coherent group to the smallest reliable evidence at the user-relevant or public boundary containing every approved condition. A mock is insufficient when it supplies or bypasses that behavior. Use representative accepted and rejected boundaries and regressions. Cite existing coverage only when it actually proves preserved behavior; otherwise plan focused evidence or record the gap. Do not test unresolved or unapproved behavior. Additional implementation verification covers only distinct material risks. Routine quality checks are supporting evidence.

Do not add implementation or completion notes during planning. Add `## Implementation Notes` only after execution starts and immutable `## Completion Notes` only after completion.

- `Draft` records planning but does not authorize execution.
- `Approved` means the user has approved execution of that plan.
- Material changes before execution return the plan to `Draft` until approved again.

### Presenting an execution plan

Before approval, store the complete `Draft` plan, then summarize outcome, scope, approach, material decisions or questions, acceptance evidence, documentation audience, risks, and exclusions. Prefer conceptual boundaries over file inventories unless location is material. Apply changes, request approval, and state that execution waits.

## Completing task files (handoff executor)

1. Read the allowed task files and inspect the relevant repository state.
2. Write the complete execution plan as `Draft`. If one exists from an earlier session, reassess it and present it again.
3. Present the plan as described above and obtain explicit approval.
4. Mark the plan `Approved`, then execute and continuously update its task checklist.
5. Keep requirement evidence and parent status current. Record discoveries and plan changes in `## Implementation Notes`; ask about high-impact ambiguities or material changes. Clear, safe, in-scope fixes may be made and then reported.
6. Append immutable `## Completion Notes` covering the outcome, requirement evidence, verification performed or blocked, plan deviations and findings, and unresolved or deferred scope.
7. Put later corrections under `## Post-completion follow-up`. Ask before reopening or materially extending the task, or creating another task.

Approval authorizes execution only when the original request includes execution or completion and the agent explicitly said execution would begin after approval. Steps 2–4 do not require duplicate approval when the user has already approved the plan, asked execution to start, and asks for a task file only to track that execution.
