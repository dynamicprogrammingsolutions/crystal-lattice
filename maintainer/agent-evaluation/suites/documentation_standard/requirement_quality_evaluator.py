from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

from .requirement_quality import (
    PRODUCER_CASES,
    SCENARIOS,
    RequirementQualityScenario,
)
from .support import AssertionFinding, REPOSITORY_ROOT


FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures"
ACCEPTED_BASELINE_PATH = (
    FIXTURE_ROOT / "accepted_requirement_quality_baseline.json"
)
ACCEPTED_ANCHORS_PATH = (
    FIXTURE_ROOT / "accepted_requirement_quality_anchors.json"
)
DEFAULT_ARTIFACT_ROOT = (
    REPOSITORY_ROOT / "tmp" / "agent-evaluation" / "documentation-standard"
)
EVALUATOR_PROMPT_VERSION = "v3"

REQUIREMENT_CLASSIFICATIONS = {
    "traceable_target_outcome",
    "valid_decomposition",
    "necessary_derived_behavior",
    "permissible_design_closure",
    "approved_quality_requirement",
    "unresolved_design_choice",
    "unsupported_public_behavior",
    "implementation_constraint",
    "acceptance_example_promoted",
    "wrong_record_role",
}
SIGNALS = {
    "compatibility_fragmentation",
    "database_query_strategy",
    "documentation_as_requirement",
    "exact_accessibility_mechanism",
    "filter_variant_fragmentation",
    "internal_parsing_mechanism",
    "missing_parameter_default_choice",
    "operation_fragmentation",
    "task_scope_as_requirement",
    "testing_as_requirement",
    "unapproved_empty_state",
    "unknown_filter_value_behavior",
    "verification_as_requirement",
}
COVERAGE_STATUSES = {"complete", "partial", "missing"}
EXPANSION_SEVERITIES = {"none", "low", "medium", "high"}
REVIEW_BURDENS = {"low", "medium", "high"}
ITEM_SEVERITIES = {"minor", "material"}
GROUPING_KINDS = {"valid_decomposition", "fragmentation", "overpacked"}
TESTING_LEVELS = {"complete", "partial", "missing"}
TESTING_LAYER_SELECTION = {"appropriate", "mixed", "poor"}
TESTING_CROSSING = {"present", "not_required", "missing"}
TESTING_DEGREES = {"none", "minor", "material"}
TESTING_FOCUS = {"focused", "mixed", "bloated"}


def load_accepted_dataset() -> dict[str, Any]:
    value = json.loads(ACCEPTED_BASELINE_PATH.read_text(encoding="utf-8"))
    validate_dataset(value, expected_dataset="initial-minimal-guidance-20260914")
    return value


