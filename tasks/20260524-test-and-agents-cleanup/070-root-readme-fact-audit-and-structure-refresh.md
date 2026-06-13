# Root README Fact Audit And Structure Refresh

Audit the repo-root `README.md` for factual correctness and contributor steering, then update it so it matches the current repo structure, terminology, command guidance, and documentation entrypoints. This is the README counterpart to the root `AGENTS.md` fact-audit work in task `050`, but it should coordinate with follow-up tasks `051` and `052` rather than duplicating their narrower fixes blindly.

## Requirements checklist

- [ ] Audit the stated facts in root `README.md` across repo structure, plugin terminology, docs references, setup guidance, and command examples.
- [ ] Refresh the repository layout section so it matches the current repo shape and terminology.
- [ ] Align root README plugin terminology with the decisions already made in task `050`.
- [ ] Check root README command examples for drift against current test, install, and build guidance.
- [ ] Promote the current plugin-docs home and other current documentation entrypoints where needed.
- [ ] Decide whether implementation should stay in the root README or split into `071+` follow-up subtasks.

Parent Task: `tasks/20260524-test-and-agents-cleanup/000-main.md`

Depends On: `tasks/20260524-test-and-agents-cleanup/050-root-agents-fact-audit-and-structure-refresh.md`

## Why this task exists

The root `README.md` still acts as a top-level onboarding and repo-navigation document, but parts of it are already known to be stale or incomplete relative to the current repo:

- plugin terminology has drifted
- repo structure descriptions are incomplete
- command examples may no longer match the newer testing guidance
- root docs entrypoints should reflect the promoted `plugins/docs/` model

Tasks `051` and `052` are already set aside for narrower fallout around plugin terminology/docs entrypoints and setup/install guidance. This task should take a broader README view and coordinate with those outcomes rather than re-solving them independently.

## Findings already verified

### Plugin docs section is partly current

- `README.md:282-293`
  - already lists the richer `plugins/docs/*` pages

### Repository layout section is stale in plugin taxonomy

- `README.md:379-390`
  - still says:
    - `core/python/plugins` are built-in Python plugins
    - repo-root `plugins/` are optional plugin bundles

That no longer matches runtime terminology after task `050`.

### Command examples need a broader fact check

Examples already observed in root README include:

- mobile-facing npm commands
- plugin-install examples
- example-test commands such as `pytest core/python/examples/tests -qs`

These should be rechecked against the current command model rather than assumed current.

## Suggested scope

This task should focus on the root README itself. If it uncovers substantial fallout in adjacent docs, prefer splitting follow-ups such as:

- `071-root-readme-command-matrix-alignment.md`
- `072-root-readme-repo-map-and-docs-entrypoints.md`

Only create those if the task genuinely needs to branch.

## Suggested implementation steps

1. Re-read `README.md` end-to-end and classify each major section as accurate, stale, misleading, or incomplete.
2. Rework the repository layout and top-level orientation sections using the terminology settled in task `050`.
3. Recheck install, example, test, and build commands against the current repo state.
4. Coordinate with tasks `051` and `052` where they overlap, instead of creating contradictory wording.
5. Decide whether additional follow-up subtasks are needed or whether the root README can be updated directly in one pass.

## Likely files to inspect

- `README.md`
- `AGENTS.md`
- `package.json`
- `application/python/README.md`
- `plugins/AGENTS.md`
- `plugins/docs/index.md`