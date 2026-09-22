"""Task-guidance result-package adapter and command-line entry point.

The adapter selects the frozen consolidated records of one completed
task-guidance evaluation plus its raw run directories and produces a durable
result package using the shared ``agent_eval.result_packages`` support and the
Crystal Lattice review projection. Collection never invokes a producer,
handoff, continuation, or assessor model.

The package is review-first and self-contained. Each run directory — subject
runs and assessor runs alike — holds a concise full-session Markdown
transcript (prompt and response included verbatim as conversation turns, with
header links to the effective config and delivered instructions), the generated
task files, and one slim ``run.json`` metadata record. Assessor run
directories additionally hold ``results.md``, the readable rendering of the
judgments. Each scenario holds a self-contained copy of its reviewed target.
Shared directories hold the full sanitized effective configs and the compiled
system messages, each committed once and referenced by every run; system
messages are named by provider and content hash. Only the manifest, run
records, the aggregate status record, configs, and the report configuration
are machine-readable.

The scenario definitions (targets, prompts, and the fixed prompt templates)
are exported separately by ``extract-scenarios`` into the ``scenarios/``
documentation tree; git tracks their evolution between evaluations while each
result package freezes its own copies. The two exports do not reference each
other.

Commands:

- ``extract-scenarios`` writes the scenario definitions export from the suite
  sources;
- ``collect`` writes the committed package records from the frozen dataset
  and raw runs, reconstructing GPT system messages from the preserved runtime
  sources with SHA-256 verification;
- ``render`` regenerates the navigation, matrix, and cost views from the
  committed package alone;
- ``check`` verifies manifest hashes and byte-for-byte regeneration.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from posixpath import relpath
from typing import Any, Iterable, Mapping, Sequence

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
for import_root in (REPOSITORY_ROOT, PACKAGE_ROOT / "src"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from agent_eval.crystal_lattice import (  # noqa: E402
    project_effective_config_view,
    project_session_review,
    render_session_markdown,
)
from agent_eval.result_packages import (  # noqa: E402
    CollectedFile,
    GeneratedView,
    PackageRecords,
    apply_replacements,
    availability,
    check_result_package,
    collect_result_package,
    render_json_text,
    render_result_package,
    sha256_text,
)

from .artifacts import record_paths  # noqa: E402
from .fixtures import TaskGuidanceWorkspaceFactory  # noqa: E402
from .handoff_semantic import HANDOFF_ASSESSMENT_PROMPT_TEMPLATE  # noqa: E402
from .handoffs import (  # noqa: E402
    PLAN_PROMPT,
    CanonicalHandoffWorkspaceFactory,
)
from .results import (  # noqa: E402
    _handoff_identity,
    _producer_identity,
    render_summary,
)
from .runner import (  # noqa: E402
    PROFILES,
    WorkspaceAwareEnvironment,
    _project_config_for_profile,
    _reload_context_with_defaults,
    _runtime_config_root,
)
from .scenarios import SCENARIOS  # noqa: E402
from .semantic import (  # noqa: E402
    QUALITY_DIMENSIONS,
    TASK_CREATION_ASSESSMENT_PROMPT_TEMPLATE,
)

SUITE_ROOT = PACKAGE_ROOT / "suites" / "task_guidance"
DEFAULT_ARTIFACT_ROOT = REPOSITORY_ROOT / "tmp" / "agent-evaluation" / "task-guidance"
DEFAULT_RESULTS_ROOT = SUITE_ROOT / "fixtures" / "results"
DEFAULT_PACKAGES_ROOT = (
    REPOSITORY_ROOT
    / "maintainer"
    / "docs"
    / "evaluations"
    / "task-guidance"
    / "results"
)
DEFAULT_SCENARIOS_ROOT = (
    REPOSITORY_ROOT
    / "maintainer"
    / "docs"
    / "evaluations"
    / "task-guidance"
    / "scenarios"
)
REPORT_CONFIG_SOURCE = SUITE_ROOT / "result_report_config.toml"
GENERATOR_VERSION = "task-guidance-result-package-v3"

PRODUCER_RECORD = "task-guidance-producer.json"
HANDOFF_RECORD = "task-guidance-handoff-plan.json"
SAME_AGENT_RECORD = "task-guidance-same-agent-plan.json"
NEGATIVE_CONTROL_RECORD = "task-guidance-negative-control.json"
SEMANTIC_RECORD = "task-guidance-semantic.json"
HANDOFF_SEMANTIC_RECORD = "task-guidance-handoff-semantic.json"

KIND_TASK_CREATION = "task-creation"
KIND_PLAN_RETAIN = "plan-retain"
KIND_PLAN_OMIT = "plan-omit"
KIND_CONTINUATION = "continuation"
KIND_CONTROL = "control"


@dataclass(frozen=True)
class DatasetSpec:
    key: str
    dataset_id: str
    label: str
    package_name: str
    producer_attempt: str
    handoff_attempt: str
    semantic_attempt: str
    bundle: Path

    @property
    def frozen_results(self) -> Path:
        return DEFAULT_RESULTS_ROOT / f"task_guidance_{self.key}_results.json"


DATASETS: dict[str, DatasetSpec] = {
    "b0": DatasetSpec(
        key="b0",
        dataset_id="task-guidance-b0-20260919",
        label="current-guidance baseline",
        package_name="20260919-current-guidance-b0",
        producer_attempt="b0-v5-r1",
        handoff_attempt="b0-v5-r1",
        semantic_attempt="b0-metrics1",
        bundle=REPOSITORY_ROOT / "maintainer" / "guidance" / "current",
    ),
    "b1": DatasetSpec(
        key="b1",
        dataset_id="task-guidance-b1-20260919",
        label="task-mechanics candidate",
        package_name="20260919-task-mechanics-b1",
        producer_attempt="b1-v1-r1",
        handoff_attempt="b1-v1-r1",
        semantic_attempt="b1-metrics1",
        bundle=REPOSITORY_ROOT
        / "maintainer"
        / "guidance"
        / "candidates"
        / "task-mechanics-b1",
    ),
}


def _dirname(path: str) -> str:
    return str(PurePosixPath(path).parent)


def _link(target: str, page: str) -> str:
    return relpath(target, _dirname(page))


def extract_scenarios(*, output_dir: Path) -> Path:
    """Write the scenario definitions export from the suite sources.

    The export holds the evaluation's scenario definitions — reviewed
    targets, exact producer prompts, and the fixed prompt templates — in a
    form meant for human review. Scenario definitions may change between
    evaluations; git tracks the evolution of this tree while each result
    package freezes its own copies of the material it was produced with.
    """

    files: list[tuple[str, str]] = []
    files.append(
        (
            "templates/handoff-plan-prompt.md",
            _generated_note(
                "Fixed instruction sent to a fresh planning agent together with"
                " a task file; asks for the Draft implementation plan without"
                " modifying files."
            )
            + PLAN_PROMPT
            + "\n",
        )
    )
    files.append(
        (
            "templates/task-creation-assessment-prompt.md",
            _generated_note(
                "Fixed instruction part of the task-creation semantic"
                " assessment prompt. Per-evaluation material is substituted"
                " into the $placeholders: $scenario_id, $target_json,"
                " $prompt, $records_json."
            )
            + TASK_CREATION_ASSESSMENT_PROMPT_TEMPLATE.template,
        )
    )
    files.append(
        (
            "templates/handoff-assessment-prompt.md",
            _generated_note(
                "Fixed instruction part of the handoff semantic assessment"
                " prompt. Per-evaluation material is substituted into the"
                " $placeholders: $scenario_id, $target_json, $records_json."
            )
            + HANDOFF_ASSESSMENT_PROMPT_TEMPLATE.template,
        )
    )
    for scenario in SCENARIOS:
        scenario_id = scenario.scenario_id
        files.append(
            (
                f"{scenario_id}/target.md",
                f"# Reviewed target — {scenario_id}\n\n"
                + "\n".join(_target_markdown(scenario.target)).rstrip()
                + "\n",
            )
        )
        files.append((f"{scenario_id}/prompt.md", scenario.prompt.rstrip() + "\n"))

    lines = [
        "# Task-guidance evaluation scenarios",
        "",
        "Scenario definitions for the task-guidance evaluation suite,"
        " generated from the suite sources in"
        " `maintainer/agent-evaluation/suites/task_guidance/`"
        " (`result_package.py extract-scenarios`).",
        "",
        "These definitions may change between evaluations; git tracks their"
        " evolution here while each result package under `../results/`"
        " freezes its own copies of the material it was produced with.",
        "",
        "## Prompt templates",
        "",
        "| Template | Used by |",
        "|---|---|",
        "| [handoff-plan-prompt.md](templates/handoff-plan-prompt.md) |"
        " fresh planning agents in handoff scenarios |",
        "| [task-creation-assessment-prompt.md]"
        "(templates/task-creation-assessment-prompt.md) |"
        " task-creation semantic assessor |",
        "| [handoff-assessment-prompt.md]"
        "(templates/handoff-assessment-prompt.md) |"
        " handoff semantic assessor |",
        "",
        "## Scenarios",
        "",
        "| Scenario | Reviewed target | Producer prompt |",
        "|---|---|---|",
    ]
    for scenario in SCENARIOS:
        scenario_id = scenario.scenario_id
        lines.append(
            f"| `{scenario_id}`"
            f" | [target]({scenario_id}/target.md)"
            f" | [prompt]({scenario_id}/prompt.md) |"
        )
    files.append(("index.md", "\n".join(lines) + "\n"))

    for relative, content in sorted(files):
        target = output_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return output_dir


def _generated_note(note: str) -> str:
    return f"<!-- {note} -->\n\n"


def collect(
    dataset: DatasetSpec,
    *,
    package_dir: Path,
    artifact_root: Path,
    frozen_path: Path,
    cells: Sequence[str] | None = None,
    reconstruct: bool = True,
) -> Path:
    """Collect one durable result package without any model request."""

    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    if frozen.get("dataset_id") != dataset.dataset_id:
        raise ValueError(
            f"frozen dataset {frozen.get('dataset_id')!r} does not match"
            f" dataset {dataset.key!r} ({dataset.dataset_id!r})"
        )
    selected_cells = _parse_cells(cells)
    discovery = _discover_runs(dataset, artifact_root, frozen)
    files: list[CollectedFile] = []
    runs: list[dict[str, Any]] = []
    system_messages = _SystemMessageStore()
    configs = _ConfigStore()

    files.append(
        CollectedFile(
            relative_path="aggregate.json",
            content=render_json_text(
                {
                    "schema_version": 1,
                    "dataset_id": frozen["dataset_id"],
                    "label": frozen["label"],
                    "attempts": frozen["attempts"],
                    "status": frozen["status"],
                    "semantic_quality": frozen["semantic_quality"],
                    "invalid_records": [
                        {"group": group, "record": record}
                        for group in (
                            "producer_records",
                            "handoff_records",
                            "same_agent_records",
                        )
                        for record in frozen.get(group, ())
                        if record.get("valid") is False
                    ],
                    "provider_blocker_records": frozen.get(
                        "provider_blocker_records", []
                    ),
                }
            ),
            provenance={
                "source": "frozen consolidated dataset",
                "path": str(frozen_path.relative_to(REPOSITORY_ROOT)),
                "sha256": sha256_text(frozen_path.read_text(encoding="utf-8")),
            },
        )
    )

    for scenario in SCENARIOS:
        if selected_cells is not None and not any(
            cell[0] == scenario.scenario_id for cell in selected_cells
        ):
            continue
        _collect_scenario(
            scenario,
            dataset=dataset,
            frozen=frozen,
            discovery=discovery,
            artifact_root=artifact_root,
            selected_cells=selected_cells,
            reconstruct=reconstruct,
            system_messages=system_messages,
            configs=configs,
            runs=runs,
            files=files,
        )

    files.extend(system_messages.files())
    files.extend(configs.files())
    identity = {
        "name": dataset.package_name,
        "label": frozen["label"],
        "dataset_id": frozen["dataset_id"],
        "suite": "task-guidance",
        "attempts": frozen["attempts"],
        "scenario_count": len(
            {scenario.scenario_id for scenario in SCENARIOS}
            if selected_cells is None
            else {cell[0] for cell in selected_cells}
        ),
        "partial": selected_cells is not None,
    }
    collect_result_package(
        package_dir,
        identity=identity,
        runs=runs,
        files=files,
        report_config_text=REPORT_CONFIG_SOURCE.read_text(encoding="utf-8"),
        generator_version=GENERATOR_VERSION,
        replace=True,
    )
    render_result_package(
        package_dir, view_builders=[_build_index_views, _build_case_views]
    )
    problems = check_result_package(
        package_dir, view_builders=[_build_index_views, _build_case_views]
    )
    if problems:
        raise RuntimeError(
            "collected package failed its own check:\n" + "\n".join(problems)
        )
    return package_dir


def _parse_cells(cells: Sequence[str] | None) -> list[tuple[str, str, str]] | None:
    if not cells:
        return None
    parsed: list[tuple[str, str, str]] = []
    for cell in cells:
        parts = tuple(cell.split(":"))
        if len(parts) != 3:
            raise ValueError(f"cell must be scenario:profile:effort, got {cell!r}")
        parsed.append(parts)
    return parsed


def _discover_runs(
    dataset: DatasetSpec,
    artifact_root: Path,
    frozen: Mapping[str, Any],
) -> dict[str, Path]:
    """Map each frozen record identity to its raw run directory."""

    mapping: dict[str, Path] = {}
    groups = (
        (PRODUCER_RECORD, "producer_records", _producer_identity),
        (HANDOFF_RECORD, "handoff_records", _handoff_identity),
        (SAME_AGENT_RECORD, "same_agent_records", _producer_identity),
        (NEGATIVE_CONTROL_RECORD, "negative_control_records", _handoff_identity),
    )
    for record_name, group, identity_of in groups:
        wanted = {
            identity_of(record)
            for record in frozen.get(group, ())
            if isinstance(record, Mapping)
        }
        if not wanted:
            continue
        selected: dict[str, tuple[float, Path]] = {}
        for path in record_paths(artifact_root, record_name):
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(value, dict):
                continue
            attempt = value.get("run_attempt")
            if (
                attempt not in (dataset.producer_attempt, dataset.handoff_attempt)
                or identity_of(value) not in wanted
            ):
                continue
            key = identity_of(value)
            modified = path.stat().st_mtime
            if key not in selected or modified > selected[key][0]:
                selected[key] = (modified, path.parents[1])
        for key in wanted:
            if key not in selected:
                raise FileNotFoundError(
                    f"no raw run found for {record_name} identity {key!r}"
                )
            mapping[f"{group}:{key}"] = selected[key][1]
    for group, record_name, predicate in (
        (
            "semantic_records",
            SEMANTIC_RECORD,
            lambda value: (
                value.get("producer_attempt") == dataset.producer_attempt,
                value.get("semantic_attempt") == dataset.semantic_attempt,
            ),
        ),
        (
            "handoff_semantic_records",
            HANDOFF_SEMANTIC_RECORD,
            lambda value: (
                value.get("producer_attempt") == dataset.producer_attempt,
                value.get("handoff_attempt") == dataset.handoff_attempt,
                value.get("semantic_attempt") == dataset.semantic_attempt,
            ),
        ),
    ):
        for record in frozen.get(group, ()):
            scenario_id = record.get("scenario_id")
            selected_path: Path | None = None
            latest = -1.0
            for path in record_paths(artifact_root, record_name):
                try:
                    value = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                if (
                    not isinstance(value, dict)
                    or value.get("scenario_id") != scenario_id
                    or not all(predicate(value))
                ):
                    continue
                modified = path.stat().st_mtime
                if modified > latest:
                    latest = modified
                    selected_path = path.parents[1]
            if selected_path is None:
                raise FileNotFoundError(
                    f"no raw run found for {record_name} scenario {scenario_id!r}"
                )
            mapping[f"{group}:{scenario_id}"] = selected_path
    return mapping


class _SystemMessageStore:
    """Deduplicate normalized compiled system messages across runs."""

    def __init__(self) -> None:
        self._entries: dict[str, dict[str, Any]] = {}

    def add(
        self,
        *,
        key: str,
        text: str,
        original_sha256: str,
        availability_record: Mapping[str, Any],
        source: str,
    ) -> dict[str, Any]:
        normalized_sha256 = sha256_text(text)
        entry = self._entries.get(key)
        if entry is None:
            entry = {"relative_path": f"shared/system-messages/{key}.md", "texts": {}}
            self._entries[key] = entry
        if normalized_sha256 not in entry["texts"]:
            entry["texts"][normalized_sha256] = {
                "relative_path": (
                    f"shared/system-messages/{key}-{normalized_sha256[:12]}.md"
                ),
                "text": text,
            }
        variant = entry["texts"][normalized_sha256]
        return {
            "path": variant["relative_path"],
            "original_sha256": original_sha256,
            "normalized_sha256": normalized_sha256,
            "availability": dict(availability_record),
            "source": source,
        }

    def files(self) -> list[CollectedFile]:
        values: list[CollectedFile] = []
        for key in sorted(self._entries):
            entry = self._entries[key]
            for normalized_sha256 in sorted(entry["texts"]):
                variant = entry["texts"][normalized_sha256]
                values.append(
                    CollectedFile(
                        relative_path=variant["relative_path"],
                        content=variant["text"],
                    )
                )
        return values


class _ConfigStore:
    """Deduplicate sanitized effective-configuration views."""

    def __init__(self) -> None:
        self._entries: dict[str, str] = {}

    def add(self, key: str, view: Mapping[str, Any]) -> str:
        if key not in self._entries:
            self._entries[key] = render_json_text(view)
        return f"shared/configs/{key}.json"

    def files(self) -> list[CollectedFile]:
        return [
            CollectedFile(
                relative_path=f"shared/configs/{key}.json",
                content=self._entries[key],
            )
            for key in sorted(self._entries)
        ]


def _collect_scenario(
    scenario,
    *,
    dataset: DatasetSpec,
    frozen: Mapping[str, Any],
    discovery: Mapping[str, Path],
    artifact_root: Path,
    selected_cells: Sequence[tuple[str, str, str]] | None,
    reconstruct: bool,
    system_messages: _SystemMessageStore,
    configs: _ConfigStore,
    runs: list[dict[str, Any]],
    files: list[CollectedFile],
) -> None:
    scenario_id = scenario.scenario_id
    target = _record_for(frozen["producer_records"], scenario_id)["target"]
    files.append(
        CollectedFile(
            relative_path=f"scenarios/{scenario_id}/target.md",
            content=(
                f"# Reviewed target — {scenario_id}\n\n"
                + "\n".join(_target_markdown(target)).rstrip()
                + "\n"
            ),
        )
    )
    cells = _cells_for(frozen, scenario_id)
    for cell_key in sorted(cells):
        profile, effort = cell_key.split("-", 1)
        if (
            selected_cells is not None
            and (scenario_id, profile, effort) not in selected_cells
        ):
            continue
        _collect_cell(
            scenario,
            cell_key,
            profile=profile,
            effort=effort,
            dataset=dataset,
            frozen=frozen,
            discovery=discovery,
            artifact_root=artifact_root,
            reconstruct=reconstruct,
            system_messages=system_messages,
            configs=configs,
            runs=runs,
            files=files,
        )
    _collect_assessment(
        scenario,
        dataset=dataset,
        frozen=frozen,
        discovery=discovery,
        artifact_root=artifact_root,
        system_messages=system_messages,
        configs=configs,
        runs=runs,
        files=files,
    )


def _cells_for(frozen: Mapping[str, Any], scenario_id: str) -> set[str]:
    cells: set[str] = set()
    for record in frozen["producer_records"]:
        if record.get("scenario_id") != scenario_id:
            continue
        producer = record["producer"]
        cells.add(f"{producer['profile']}-{producer['reasoning_effort']}")
    return cells


def _collect_cell(
    scenario,
    cell_key: str,
    *,
    profile: str,
    effort: str,
    dataset: DatasetSpec,
    frozen: Mapping[str, Any],
    discovery: Mapping[str, Path],
    artifact_root: Path,
    reconstruct: bool,
    system_messages: _SystemMessageStore,
    configs: _ConfigStore,
    runs: list[dict[str, Any]],
    files: list[CollectedFile],
) -> None:
    scenario_id = scenario.scenario_id
    cell_prefix = f"scenarios/{scenario_id}/{cell_key}"
    model_profile = PROFILES[profile]

    producer = _find(frozen["producer_records"], scenario_id, profile, effort)
    producer_run_dir = discovery[f"producer_records:{scenario_id}:{profile}:{effort}"]
    _collect_run(
        KIND_TASK_CREATION,
        producer,
        subdir=None,
        run_dir=producer_run_dir,
        scenario=scenario,
        dataset=dataset,
        profile=model_profile,
        effort=effort,
        factory=TaskGuidanceWorkspaceFactory(scenario=scenario, bundle=dataset.bundle),
        artifact_root=artifact_root,
        system_messages=system_messages,
        configs=configs,
        runs=runs,
        files=files,
        cell_prefix=cell_prefix,
        task_files=producer.get("task_files") or {},
        reconstruct=reconstruct,
    )

    for variant, kind, subdir in (
        ("retain", KIND_PLAN_RETAIN, "plan-retain"),
        ("omit", KIND_PLAN_OMIT, "plan-omit"),
    ):
        handoff = _find_variant(
            frozen["handoff_records"], scenario_id, variant, profile, effort
        )
        if handoff is None:
            continue
        handoff_run_dir = discovery[
            f"handoff_records:{scenario_id}:{variant}:{profile}:{effort}"
        ]
        _collect_run(
            kind,
            handoff,
            subdir=subdir,
            run_dir=handoff_run_dir,
            scenario=scenario,
            dataset=dataset,
            profile=model_profile,
            effort=effort,
            factory=CanonicalHandoffWorkspaceFactory(
                scenario=scenario,
                variant=variant,
                bundle=dataset.bundle,
            ),
            artifact_root=artifact_root,
            system_messages=system_messages,
            configs=configs,
            runs=runs,
            files=files,
            cell_prefix=cell_prefix,
            task_files=handoff.get("task_files") or {},
            reconstruct=reconstruct,
        )

    same_agent = _find(frozen["same_agent_records"], scenario_id, profile, effort)
    if same_agent is not None:
        same_agent_run_dir = discovery[
            f"same_agent_records:{scenario_id}:{profile}:{effort}"
        ]
        _collect_run(
            KIND_CONTINUATION,
            same_agent,
            subdir="continuation",
            run_dir=same_agent_run_dir,
            scenario=scenario,
            dataset=dataset,
            profile=model_profile,
            effort=effort,
            factory=TaskGuidanceWorkspaceFactory(
                scenario=scenario,
                bundle=dataset.bundle,
            ),
            artifact_root=artifact_root,
            system_messages=system_messages,
            configs=configs,
            runs=runs,
            files=files,
            cell_prefix=cell_prefix,
            task_files=same_agent.get("task_files") or {},
            lineage=True,
            reconstruct=False,
        )

    negative = _find_variant(
        frozen["negative_control_records"], scenario_id, "incomplete", profile, effort
    )
    if negative is not None:
        negative_run_dir = discovery[
            f"negative_control_records:{scenario_id}:incomplete:{profile}:{effort}"
        ]
        _collect_run(
            KIND_CONTROL,
            negative,
            subdir="control",
            run_dir=negative_run_dir,
            scenario=scenario,
            dataset=dataset,
            profile=model_profile,
            effort=effort,
            factory=CanonicalHandoffWorkspaceFactory(
                scenario=scenario,
                variant="incomplete",
                bundle=dataset.bundle,
            ),
            artifact_root=artifact_root,
            system_messages=system_messages,
            configs=configs,
            runs=runs,
            files=files,
            cell_prefix=cell_prefix,
            task_files=negative.get("task_files") or {},
            reconstruct=False,
        )


def _find(
    records: Iterable[Mapping[str, Any]],
    scenario_id: str,
    profile: str,
    effort: str,
) -> Mapping[str, Any] | None:
    for record in records:
        producer = record.get("producer") or {}
        if (
            record.get("scenario_id") == scenario_id
            and producer.get("profile") == profile
            and producer.get("reasoning_effort") == effort
        ):
            return record
    return None


def _find_variant(
    records: Iterable[Mapping[str, Any]],
    scenario_id: str,
    variant: str,
    profile: str,
    effort: str,
) -> Mapping[str, Any] | None:
    for record in records:
        producer = record.get("producer") or {}
        if (
            record.get("scenario_id") == scenario_id
            and record.get("variant") == variant
            and producer.get("profile") == profile
            and producer.get("reasoning_effort") == effort
        ):
            return record
    return None


def _collect_run(
    kind: str,
    record: Mapping[str, Any],
    *,
    subdir: str | None,
    run_dir: Path,
    scenario,
    dataset: DatasetSpec,
    profile,
    effort: str,
    factory,
    artifact_root: Path,
    system_messages: _SystemMessageStore,
    configs: _ConfigStore,
    runs: list[dict[str, Any]],
    files: list[CollectedFile],
    cell_prefix: str,
    task_files: Mapping[str, str],
    lineage: bool = False,
    reconstruct: bool = True,
    system_message_key: str | None = None,
    config_key: str | None = None,
) -> dict[str, Any]:
    run_prefix = cell_prefix if subdir is None else f"{cell_prefix}/{subdir}"
    run_id = run_dir.name
    session_path = run_dir / "raw" / "environment" / "crystal-lattice-session.json"
    observation_path = (
        run_dir / "raw" / "environment" / "crystal-lattice-observation.json"
    )
    session = (
        json.loads(session_path.read_text(encoding="utf-8"))
        if session_path.is_file()
        else None
    )
    observation = (
        json.loads(observation_path.read_text(encoding="utf-8"))
        if observation_path.is_file()
        else None
    )
    result_summary = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
    workspace = Path(str(result_summary["workspace"]))
    replacements = _path_replacements(workspace)

    inherited_prefix: dict[str, Any] | None = None
    parent_run_id = result_summary.get("parent_run_id")
    if lineage:
        if parent_run_id:
            parent_dir = run_dir.parent / str(parent_run_id)
            parent_session_path = (
                parent_dir / "raw" / "environment" / "crystal-lattice-session.json"
            )
            if parent_session_path.is_file():
                parent_session = json.loads(
                    parent_session_path.read_text(encoding="utf-8")
                )
                inherited_prefix = {
                    "length": len(parent_session.get("messages", [])),
                    "availability": availability(
                        "captured",
                        detail="bounded by the parent run's saved session",
                    ),
                }
            else:
                inherited_prefix = {
                    "length": None,
                    "availability": availability(
                        "unavailable", detail="parent session not retained"
                    ),
                }
        else:
            inherited_prefix = {
                "length": None,
                "availability": availability(
                    "unavailable", detail="parent run identity not recorded"
                ),
            }

    instructions = _stage_instructions(
        record,
        session=session,
        profile=profile,
        effort=effort,
        scenario=scenario,
        dataset=dataset,
        factory=factory,
        workspace=workspace,
        run_dir=run_dir,
        artifact_root=artifact_root,
        replacements=replacements,
        reconstruct=reconstruct,
    )
    system_message = (
        system_messages.add(
            key=system_message_key or profile.name,
            text=instructions["text"],
            original_sha256=instructions["original_sha256"],
            availability_record=instructions["availability"],
            source=instructions["source"],
        )
        if instructions["text"] is not None
        else {"availability": instructions["availability"], "source": None}
    )
    config_path = configs.add(
        config_key or f"{profile.name}-{effort}",
        _effective_config_view(
            profile=profile,
            effort=effort,
            workspace=workspace,
            artifact_root=artifact_root,
            replacements=replacements,
        ),
    )

    review = (
        project_session_review(
            session,
            observation=observation,
            supplied_instructions=(
                {
                    "text": instructions["text"],
                    "source": instructions["source"],
                    "availability": instructions["availability"],
                }
                if instructions["text"] is not None
                and instructions["availability"]["state"] != "captured"
                else None
            ),
            inherited_prefix=inherited_prefix,
            path_replacements=replacements,
        )
        if session is not None
        else None
    )
    if review is not None:
        session_page = f"{run_prefix}/session.md"
        instructions_state = instructions["availability"]["state"]
        instructions_label = system_message_key or f"{profile.name}-{effort}"
        if system_message.get("path"):
            instructions_note = (
                f"[{instructions_label}]"
                f"({_link(system_message['path'], session_page)})"
                f" — {instructions_state}"
                f" (original SHA-256 `{system_message['original_sha256'][:16]}…`)"
            )
        else:
            instructions_note = f"**{instructions_state}**"
        tools = ", ".join(
            str(tool)
            for tool in (record.get("delivery") or {}).get("active_tools") or []
        )
        context: dict[str, str] = {
            "Run": f"`{run_id}`",
            "Model": f"{profile.model} (effort {effort})",
        }
        if tools:
            context["Tools"] = tools
        context["Delivered instructions"] = instructions_note
        context["Config"] = (
            f"[{config_key or f'{profile.name}-{effort}'}]"
            f"({_link(config_path, session_page)})"
        )
        files.append(
            CollectedFile(
                relative_path=session_page,
                content=render_session_markdown(
                    review,
                    title=(
                        f"{scenario.scenario_id} · {kind} ·"
                        f" {profile.name} {effort}"
                    ),
                    context=context,
                ),
            )
        )

    exported_task_files: list[str] = []
    for relative, content in sorted((task_files or {}).items()):
        target = f"{run_prefix}/task-files/{relative}"
        files.append(CollectedFile(relative_path=target, content=str(content)))
        exported_task_files.append(f"task-files/{relative}")

    usage = (
        review["usage"]
        if review
        else {
            "availability": availability(
                "unavailable", detail="saved session is missing"
            ),
        }
    )
    runs.append(
        {
            "run_id": run_id,
            "label": f"{scenario.scenario_id} {kind} {profile.name} {effort}",
            "provider": profile.name,
            "model": profile.model,
            "reasoning_effort": effort,
            "usage": usage,
            "kind": kind,
            "scenario_id": scenario.scenario_id,
        }
    )
    run_record: dict[str, Any] = {
        "run_id": run_id,
        "kind": kind,
        "provider": profile.name,
        "model": profile.model,
        "reasoning_effort": effort,
        "system_message": system_message,
        "config": config_path,
        "task_files": exported_task_files,
    }
    if "valid" in record or record.get("invalid_reasons"):
        run_record["valid"] = record.get("valid")
        run_record["invalid_reasons"] = record.get("invalid_reasons", [])
    if lineage:
        run_record["lineage"] = {
            "parent_run_id": parent_run_id,
            "inherited_prefix": inherited_prefix,
        }
    files.append(
        CollectedFile(
            relative_path=f"{run_prefix}/run.json",
            content=render_json_text(run_record),
        )
    )
    return run_record


def _stage_instructions(
    record: Mapping[str, Any],
    *,
    session: Mapping[str, Any] | None,
    profile,
    effort: str,
    scenario,
    dataset: DatasetSpec,
    factory,
    workspace: Path,
    run_dir: Path,
    artifact_root: Path,
    replacements: Mapping[str, str],
    reconstruct: bool,
) -> dict[str, Any]:
    _ = scenario
    delivery = record.get("delivery") or {}
    expected_hash = delivery.get("compiled_sha256")
    if session is not None:
        for message in session.get("messages", []):
            if message.get("role") not in {"system", "developer"}:
                continue
            compiled = (message.get("metadata") or {}).get("compiled_content")
            if isinstance(compiled, str) and compiled.strip():
                return {
                    "text": apply_replacements(compiled, replacements),
                    "original_sha256": sha256_text(compiled),
                    "availability": availability(
                        "captured", detail="retained by the saved session"
                    ),
                    "source": "session.compiled_content",
                }
    if (
        reconstruct
        and expected_hash
        and profile.name == "gpt"
        and workspace == run_dir / "workspace"
    ):
        body = _reconstruct_compiled_message(
            profile=profile,
            effort=effort,
            dataset=dataset,
            factory=factory,
            workspace=workspace,
            run_dir=run_dir,
            artifact_root=artifact_root,
        )
        if body is not None:
            actual = sha256_text(body)
            return {
                "text": apply_replacements(body, replacements),
                "original_sha256": actual,
                "availability": availability(
                    "reconstructed",
                    detail=(
                        "recompiled from the preserved runtime-config sources;"
                        " SHA-256 matches the recorded delivery hash"
                        if actual == expected_hash
                        else "recompiled from the preserved runtime-config"
                        " sources; SHA-256 does NOT match the recorded"
                        " delivery hash"
                    ),
                    verified=actual == expected_hash,
                ),
                "source": "recompiled-from-preserved-sources",
            }
    detail = (
        "saved session retains no system message and no delivery hash was"
        " recorded"
        if not expected_hash
        else "reconstruction was not run for this stage"
        if not reconstruct
        else "reconstruction failed or was not applicable"
    )
    return {
        "text": None,
        "original_sha256": None,
        "availability": availability("unavailable", detail=detail),
        "source": None,
    }


def _reconstruct_compiled_message(
    *,
    profile,
    effort: str,
    dataset: DatasetSpec,
    factory,
    workspace: Path,
    run_dir: Path,
    artifact_root: Path,
) -> str | None:
    """Recompile one compiled system message without any model request.

    The pristine fixture workspace is recreated at its original recorded path
    because the compiled message embeds the run's absolute workspace path.
    The workspace is removed again after compilation.
    """

    if not (run_dir / "result.json").is_file():
        return None
    if workspace.exists():
        return None
    try:
        created = factory(workspace)
        if created != workspace:
            return None
        runtime_config = _runtime_config_root(
            bundle=dataset.bundle, artifact_root=artifact_root
        )
        projected = _project_config_for_profile(
            runtime_config / "config.json",
            artifact_root=artifact_root,
            profile=profile,
        )
        environment = WorkspaceAwareEnvironment.from_config(
            projected,
            environment={
                "CONFIG_DIR": str(runtime_config),
                "CHATGPT_TEST_STATE_DIR": str(
                    Path(
                        os.getenv(
                            "CHATGPT_TEST_STATE_DIR",
                            str(Path.home() / ".crystal"),
                        )
                    ).expanduser()
                ),
                "BUILTIN_PLUGINS": str(REPOSITORY_ROOT / "plugins"),
                "PIP_CONSTRAINT": str(
                    PACKAGE_ROOT / "constraints" / "plugin-runtime.txt"
                ),
                "OLLAMA_OPENAI_BASE_URL": os.getenv(
                    "OLLAMA_OPENAI_BASE_URL", "http://localhost:11434/v1"
                ),
            },
        )
        with tempfile.TemporaryDirectory() as tmp:
            from agent_eval.services import (
                ArtifactWriter,
                EvidenceJournal,
                RunServices,
            )

            services = RunServices(
                run_id=f"reconstruct-{run_dir.name}",
                name="reconstruct",
                artifact_dir=Path(tmp),
                workspace=workspace,
                parent=None,
                evidence=EvidenceJournal(),
                artifacts=ArtifactWriter(Path(tmp) / "artifacts"),
            )
            with environment.open(
                services=services, workspace=workspace, parent_snapshot=None
            ) as context:
                context.start(profile.agent_id)
                context.config.update(
                    profile.request_overrides(workspace, reasoning_effort=effort)
                )
                _reload_context_with_defaults(context)
                effective = context.effective_config()
                _, result = context.core.execute_session_action(
                    context.session,
                    effective,
                    plugin_id="system_message",
                    action_id="show_compiled_system_message",
                    params={},
                )
                body = result.get("display", {}).get("body")
                if not isinstance(body, str):
                    return None
                return body
    except Exception:
        return None
    finally:
        factory.cleanup(workspace)


def _effective_config_view(
    *,
    profile,
    effort: str,
    workspace: Path,
    artifact_root: Path,
    replacements: Mapping[str, str],
) -> dict[str, Any]:
    projected_path = artifact_root / "projected-config" / f"{profile.name}-v1.json"
    projected = (
        json.loads(projected_path.read_text(encoding="utf-8"))
        if projected_path.is_file()
        else {}
    )
    overrides = profile.request_overrides(workspace, reasoning_effort=effort)
    return project_effective_config_view(
        {
            "agent_id": profile.agent_id,
            "model": profile.model,
            "reasoning_effort": effort,
            "projected_config": projected,
            "request_overrides": overrides,
        },
        path_replacements=replacements,
    )


def _path_replacements(workspace: Path) -> dict[str, str]:
    """Build the path-normalization map for one run.

    The exact workspace path is replaced first; the user's home directory is
    replaced afterwards so model-produced paths that reference the local
    machine (including mistaken shortened paths) stay reviewable without
    committing machine-specific prefixes.
    """

    replacements = {str(workspace): "<workspace>"}
    home = str(Path.home())
    if home and home != str(workspace):
        replacements[home] = "~"
    return replacements


def _collect_assessment(
    scenario,
    *,
    dataset: DatasetSpec,
    frozen: Mapping[str, Any],
    discovery: Mapping[str, Path],
    artifact_root: Path,
    system_messages: _SystemMessageStore,
    configs: _ConfigStore,
    runs: list[dict[str, Any]],
    files: list[CollectedFile],
) -> None:
    scenario_id = scenario.scenario_id
    semantic = _semantic_for(frozen["semantic_records"], scenario_id)
    if semantic is not None:
        _collect_assessment_record(
            name="task-creation",
            title="Task-creation semantic assessment",
            record=semantic,
            run_dir=discovery[f"semantic_records:{scenario_id}"],
            scenario=scenario,
            dataset=dataset,
            artifact_root=artifact_root,
            system_messages=system_messages,
            configs=configs,
            runs=runs,
            files=files,
        )
    handoff_semantic = _semantic_for(frozen["handoff_semantic_records"], scenario_id)
    if handoff_semantic is not None:
        _collect_assessment_record(
            name="handoff",
            title="Handoff semantic assessment",
            record=handoff_semantic,
            run_dir=discovery[f"handoff_semantic_records:{scenario_id}"],
            scenario=scenario,
            dataset=dataset,
            artifact_root=artifact_root,
            system_messages=system_messages,
            configs=configs,
            runs=runs,
            files=files,
        )


def _record_for(
    records: Iterable[Mapping[str, Any]], scenario_id: str
) -> Mapping[str, Any]:
    for record in records:
        if record.get("scenario_id") == scenario_id:
            return record
    raise KeyError(f"no record for scenario {scenario_id!r}")


def _semantic_for(
    records: Iterable[Mapping[str, Any]], scenario_id: str
) -> Mapping[str, Any] | None:
    for record in records:
        if record.get("scenario_id") == scenario_id:
            return record
    return None


def _collect_assessment_record(
    *,
    name: str,
    title: str,
    record: Mapping[str, Any],
    run_dir: Path,
    scenario,
    dataset: DatasetSpec,
    artifact_root: Path,
    system_messages: _SystemMessageStore,
    configs: _ConfigStore,
    runs: list[dict[str, Any]],
    files: list[CollectedFile],
) -> None:
    """Collect one assessor run with the same shape as a subject run.

    The assessor run directory holds ``run.json`` and the full session
    transcript (exact prompt and raw response) exactly like a subject run,
    plus ``results.md`` — the readable rendering of the judgments.
    """

    scenario_id = scenario.scenario_id
    run_prefix = f"scenarios/{scenario_id}/assessment/{name}"
    profile = PROFILES["glm"]
    effort = "max"
    run_record = _collect_run(
        f"{name}-assessment",
        record,
        subdir=None,
        run_dir=run_dir,
        scenario=scenario,
        dataset=dataset,
        profile=profile,
        effort=effort,
        factory=None,
        artifact_root=artifact_root,
        system_messages=system_messages,
        configs=configs,
        runs=runs,
        files=files,
        cell_prefix=run_prefix,
        task_files={},
        reconstruct=False,
        system_message_key="glm-assessor",
        config_key=f"glm-assessor-{effort}",
    )
    results_page = f"{run_prefix}/results.md"
    files.append(
        CollectedFile(
            relative_path=results_page,
            content=_assessment_results_markdown(
                title=title,
                kind=name,
                record=record,
                target_path=f"scenarios/{scenario_id}/target.md",
                assessor={
                    "run_id": run_record["run_id"],
                    "model": run_record["model"],
                    "reasoning_effort": run_record["reasoning_effort"],
                    "config_path": run_record["config"],
                    "system_message": run_record["system_message"],
                },
                page=results_page,
                rubric_note=(
                    "- Rubric: fragmentation uses none/low/medium/high mapped"
                    " to 100/67/33/0; every other dimension uses"
                    " none/partial/present mapped to 100/50/0. An"
                    " assessment's overall success is the equal-weight"
                    " average of the six dimension scores."
                    if name == "task-creation"
                    else "- Rubric: the assessor scores handoff quality 0-100"
                    " from plan coverage, lost facts, invented scope,"
                    " rediscovery breadth, documentation and testing"
                    " boundaries, and whether the plan is self-contained."
                ),
            ),
        )
    )


def _assessment_results_markdown(
    *,
    title: str,
    kind: str,
    record: Mapping[str, Any],
    target_path: str,
    assessor: Mapping[str, Any],
    page: str,
    rubric_note: str,
) -> str:
    system_message = assessor.get("system_message") or {}
    config_link = _link(assessor["config_path"], page)
    lines = [
        f"# {title}",
        "",
        f"- Assessor: `{assessor['model']}` (effort {assessor['reasoning_effort']})"
        f" · run `{assessor['run_id']}`",
        f"- Assessor config: [{assessor['config_path'].split('/')[-1]}]({config_link})",
    ]
    if system_message.get("path"):
        message_link = _link(system_message["path"], page)
        lines.append(
            f"- Assessor system message:"
            f" [{system_message['path'].split('/')[-1]}]({message_link})"
            f" (original SHA-256 `{system_message.get('original_sha256', '')[:16]}…`)"
        )
    else:
        state = (system_message.get("availability") or {}).get("state")
        lines.append(f"- Assessor system message: **{state}**")
    lines.extend(
        [
            "- Full transcript: [session.md](session.md) — includes the exact"
            " prompt and the raw response",
            f"- Reviewed target: [{target_path.split('/')[-2]}]"
            f"({_link(target_path, page)})",
            rubric_note,
            "",
            "## Judgments",
            "",
        ]
    )
    for assessment in (record.get("assessment") or {}).get("assessments", ()):
        # The judgment schema follows the assessment kind, not field presence:
        # task-creation responses legitimately carry a handoff_quality_score
        # field because the prompt's JSON shape includes it.
        if kind == "handoff":
            lines.extend(_handoff_judgment_markdown(assessment))
        else:
            lines.extend(_judgment_markdown(assessment))
        lines.append("")
    invalid = record.get("invalid_producer_records") or []
    if invalid:
        lines.extend(["## Excluded records", ""])
        for item in invalid:
            producer = item.get("producer") or {}
            reasons = "; ".join(str(r) for r in item.get("invalid_reasons", ()))
            lines.append(
                f"- {producer.get('profile')} {producer.get('reasoning_effort')}:"
                f" {reasons}"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _target_markdown(target: Mapping[str, Any]) -> list[str]:
    sizes = ", ".join(
        str(size) for size in target.get("acceptable_partition_sizes", ())
    )
    project = target.get("project")
    if isinstance(project, Mapping):
        project_name = str(project.get("name", ""))
    else:
        project_name = str(project or "")
    lines = [
        f"**{target.get('title', '')}** — {target.get('task_summary', '')}",
        "",
        f"Category: {target.get('category')} · Project: `{project_name}`"
        f" · Acceptable partition sizes: {sizes}",
        "",
        "**Approved outcomes**",
        "",
    ]
    for outcome in target.get("approved_outcomes", ()):
        lines.append(f"- {outcome.get('id')}: {outcome.get('outcome')}")
    lines.extend(["", "**Coherent deliverables**", ""])
    for deliverable in target.get("coherent_deliverables", ()):
        dependencies = deliverable.get("dependencies") or []
        suffix = (
            f" (depends on {', '.join(str(item) for item in dependencies)})"
            if dependencies
            else ""
        )
        lines.append(
            f"- **{deliverable.get('id')}** — {deliverable.get('title')}{suffix}"
        )
        lines.append(f"  {deliverable.get('independent_value')}")
        outcomes = ", ".join(str(item) for item in deliverable.get("outcomes", ()))
        lines.append(f"  - Outcomes: {outcomes}")
    sections = (
        ("Important crossings", "important_crossings"),
        ("Acceptable alternatives", "acceptable_alternatives"),
        ("Fragmentation examples", "fragmentation_examples"),
        ("Overpacking examples", "overpacking_examples"),
        ("Open questions", "open_questions"),
    )
    for heading, key in sections:
        values = target.get(key) or []
        if values:
            lines.extend(["", f"**{heading}**", ""])
            for value in values:
                lines.append(f"- {value}")
    handoff = target.get("handoff") or {}
    if handoff:
        lines.extend(["", "**Handoff expectations**", ""])
        for key, value in handoff.items():
            lines.append(f"- {key.replace('_', ' ')}: {value}")
    return lines


def _judgment_markdown(assessment: Mapping[str, Any]) -> list[str]:
    producer = assessment.get("producer") or {}
    metrics = assessment.get("quality_metrics") or {}
    lines = [
        f"### {producer.get('profile')} · {producer.get('reasoning_effort')}"
        f" — overall {assessment.get('overall_success_percentage')}",
        "",
        f"{assessment.get('actual_task_count')} tasks ·"
        f" {assessment.get('semantic_deliverable_count')} semantic deliverables ·"
        f" fragmentation ratio {assessment.get('fragmentation_ratio')}"
        f" ({assessment.get('fragmentation_severity')}) ·"
        f" outcome coverage {assessment.get('outcome_coverage')} ·"
        f" crossing ownership {assessment.get('crossing_ownership')}",
        "",
        "| Dimension | Status | Score |",
        "|---|---|---:|",
    ]
    for dimension in QUALITY_DIMENSIONS:
        item = metrics.get(dimension) or {}
        lines.append(f"| {dimension} | {item.get('status')} | {item.get('score')} |")
    lines.append("")
    for dimension in QUALITY_DIMENSIONS:
        item = metrics.get(dimension) or {}
        for occurrence in item.get("occurrences") or ():
            paths = ", ".join(f"`{path}`" for path in occurrence.get("task_paths", ()))
            suffix = f" ({paths})" if paths else ""
            lines.append(
                f"- **{dimension}**: {occurrence.get('description')}{suffix}"
            )
    missing = assessment.get("missing_outcomes") or []
    if missing:
        lines.append(
            "- Missing outcomes: " + ", ".join(f"`{item}`" for item in missing)
        )
    for mapping in assessment.get("deliverable_mappings") or ():
        paths = ", ".join(f"`{path}`" for path in mapping.get("task_paths", ()))
        lines.append(
            f"- Deliverable {mapping.get('deliverable_id')} → {paths}"
            f" ({mapping.get('coherence')}, {mapping.get('coverage')}) —"
            f" {mapping.get('reason')}"
        )
    for label, key in (
        ("Mergeable groups", "mergeable_groups"),
        ("Overpacked tasks", "overpacked_tasks"),
        ("Layer fragments", "automatic_layer_fragments"),
        ("Unmatched tasks", "unmatched_tasks"),
        ("Added obligations", "added_obligations"),
    ):
        values = assessment.get(key) or []
        if values:
            rendered = ", ".join(
                f"`{value}`" if isinstance(value, str) else str(value)
                for value in values
            )
            lines.append(f"- {label}: {rendered}")
    for issue in assessment.get("dependency_issues") or ():
        lines.append(f"- Dependency issue: {issue}")
    summary = assessment.get("summary")
    if summary:
        lines.extend(["", f"> {summary}"])
    return lines


def _handoff_judgment_markdown(assessment: Mapping[str, Any]) -> list[str]:
    producer = assessment.get("producer") or {}
    lines = [
        f"### {producer.get('profile')} · {producer.get('reasoning_effort')}"
        f" ({assessment.get('variant')}, {assessment.get('stage')})"
        f" — handoff quality {assessment.get('handoff_quality_score')}",
        "",
        f"- Plan coverage: {assessment.get('plan_coverage')}"
        f" · Documentation boundary: {assessment.get('documentation_boundary')}"
        f" · Testing boundary: {assessment.get('testing_boundary')}",
        f"- Task self-contained: {_yes_no(assessment.get('task_self_contained'))}"
        f" · Broad rediscovery: {_yes_no(assessment.get('broad_rediscovery'))}",
    ]
    for label, key in (
        ("Lost facts or decisions", "lost_facts_or_decisions"),
        ("Invented scope or decisions", "invented_scope_or_decisions"),
        ("Missing outcomes", "missing_outcomes"),
    ):
        values = assessment.get(key) or []
        if values:
            lines.append(f"- {label}:")
            for value in values:
                lines.append(f"  - {value}")
        else:
            lines.append(f"- {label}: none")
    efficiency = assessment.get("efficiency_interpretation")
    if efficiency:
        lines.append(f"- Efficiency: {efficiency}")
    summary = assessment.get("summary")
    if summary:
        lines.extend(["", f"> {summary}"])
    return lines


def _yes_no(value: Any) -> str:
    return "yes" if value else "no"


def _build_index_views(records: PackageRecords) -> list[GeneratedView]:
    aggregate = records.collected_json("aggregate.json")
    identity = dict(records.identity)
    lines = [
        f"# {identity.get('label', 'Task-guidance evaluation')} result package",
        "",
        f"- Dataset: `{identity.get('dataset_id')}`",
        f"- Producer attempt: `{aggregate['attempts']['producer']}`",
        f"- Handoff attempt: `{aggregate['attempts']['handoff']}`",
        f"- Semantic attempt: `{aggregate['attempts']['semantic']}`",
        "",
        "This package preserves the completed evaluation's reviewed inputs,"
        " model outputs, execution context, semantic assessments, and usage"
        " evidence. Every navigation, matrix, and cost view regenerates"
        " deterministically from the committed records.",
        "",
        "## Navigation",
        "",
        "- [Quality matrix](matrix.md) — status and semantic dimensions.",
        "- [Usage and estimated cost](costs.md) — one row per run.",
        "- [Scenario cells and assessments](#scenarios) below.",
        "",
        "## Scenarios",
        "",
    ]
    scenario_ids = sorted(
        {
            path.split("/")[1]
            for path in records.collected_paths
            if path.startswith("scenarios/")
        }
    )
    for scenario_id in scenario_ids:
        lines.append(f"- [`{scenario_id}`](scenarios/{scenario_id}/index.md)")
    lines.extend(
        [
            "",
            "## Known limitations",
            "",
            "- Historical GLM runs saved no provider usage metadata; their"
            " usage and estimated cost remain unknown.",
            "- GPT same-agent continuation runs recorded no compiled-message"
            " hash, so their delivered instructions stay unavailable rather"
            " than reconstructed without verification.",
            "- Session transcripts omit full tool-result content and"
            " encrypted reasoning; concise failure excerpts are retained.",
        ]
    )
    return [
        GeneratedView(relative_path="index.md", content="\n".join(lines) + "\n"),
        GeneratedView(
            relative_path="matrix.md",
            content=_matrix_markdown(aggregate),
        ),
    ]


def _matrix_markdown(aggregate: Mapping[str, Any]) -> str:
    """Render the status matrix from the committed aggregate record."""

    groups: dict[str, list[Mapping[str, Any]]] = {
        "producer_records": [],
        "handoff_records": [],
        "same_agent_records": [],
    }
    for entry in aggregate.get("invalid_records", ()):
        group = entry.get("group")
        if group in groups:
            groups[group].append(entry["record"])
    return render_summary(
        {
            "label": aggregate["label"],
            "attempts": aggregate["attempts"],
            "status": aggregate["status"],
            "semantic_quality": aggregate["semantic_quality"],
            "producer_records": groups["producer_records"],
            "handoff_records": groups["handoff_records"],
            "same_agent_records": groups["same_agent_records"],
            "provider_blocker_records": aggregate.get(
                "provider_blocker_records", []
            ),
        }
    )


def _build_case_views(records: PackageRecords) -> list[GeneratedView]:
    views: list[GeneratedView] = []
    scenario_ids = sorted(
        {
            path.split("/")[1]
            for path in records.collected_paths
            if path.startswith("scenarios/")
        }
    )
    for scenario_id in scenario_ids:
        views.extend(_scenario_views(records, scenario_id))
    return views


def _scenario_views(records: PackageRecords, scenario_id: str) -> list[GeneratedView]:
    prefix = f"scenarios/{scenario_id}"
    lines = [
        f"# Scenario `{scenario_id}`",
        "",
        "- [Reviewed target](target.md)",
        "",
        "## Cells",
        "",
        "| Cell | Runs |",
        "|---|---|",
    ]
    cell_keys = sorted(
        {
            path.split("/")[2]
            for path in records.collected_paths
            if path.startswith(f"{prefix}/")
            and path.split("/")[2] != "assessment"
            and path.endswith("/run.json")
        }
    )
    for cell_key in cell_keys:
        runs = _cell_runs(records, scenario_id, cell_key)
        kinds = ", ".join(f"`{run['kind']}`" for run in runs)
        lines.append(f"| [`{cell_key}`]({cell_key}/index.md) | {kinds} |")
    lines.extend(["", "## Assessment", ""])
    for name, title in (
        ("task-creation", "Task-creation semantic assessment"),
        ("handoff", "Handoff semantic assessment"),
    ):
        if f"{prefix}/assessment/{name}/results.md" in records.collected_paths:
            lines.append(f"- [{title}](assessment/{name}/results.md)")
            lines.append(
                f"  - [Assessor session](assessment/{name}/session.md) —"
                " exact prompt and raw response"
            )
    views = [
        GeneratedView(
            relative_path=f"{prefix}/index.md",
            content="\n".join(lines) + "\n",
        )
    ]
    for cell_key in cell_keys:
        views.extend(_cell_views(records, scenario_id, cell_key))
    return views


def _cell_runs(
    records: PackageRecords, scenario_id: str, cell_key: str
) -> list[dict[str, Any]]:
    prefix = f"scenarios/{scenario_id}/{cell_key}"
    run_paths = [
        path
        for path in records.collected_paths
        if path == f"{prefix}/run.json"
        or (
            path.startswith(f"{prefix}/")
            and path.endswith("/run.json")
            and path.count("/") == prefix.count("/") + 2
        )
    ]
    runs = [records.collected_json(path) for path in sorted(run_paths)]
    runs.sort(
        key=lambda run: (
            0 if run.get("kind") == KIND_TASK_CREATION else 1,
            run.get("kind") or "",
        )
    )
    return runs


def _cell_views(
    records: PackageRecords, scenario_id: str, cell_key: str
) -> list[GeneratedView]:
    page = f"scenarios/{scenario_id}/{cell_key}/index.md"
    prefix = f"scenarios/{scenario_id}/{cell_key}"
    runs = _cell_runs(records, scenario_id, cell_key)
    producer = runs[0] if runs else {}
    lines = [
        f"# Cell `{scenario_id}` — `{cell_key}`",
        "",
        f"- Model: `{producer.get('model')}` (profile `{producer.get('provider')}`,"
        f" effort `{producer.get('reasoning_effort')}`)",
        "",
        "## Runs",
        "",
    ]
    for run in runs:
        status = "valid" if run.get("valid") else "invalid"
        run_dir = (
            prefix
            if run["kind"] == KIND_TASK_CREATION
            else f"{prefix}/{_subdir_for(run['kind'])}"
        )
        lines.append(f"### `{run['kind']}` ({status})")
        lines.append("")
        lines.append(
            f"- [Session]({_link(f'{run_dir}/session.md', page)})"
            " — includes the prompt and response"
        )
        for task_file in run.get("task_files", ()):
            name = PurePosixPath(task_file).name
            lines.append(
                f"- Task file [`{name}`]({_link(f'{run_dir}/{task_file}', page)})"
            )
        system_message = run.get("system_message") or {}
        if system_message.get("path"):
            state = (system_message.get("availability") or {}).get("state")
            lines.append(
                f"- [Delivered instructions]({_link(system_message['path'], page)})"
                f" — {state}"
                f" (original SHA-256"
                f" `{system_message.get('original_sha256', '')[:16]}…`)"
            )
        else:
            state = (system_message.get("availability") or {}).get("state")
            lines.append(f"- Delivered instructions: **{state}**")
        if run.get("config"):
            lines.append(f"- [Effective config]({_link(run['config'], page)})")
        if run.get("lineage"):
            lineage = run["lineage"]
            lines.append(f"- Continuation parent run: `{lineage.get('parent_run_id')}`")
        if run.get("invalid_reasons"):
            lines.append(
                "- Invalid because: "
                + "; ".join(str(item) for item in run["invalid_reasons"])
            )
        lines.append("")
    lines.extend(["## Assessment", ""])
    for name, title in (
        ("task-creation", "Task-creation semantic results"),
        ("handoff", "Handoff semantic results"),
    ):
        path = f"scenarios/{scenario_id}/assessment/{name}/results.md"
        if path in records.collected_paths:
            lines.append(f"- [{title}]({_link(path, page)})")
    return [
        GeneratedView(relative_path=page, content="\n".join(lines) + "\n")
    ]


def _subdir_for(kind: str) -> str:
    return {
        KIND_PLAN_RETAIN: "plan-retain",
        KIND_PLAN_OMIT: "plan-omit",
        KIND_CONTINUATION: "continuation",
        KIND_CONTROL: "control",
    }[kind]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    scenarios_parser = commands.add_parser(
        "extract-scenarios",
        help="write the scenario definitions export (targets, prompts,"
        " prompt templates)",
    )
    scenarios_parser.add_argument(
        "--output", type=Path, default=DEFAULT_SCENARIOS_ROOT
    )

    collect_parser = commands.add_parser(
        "collect", help="collect a durable result package"
    )
    collect_parser.add_argument("--dataset", choices=sorted(DATASETS), required=True)
    collect_parser.add_argument(
        "--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT
    )
    collect_parser.add_argument("--frozen", type=Path, default=None)
    collect_parser.add_argument("--output", type=Path, default=None)
    collect_parser.add_argument(
        "--cells",
        nargs="*",
        default=None,
        help="collect only these scenario:profile:effort cells",
    )
    collect_parser.add_argument(
        "--no-reconstruction",
        action="store_true",
        help="skip GPT compiled-message reconstruction",
    )

    render_parser = commands.add_parser("render", help="regenerate package views")
    render_parser.add_argument("--package", type=Path, required=True)

    check_parser = commands.add_parser("check", help="verify a package")
    check_parser.add_argument("--package", type=Path, required=True)

    args = parser.parse_args(argv)
    if args.command == "extract-scenarios":
        output = extract_scenarios(output_dir=args.output.expanduser().resolve())
        print(output)
        return 0
    if args.command == "collect":
        dataset = DATASETS[args.dataset]
        frozen = args.frozen or dataset.frozen_results
        output = args.output or DEFAULT_PACKAGES_ROOT / dataset.package_name
        package = collect(
            dataset,
            package_dir=output,
            artifact_root=args.artifact_root.expanduser().resolve(),
            frozen_path=frozen,
            cells=args.cells,
            reconstruct=not args.no_reconstruction,
        )
        print(package)
        return 0
    if args.command == "render":
        written = render_result_package(
            args.package, view_builders=[_build_index_views, _build_case_views]
        )
        print(f"rendered {len(written)} views into {args.package}")
        return 0
    problems = check_result_package(
        args.package, view_builders=[_build_index_views, _build_case_views]
    )
    if problems:
        print("package check failed:")
        for problem in problems:
            print(f"- {problem}")
        return 1
    print(f"package check passed: {args.package}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())