from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .support import GuidanceSource, PACKAGE_ROOT, SPEC_ROOT, extract_blockquote, extract_section


TARGET_DIR = SPEC_ROOT / "targets"
GUIDANCE_VARIANT_ROOT = (
    PACKAGE_ROOT
    / "suites"
    / "documentation_standard"
    / "guidance_variants"
    / "requirement-minimal"
)
CURRENT_TASK_GUIDANCE_PATHS = (
    "docs/development/documentation.md",
    "agents/TASKS-v7.md",
)
CURRENT_TASK_GUIDANCE_REVISION = (
    "73a2f4bf9d326118f9dc8b87c2e57b9c75fe8f11"
)
PRODUCER_CASES = (
    ("glm", "low"),
    ("glm", "high"),
    ("glm", "max"),
    ("gpt", "medium"),
    ("gpt", "high"),
    ("gpt", "xhigh"),
    ("gpt", "max"),
)


@dataclass(frozen=True)
class RequirementQualityScenario:
    scenario_id: str
    spec_file: str
    target_file: str
    fixture_id: str
    package_prefix: str
    project_name: str
    project_kind: str
    upstream: str | None = None
    upstream_revision: str | None = None

    @property
    def spec_path(self) -> Path:
        return SPEC_ROOT / self.spec_file

    @property
    def target_path(self) -> Path:
        return TARGET_DIR / self.target_file


CONTROL_SCENARIOS = (
    RequirementQualityScenario(
        scenario_id="30-batch-enqueue",
        spec_file="30-batch-enqueue-requirement-quality.md",
        target_file="30-batch-enqueue.json",
        fixture_id="requirement-quality-batch",
        package_prefix="packages/offline-queue/docs/development/",
        project_name="offline-queue",
        project_kind="package API control",
    ),
    RequirementQualityScenario(
        scenario_id="31-request-timeout",
        spec_file="31-request-timeout-requirement-quality.md",
        target_file="31-request-timeout.json",
        fixture_id="requirement-quality-timeout",
        package_prefix="packages/request-client/docs/development/",
        project_name="request-client",
        project_kind="package API control",
    ),
    RequirementQualityScenario(
        scenario_id="32-report-output",
        spec_file="32-report-output-requirement-quality.md",
        target_file="32-report-output.json",
        fixture_id="requirement-quality-output",
        package_prefix="packages/report-cli/docs/development/",
        project_name="report-cli",
        project_kind="package CLI control",
    ),
)

PRIMARY_SCENARIOS = (
    RequirementQualityScenario(
        scenario_id="33-eleventy-archive-pagination",
        spec_file="33-eleventy-archive-pagination.md",
        target_file="33-eleventy-archive-pagination.json",
        fixture_id="requirement-quality-eleventy",
        package_prefix="docs/development/",
        project_name="Eleventy Base Blog",
        project_kind="public static website",
        upstream="https://github.com/11ty/eleventy-base-blog",
        upstream_revision="26b26106d7fbb30b7b40d9ef52589d10ddbcb462",
    ),
    RequirementQualityScenario(
        scenario_id="34-fastapi-notes-pagination",
        spec_file="34-fastapi-notes-pagination.md",
        target_file="34-fastapi-notes-pagination.json",
        fixture_id="requirement-quality-fastapi",
        package_prefix="docs/development/",
        project_name="FastAPI CRUD Async",
        project_kind="public REST API with a large-response performance concern",
        upstream="https://github.com/testdrivenio/fastapi-crud-async",
        upstream_revision="4fa7ae952ece61e228135285de1b6a5ff65a1dc8",
    ),
    RequirementQualityScenario(
        scenario_id="35-flask-vue-book-filter",
        spec_file="35-flask-vue-book-filter.md",
        target_file="35-flask-vue-book-filter.json",
        fixture_id="requirement-quality-flask-vue",
        package_prefix="docs/development/",
        project_name="Flask-Vue CRUD",
        project_kind="user-facing full-stack web application",
        upstream="https://github.com/testdrivenio/flask-vue-crud",
        upstream_revision="be91da59a10d07384537c2f76f4505eb344d1682",
    ),
)

SCENARIOS = PRIMARY_SCENARIOS
ALL_SCENARIOS = (*PRIMARY_SCENARIOS, *CONTROL_SCENARIOS)


def scenario_by_id(scenario_id: str) -> RequirementQualityScenario:
    for scenario in ALL_SCENARIOS:
        if scenario.scenario_id == scenario_id:
            return scenario
    raise KeyError(f"unknown requirement-quality scenario: {scenario_id}")


def load_target(scenario: RequirementQualityScenario) -> dict[str, Any]:
    value = json.loads(scenario.target_path.read_text(encoding="utf-8"))
    validate_target(value, expected_id=scenario.scenario_id)
    return value