def load_accepted_anchors() -> dict[str, Any]:
    value = json.loads(ACCEPTED_ANCHORS_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError("accepted anchors must use schema_version 1")
    if value.get("dataset_id") != "initial-minimal-guidance-20260914":
        raise ValueError("accepted anchors use an unexpected dataset_id")
    scenarios = value.get("scenarios")
    if not isinstance(scenarios, dict) or not scenarios:
        raise ValueError("accepted anchors need scenario mappings")
    return value


def load_task_dataset(
    artifact_root: Path = DEFAULT_ARTIFACT_ROOT,
) -> dict[str, Any]:
    return _load_task_dataset(
        artifact_root=artifact_root,
        dataset_id="current-task-guidance-20260914",
        test_prefix="requirement-task-current",
    )


def load_candidate_task_dataset(
    artifact_root: Path = DEFAULT_ARTIFACT_ROOT,
) -> dict[str, Any]:
    return _load_task_dataset(
        artifact_root=artifact_root,
        dataset_id="candidate-task-guidance-20260915",
        test_prefix="requirement-task-candidate",
    )


def load_candidate_v2_task_dataset(
    artifact_root: Path = DEFAULT_ARTIFACT_ROOT,
) -> dict[str, Any]:
    return _load_task_dataset(
        artifact_root=artifact_root,
        dataset_id="candidate-task-guidance-v2-20260915",
        test_prefix="requirement-task-candidate-v2",
    )


def load_candidate_v3_task_dataset(
    artifact_root: Path = DEFAULT_ARTIFACT_ROOT,
    *,
    scenario_ids: tuple[str, ...] | None = None,
    producer_cases: tuple[tuple[str, str], ...] = PRODUCER_CASES,
) -> dict[str, Any]:
    return _load_task_dataset(
        artifact_root=artifact_root,
        dataset_id="candidate-task-guidance-v3-20260915",
        test_prefix="requirement-task-candidate-v3",
        scenario_ids=scenario_ids,
        producer_cases=producer_cases,
    )


def _load_task_dataset(
    *,
    artifact_root: Path,
    dataset_id: str,
    test_prefix: str,
    scenario_ids: tuple[str, ...] | None = None,
    producer_cases: tuple[tuple[str, str], ...] = PRODUCER_CASES,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    selected_scenarios = scenario_ids or tuple(
        scenario.scenario_id for scenario in SCENARIOS
    )
    for scenario_id in selected_scenarios:
        for profile, effort in producer_cases:
            pattern = (
                f"*{test_prefix}-{scenario_id}-{effort}-*/"
                f"records/{test_prefix}.json"
            )
            paths = sorted((artifact_root / profile / "runs").glob(pattern))
            matching: list[tuple[Path, dict[str, Any]]] = []
            for path in paths:
                value = json.loads(path.read_text(encoding="utf-8"))
                producer = value.get("producer")
                if (
                    value.get("dataset_id") == dataset_id
                    and isinstance(producer, dict)
                    and producer.get("profile") == profile
                    and producer.get("reasoning_effort") == effort
                ):
                    matching.append((path, value))
            if not matching:
                raise FileNotFoundError(
                    f"missing task dataset record for "
                    f"{scenario_id}/{profile}/{effort}"
                )
            path, value = matching[-1]
            records.append(
                {
                    "candidate_id": f"{profile}-{effort}",
                    "scenario_id": scenario_id,
                    "producer": value["producer"],
                    "generated_files": value["generated_files"],
                    "changed_paths": value["changed_paths"],
                    "source_run_id": path.parents[1].name,
                    "source_record_sha256": hashlib.sha256(
                        path.read_bytes()
                    ).hexdigest(),
                    "guidance": value["guidance"],
                    "producer_result": {
                        "completed": any(
                            finding.get("name") == "run completed"
                            and finding.get("passed") is True
                            for finding in value.get("findings", [])
                            if isinstance(finding, dict)
                        ),
                        "response": value.get("response", ""),
                        "findings": value.get("findings", []),
                    },
                }
            )
    dataset = {
        "schema_version": 1,
        "dataset_id": dataset_id,
        "description": (
            "Task files and Draft plans produced with paired documentation "
            "and TASKS-v7 guidance."
        ),
        "records": records,
    }
    validate_dataset(
        dataset,
        expected_dataset=dataset_id,
    )
    return dataset


def validate_dataset(
    value: object,
    *,
    expected_dataset: str | None = None,
) -> None:
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError("requirement-quality dataset must use schema_version 1")
    dataset_id = value.get("dataset_id")
    if not isinstance(dataset_id, str) or not dataset_id:
        raise ValueError("requirement-quality dataset needs a dataset_id")
    if expected_dataset is not None and dataset_id != expected_dataset:
        raise ValueError(
            f"expected dataset {expected_dataset!r}, got {dataset_id!r}"
        )
    records = value.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("requirement-quality dataset needs records")
    keys: set[tuple[str, str]] = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("dataset records must be objects")
        scenario_id = record.get("scenario_id")
        candidate_id = record.get("candidate_id")
        if not isinstance(scenario_id, str) or not scenario_id:
            raise ValueError("dataset record needs scenario_id")
        if not isinstance(candidate_id, str) or not candidate_id:
            raise ValueError("dataset record needs candidate_id")
        key = (scenario_id, candidate_id)
        if key in keys:
            raise ValueError(f"duplicate dataset record: {key}")
        keys.add(key)
        files = record.get("generated_files")
        if not isinstance(files, dict):
            raise ValueError(f"dataset record {key} needs generated_files")
        producer_result = record.get("producer_result")
        producer_completed = (
            isinstance(producer_result, dict)
            and producer_result.get("completed") is True
        )
        if not files and producer_completed:
            raise ValueError(
                f"completed dataset record {key} needs generated_files"
            )
        if any(
            not isinstance(path, str)
            or not isinstance(content, str)
            or not content.strip()
            for path, content in files.items()
        ):
            raise ValueError(f"dataset record {key} has invalid generated_files")


def dataset_records_for_scenario(
    dataset: dict[str, Any],
    scenario: RequirementQualityScenario,
) -> list[dict[str, Any]]:
    values = [
        record
        for record in dataset["records"]
        if record["scenario_id"] == scenario.scenario_id
    ]
    expected = [f"{profile}-{effort}" for profile, effort in PRODUCER_CASES]
    by_id = {record["candidate_id"]: record for record in values}
    unknown = set(by_id).difference(expected)
    if not by_id or unknown:
        raise ValueError(
            f"dataset candidates for {scenario.scenario_id} are empty or "
            f"outside the producer matrix: unknown={sorted(unknown)!r}, "
            f"got={sorted(by_id)!r}"
        )
    return [
        by_id[candidate_id]
        for candidate_id in expected
        if candidate_id in by_id
    ]


def dataset_sha256(dataset: dict[str, Any]) -> str:
    rendered = json.dumps(dataset, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def build_evaluator_prompt(
    *,
    dataset_id: str,
    scenario: RequirementQualityScenario,
    target: dict[str, Any],
    candidates: list[dict[str, Any]],
    assess_testing: bool,
) -> str:
    target_value = {
        key: target[key]
        for key in (
            "scenario_id",
            "title",
            "task_summary",
            "project",
            "required_outcomes",
            "compatibility_constraints",
            "acceptable_grouping",
            "supporting_details",
            "optional_adjacent_work",
            "not_prescribed",
            "open_questions",
            "task_file_scope" if assess_testing else "task_scope",
        )
    }
    if assess_testing:
        target_value["testing_expectations"] = target["testing_expectations"]
    candidate_values = [
        {
            "candidate_id": value["candidate_id"],
            "producer": value["producer"],
            "generated_files": value["generated_files"],
            "producer_result": value.get(
                "producer_result",
                {"completed": True},
            ),
        }
        for value in candidates
    ]
    testing_instruction = (
        """
For each task-file candidate, also assess the execution plan's requirement
verification and optional additional implementation verification. Testing
quality is not inferred from the user prompt; assess the plan that the current
task guidance naturally produced. Map the scenario's required_evidence items,
check the important crossing, and identify unnecessary tests, missing tests,
implementation coupling, duplication, combinatorial expansion, and verification
focus.
"""
        if assess_testing
        else """
Set testing_plan_assessment to null for every candidate. These candidates are
specification/requirements documents rather than task execution plans.
"""
    )
    schema = {
        "schema_version": 1,
        "dataset_id": dataset_id,
        "scenario_id": scenario.scenario_id,
        "assessments": [
            {
                "candidate_id": "one supplied candidate_id",
                "requirement_assessment": {
                    "coverage_status": "complete | partial | missing",
                    "coverage": [
                        {
                            "outcome_id": "one required outcome id",
                            "status": "complete | partial | missing",
                            "evidence": "short exact or closely paraphrased candidate evidence",
                            "notes": "concise reasoning",
                        }
                    ],
                    "signals": ["zero or more allowed signal names"],
                    "added_obligations": [
                        {
                            "summary": "candidate obligation not already represented by a required outcome",
                            "classification": "one allowed requirement classification",
                            "severity": "minor | material",
                            "source_excerpt": "short candidate excerpt",
                            "rationale": "why this classification applies",
                        }
                    ],
                    "grouping": [
                        {
                            "kind": "valid_decomposition | fragmentation | overpacked",
                            "severity": "minor | material",
                            "summary": "concise grouping observation",
                        }
                    ],
                    "expansion_severity": "none | low | medium | high",
                    "review_burden": "low | medium | high",
                    "summary": "concise overall requirement assessment",
                },
                "testing_plan_assessment": (
                    {
                        "required_evidence": [
                            {
                                "expectation_index": 0,
                                "status": "complete | partial | missing",
                                "evidence": "short candidate evidence",
                            }
                        ],
                        "overall_coverage": "complete | partial | missing",
                        "layer_selection": "appropriate | mixed | poor",
                        "important_crossing": "present | not_required | missing",
                        "unnecessary_tests": ["concise items"],
                        "missing_tests": ["concise items"],
                        "implementation_coupling": ["concise items"],
                        "duplication": "none | minor | material",
                        "combinatorial_expansion": "none | minor | material",
                        "verification_focus": "focused | mixed | bloated",
                        "summary": "concise overall testing-plan assessment",
                    }
                    if assess_testing
                    else None
                ),
            }
        ],
    }
    allowed_classifications = ", ".join(sorted(REQUIREMENT_CLASSIFICATIONS))
    allowed_signals = ", ".join(sorted(SIGNALS))
    return f"""You are evaluating requirements and plans produced for one
small software-project task. Judge semantic completion and expansion, not
writing style. Do not improve the candidates and do not infer approval merely
because an idea is sensible.

Apply these distinctions:

- A traceable target outcome restates an approved required outcome.
- Valid decomposition separates independently meaningful completion outcomes.
- Fragmentation separates variants, operations, edge cases, protected
  surfaces, or test cases that would be clearer beneath one requirement.
- The fact that two details can regress independently is not by itself enough
  to justify separate requirements. Separate them when independent acceptance,
  deferral, ownership, evidence, or status tracking adds value. When one target
  groups protected surfaces and the candidate creates one row for every
  surface without such a reason, classify fragmentation.
- Necessary derived behavior is logically required for the approved target.
- Permissible design closure selects a choice the target explicitly leaves to
  the specification or task. A target saying that an exact mechanism is not
  prescribed is not permission to make that mechanism a requirement.
- A quality requirement is valid only when the target or an applicable
  approved constraint requires it.
- An unresolved design choice changes public behavior and should have been
  raised rather than silently made normative. When the target leaves public
  behavior unspecified and does not explicitly grant design latitude, every
  concrete selected behavior is an unresolved design choice even if it seems
  natural or necessary to implement something.
- A question or recommendation that explicitly remains outside requirements
  and implementation pending approval is not an added obligation and does not
  increase expansion severity. Classify it only if the candidate makes the
  proposed behavior part of the completion contract or selects it in the
  implementation plan before approval.
- Unsupported public behavior adds an observable contract not requested or
  approved.
- An implementation constraint mandates technology, architecture, algorithm,
  query shape, or another internal approach.
- Acceptance examples may clarify a requirement but should not automatically
  become separate completion obligations.
- Implementation work, tests, verification procedures, documentation work,
  and task mutation boundaries are wrong-record material when promoted into
  product requirements.
- Requirement count is not a verdict. Several rows can express one outcome,
  and one row can contain several obligations.
- For task-file candidates, assess product requirements from the Requirements
  checklist and any other text that claims a completed-state obligation.
  Implementation decisions and work steps are legitimate in the execution
  plan; classify them as requirement expansion only when the task promotes
  them into the product completion contract.
- If producer_result.completed is false or generated_files is empty, do not
  infer missing content. Mark requirement coverage and testing coverage
  missing, explain the incomplete producer result, and keep semantic expansion
  separate from the execution failure.

Use these expansion-severity definitions:

- none: no semantic addition and no fragmentation;
- low: at most a few minor details or useful design choices, with no material
  unsupported behavior, unresolved public contract, implementation constraint,
  or wrong-record obligation;
- medium: one material unresolved or unsupported choice, or several minor
  additions/fragmentation/wrong-record items that noticeably increase scope or
  review burden;
- high: multiple distinct material additions, a material implementation
  constraint, a material unsupported behavior combined with fragmentation, or
  cumulative additions that substantially enlarge the completion contract or
  human review burden.

Known signal meanings:

- compatibility_fragmentation: one grouped compatibility outcome is split into
  separate protected-surface requirements without an independent tracking
  reason;
- database_query_strategy: SQL, ORM, database-side slicing, or separate-count
  mechanics are made mandatory;
- documentation_as_requirement: documentation production or non-production is
  made a product requirement;
- exact_accessibility_mechanism: exact labels, ARIA attributes, relation
  attributes, landmarks, or markup techniques are required beyond the
  accessibility outcome;
- filter_variant_fragmentation: All, Read, and Unread variants of one filter
  contract are unnecessarily split;
- internal_parsing_mechanism: string parsing, truthiness, component state, or
  another internal mechanism is made normative;
- missing_parameter_default_choice: behavior for an omitted companion
  pagination parameter is selected although the target does not authorize it;
- operation_fragmentation: add, update, and delete variants of one refresh
  outcome are unnecessarily split;
- task_scope_as_requirement: mutation boundaries or task authorization are
  made product requirements;
- testing_as_requirement or verification_as_requirement: tests, test coverage,
  or verification work is made a product requirement;
- unapproved_empty_state: empty-collection behavior not required by the target
  is made normative;
- unknown_filter_value_behavior: unsupported query values receive an invented
  public contract.

Allowed added-obligation classifications:
{allowed_classifications}

Allowed signals:
{allowed_signals}

Use signals only when the candidate materially exhibits that pattern. Assess
producer identity and effort openly, but do not change the semantic target
because of them.

{testing_instruction}

Return JSON only, with no Markdown fence or explanatory text. Include every
candidate exactly once and every required outcome exactly once per candidate.
For task-file testing, include every required_evidence expectation exactly once
using its zero-based index. Keep excerpts and explanations concise; list only
material added obligations and grouping findings.

Required response shape:
{json.dumps(schema, indent=2)}

Dataset:
{dataset_id}

Hidden evaluator target:
{json.dumps(target_value, indent=2, sort_keys=True)}

Candidate outputs:
{json.dumps(candidate_values, indent=2, sort_keys=True)}
"""


def parse_evaluator_response_with_repairs(
    text: str,
) -> tuple[dict[str, Any], tuple[str, ...]]:
    value = text.strip()
    fenced = re.fullmatch(
        r"```(?:json)?\s*(\{.*\})\s*```",
        value,
        flags=re.DOTALL,
    )
    if fenced is not None:
        value = fenced.group(1)
    start = value.find("{")
    end = value.rfind("}")
    if start < 0 or end <= start:
        raise json.JSONDecodeError("no JSON object found", value, 0)
    value = value[start : end + 1]
    repairs: list[str] = []
    for _ in range(8):
        try:
            parsed = json.loads(value)
            break
        except json.JSONDecodeError as error:
            position = error.pos
            missing_candidate_close = (
                2 <= position < len(value)
                and value[position] == "{"
                and value[position - 1] == ","
                and value[position - 2] == "}"
                and value.startswith('{"candidate_id"', position)
            )
            missing_final_candidate_close = (
                1 <= position < len(value)
                and value[position] == "]"
                and value[position - 1] == "}"
                and value[position:] == "]}"
            )
            if missing_candidate_close:
                value = value[: position - 1] + "}" + value[position - 1 :]
                repairs.append(
                    "inserted missing outer candidate-closing brace before "
                    f"character {position}"
                )
                continue
            if missing_final_candidate_close:
                value = value[:position] + "}" + value[position:]
                repairs.append(
                    "inserted missing final candidate-closing brace before "
                    f"character {position}"
                )
                continue
            previous = position - 1
            while previous >= 0 and value[previous].isspace():
                previous -= 1
            trailing_comma = (
                position < len(value)
                and value[position] in "}]"
                and previous >= 0
                and value[previous] == ","
            )
            if trailing_comma:
                value = value[:previous] + value[previous + 1 :]
                repairs.append(
                    "removed trailing comma before closing delimiter near "
                    f"character {position}"
                )
                continue
            raise
    else:
        raise json.JSONDecodeError(
            "too many evaluator response repairs",
            value,
            0,
        )
    if not isinstance(parsed, dict):
        raise ValueError("semantic evaluator response must be a JSON object")
    return parsed, tuple(repairs)


def parse_evaluator_response(text: str) -> dict[str, Any]:
    parsed, _ = parse_evaluator_response_with_repairs(text)
    return parsed


def validate_evaluator_result(
    value: object,
    *,
    dataset_id: str,
    scenario: RequirementQualityScenario,
    target: dict[str, Any],
    candidate_ids: Iterable[str],
    assess_testing: bool,
) -> None:
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError("semantic evaluator result must use schema_version 1")
    if value.get("dataset_id") != dataset_id:
        raise ValueError("semantic evaluator dataset_id does not match")
    if value.get("scenario_id") != scenario.scenario_id:
        raise ValueError("semantic evaluator scenario_id does not match")
    assessments = value.get("assessments")
    if not isinstance(assessments, list):
        raise ValueError("semantic evaluator assessments must be a list")
    expected_candidates = set(candidate_ids)
    actual_candidates = {
        item.get("candidate_id")
        for item in assessments
        if isinstance(item, dict)
    }
    if actual_candidates != expected_candidates or len(assessments) != len(
        expected_candidates
    ):
        raise ValueError(
            "semantic evaluator candidates do not match: "
            f"expected={sorted(expected_candidates)!r}, "
            f"got={sorted(str(item) for item in actual_candidates)!r}"
        )
    outcome_ids = {
        item["id"]
        for item in target["required_outcomes"]
    }
    expected_testing = len(
        target.get("testing_expectations", {}).get("required_evidence", [])
    )
    for assessment in assessments:
        if not isinstance(assessment, dict):
            raise ValueError("semantic evaluator assessment must be an object")
        candidate_id = assessment["candidate_id"]
        requirement = assessment.get("requirement_assessment")
        if not isinstance(requirement, dict):
            raise ValueError(f"{candidate_id}: missing requirement_assessment")
        _require_enum(
            requirement,
            "coverage_status",
            COVERAGE_STATUSES,
            candidate_id,
        )
        _require_enum(
            requirement,
            "expansion_severity",
            EXPANSION_SEVERITIES,
            candidate_id,
        )
        _require_enum(
            requirement,
            "review_burden",
            REVIEW_BURDENS,
            candidate_id,
        )
        coverage = requirement.get("coverage")
        if not isinstance(coverage, list):
            raise ValueError(f"{candidate_id}: coverage must be a list")
        actual_outcomes = {
            item.get("outcome_id")
            for item in coverage
            if isinstance(item, dict)
        }
        if actual_outcomes != outcome_ids or len(coverage) != len(outcome_ids):
            raise ValueError(
                f"{candidate_id}: coverage outcomes do not match target"
            )
        for item in coverage:
            if not isinstance(item, dict):
                raise ValueError(f"{candidate_id}: invalid coverage item")
            _require_enum(item, "status", COVERAGE_STATUSES, candidate_id)
            _require_text(item, "evidence", candidate_id)
            _require_string(item, "notes", candidate_id)
        signals = requirement.get("signals")
        if (
            not isinstance(signals, list)
            or any(not isinstance(item, str) or item not in SIGNALS for item in signals)
            or len(signals) != len(set(signals))
        ):
            raise ValueError(f"{candidate_id}: invalid signals")
        additions = requirement.get("added_obligations")
        if not isinstance(additions, list):
            raise ValueError(f"{candidate_id}: added_obligations must be a list")
        for item in additions:
            if not isinstance(item, dict):
                raise ValueError(f"{candidate_id}: invalid added obligation")
            _require_enum(
                item,
                "classification",
                REQUIREMENT_CLASSIFICATIONS,
                candidate_id,
            )
            _require_enum(item, "severity", ITEM_SEVERITIES, candidate_id)
            for key in ("summary", "source_excerpt", "rationale"):
                _require_text(item, key, candidate_id)
        grouping = requirement.get("grouping")
        if not isinstance(grouping, list):
            raise ValueError(f"{candidate_id}: grouping must be a list")
        for item in grouping:
            if not isinstance(item, dict):
                raise ValueError(f"{candidate_id}: invalid grouping item")
            _require_enum(item, "kind", GROUPING_KINDS, candidate_id)
            _require_enum(item, "severity", ITEM_SEVERITIES, candidate_id)
            _require_text(item, "summary", candidate_id)
        _require_text(requirement, "summary", candidate_id)

        testing = assessment.get("testing_plan_assessment")
        if not assess_testing:
            if testing is not None:
                raise ValueError(
                    f"{candidate_id}: testing_plan_assessment must be null"
                )
            continue
        if not isinstance(testing, dict):
            raise ValueError(
                f"{candidate_id}: missing testing_plan_assessment"
            )
        evidence = testing.get("required_evidence")
        if not isinstance(evidence, list):
            raise ValueError(
                f"{candidate_id}: testing required_evidence must be a list"
            )
        actual_indexes = {
            item.get("expectation_index")
            for item in evidence
            if isinstance(item, dict)
        }
        if actual_indexes != set(range(expected_testing)) or len(evidence) != (
            expected_testing
        ):
            raise ValueError(
                f"{candidate_id}: testing evidence indexes do not match target"
            )
        for item in evidence:
            if not isinstance(item, dict):
                raise ValueError(
                    f"{candidate_id}: invalid testing evidence item"
                )
            _require_enum(item, "status", TESTING_LEVELS, candidate_id)
            _require_text(item, "evidence", candidate_id)
        _require_enum(
            testing,
            "overall_coverage",
            TESTING_LEVELS,
            candidate_id,
        )
        _require_enum(
            testing,
            "layer_selection",
            TESTING_LAYER_SELECTION,
            candidate_id,
        )
        _require_enum(
            testing,
            "important_crossing",
            TESTING_CROSSING,
            candidate_id,
        )
        for key in ("duplication", "combinatorial_expansion"):
            _require_enum(testing, key, TESTING_DEGREES, candidate_id)
        _require_enum(
            testing,
            "verification_focus",
            TESTING_FOCUS,
            candidate_id,
        )
        for key in (
            "unnecessary_tests",
            "missing_tests",
            "implementation_coupling",
        ):
            items = testing.get(key)
            if not isinstance(items, list) or any(
                not isinstance(item, str) or not item.strip() for item in items
            ):
                raise ValueError(f"{candidate_id}: invalid testing {key}")
        _require_text(testing, "summary", candidate_id)


def calibration_findings(
    result: dict[str, Any],
    *,
    anchors: dict[str, Any],
    scenario: RequirementQualityScenario,
) -> tuple[AssertionFinding, ...]:
    scenario_anchors = anchors["scenarios"][scenario.scenario_id]
    by_id = {
        item["candidate_id"]: item
        for item in result["assessments"]
    }
    findings: list[AssertionFinding] = []
    for candidate_id, allowed in scenario_anchors["allowed_coverage"].items():
        actual = by_id[candidate_id]["requirement_assessment"]["coverage_status"]
        findings.append(
            AssertionFinding(
                f"{candidate_id} coverage matches accepted interpretation",
                actual in allowed,
                f"actual={actual!r}, allowed={allowed!r}",
            )
        )
    for candidate_id, allowed in scenario_anchors[
        "allowed_expansion_severity"
    ].items():
        actual = by_id[candidate_id]["requirement_assessment"][
            "expansion_severity"
        ]
        findings.append(
            AssertionFinding(
                f"{candidate_id} expansion matches accepted interpretation",
                actual in allowed,
                f"actual={actual!r}, allowed={allowed!r}",
            )
        )
    for candidate_id, expected in scenario_anchors["required_signals"].items():
        actual = set(
            by_id[candidate_id]["requirement_assessment"]["signals"]
        )
        missing = sorted(set(expected) - actual)
        findings.append(
            AssertionFinding(
                f"{candidate_id} reproduces accepted semantic signals",
                not missing,
                f"missing={missing!r}, actual={sorted(actual)!r}",
            )
        )
    for candidate_id, alternatives in scenario_anchors.get(
        "required_any_signals",
        {},
    ).items():
        actual = set(
            by_id[candidate_id]["requirement_assessment"]["signals"]
        )
        missing_groups = [
            group
            for group in alternatives
            if not actual.intersection(group)
        ]
        findings.append(
            AssertionFinding(
                f"{candidate_id} reproduces accepted alternative signals",
                not missing_groups,
                (
                    f"missing_groups={missing_groups!r}, "
                    f"actual={sorted(actual)!r}"
                ),
            )
        )
    return tuple(findings)


def task_quality_findings(
    result: dict[str, Any],
) -> tuple[AssertionFinding, ...]:
    findings: list[AssertionFinding] = []
    disallowed = {
        "unresolved_design_choice",
        "unsupported_public_behavior",
        "implementation_constraint",
        "wrong_record_role",
    }
    for assessment in result["assessments"]:
        candidate_id = assessment["candidate_id"]
        requirement = assessment["requirement_assessment"]
        additions = requirement["added_obligations"]
        material_disallowed = [
            item
            for item in additions
            if item["severity"] == "material"
            and item["classification"] in disallowed
        ]
        material_fragmentation = [
            item
            for item in requirement["grouping"]
            if item["kind"] == "fragmentation"
            and item["severity"] == "material"
        ]
        findings.extend(
            (
                AssertionFinding(
                    f"{candidate_id} covers the approved requirements",
                    requirement["coverage_status"] == "complete",
                    requirement["summary"],
                ),
                AssertionFinding(
                    f"{candidate_id} avoids material semantic expansion",
                    not material_disallowed,
                    repr(material_disallowed),
                ),
                AssertionFinding(
                    f"{candidate_id} keeps requirement grouping proportionate",
                    not material_fragmentation,
                    repr(material_fragmentation),
                ),
            )
        )
        testing = assessment["testing_plan_assessment"]
        assert isinstance(testing, dict)
        findings.extend(
            (
                AssertionFinding(
                    f"{candidate_id} testing covers decisive evidence",
                    testing["overall_coverage"] == "complete",
                    testing["summary"],
                ),
                AssertionFinding(
                    f"{candidate_id} testing uses appropriate layers",
                    testing["layer_selection"] == "appropriate",
                    testing["summary"],
                ),
                AssertionFinding(
                    f"{candidate_id} testing includes the important crossing",
                    testing["important_crossing"] in {"present", "not_required"},
                    testing["summary"],
                ),
                AssertionFinding(
                    f"{candidate_id} testing avoids material duplication",
                    testing["duplication"] != "material",
                    repr(testing["unnecessary_tests"]),
                ),
                AssertionFinding(
                    f"{candidate_id} testing avoids combinatorial expansion",
                    testing["combinatorial_expansion"] != "material",
                    repr(testing["unnecessary_tests"]),
                ),
                AssertionFinding(
                    f"{candidate_id} testing avoids implementation coupling",
                    not testing["implementation_coupling"],
                    repr(testing["implementation_coupling"]),
                ),
                AssertionFinding(
                    f"{candidate_id} verification remains focused",
                    testing["verification_focus"] == "focused",
                    testing["summary"],
                ),
            )
        )
    return tuple(findings)


def _require_enum(
    value: dict[str, Any],
    key: str,
    allowed: set[str],
    candidate_id: str,
) -> None:
    item = value.get(key)
    if item not in allowed:
        raise ValueError(
            f"{candidate_id}: {key} must be one of {sorted(allowed)!r}, "
            f"got {item!r}"
        )


def _require_text(
    value: dict[str, Any],
    key: str,
    candidate_id: str,
) -> None:
    item = value.get(key)
    if not isinstance(item, str) or not item.strip():
        raise ValueError(f"{candidate_id}: {key} must be non-empty text")


def _require_string(
    value: dict[str, Any],
    key: str,
    candidate_id: str,
) -> None:
    if not isinstance(value.get(key), str):
        raise ValueError(f"{candidate_id}: {key} must be text")