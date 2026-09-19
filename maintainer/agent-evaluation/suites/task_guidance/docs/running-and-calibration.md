# Running and calibrating the task-guidance suite

> **Not implemented:** No task-guidance suite commands are available at this
> path yet. The existing human-operated workflow remains documented in
> `test/task_guidance/README.md`.

## Planned sequence

1. Validate the reviewed scenario contracts and canonical plans.
2. Run deterministic suite tests and Crystal Lattice message/tool preflights.
3. Run B0 with current guidance unchanged.
4. Review validity, semantic behavior, and efficiency variance.
5. Propose and approve the shortest B1 task-mechanics wording.
6. Run paired B1 cases and nondegradation checks.
7. Freeze B1.
8. Compile v3/v4 and optional v5 from one semantic rule set.
9. Run focused sensitive cases.
10. Run the full justified matrix only for the selected candidate.

## Planned identities

Cache and evidence identity will include:

- project and pinned revision;
- scenario contract and canonical stage input;
- task/plan variant;
- guidance bundle and compilation hash;
- instruction delivery;
- model and effort;
- stage prompt;
- run attempt.

Retries keep the canonical dataset identity and use a separate run-attempt key.

## Upstream gates

Semantic assessment starts only from structurally valid producer records.
Pairwise review starts only from structurally valid semantic records.
Behavioral assertion failures remain evidence and do not block downstream
interpretation.

## Calibration

B0 calibrates:

- scenario assertions;
- semantic targets;
- task topology normalization;
- fresh-agent handoff expectations;
- tool-call categories and variance;
- the need for a negative control.

B1 calibration requires human approval because it changes maintained task
guidance. Placement candidates are not created until B1 is accepted as the
safe baseline.

## Historical workflow

The existing CLI under `test/task_guidance/` remains the source for:

- imported planning sessions;
- retain-plan and omit-plan forks;
- deterministic assertions;
- empirical review;
- review-bundle generation.

Migration must preserve readable historical records or document a compatibility
path.