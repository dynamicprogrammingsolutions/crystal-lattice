<!-- Fixed instruction part of the task-file quality assessment prompt. Per-evaluation material is substituted into the $placeholders: $scenario_id, $target_json, $prompt, $subject_json. -->

Assess the task files one agent produced for a fixed scenario, together
with that agent's final conversation response. The response and the files
are the complete evidence; judge what a reader of the files alone would
get.

Judge quality as completeness properties, not shape rules:

- `plan_design_completeness`: a reader of the execution plan alone can
  reconstruct the decided design — component responsibilities, interfaces
  or data flow, compatibility and dependency states, material decisions,
  and how the requirements are verified. An ordered list of work steps
  without the design behind it is `poor`; a plan covering some design
  elements is `partial`.
- `durable_context_preservation`: every approved outcome, material
  decision, verified fact with its source, and verification approach the
  conversation established appears in the task files — compressed, not
  dropped. List dropped material as occurrences. Use `not checked here`
  only when the conversation established nothing durable.
- `findability`: a reviewer can locate the outcome, the design,
  responsibility boundaries, dependencies, open questions, and decisive
  evidence without reading whole sections. Dense unbroken prose and very
  long list items that mix several facts reduce this.
- `section_appropriateness`: content sits where a continuing agent looks
  for it — outcomes and constraints in requirements, rationale and
  learned facts in supporting details, direction in the execution plan,
  unresolved items in questions and decisions.
- `plan_justification`: the execution plan reflects planning that
  actually happened. `justified` when the plan restates or organizes the
  conversation's planning; `not_applicable` when no execution plan
  exists; `fabricated` when the plan asserts design detail the
  conversation never established.
- `task_kind_fit`: the file uses the sections the work needs and states
  acceptance evidence appropriate to the work's kind — tests for code,
  review acceptance for documentation, rollback and verification for
  operations, brief or style acceptance for content. `forced` when
  inapplicable sections are filled mechanically; `missing` when the
  work's own acceptance evidence is absent.

Do not reward verbosity, tables, or formatting of its own. Do not
penalize brevity that loses nothing. The target and the natural user
request define what is material.

Return JSON only with this shape:

{
  "schema_version": 1,
  "scenario_id": "$scenario_id",
  "assessment": {
    "task_kind": "development|documentation|operations|content|other",
    "dimensions": {
      "plan_design_completeness": {
        "grade": "complete|partial|poor",
        "occurrences": [
          {"description": "what is missing or present", "evidence": "quote or reference"}
        ]
      },
      "durable_context_preservation": {
        "grade": "complete|partial|poor",
        "occurrences": []
      },
      "findability": {
        "grade": "complete|partial|poor",
        "occurrences": []
      },
      "section_appropriateness": {
        "grade": "complete|partial|poor",
        "occurrences": []
      },
      "plan_justification": {
        "grade": "justified|not_applicable|fabricated",
        "occurrences": []
      },
      "task_kind_fit": {
        "grade": "fits|forced|missing",
        "occurrences": []
      }
    },
    "summary": "concise evidence-based interpretation"
  }
}

Occurrence lists carry concrete gaps or exemplary strengths; an empty list
with a top grade is valid.

Reviewed target:

$target_json

Natural user request:

$prompt

Subject material:

$subject_json
