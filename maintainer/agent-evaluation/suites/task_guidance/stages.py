"""The stage catalog: what each stage the suite can run actually is.

``configuration.json`` declares which stages a category runs and each
stage's inputs; this catalog defines the fixed meaning of every stage name:
the workspace a run starts from, the earlier stage whose workspace and
session prefix a run shares (``parent``; ``None`` means a fresh session),
how the configuration expands one run, the config keys the stage takes,
the harness method that executes it, and the record file a run writes.

The catalog is consumed by the configuration tests (stage names and config
schemas), by consolidation and parametrization (expansion and record
names), and it is verified against behavior: the stage-mechanics tests run
each stage through the real kernel and assert the declared workspace
origin and parent linkage.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StageSpec:
    name: str
    workspace: str
    parent: str | None
    runs_per: str
    config: tuple[str, ...]
    executor: str
    record: str


STAGES: dict[str, StageSpec] = {
    "task-creation": StageSpec(
        name="task-creation",
        # A repo checkout at the pinned revision, replaced by the
        # scenario's fixture project and the compiled guidance; fresh session.
        workspace="fixture-project",
        parent=None,
        runs_per="scenario × producer cell",
        config=(),
        executor="run_task_creation",
        record="task-guidance-producer.json",
    ),
    "handoff-plan": StageSpec(
        name="handoff-plan",
        # A repo checkout plus the canonical handoff task file (one per
        # declared variant); fresh session — the file must stand alone.
        workspace="canonical-handoff",
        parent=None,
        runs_per="scenario × variant × producer cell",
        config=("variants",),
        executor="run_plan_from_handoff",
        record="task-guidance-handoff-plan.json",
    ),
    "continuation": StageSpec(
        name="continuation",
        # The task-creation run's workspace with the produced task files in
        # place, and that run's session as the prefix (continue_from).
        workspace="parent",
        parent="task-creation",
        runs_per="scenario × producer cell",
        config=(),
        executor="continue_same_agent_plan",
        record="task-guidance-same-agent-plan.json",
    ),
    "negative-control": StageSpec(
        name="negative-control",
        # A repo checkout plus the incomplete variant of the designated
        # scenario's canonical handoff task file; fresh session.
        workspace="canonical-handoff",
        parent=None,
        runs_per="the designated scenario × cell × variant",
        config=("scenario", "agent", "effort", "variant"),
        executor="run_negative_control",
        record="task-guidance-negative-control.json",
    ),
    "task-creation-assessment": StageSpec(
        name="task-creation-assessment",
        # A minimal stub workspace; the judged material arrives in the user
        # message; fresh session, run by the stage's declared agent.
        workspace="assessment-stub",
        parent=None,
        runs_per="scenario (the stage's declared agent)",
        config=("agent", "effort"),
        executor="run_assessment",
        record="task-guidance-semantic.json",
    ),
    "handoff-assessment": StageSpec(
        name="handoff-assessment",
        workspace="assessment-stub",
        parent=None,
        runs_per="scenario (the stage's declared agent)",
        config=("agent", "effort"),
        executor="run_assessment",
        record="task-guidance-handoff-semantic.json",
    ),
    "generated-plan": StageSpec(
        name="generated-plan",
        # A repo checkout at the pinned revision plus one producer run's
        # generated task files; fresh session — the files must stand alone.
        workspace="generated-task",
        parent="task-creation",
        runs_per="scenario × producer cell",
        config=(),
        executor="run_plan_from_generated",
        record="task-guidance-generated-plan.json",
    ),
    "task-quality-assessment": StageSpec(
        name="task-quality-assessment",
        # A minimal stub workspace; the judged material arrives in the user
        # message; fresh session, run by the stage's declared agent.
        workspace="assessment-stub",
        parent=None,
        runs_per="scenario (the stage's declared agent)",
        config=("agent", "effort"),
        executor="run_assessment",
        record="task-guidance-quality.json",
    ),
    "file-fidelity-assessment": StageSpec(
        name="file-fidelity-assessment",
        # A minimal stub workspace; the judged material (task files and
        # the producer's final response) arrives embedded in the user
        # message; fresh session, run by the stage's declared agent.
        workspace="assessment-stub",
        parent=None,
        runs_per="scenario (the stage's declared agent)",
        config=("agent", "effort"),
        executor="run_assessment",
        record="task-guidance-file-fidelity.json",
    ),
    "file-readability-assessment": StageSpec(
        name="file-readability-assessment",
        # A minimal stub workspace; the judged material (task files and
        # measured per-section structure facts) arrives embedded in the
        # user message; fresh session, run by the stage's declared agent.
        workspace="assessment-stub",
        parent=None,
        runs_per="scenario (the stage's declared agent)",
        config=("agent", "effort"),
        executor="run_assessment",
        record="task-guidance-file-readability.json",
    ),
    "plan-content-assessment": StageSpec(
        name="plan-content-assessment",
        # A minimal stub workspace; the judged material (one presented
        # plan) arrives embedded in the user message; fresh session,
        # run by the stage's declared agent. Subjects are the plan-stage
        # runs: fresh-agent plans per variant, same-agent continuations,
        # and the designated negative control.
        workspace="assessment-stub",
        parent=None,
        runs_per="scenario (the stage's declared agent)",
        config=("agent", "effort"),
        executor="run_assessment",
        record="task-guidance-plan-content.json",
    ),
}
