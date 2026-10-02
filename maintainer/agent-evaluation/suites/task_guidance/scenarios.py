from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SUITE_ROOT = Path(__file__).resolve().parent
SCENARIO_ROOT = SUITE_ROOT / "scenarios"
TARGET_ROOT = SUITE_ROOT / "targets"


@dataclass(frozen=True)
class TaskGuidanceScenario:
    scenario_id: str
    markdown_file: str
    target_file: str
    fixture_id: str
    project_family: str
    category: str

    @property
    def markdown_path(self) -> Path:
        return SCENARIO_ROOT / self.markdown_file

    @property
    def target_path(self) -> Path:
        return TARGET_ROOT / self.target_file

    @property
    def prompt(self) -> str:
        return extract_blockquote(self.markdown_path, "## Natural request")

    @property
    def target(self) -> dict[str, Any]:
        value = json.loads(self.target_path.read_text(encoding="utf-8"))
        validate_target(value, expected=self)
        return value


SCENARIOS = (
    TaskGuidanceScenario(
        scenario_id="tg01-eleventy-archive-handoff",
        markdown_file="01-eleventy-archive-single-task.md",
        target_file="tg01-eleventy-archive-handoff.json",
        fixture_id="tg01-eleventy-archive",
        project_family="eleventy",
        category="handoff",
    ),
    TaskGuidanceScenario(
        scenario_id="tg02-fastapi-pagination-handoff",
        markdown_file="02-fastapi-pagination-single-task.md",
        target_file="tg02-fastapi-pagination-handoff.json",
        fixture_id="tg02-fastapi-pagination",
        project_family="fastapi",
        category="handoff",
    ),
    TaskGuidanceScenario(
        scenario_id="tg03-flask-vue-refresh-handoff",
        markdown_file="03-flask-vue-filter-refresh-single-task.md",
        target_file="tg03-flask-vue-refresh-handoff.json",
        fixture_id="tg03-flask-vue-refresh",
        project_family="flask-vue",
        category="handoff",
    ),
    TaskGuidanceScenario(
        scenario_id="tg04-flask-vue-discovery-decomposition",
        markdown_file="04-flask-vue-book-discovery-release.md",
        target_file="tg04-flask-vue-discovery-decomposition.json",
        fixture_id="tg04-flask-vue-discovery",
        project_family="flask-vue",
        category="decomposition",
    ),
    TaskGuidanceScenario(
        scenario_id="tg05-fastapi-multi-consumer-decomposition",
        markdown_file="05-fastapi-multi-consumer-query-capability.md",
        target_file="tg05-fastapi-multi-consumer-decomposition.json",
        fixture_id="tg05-fastapi-multi-consumer",
        project_family="fastapi",
        category="decomposition",
    ),
    TaskGuidanceScenario(
        scenario_id="tg06-eleventy-author-migration-decomposition",
        markdown_file="06-eleventy-author-metadata-migration.md",
        target_file="tg06-eleventy-author-migration-decomposition.json",
        fixture_id="tg06-eleventy-author-migration",
        project_family="eleventy",
        category="decomposition",
    ),
    TaskGuidanceScenario(
        scenario_id="tg07-eleventy-decided-work-tracking",
        markdown_file="07-eleventy-decided-work-tracking.md",
        target_file="tg07-eleventy-decided-work-tracking.json",
        fixture_id="tg01-eleventy-archive",
        project_family="eleventy",
        category="kind",
    ),
    TaskGuidanceScenario(
        scenario_id="tg08-eleventy-contributor-docs",
        markdown_file="08-eleventy-contributor-docs-task.md",
        target_file="tg08-eleventy-contributor-docs.json",
        fixture_id="tg01-eleventy-archive",
        project_family="eleventy",
        category="kind",
    ),
    TaskGuidanceScenario(
        scenario_id="tg09-flask-vue-deployment-runbook",
        markdown_file="09-flask-vue-deployment-runbook-task.md",
        target_file="tg09-flask-vue-deployment-runbook.json",
        fixture_id="tg03-flask-vue-refresh",
        project_family="flask-vue",
        category="kind",
    ),
    TaskGuidanceScenario(
        scenario_id="tg10-flask-vue-interface-copy",
        markdown_file="10-flask-vue-interface-copy-task.md",
        target_file="tg10-flask-vue-interface-copy.json",
        fixture_id="tg03-flask-vue-refresh",
        project_family="flask-vue",
        category="kind",
    ),
)


def scenario_by_id(scenario_id: str) -> TaskGuidanceScenario:
    for scenario in SCENARIOS:
        if scenario.scenario_id == scenario_id:
            return scenario
    raise KeyError(f"unknown task-guidance scenario: {scenario_id}")


def extract_blockquote(path: Path, heading: str) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        start = lines.index(heading) + 1
    except ValueError as error:
        raise ValueError(f"{path} has no heading {heading!r}") from error
    values: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        if line.startswith(">"):
            values.append(line[1:].lstrip())
        elif values and not line.strip():
            break
    if not values:
        raise ValueError(f"{path} has no blockquote under {heading!r}")
    return re.sub(r"\s+", " ", " ".join(values)).strip()