def validate_target(value: object, *, expected_id: str) -> None:
    if not isinstance(value, dict):
        raise ValueError("target must be a JSON object")
    if value.get("schema_version") != 1:
        raise ValueError("target schema_version must be 1")
    if value.get("scenario_id") != expected_id:
        raise ValueError(
            f"target scenario_id must be {expected_id!r}, got "
            f"{value.get('scenario_id')!r}"
        )
    for key in ("title", "task_summary"):
        if not isinstance(value.get(key), str) or not value[key].strip():
            raise ValueError(f"target {key} must be a non-empty string")

    outcomes = value.get("required_outcomes")
    if not isinstance(outcomes, list) or not 3 <= len(outcomes) <= 8:
        raise ValueError("target required_outcomes must contain 3 to 8 entries")
    outcome_ids: set[str] = set()
    for outcome in outcomes:
        if not isinstance(outcome, dict):
            raise ValueError("each required outcome must be an object")
        outcome_id = outcome.get("id")
        description = outcome.get("outcome")
        reason = outcome.get("why_required")
        if not isinstance(outcome_id, str) or not outcome_id.strip():
            raise ValueError("each required outcome needs a non-empty id")
        if outcome_id in outcome_ids:
            raise ValueError(f"duplicate required outcome id: {outcome_id}")
        outcome_ids.add(outcome_id)
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"{outcome_id} needs a non-empty outcome")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"{outcome_id} needs a non-empty why_required")

    for key in (
        "compatibility_constraints",
        "acceptable_grouping",
        "supporting_details",
        "optional_adjacent_work",
        "not_prescribed",
        "open_questions",
    ):
        items = value.get(key)
        if not isinstance(items, list) or any(
            not isinstance(item, str) or not item.strip() for item in items
        ):
            raise ValueError(f"target {key} must be a list of non-empty strings")

    project = value.get("project")
    if project is not None:
        if not isinstance(project, dict):
            raise ValueError("target project must be an object")
        for key in ("name", "kind", "upstream", "revision"):
            item = project.get(key)
            if not isinstance(item, str) or not item.strip():
                raise ValueError(f"target project {key} must be a non-empty string")
        revision = project["revision"]
        if len(revision) != 40 or any(
            character not in "0123456789abcdef" for character in revision
        ):
            raise ValueError("target project revision must be a lowercase Git SHA")

    task_scope = value.get("task_scope")
    if task_scope is not None and (
        not isinstance(task_scope, list)
        or not task_scope
        or any(not isinstance(item, str) or not item.strip() for item in task_scope)
    ):
        raise ValueError("target task_scope must be a non-empty string list")

    task_file_scope = value.get("task_file_scope")
    if task_file_scope is not None and (
        not isinstance(task_file_scope, list)
        or not task_file_scope
        or any(
            not isinstance(item, str) or not item.strip()
            for item in task_file_scope
        )
    ):
        raise ValueError("target task_file_scope must be a non-empty string list")

    testing = value.get("testing_expectations")
    if testing is not None:
        if not isinstance(testing, dict):
            raise ValueError("target testing_expectations must be an object")
        for key in ("required_evidence", "avoid"):
            items = testing.get(key)
            if (
                not isinstance(items, list)
                or not items
                or any(
                    not isinstance(item, str) or not item.strip()
                    for item in items
                )
            ):
                raise ValueError(
                    f"target testing_expectations {key} must be a "
                    "non-empty string list"
                )
        crossing = testing.get("important_crossing")
        if not isinstance(crossing, str) or not crossing.strip():
            raise ValueError(
                "target testing_expectations important_crossing must be "
                "a non-empty string"
            )


def target_sha256(scenario: RequirementQualityScenario) -> str:
    return hashlib.sha256(scenario.target_path.read_bytes()).hexdigest()


def scenario_prompt(scenario: RequirementQualityScenario) -> str:
    return extract_blockquote(scenario.spec_path, "## Exact user prompt")


def scenario_task_file_prompt(scenario: RequirementQualityScenario) -> str:
    return extract_blockquote(
        scenario.spec_path,
        "## Exact task-file user prompt",
    )


def scenario_fixture_facts(scenario: RequirementQualityScenario) -> str:
    return extract_section(scenario.spec_path, "## Fixture facts")


def scenario_project_context(scenario: RequirementQualityScenario) -> str:
    return extract_section(scenario.spec_path, "## Project context")


def requirement_minimal_guidance_source() -> GuidanceSource:
    return GuidanceSource(
        name="requirement-minimal-v1",
        root=GUIDANCE_VARIANT_ROOT,
        paths=(
            "AGENTS.md",
            "docs/development/documentation.md",
        ),
    )


def current_task_guidance_source() -> GuidanceSource:
    return GuidanceSource(
        name="current-task-guidance-v1",
        revision=CURRENT_TASK_GUIDANCE_REVISION,
        paths=CURRENT_TASK_GUIDANCE_PATHS,
    )


def candidate_task_guidance_source() -> GuidanceSource:
    return GuidanceSource(
        name="candidate-task-guidance-v2",
        paths=CURRENT_TASK_GUIDANCE_PATHS,
    )