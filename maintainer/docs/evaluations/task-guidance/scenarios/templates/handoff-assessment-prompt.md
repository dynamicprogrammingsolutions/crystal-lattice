<!-- Fixed instruction part of the handoff semantic assessment prompt. Per-evaluation material is substituted into the $placeholders: $scenario_id, $target_json, $records_json. -->

Assess whether each task handoff and resulting plan would let another agent
continue correctly without the original conversation or broad rediscovery.

Use the reviewed target as the authority. Judge the task and plan together:
requirements and approved conditions, verified facts and source pointers,
material decisions and questions, exclusions, dependencies, testing
boundaries, documentation work, and plan status. An omit-plan task must not
contain disguised implementation direction, but the later plan must still be
complete. A retained-plan task should let the later agent reuse the plan rather
than reconstruct it unnecessarily.

Tool-call efficiency is secondary. Interpret it only after plan quality. Do not
reward a low call count when the plan omits outcomes or invents unsupported
behavior.

This is a read-only planning stage. Do not penalize a plan because newly
verified details remain in the response rather than being written back into
the task file; file mutation is prohibited here. Judge whether the presented
plan is complete and whether the durable task was sufficient to produce it.

The `incomplete` variant is an intentional negative control. It should require
more reconstruction or produce lower-quality planning than a complete handoff;
assess the result rather than assuming failure from the label.

Return JSON only:

{
  "schema_version": 1,
  "scenario_id": "$scenario_id",
  "assessments": [
    {
      "stage": "fresh-agent|same-agent",
      "variant": "retain|omit|incomplete|generated-task",
      "producer": {"profile": "glm|gpt", "reasoning_effort": "..."},
      "plan_coverage": "complete|partial|poor",
      "missing_outcomes": ["OUTCOME-ID"],
      "lost_facts_or_decisions": ["description"],
      "invented_scope_or_decisions": ["description"],
      "testing_boundary": "decisive|partial|poor",
      "documentation_boundary": "appropriate|partial|poor",
      "task_self_contained": true,
      "broad_rediscovery": true,
      "handoff_quality_score": 0,
      "efficiency_interpretation": "concise evidence-based interpretation",
      "summary": "concise evidence-based interpretation"
    }
  ]
}

Scores are integers from 0 through 100. `broad_rediscovery` is true only when
the agent repeated substantial investigation that a complete task should have
made unnecessary.

Reviewed target:

$target_json

Handoff and plan records:

$records_json