def validate_target(
    value: object,
    *,
    expected: TaskGuidanceScenario,
) -> None:
    if not isinstance(value, dict):
        raise ValueError("target must be an object")
    if value.get("schema_version") != 1:
        raise ValueError("target schema_version must be 1")
    if value.get("scenario_id") != expected.scenario_id:
        raise ValueError(f"target scenario_id must be {expected.scenario_id!r}")
    if value.get("category") != expected.category:
        raise ValueError(f"target category must be {expected.category!r}")
    project = value.get("project")
    if not isinstance(project, dict):
        raise ValueError("target project must be an object")
    if project.get("fixture_id") != expected.fixture_id:
        raise ValueError(f"target fixture_id must be {expected.fixture_id!r}")
    for key in ("title", "task_summary"):
        if not isinstance(value.get(key), str) or not value[key].strip():
            raise ValueError(f"target {key} must be a non-empty string")

    outcomes = value.get("approved_outcomes")
    if not isinstance(outcomes, list) or not outcomes:
        raise ValueError("target approved_outcomes must be a non-empty list")
    outcome_ids: set[str] = set()
    for outcome in outcomes:
        if not isinstance(outcome, dict):
            raise ValueError("approved outcome must be an object")
        outcome_id = outcome.get("id")
        description = outcome.get("outcome")
        if not isinstance(outcome_id, str) or not outcome_id:
            raise ValueError("approved outcome id must be non-empty")
        if outcome_id in outcome_ids:
            raise ValueError(f"duplicate approved outcome: {outcome_id}")
        outcome_ids.add(outcome_id)
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"{outcome_id} outcome must be non-empty")

    deliverables = value.get("coherent_deliverables")
    if not isinstance(deliverables, list) or not deliverables:
        raise ValueError("target coherent_deliverables must be non-empty")
    deliverable_ids: set[str] = set()
    for deliverable in deliverables:
        if not isinstance(deliverable, dict):
            raise ValueError("coherent deliverable must be an object")
        deliverable_id = deliverable.get("id")
        if not isinstance(deliverable_id, str) or not deliverable_id:
            raise ValueError("coherent deliverable id must be non-empty")
        if deliverable_id in deliverable_ids:
            raise ValueError(f"duplicate coherent deliverable: {deliverable_id}")
        deliverable_ids.add(deliverable_id)
        mapped = deliverable.get("outcomes")
        if (
            not isinstance(mapped, list)
            or not mapped
            or any(item not in outcome_ids for item in mapped)
        ):
            raise ValueError(
                f"{deliverable_id} outcomes must reference approved outcomes"
            )
        for key in ("title", "independent_value"):
            if (
                not isinstance(deliverable.get(key), str)
                or not deliverable[key].strip()
            ):
                raise ValueError(f"{deliverable_id} {key} must be non-empty")
        dependencies = deliverable.get("dependencies")
        if not isinstance(dependencies, list) or any(
            not isinstance(item, str) for item in dependencies
        ):
            raise ValueError(f"{deliverable_id} dependencies must be strings")

    sizes = value.get("acceptable_partition_sizes")
    if (
        not isinstance(sizes, list)
        or not sizes
        or any(not isinstance(item, int) or item < 1 for item in sizes)
    ):
        raise ValueError("acceptable_partition_sizes must contain positive integers")
    if expected.category == "decomposition" and len(deliverables) < 3:
        raise ValueError("decomposition targets need at least three deliverables")

    for key in (
        "acceptable_alternatives",
        "fragmentation_examples",
        "overpacking_examples",
        "important_crossings",
        "open_questions",
    ):
        items = value.get(key)
        if not isinstance(items, list) or any(
            not isinstance(item, str) or not item.strip() for item in items
        ):
            raise ValueError(f"target {key} must be a string list")

    if expected.category in ("handoff", "decomposition"):
        handoff = value.get("handoff")
        if not isinstance(handoff, dict):
            raise ValueError("target handoff must be an object")
        for key in ("retain_plan", "omit_plan", "fresh_agent_plan"):
            if not isinstance(handoff.get(key), str) or not handoff[key].strip():
                raise ValueError(f"target handoff {key} must be non-empty")

    # The plan content requirements are the committed plan target: what
    # a plan for this task must convey. Handoff and decomposition
    # scenarios declare them; other categories may add them later.
    if expected.category in ("handoff", "decomposition"):
        plan_target = value.get("plan_target")
        if not isinstance(plan_target, dict):
            raise ValueError("target plan_target must be an object")
        required_content = plan_target.get("required_content")
        if not isinstance(required_content, list) or not required_content:
            raise ValueError("plan_target required_content must be a non-empty list")
        requirement_ids: set[str] = set()
        for item in required_content:
            if not isinstance(item, dict):
                raise ValueError("plan content requirement must be an object")
            item_id = item.get("id")
            content = item.get("content")
            if not isinstance(item_id, str) or not item_id.strip():
                raise ValueError("plan content requirement id must be non-empty")
            if item_id in requirement_ids:
                raise ValueError(f"duplicate plan content requirement: {item_id}")
            requirement_ids.add(item_id)
            if not isinstance(content, str) or not content.strip():
                raise ValueError(f"{item_id} content must be non-empty")
            derived = item.get("derived_from", [])
            if not isinstance(derived, list) or any(
                source not in outcome_ids for source in derived
            ):
                raise ValueError(
                    f"{item_id} derived_from must reference approved outcomes"
                )
