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

The scenario definitions export is written separately by ``extract-scenarios``
into the ``scenarios/`` documentation tree: reviewed targets, exact producer
prompts, fixed prompt templates, the shared delivery material (sanitized
effective configs, compiled system messages, and every file added to the
workspaces beyond the repository checkout), and one ``input.md`` per stage and
assessment. The export is generated from one guidance bundle at a time; git
tracks its evolution between evaluations while each result package freezes its
own copies of the material it was produced with. The two exports do not
reference each other.

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
from collections import Counter
import os
import shutil
import sys
import tempfile
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
from maintainer.guidance import (  # noqa: E402
    bundle_section_path,
    compile_guidance,
)

from .artifacts import record_paths  # noqa: E402
from .configuration import (  # noqa: E402
    AGENTS,
    CATEGORIES,
    DEFAULT_ARTIFACT_ROOT,
    DEFAULT_BUNDLE,
    SCENARIOS_ROOT,
    agent_config_file,
    assessment_cell_or_history,
    assessment_cell,
    negative_control,
    plan_variants,
)
from .fixtures import (  # noqa: E402
    BASE_REVISION,
    COMMON_GITIGNORE,
    GUIDANCE_TARGET_ROOT,
    AssessmentWorkspaceFactory,
    TaskGuidanceWorkspaceFactory,
    fixture_files,
)
from .handoff_semantic import HANDOFF_ASSESSMENT_PROMPT_TEMPLATE  # noqa: E402
from .handoffs import (  # noqa: E402
    PLAN_PROMPT,
    CanonicalHandoffWorkspaceFactory,
    GeneratedTaskWorkspaceFactory,
)
from .results import render_summary  # noqa: E402
from .runner import (  # noqa: E402
    RUNNER_VERSION,
    WorkspaceAwareEnvironment,
    _reload_context_with_defaults,
    _runtime_config_root,
    request_overrides,
)
from .scenarios import SCENARIOS  # noqa: E402
from .file_quality import FILE_FIDELITY_PROMPT_TEMPLATE  # noqa: E402
from .file_quality import FILE_READABILITY_PROMPT_TEMPLATE  # noqa: E402
from .plan_content import PLAN_CONTENT_PROMPT_TEMPLATE  # noqa: E402
from .quality import QUALITY_DIMENSIONS as QUALITY_GRADES  # noqa: E402
from .quality import TASK_QUALITY_ASSESSMENT_PROMPT_TEMPLATE  # noqa: E402
from .semantic import (  # noqa: E402
    QUALITY_DIMENSIONS,
    TASK_CREATION_ASSESSMENT_PROMPT_TEMPLATE,
    assessment_subject_identity,
    expected_producer_cells,
    handoff_cell_identity,
    producer_cell_identity,
)
from .stages import STAGES  # noqa: E402

SUITE_ROOT = PACKAGE_ROOT / "suites" / "task_guidance"
REPORT_CONFIG_SOURCE = SUITE_ROOT / "result_report_config.toml"
GENERATOR_VERSION = "task-guidance-result-package-v4"

PRODUCER_RECORD = STAGES["task-creation"].record
HANDOFF_RECORD = STAGES["handoff-plan"].record
SAME_AGENT_RECORD = STAGES["continuation"].record
NEGATIVE_CONTROL_RECORD = STAGES["negative-control"].record
SEMANTIC_RECORD = STAGES["task-creation-assessment"].record
HANDOFF_SEMANTIC_RECORD = STAGES["handoff-assessment"].record
QUALITY_RECORD = STAGES["task-quality-assessment"].record
PLAN_CONTENT_RECORD = STAGES["plan-content-assessment"].record
FILE_FIDELITY_RECORD = STAGES["file-fidelity-assessment"].record
FILE_READABILITY_RECORD = STAGES["file-readability-assessment"].record
GENERATED_PLAN_RECORD = STAGES["generated-plan"].record

KIND_TASK_CREATION = "task-creation"
KIND_PLAN_RETAIN = "plan-retain"
KIND_PLAN_OMIT = "plan-omit"
KIND_CONTINUATION = "continuation"
KIND_CONTROL = "control"
KIND_GENERATED_PLAN = "generated-plan"


def _dirname(path: str) -> str:
    return str(PurePosixPath(path).parent)


def _link(target: str, page: str) -> str:
    return relpath(target, _dirname(page))


NEGATIVE_CONTROL_SCENARIO = negative_control("handoff")["scenario"]
# Mirrors the negative-control designation in the configuration: only this
# scenario runs the incomplete-handoff control stage.


def _run_labels(frozen: Mapping[str, Any]) -> set[str]:
    """The run selection recorded by a frozen dataset (both shapes).

    Historical datasets record per-stage attempts; datasets frozen by the
    current ``freeze`` adapter record run labels. Discovery matches a
    run when its resolved label is in this set.
    """

    labels = frozen.get("labels")
    if isinstance(labels, list):
        return {str(item) for item in labels}
    attempts = frozen.get("attempts")
    if isinstance(attempts, Mapping):
        return {str(item) for item in attempts.values()}
    raise ValueError("frozen dataset records neither labels nor attempts")


def _resolve_bundle(
    frozen: Mapping[str, Any],
    bundle: Path | None,
) -> Path:
    """The guidance bundle of a collection: explicit override, then the
    bundle provenance recorded by the freeze adapter."""

    if bundle is not None:
        return bundle
    provenance = frozen.get("bundle")
    if isinstance(provenance, Mapping) and provenance.get("path"):
        return Path(str(provenance["path"]))
    raise ValueError(
        "no guidance bundle: pass --bundle or freeze with bundle provenance"
    )


def _selection_fields(frozen: Mapping[str, Any]) -> dict[str, Any]:
    """The run-selection provenance fields of a frozen dataset (both shapes)."""

    if isinstance(frozen.get("labels"), list):
        return {"labels": list(frozen["labels"])}
    if isinstance(frozen.get("attempts"), Mapping):
        return {"attempts": dict(frozen["attempts"])}
    raise ValueError("frozen dataset records neither labels nor attempts")


def extract_scenarios(*, output_dir: Path, bundle: Path, artifact_root: Path) -> Path:
    """Write the scenario definitions export from the suite sources.

    The export holds the evaluation's input definitions: reviewed targets,
    exact producer prompts, fixed prompt templates, the shared delivery
    material (sanitized effective configs, compiled system messages, and
    every file added to the workspaces beyond the repository checkout), and
    one ``input.md`` per stage and assessment describing what that stage
    feeds the model. The export is generated from one guidance bundle at a
    time; git tracks the tree's evolution between evaluations while each
    result package freezes its own copies of the material it was produced
    with. The two exports do not reference each other.
    """

    files: list[tuple[str, str]] = []
    files.extend(_template_export_files())
    files.extend(_included_files_exports(bundle=bundle))
    delivery = _compile_definitions_delivery(bundle=bundle, artifact_root=artifact_root)
    files.extend(delivery["files"])
    for scenario in SCENARIOS:
        files.extend(_scenario_export_files(scenario, delivery, bundle=bundle))
    files.append(("index.md", _scenarios_index_text(bundle=bundle)))

    # The export is fully generated: replace any previous state wholesale so
    # renamed content never leaves stale files behind.
    if output_dir.exists():
        shutil.rmtree(output_dir)
    for relative, content in sorted(files):
        target = output_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return output_dir


def _template_export_files() -> list[tuple[str, str]]:
    return [
        (
            "templates/handoff-plan-prompt.md",
            _generated_note(
                "Fixed instruction sent to a fresh planning agent together with"
                " a task file; asks for the Draft implementation plan without"
                " modifying files. The same prompt is the new user turn of"
                " the same-agent continuation stage."
            )
            + PLAN_PROMPT
            + "\n",
        ),
        (
            "templates/task-creation-assessment-prompt.md",
            _generated_note(
                "Fixed instruction part of the task-creation semantic"
                " assessment prompt. Per-evaluation material is substituted"
                " into the $placeholders: $scenario_id, $target_json,"
                " $prompt, $subject_json."
            )
            + TASK_CREATION_ASSESSMENT_PROMPT_TEMPLATE.template,
        ),
        (
            "templates/task-quality-assessment-prompt.md",
            _generated_note(
                "Fixed instruction part of the task-file quality assessment"
                " prompt. Per-evaluation material is substituted into the"
                " $placeholders: $scenario_id, $target_json, $prompt,"
                " $subject_json."
            )
            + TASK_QUALITY_ASSESSMENT_PROMPT_TEMPLATE.template,
        ),
        (
            "templates/plan-content-assessment-prompt.md",
            _generated_note(
                "Fixed instruction part of the presented-plan content"
                " assessment prompt. Per-evaluation material is substituted"
                " into the $placeholders: $scenario_id,"
                " $generic_requirements, $task_requirements,"
                " $approved_outcomes, $presented_plan."
            )
            + PLAN_CONTENT_PROMPT_TEMPLATE.template,
        ),
        (
            "templates/file-fidelity-assessment-prompt.md",
            _generated_note(
                "Fixed instruction part of the task-file fidelity assessment"
                " prompt. Per-evaluation material is substituted into the"
                " $placeholders: $scenario_id, $target_excerpt, $prompt,"
                " $conversation, $task_files."
            )
            + FILE_FIDELITY_PROMPT_TEMPLATE.template,
        ),
        (
            "templates/file-readability-assessment-prompt.md",
            _generated_note(
                "Fixed instruction part of the task-file readability"
                " assessment prompt. Per-evaluation material is substituted"
                " into the $placeholders: $scenario_id, $context_excerpt,"
                " $structure_facts, $task_files."
            )
            + FILE_READABILITY_PROMPT_TEMPLATE.template,
        ),
        (
            "templates/handoff-assessment-prompt.md",
            _generated_note(
                "Fixed instruction part of the handoff semantic assessment"
                " prompt. Per-evaluation material is substituted into the"
                " $placeholders: $scenario_id, $target_json, $subject_json."
            )
            + HANDOFF_ASSESSMENT_PROMPT_TEMPLATE.template,
        ),
    ]


def _included_files_exports(*, bundle: Path) -> list[tuple[str, str]]:
    """Export every file the workspace factories add beyond the checkout.

    The repository checkout itself is never included; the stage inputs
    record its revision instead. Fixture project files, the guidance
    compilation, the documentation section, the compilation lock, and the
    assessor workspace stub are all included.
    """

    files: list[tuple[str, str]] = []
    for scenario in SCENARIOS:
        fixture = {
            ".gitignore": COMMON_GITIGNORE,
            **fixture_files(scenario.fixture_id),
        }
        for relative, content in sorted(fixture.items()):
            files.append(
                (
                    f"shared/included-files/fixtures/{scenario.fixture_id}"
                    f"/{relative}",
                    content.rstrip() + "\n",
                )
            )
    for family in sorted({scenario.project_family for scenario in SCENARIOS}):
        compilation = compile_guidance(
            bundle=bundle,
            target=GUIDANCE_TARGET_ROOT / family,
            repository_root=REPOSITORY_ROOT,
        )
        for relative, content in sorted(compilation.outputs.items()):
            files.append(
                (
                    f"shared/included-files/guidance/{family}/{relative}",
                    content.decode("utf-8"),
                )
            )
        documentation = bundle_section_path(
            bundle=bundle,
            section="documentation",
            repository_root=REPOSITORY_ROOT,
        )
        files.append(
            (
                f"shared/included-files/guidance/{family}"
                "/docs/development/documentation.md",
                documentation.read_text(encoding="utf-8"),
            )
        )
        lock = dict(compilation.lock)
        # The production lock records absolute bundle and target paths; the
        # committed export normalizes them to repository-relative paths.
        for section, source in (
            ("bundle", bundle),
            ("target", GUIDANCE_TARGET_ROOT / family),
        ):
            value = lock.get(section)
            if isinstance(value, dict) and "path" in value:
                lock[section] = {
                    **value,
                    "path": str(source.resolve().relative_to(REPOSITORY_ROOT)),
                }
        files.append(
            (
                f"shared/included-files/guidance/{family}/.guidance-lock.json",
                json.dumps(lock, indent=2, sort_keys=True) + "\n",
            )
        )
    files.append(
        (
            "shared/included-files/assessment/README.md",
            "# Task-guidance semantic assessment\n",
        )
    )
    return files


def _compile_definitions_delivery(
    *,
    bundle: Path,
    artifact_root: Path,
) -> dict[str, Any]:
    """Compile the shared configs, system messages, and tool sets.

    One workspace per project family is prepared with the production
    factory and the delivered system message is compiled through the
    production system-message action — deterministically, without any
    model request. Machine-specific workspace paths are normalized exactly
    like the result packages normalize them.
    """

    system_messages = _SystemMessageStore()
    configs = _ConfigStore()
    messages: dict[tuple[str, str], str] = {}
    tools: dict[str, list[str]] = {}
    workspaces: dict[str, Path] = {}
    replacements: dict[str, dict[str, str]] = {}
    compiled_record = {
        "state": "compiled",
        "detail": (
            "compiled from the current suite sources and the selected"
            " guidance bundle"
        ),
    }
    families = sorted({scenario.project_family for scenario in SCENARIOS})
    family_scenario = {scenario.project_family: scenario for scenario in SCENARIOS}
    efforts: dict[str, set[str]] = {}
    for scenario in SCENARIOS:
        for provider, effort in expected_producer_cells(scenario):
            efforts.setdefault(provider, set()).add(effort)
    for family in families:
        scenario = family_scenario[family]
        factory = TaskGuidanceWorkspaceFactory(scenario=scenario, bundle=bundle)
        providers = sorted(
            {provider for provider, _ in expected_producer_cells(scenario)}
        )
        for provider in providers:
            with tempfile.TemporaryDirectory() as tmp:
                # Resolve symlinks (macOS /var → /private/var) so the
                # normalization map matches the path the environment
                # embeds into the compiled message.
                workspace = (Path(tmp) / "workspace").resolve()
                factory(workspace)
                compiled = _compile_system_message_for_workspace(
                    agent_name=provider,
                    effort=sorted(efforts[provider])[0],
                    bundle=bundle,
                    workspace=workspace,
                    artifact_root=artifact_root,
                    run_label=f"definitions-{provider}-{family}",
                )
            if compiled is None:
                raise RuntimeError(
                    f"system-message compilation returned no content for"
                    f" {provider} in family {family}"
                )
            body, active_tools = compiled
            message_replacements = _path_replacements(workspace)
            record = system_messages.add(
                key=provider,
                text=apply_replacements(body, message_replacements),
                original_sha256=sha256_text(body),
                availability_record=compiled_record,
                source="compiled-from-suite-sources",
            )
            messages[(provider, family)] = record["path"]
            tools[provider] = active_tools
            workspaces[provider] = workspace
            replacements[provider] = message_replacements

    assessor_name, assessor_effort = assessment_cell(
        "handoff", "task-creation-assessment"
    )
    assessor_factory = AssessmentWorkspaceFactory()
    with tempfile.TemporaryDirectory() as tmp:
        assessor_workspace = (Path(tmp) / "workspace").resolve()
        assessor_factory(assessor_workspace)
        compiled = _compile_system_message_for_workspace(
            agent_name=assessor_name,
            effort=assessor_effort,
            bundle=bundle,
            workspace=assessor_workspace,
            artifact_root=artifact_root,
            run_label="definitions-assessor",
            include_tasks=False,
        )
    if compiled is None:
        raise RuntimeError("assessor system-message compilation returned no content")
    assessor_body, assessor_tools = compiled
    assessor_replacements = _path_replacements(assessor_workspace)
    assessor_record = system_messages.add(
        key=f"{assessor_name}-assessor",
        text=apply_replacements(assessor_body, assessor_replacements),
        original_sha256=sha256_text(assessor_body),
        availability_record=compiled_record,
        source="compiled-from-suite-sources",
    )
    tools["assessor"] = assessor_tools

    config_paths: dict[str, str] = {}
    for provider in sorted(workspaces):
        for effort in sorted(efforts[provider]):
            key = f"{provider}-{effort}"
            config_paths[key] = configs.add(
                key,
                _effective_config_view(
                    agent_name=provider,
                    effort=effort,
                    workspace=workspaces[provider],
                    artifact_root=artifact_root,
                    replacements=replacements[provider],
                ),
            )
    config_paths[f"{assessor_name}-assessor-{assessor_effort}"] = configs.add(
        f"{assessor_name}-assessor-{assessor_effort}",
        _effective_config_view(
            agent_name=assessor_name,
            effort=assessor_effort,
            workspace=assessor_workspace,
            artifact_root=artifact_root,
            replacements=assessor_replacements,
            include_tasks=False,
        ),
    )
    files = [(file.relative_path, file.content) for file in system_messages.files()]
    files += [(file.relative_path, file.content) for file in configs.files()]
    return {
        "files": files,
        "messages": messages,
        "assessor_message": assessor_record["path"],
        "tools": tools,
        "config_paths": config_paths,
    }


def _scenario_export_files(
    scenario, delivery: Mapping[str, Any], *, bundle: Path
) -> list[tuple[str, str]]:
    scenario_id = scenario.scenario_id
    files: list[tuple[str, str]] = [
        (
            f"{scenario_id}/target.md",
            f"# Reviewed target — {scenario_id}\n\n"
            + "\n".join(_target_markdown(scenario.target)).rstrip()
            + "\n",
        ),
        (f"{scenario_id}/prompt.md", scenario.prompt.rstrip() + "\n"),
    ]
    if "handoff-plan" in CATEGORIES[scenario.category]["stages"]:
        variants = list(plan_variants(scenario.category))
        if scenario_id == NEGATIVE_CONTROL_SCENARIO:
            control = negative_control(scenario.category)
            assert control is not None
            variants.append(control["variant"])
        for variant in variants:
            source = CanonicalHandoffWorkspaceFactory(
                scenario=scenario, variant=variant, bundle=bundle
            ).source_path
            files.append(
                (
                    f"{scenario_id}/handoffs/{variant}.md",
                    source.read_text(encoding="utf-8"),
                )
            )
    files.append(
        (
            f"{scenario_id}/task-creation/input.md",
            _stage_input_markdown(
                scenario,
                delivery,
                stage="task-creation",
                page=f"{scenario_id}/task-creation/input.md",
                intro=(
                    "The producer stage asks the model to turn the natural"
                    " request into task files in the prepared workspace."
                ),
                extra=[
                    "- Prompt: [prompt.md](../prompt.md)",
                    "- Reviewed target: [target.md](../target.md)",
                ],
            ),
        )
    )
    if scenario.category == "handoff":
        for variant, stage, note in (
            (
                "retain",
                "plan-retain",
                "The fresh planning stage hands the retained-Draft canonical"
                " handoff task file to a new agent and asks for the"
                " implementation plan.",
            ),
            (
                "omit",
                "plan-omit",
                "The fresh planning stage hands the Draft-omitted canonical"
                " handoff task file to a new agent and asks for the"
                " implementation plan.",
            ),
        ):
            files.append(
                (
                    f"{scenario_id}/{stage}/input.md",
                    _stage_input_markdown(
                        scenario,
                        delivery,
                        stage=stage,
                        page=f"{scenario_id}/{stage}/input.md",
                        intro=note,
                        extra=[
                            "- Canonical handoff task file:"
                            f" [../handoffs/{variant}.md]"
                            f"(../handoffs/{variant}.md) — written to"
                            " `tasks/` in the workspace",
                            "- Prompt:"
                            " [handoff-plan-prompt.md]"
                            "(../../templates/handoff-plan-prompt.md)",
                            "- Reviewed target: [target.md](../target.md)",
                        ],
                    ),
                )
            )
        files.append(
            (
                f"{scenario_id}/continuation/input.md",
                _stage_input_markdown(
                    scenario,
                    delivery,
                    stage="continuation",
                    page=f"{scenario_id}/continuation/input.md",
                    intro=(
                        "The same-agent continuation adds the plan prompt as"
                        " a new user turn to the inherited producer session;"
                        " the workspace and the delivered instructions are"
                        " the producer run's."
                    ),
                    extra=[
                        "- Inherits: the producer run's session and"
                        " workspace; the delivered instructions are the"
                        " producer's compiled system message",
                        "- New user turn:"
                        " [handoff-plan-prompt.md]"
                        "(../../templates/handoff-plan-prompt.md)",
                        "- Reviewed target: [target.md](../target.md)",
                    ],
                ),
            )
        )
        if scenario_id == NEGATIVE_CONTROL_SCENARIO:
            files.append(
                (
                    f"{scenario_id}/control/input.md",
                    _stage_input_markdown(
                        scenario,
                        delivery,
                        stage="control",
                        page=f"{scenario_id}/control/input.md",
                        intro=(
                            "The negative control hands the intentionally"
                            " incomplete canonical handoff task file to a"
                            " fresh agent; a sound plan must flag the gaps"
                            " instead of inventing scope."
                        ),
                        extra=[
                            "- Canonical handoff task file:"
                            " [../handoffs/incomplete.md]"
                            "(../handoffs/incomplete.md) — written to"
                            " `tasks/` in the workspace",
                            "- Prompt:"
                            " [handoff-plan-prompt.md]"
                            "(../../templates/handoff-plan-prompt.md)",
                            "- Reviewed target: [target.md](../target.md)",
                        ],
                    ),
                )
            )
    assessments = [("task-creation", "task-creation")]
    if scenario.category == "handoff":
        assessments.append(("handoff", "handoff"))
    for name, template in assessments:
        template_note = (
            "task-creation-assessment-prompt.md"
            if name == "task-creation"
            else "handoff-assessment-prompt.md"
        )
        files.append(
            (
                f"{scenario_id}/assessment/{name}/input.md",
                _assessment_input_markdown(
                    scenario,
                    delivery,
                    name=name,
                    page=f"{scenario_id}/assessment/{name}/input.md",
                    template_note=template_note,
                ),
            )
        )
    return files


def _stage_input_markdown(
    scenario,
    delivery: Mapping[str, Any],
    *,
    stage: str,
    page: str,
    intro: str,
    extra: Sequence[str],
) -> str:
    """Render one stage input page in the session-header format."""

    scenario_id = scenario.scenario_id
    cells = expected_producer_cells(scenario)
    models = " · ".join(
        f"{AGENTS[provider]['model']} ({provider} {effort})"
        for provider, effort in cells
    )
    instructions = " · ".join(
        f"[{provider}]"
        f"({_link(delivery['messages'][(provider, scenario.project_family)], page)})"
        for provider, _ in cells
    )
    config_links = " · ".join(
        f"[{provider}-{effort}]"
        f"({_link(delivery['config_paths'][f'{provider}-{effort}'], page)})"
        for provider, effort in cells
    )
    tools = " · ".join(
        f"{provider}: {', '.join(delivery['tools'][provider])}" for provider, _ in cells
    )
    project = scenario.target.get("project") or {}
    lines = [
        f"# Input — {scenario_id} · {stage}",
        "",
        intro,
        "",
        f"- Models: {models}",
        f"- Tools: {tools}",
        f"- Delivered instructions: {instructions}",
        f"- Config: {config_links}",
        "- Workspace: this repository's history at"
        f" `{BASE_REVISION}` (checkout content not included); the producer"
        " working tree is replaced by the files below",
        "- Fixture project:"
        f" {project.get('name', 'unknown')} —"
        f" {project.get('upstream', 'unknown')}"
        f" @ `{project.get('revision', 'unknown')}`"
        f" → [fixture files]({_link(f'shared/included-files/fixtures/{scenario.fixture_id}', page)})",
        "- Guidance:"
        f" [AGENTS.md, documentation, lock]({_link(f'shared/included-files/guidance/{scenario.project_family}', page)})",
        *extra,
    ]
    return "\n".join(lines) + "\n"


def _assessment_input_markdown(
    scenario,
    delivery: Mapping[str, Any],
    *,
    name: str,
    page: str,
    template_note: str,
) -> str:
    """Render one assessment input page in the session-header format."""

    scenario_id = scenario.scenario_id
    assessor_name, assessor_effort = assessment_cell(
        "handoff", "task-creation-assessment"
    )
    lines = [
        f"# Input — {scenario_id} · {name} assessment",
        "",
        "The assessor judges the scenario's runs against the reviewed"
        " target. Per-evaluation records are substituted into the prompt"
        " template's $placeholders; the exact prompts and responses live in"
        " the result packages.",
        "",
        f"- Assessor: {AGENTS[assessor_name]['model']}"
        f" ({assessor_name} {assessor_effort})",
        f"- Tools: {', '.join(delivery['tools']['assessor'])}",
        "- Delivered instructions:"
        f" [{assessor_name}-assessor]({_link(delivery['assessor_message'], page)})",
        "- Config:"
        f" [{assessor_name}-assessor-{assessor_effort}]"
        f"({_link(delivery['config_paths'][f'{assessor_name}-assessor-{assessor_effort}'], page)})",
        "- Workspace: this repository's history at"
        f" `{BASE_REVISION}` plus a"
        f" [README stub]({_link('shared/included-files/assessment/README.md', page)})",
        f"- Prompt template: [{template_note}](../../../templates/{template_note})",
        "- Reviewed target: [target.md](../../target.md)",
    ]
    return "\n".join(lines) + "\n"


def _scenarios_index_text(*, bundle: Path) -> str:
    lines = [
        "# Task-guidance evaluation scenarios",
        "",
        "Scenario definitions and stage inputs for the task-guidance"
        " evaluation suite, generated from the suite sources in"
        " `maintainer/agent-evaluation/suites/task_guidance/`"
        " (`result_package.py extract-scenarios`) with the guidance bundle"
        f" `{bundle.relative_to(REPOSITORY_ROOT)}`.",
        "",
        "These definitions may change between evaluations; git tracks their"
        " evolution here while each result package under `../results/`"
        " freezes its own copies of the material it was produced with.",
        "",
        "## Shared inputs",
        "",
        "| Material | Contents |",
        "|---|---|",
        "| [configs](shared/configs/) | sanitized effective configurations"
        " per profile |",
        "| [system-messages](shared/system-messages/) | compiled delivered"
        " instructions per provider and project family |",
        "| [included-files](shared/included-files/) | every file added to"
        " the workspaces: fixture projects, guidance compilation,"
        " assessor stub |",
        "",
        "## Prompt templates",
        "",
        "| Template | Used by |",
        "|---|---|",
        "| [handoff-plan-prompt.md](templates/handoff-plan-prompt.md) |"
        " fresh planning agents and same-agent continuations |",
        "| [task-creation-assessment-prompt.md]"
        "(templates/task-creation-assessment-prompt.md) |"
        " task-creation semantic assessor |",
        "| [handoff-assessment-prompt.md]"
        "(templates/handoff-assessment-prompt.md) |"
        " handoff semantic assessor |",
        "",
        "## Scenarios",
        "",
        "| Scenario | Reviewed target | Producer prompt | Stage inputs |",
        "|---|---|---|---|",
    ]
    for scenario in SCENARIOS:
        scenario_id = scenario.scenario_id
        stages = ["task-creation"]
        if scenario.category == "handoff":
            stages.extend(["plan-retain", "plan-omit", "continuation"])
            if scenario_id == NEGATIVE_CONTROL_SCENARIO:
                stages.append("control")
        stage_links = " · ".join(
            f"[{stage}]({scenario_id}/{stage}/input.md)" for stage in stages
        )
        assessment_links = [
            f"[task-creation]({scenario_id}/assessment/task-creation/input.md)"
        ]
        if scenario.category == "handoff":
            assessment_links.append(
                f"[handoff]({scenario_id}/assessment/handoff/input.md)"
            )
        lines.append(
            f"| `{scenario_id}`"
            f" | [target]({scenario_id}/target.md)"
            f" | [prompt]({scenario_id}/prompt.md)"
            f" | {stage_links} · assessments: {' · '.join(assessment_links)} |"
        )
    return "\n".join(lines) + "\n"


def _generated_note(note: str) -> str:
    return f"<!-- {note} -->\n\n"


def collect(
    *,
    package_dir: Path,
    artifact_root: Path,
    frozen_path: Path,
    cells: Sequence[str] | None = None,
    reconstruct: bool = True,
    bundle: Path | None = None,
) -> Path:
    """Collect one durable result package without any model request.

    The dataset identity — id, label, run selection, and guidance bundle
    — is read from the frozen dataset file; the package name is the
    output directory name.
    """

    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    resolved_bundle = _resolve_bundle(frozen, bundle)
    selected_cells = _parse_cells(cells)
    discovery = _discover_runs(artifact_root, frozen)
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
                    **_selection_fields(frozen),
                    "status": frozen["status"],
                    "semantic_quality": frozen["semantic_quality"],
                    "assessment_details": _assessment_details(frozen),
                    "invalid_records": [
                        {
                            "group": group,
                            # The run id is freeze-to-collect mapping
                            # metadata, not part of the reviewed evidence.
                            "record": _without_run_id(record),
                        }
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
                "path": _provenance_path(frozen_path),
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
            bundle=resolved_bundle,
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
        "name": package_dir.name,
        "label": frozen["label"],
        "dataset_id": frozen["dataset_id"],
        "suite": "task-guidance",
        **_selection_fields(frozen),
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


def _provenance_path(path: Path) -> str:
    """Record a repository-relative provenance path when one exists."""

    try:
        return str(path.resolve().relative_to(REPOSITORY_ROOT))
    except ValueError:
        return str(path)


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


def _record_label(path: Path, value: Mapping[str, Any]) -> Any:
    """The run label of one raw record (sibling provenance, then legacy)."""

    sibling = path.parent / "run-model.json"
    if sibling.exists():
        try:
            provenance = json.loads(sibling.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            provenance = {}
        if isinstance(provenance, dict):
            label = provenance.get("label")
            if isinstance(label, str) and label:
                return label
    return value.get("run_attempt")


def _without_run_id(record: Mapping[str, Any]) -> dict[str, Any]:
    """The record as evidence, without the freeze-to-collect mapping field."""

    return {key: value for key, value in record.items() if key != "run_id"}


def _has_run_id(record: Mapping[str, Any]) -> bool:
    run_id = record.get("run_id")
    return isinstance(run_id, str) and bool(run_id)


def _map_exact_runs(
    artifact_root: Path,
    mapping: dict[str, Path],
    records: Iterable[Mapping[str, Any]],
) -> None:
    """Map every run-id-carrying record to its exact run directory.

    The frozen dataset names the raw run of every current record, so the
    collector never has to guess which run produced a record — multiple
    samples of one cell each resolve to their own run.
    """

    for record in records:
        run_id = record.get("run_id")
        if not isinstance(run_id, str) or not run_id or run_id in mapping:
            continue
        matches = sorted(artifact_root.glob(f"*/runs/{run_id}"))
        if not matches:
            raise FileNotFoundError(f"no raw run found for run id {run_id!r}")
        mapping[run_id] = matches[0]


def _run_dir_for(
    discovery: Mapping[str, Path],
    record: Mapping[str, Any],
    fallback_key: str,
) -> Path:
    """The record's named run when it carries one, else the fallback key."""

    run_id = record.get("run_id")
    if isinstance(run_id, str) and run_id:
        return discovery[run_id]
    return discovery[fallback_key]


def _discover_runs(
    artifact_root: Path,
    frozen: Mapping[str, Any],
) -> dict[str, Path]:
    """Map each frozen record to its raw run directory.

    A record that names a run id maps to that exact run. A record without
    one — a historical frozen dataset — falls back to the newest raw run
    whose resolved label (the run-model sibling's label for current
    records, the legacy ``run_attempt`` field for historical ones) and
    identity match the record.
    """

    # Labels are needed only by the fallback path. A dataset frozen with
    # default latest-label selection records no label list, and every one
    # of its records names its exact run — so label resolution stays lazy.
    labels: set[str] | None = None

    def _fallback_labels() -> set[str]:
        nonlocal labels
        if labels is None:
            labels = _run_labels(frozen)
        return labels

    mapping: dict[str, Path] = {}
    groups = (
        (PRODUCER_RECORD, "producer_records", producer_cell_identity),
        (HANDOFF_RECORD, "handoff_records", handoff_cell_identity),
        (SAME_AGENT_RECORD, "same_agent_records", producer_cell_identity),
        (NEGATIVE_CONTROL_RECORD, "negative_control_records", handoff_cell_identity),
        (QUALITY_RECORD, "quality_records", assessment_subject_identity),
        (
            GENERATED_PLAN_RECORD,
            "generated_plan_records",
            producer_cell_identity,
        ),
    )
    for record_name, group, identity_of in groups:
        records = [
            record for record in frozen.get(group, ()) if isinstance(record, Mapping)
        ]
        _map_exact_runs(artifact_root, mapping, records)
        wanted = {identity_of(record) for record in records if not _has_run_id(record)}
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
            if (
                _record_label(path, value) not in _fallback_labels()
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
    for group, record_name in (
        ("semantic_records", SEMANTIC_RECORD),
        ("handoff_semantic_records", HANDOFF_SEMANTIC_RECORD),
        ("quality_records", QUALITY_RECORD),
        ("plan_content_records", PLAN_CONTENT_RECORD),
        ("file_fidelity_records", FILE_FIDELITY_RECORD),
        ("file_readability_records", FILE_READABILITY_RECORD),
    ):
        records = [
            record for record in frozen.get(group, ()) if isinstance(record, Mapping)
        ]
        _map_exact_runs(artifact_root, mapping, records)
        for record in records:
            if _has_run_id(record):
                continue
            scenario_id = record.get("scenario_id")
            subject = record.get("subject")
            if not isinstance(subject, Mapping):
                subject = None
            assessment = record.get("assessment")
            variant = (
                assessment.get("variant") if isinstance(assessment, Mapping) else None
            )
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
                    or _record_label(path, value) not in _fallback_labels()
                ):
                    continue
                if subject is not None:
                    raw_subject = value.get("subject")
                    if not isinstance(raw_subject, Mapping):
                        continue
                    if (
                        raw_subject.get("profile"),
                        raw_subject.get("reasoning_effort"),
                        raw_subject.get("sample_index"),
                    ) != (
                        subject.get("profile"),
                        subject.get("reasoning_effort"),
                        subject.get("sample_index"),
                    ):
                        continue
                    # Handoff judgments of one producer cell share the
                    # subject mapping; the assessment variant is the
                    # dimension that tells them apart.
                    raw_assessment = value.get("assessment")
                    raw_variant = (
                        raw_assessment.get("variant")
                        if isinstance(raw_assessment, Mapping)
                        else None
                    )
                    if raw_variant != variant:
                        continue
                modified = path.stat().st_mtime
                if modified > latest:
                    latest = modified
                    selected_path = path.parents[1]
            if selected_path is None:
                raise FileNotFoundError(
                    f"no raw run found for {record_name} scenario {scenario_id!r}"
                )
            if subject is not None:
                mapping[
                    f"{group}:{scenario_id}:{variant}:"
                    f"{subject.get('profile')}:"
                    f"{subject.get('reasoning_effort')}:s{subject.get('sample_index')}"
                ] = selected_path
            else:
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
    bundle: Path,
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
    # A frozen dataset predating later scenarios collects only what it
    # holds; absent scenarios export nothing rather than failing.
    present = any(
        isinstance(record, Mapping) and record.get("scenario_id") == scenario_id
        for group in (
            "producer_records",
            "handoff_records",
            "same_agent_records",
            "negative_control_records",
            "generated_plan_records",
            "semantic_records",
            "handoff_semantic_records",
            "quality_records",
        )
        for record in frozen.get(group, ())
    )
    if not present:
        return
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
            bundle=bundle,
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
        bundle=bundle,
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
    bundle: Path,
    frozen: Mapping[str, Any],
    discovery: Mapping[str, Path],
    artifact_root: Path,
    reconstruct: bool,
    system_messages: _SystemMessageStore,
    configs: _ConfigStore,
    runs: list[dict[str, Any]],
    files: list[CollectedFile],
) -> None:
    """Collect one producer cell subtree: every sample of every stage.

    Layout: ``scenarios/<id>/<cell>/s<N>/`` holds one producer sample
    (run, session, task files, ``invalid.md`` when invalid); stage runs
    (``plan-retain``, ``plan-omit``, ``continuation``, ``control``,
    ``generated-plan``) hold their own samples the same way, so every
    judgment's subject stays inspectable beside the evidence.
    """

    scenario_id = scenario.scenario_id
    cell_prefix = f"scenarios/{scenario_id}/{cell_key}"

    def _stage_entries(
        records: Sequence[Mapping[str, Any]], fallback_key: str
    ) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for record in records:
            run_dir = _run_dir_for(discovery, record, fallback_key)
            entries.append(
                {
                    "record": record,
                    "run_dir": run_dir,
                    "sample": _run_model_sample(run_dir),
                    "label": _run_label(run_dir),
                }
            )
        return entries

    def _collect_group(
        kind: str,
        entries: Sequence[Mapping[str, Any]],
        *,
        stage_dir: str | None,
        factory_of,
        lineage: bool = False,
        reconstruct_stage: bool = True,
        inherited_instructions: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any] | None:
        """Collect one stage group's samples; return the first instructions."""

        first_instructions: Mapping[str, Any] | None = None
        for entry, sample_dir in zip(entries, _assign_sample_dirs(entries)):
            sample_prefix = (
                f"{cell_prefix}/{sample_dir}"
                if stage_dir is None
                else f"{cell_prefix}/{stage_dir}/{sample_dir}"
            )
            stage_label = stage_dir or "producer"
            _, instructions = _collect_run(
                kind,
                entry["record"],
                subdir=None,
                run_dir=entry["run_dir"],
                scenario=scenario,
                bundle=bundle,
                profile=profile,
                effort=effort,
                factory=factory_of(entry["record"]),
                artifact_root=artifact_root,
                system_messages=system_messages,
                configs=configs,
                runs=runs,
                files=files,
                cell_prefix=sample_prefix,
                task_files=entry["record"].get("task_files") or {},
                lineage=lineage,
                reconstruct=reconstruct_stage,
                inherited_instructions=inherited_instructions,
            )
            _write_invalid_note(
                entry["record"],
                sample_prefix,
                files=files,
                title=f"{scenario_id} {cell_key} {stage_label} {sample_dir}",
                label=entry["label"],
            )
            if first_instructions is None:
                first_instructions = instructions
        return first_instructions

    producer_instructions = _collect_group(
        KIND_TASK_CREATION,
        _stage_entries(
            _find_all(frozen["producer_records"], scenario_id, profile, effort),
            f"producer_records:{scenario_id}:{profile}:{effort}",
        ),
        stage_dir=None,
        factory_of=lambda record: TaskGuidanceWorkspaceFactory(
            scenario=scenario, bundle=bundle
        ),
        reconstruct_stage=reconstruct,
    )

    for variant, kind, subdir in (
        ("retain", KIND_PLAN_RETAIN, "plan-retain"),
        ("omit", KIND_PLAN_OMIT, "plan-omit"),
    ):
        _collect_group(
            kind,
            _stage_entries(
                _find_all_variant(
                    frozen["handoff_records"], scenario_id, variant, profile, effort
                ),
                f"handoff_records:{scenario_id}:{variant}:{profile}:{effort}",
            ),
            stage_dir=subdir,
            factory_of=lambda record, variant=variant: CanonicalHandoffWorkspaceFactory(
                scenario=scenario,
                variant=variant,
                bundle=bundle,
            ),
            reconstruct_stage=reconstruct,
        )

    _collect_group(
        KIND_CONTINUATION,
        _stage_entries(
            _find_all(frozen["same_agent_records"], scenario_id, profile, effort),
            f"same_agent_records:{scenario_id}:{profile}:{effort}",
        ),
        stage_dir="continuation",
        factory_of=lambda record: TaskGuidanceWorkspaceFactory(
            scenario=scenario, bundle=bundle
        ),
        lineage=True,
        reconstruct_stage=False,
        inherited_instructions=producer_instructions,
    )

    _collect_group(
        KIND_CONTROL,
        _stage_entries(
            _find_all_variant(
                frozen["negative_control_records"],
                scenario_id,
                "incomplete",
                profile,
                effort,
            ),
            f"negative_control_records:{scenario_id}:incomplete:{profile}:{effort}",
        ),
        stage_dir="control",
        factory_of=lambda record: CanonicalHandoffWorkspaceFactory(
            scenario=scenario,
            variant="incomplete",
            bundle=bundle,
        ),
        reconstruct_stage=False,
    )

    _collect_group(
        KIND_GENERATED_PLAN,
        _stage_entries(
            _find_all(
                frozen.get("generated_plan_records", ()),
                scenario_id,
                profile,
                effort,
            ),
            f"generated_plan_records:{scenario_id}:{profile}:{effort}",
        ),
        stage_dir="generated-plan",
        factory_of=lambda record: GeneratedTaskWorkspaceFactory(
            scenario=scenario,
            bundle=bundle,
            task_files=record.get("task_files") or {},
        ),
        reconstruct_stage=reconstruct,
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


def _find_all(
    records: Iterable[Mapping[str, Any]],
    scenario_id: str,
    profile: str,
    effort: str,
) -> list[Mapping[str, Any]]:
    """Return every sample of one cell, ordered by sample index."""

    matches = [
        record
        for record in records
        if isinstance(record, Mapping)
        and record.get("scenario_id") == scenario_id
        and (record.get("producer") or {}).get("profile") == profile
        and (record.get("producer") or {}).get("reasoning_effort") == effort
    ]
    return sorted(matches, key=_sample_index)


def _find_all_variant(
    records: Iterable[Mapping[str, Any]],
    scenario_id: str,
    variant: str,
    profile: str,
    effort: str,
) -> list[Mapping[str, Any]]:
    """Return every sample of one variant cell, ordered by sample index."""

    matches = [
        record
        for record in records
        if isinstance(record, Mapping)
        and record.get("scenario_id") == scenario_id
        and record.get("variant") == variant
        and (record.get("producer") or {}).get("profile") == profile
        and (record.get("producer") or {}).get("reasoning_effort") == effort
    ]
    return sorted(matches, key=_sample_index)


def _sample_index(record: Mapping[str, Any]) -> int:
    """Sample directory index; records without one share ``s0``."""

    value = record.get("sample_index")
    return 0 if value is None else int(value)


def _run_model_sample(run_dir: Path) -> int:
    """The run's own sample index, as the consolidation core numbers it."""

    path = run_dir / "records" / "run-model.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    sample = value.get("sample_index") if isinstance(value, dict) else None
    return sample if isinstance(sample, int) and sample >= 0 else 0


def _run_label(run_dir: Path) -> str | None:
    """The run's recorded label, when its run model kept one."""

    path = run_dir / "records" / "run-model.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    label = value.get("label") if isinstance(value, dict) else None
    return label if isinstance(label, str) and label else None


def _assign_sample_dirs(
    entries: Sequence[Mapping[str, Any]],
) -> list[str]:
    """One sample directory per record of one cell-stage group.

    Valid records claim the sample index their run model recorded (the
    same numbering assessment subjects use), so judgments land beside
    the evidence they judge. Invalid records fill the remaining free
    indexes — a re-run of a failed sample under a new label then reads
    as the next sample instead of colliding with the valid one.
    """

    def claim_order(index: int) -> tuple[int, str]:
        return (entries[index]["sample"], entries[index]["run_dir"].name)

    valid_indexes = [
        index
        for index, entry in enumerate(entries)
        if entry["record"].get("valid") is not False
    ]
    invalid_indexes = [
        index
        for index, entry in enumerate(entries)
        if entry["record"].get("valid") is False
    ]
    assigned: dict[int, str] = {}
    used: set[int] = set()
    leftover: list[int] = []
    for index in sorted(valid_indexes, key=claim_order):
        sample = entries[index]["sample"]
        if sample in used:
            leftover.append(index)
            continue
        assigned[index] = f"s{sample}"
        used.add(sample)
    next_free = 0
    for index in leftover + sorted(invalid_indexes, key=claim_order):
        while next_free in used:
            next_free += 1
        assigned[index] = f"s{next_free}"
        used.add(next_free)
    return [assigned[index] for index in range(len(entries))]


def _is_provider_failure(record: Mapping[str, Any]) -> bool:
    reasons = record.get("invalid_reasons") or []
    return any(
        isinstance(reason, str) and reason.startswith("run failure:")
        for reason in reasons
    )


def _write_invalid_note(
    record: Mapping[str, Any],
    sample_prefix: str,
    *,
    files: list[CollectedFile],
    title: str,
    label: str | None = None,
) -> None:
    """Export one invalid sample's recorded reasons beside its evidence."""

    if record.get("valid") is not False and not record.get("invalid_reasons"):
        return
    reasons = [str(reason) for reason in record.get("invalid_reasons") or []]
    category = (
        "provider failure" if _is_provider_failure(record) else "validity failure"
    )
    lines = [
        f"# Invalid sample — {title}",
        "",
        f"- Category: **{category}**",
    ]
    if label:
        lines.append(f"- Run label: `{label}`")
    if reasons:
        lines.append("- Recorded reasons:")
        lines.extend(f"  - {reason}" for reason in reasons)
    response = record.get("response")
    if isinstance(response, str) and response.strip():
        excerpt = " ".join(response.split())
        if len(excerpt) > 400:
            excerpt = excerpt[:400] + "…"
        lines.extend(
            [
                "- Response excerpt:",
                "",
                "> " + excerpt,
            ]
        )
    lines.append("- Session (if exported): [session.md](session.md)")
    files.append(
        CollectedFile(
            relative_path=f"{sample_prefix}/invalid.md",
            content="\n".join(lines) + "\n",
        )
    )


def _collect_run(
    kind: str,
    record: Mapping[str, Any],
    *,
    subdir: str | None,
    run_dir: Path,
    scenario,
    bundle: Path,
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
    inherited_instructions: Mapping[str, Any] | None = None,
    config_include_tasks: bool = True,
) -> tuple[dict[str, Any], dict[str, Any]]:
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
        bundle=bundle,
        factory=factory,
        workspace=workspace,
        run_dir=run_dir,
        artifact_root=artifact_root,
        replacements=replacements,
        reconstruct=reconstruct,
    )
    if (
        instructions["text"] is None
        and inherited_instructions is not None
        and inherited_instructions.get("text") is not None
    ):
        # A same-agent continuation inherits the producer's session, so its
        # delivered instructions are the producer's compiled system message
        # even though the continuation's own saved session retained no text.
        producer_state = inherited_instructions["availability"]["state"]
        instructions = {
            "text": inherited_instructions["text"],
            "original_sha256": inherited_instructions["original_sha256"],
            "availability": availability(
                "inherited",
                detail=(
                    "inherited from the cell's producer run, whose delivered"
                    f" instructions are {producer_state}"
                ),
            ),
            "source": "inherited-from-producer-run",
        }
    system_message = (
        system_messages.add(
            key=system_message_key or profile,
            text=instructions["text"],
            original_sha256=instructions["original_sha256"],
            availability_record=instructions["availability"],
            source=instructions["source"],
        )
        if instructions["text"] is not None
        else {"availability": instructions["availability"], "source": None}
    )
    config_path = configs.add(
        config_key or f"{profile}-{effort}",
        _effective_config_view(
            agent_name=profile,
            effort=effort,
            workspace=workspace,
            artifact_root=artifact_root,
            replacements=replacements,
            include_tasks=config_include_tasks,
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
        instructions_label = system_message_key or f"{profile}-{effort}"
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
            "Model": f"{AGENTS[profile]['model']} (effort {effort})",
        }
        if tools:
            context["Tools"] = tools
        context["Delivered instructions"] = instructions_note
        context["Config"] = (
            f"[{config_key or f'{profile}-{effort}'}]"
            f"({_link(config_path, session_page)})"
        )
        files.append(
            CollectedFile(
                relative_path=session_page,
                content=render_session_markdown(
                    review,
                    title=(f"{scenario.scenario_id} · {kind} ·" f" {profile} {effort}"),
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
            "label": f"{scenario.scenario_id} {kind} {profile} {effort}",
            "provider": profile,
            "model": AGENTS[profile]["model"],
            "reasoning_effort": effort,
            "usage": usage,
            "kind": kind,
            "scenario_id": scenario.scenario_id,
        }
    )
    run_record: dict[str, Any] = {
        "run_id": run_id,
        "kind": kind,
        "provider": profile,
        "model": AGENTS[profile]["model"],
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
    return run_record, instructions


def _stage_instructions(
    record: Mapping[str, Any],
    *,
    session: Mapping[str, Any] | None,
    profile,
    effort: str,
    scenario,
    bundle: Path,
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
        and profile == "gpt"
        and workspace == run_dir / "workspace"
    ):
        body = _reconstruct_compiled_message(
            agent_name=profile,
            effort=effort,
            bundle=bundle,
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
        "saved session retains no system message and no delivery hash was" " recorded"
        if not expected_hash
        else (
            "reconstruction was not run for this stage"
            if not reconstruct
            else "reconstruction failed or was not applicable"
        )
    )
    return {
        "text": None,
        "original_sha256": None,
        "availability": availability("unavailable", detail=detail),
        "source": None,
    }


def _reconstruct_compiled_message(
    *,
    agent_name: str,
    effort: str,
    bundle: Path,
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
        compiled = _compile_system_message_for_workspace(
            agent_name=agent_name,
            effort=effort,
            bundle=bundle,
            workspace=workspace,
            artifact_root=artifact_root,
            run_label=f"reconstruct-{run_dir.name}",
        )
        return None if compiled is None else compiled[0]
    except Exception:
        return None
    finally:
        factory.cleanup(workspace)


def _compile_system_message_for_workspace(
    *,
    agent_name: str,
    effort: str,
    bundle: Path,
    workspace: Path,
    artifact_root: Path,
    run_label: str,
    include_tasks: bool = True,
) -> tuple[str, list[str]] | None:
    """Compile the delivered system message for one prepared workspace.

    Runs the production system-message action inside the pinned runtime
    environment — no model request is made. Returns the compiled message and
    the active tool names; raises on failure so callers decide policy.
    """

    runtime_config = _runtime_config_root(bundle=bundle, artifact_root=artifact_root)
    agent_config = agent_config_file(
        agent_name,
        artifact_root=artifact_root,
        version=RUNNER_VERSION,
    )
    environment = WorkspaceAwareEnvironment.from_config(
        agent_config,
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
            "PIP_CONSTRAINT": str(PACKAGE_ROOT / "constraints" / "plugin-runtime.txt"),
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
            run_id=run_label,
            name="compile",
            artifact_dir=Path(tmp),
            workspace=workspace,
            parent=None,
            evidence=EvidenceJournal(),
            artifacts=ArtifactWriter(Path(tmp) / "artifacts"),
        )
        with environment.open(
            services=services, workspace=workspace, parent_snapshot=None
        ) as context:
            context.start(AGENTS[agent_name]["agent_id"])
            context.config.update(
                request_overrides(
                    agent_name,
                    workspace,
                    reasoning_effort=effort,
                    include_tasks=include_tasks,
                )
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
            active = context.core.get_plugins_for_config(effective)
            tools = [
                str(tool)
                for tool in (
                    active.get("tools", []) if isinstance(active, Mapping) else []
                )
            ]
            return body, tools


def _effective_config_view(
    *,
    agent_name: str,
    effort: str,
    workspace: Path,
    artifact_root: Path,
    replacements: Mapping[str, str],
    include_tasks: bool = True,
) -> dict[str, Any]:
    agent_config = agent_config_file(
        agent_name,
        artifact_root=artifact_root,
        version=RUNNER_VERSION,
    )
    runtime_config = (
        json.loads(agent_config.read_text(encoding="utf-8"))
        if agent_config.is_file()
        else {}
    )
    overrides = request_overrides(
        agent_name,
        workspace,
        reasoning_effort=effort,
        include_tasks=include_tasks,
    )
    return project_effective_config_view(
        {
            "agent_id": AGENTS[agent_name]["agent_id"],
            "model": AGENTS[agent_name]["model"],
            "reasoning_effort": effort,
            "runtime_config": runtime_config,
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
    bundle: Path,
    frozen: Mapping[str, Any],
    discovery: Mapping[str, Path],
    artifact_root: Path,
    system_messages: _SystemMessageStore,
    configs: _ConfigStore,
    runs: list[dict[str, Any]],
    files: list[CollectedFile],
) -> None:
    scenario_id = scenario.scenario_id
    # One assessment.md per judged subject accumulates every stage's
    # judgment of that subject, written after all stages collected.
    subject_notes: dict[str, list[str]] = {}
    for name, group, title in (
        (
            "task-creation",
            "semantic_records",
            "Task-creation semantic assessment",
        ),
        ("handoff", "handoff_semantic_records", "Handoff semantic assessment"),
        (
            "task-quality",
            "quality_records",
            "Task-file quality assessment",
        ),
        (
            "plan-content",
            "plan_content_records",
            "Presented-plan content assessment",
        ),
        (
            "file-fidelity",
            "file_fidelity_records",
            "Task-file fidelity assessment",
        ),
        (
            "file-readability",
            "file_readability_records",
            "Task-file readability assessment",
        ),
    ):
        records = [
            record
            for record in frozen.get(group, ())
            if isinstance(record, Mapping) and record.get("scenario_id") == scenario_id
        ]
        if not records:
            continue
        if all(isinstance(record.get("subject"), Mapping) for record in records):
            _collect_per_subject_assessment(
                name=name,
                title=title,
                group=group,
                records=records,
                scenario=scenario,
                bundle=bundle,
                discovery=discovery,
                artifact_root=artifact_root,
                system_messages=system_messages,
                configs=configs,
                runs=runs,
                files=files,
                subject_notes=subject_notes,
            )
        else:
            _collect_assessment_record(
                name=name,
                title=title,
                record=records[0],
                run_dir=_run_dir_for(discovery, records[0], f"{group}:{scenario_id}"),
                scenario=scenario,
                bundle=bundle,
                artifact_root=artifact_root,
                system_messages=system_messages,
                configs=configs,
                runs=runs,
                files=files,
            )
    for subject_dir, notes in sorted(subject_notes.items()):
        page = f"{subject_dir}/assessment.md"
        evidence_links = (
            f"[session.md]({_link(f'{subject_dir}/session.md', page)})"
            f" · [run.json]({_link(f'{subject_dir}/run.json', page)})"
        )
        files.append(
            CollectedFile(
                relative_path=page,
                content=(
                    f"# Assessment — "
                    f"{subject_dir.split('/', 1)[1].replace('/', ' · ')}\n\n"
                    + "\n".join(notes).rstrip()
                    + f"\n\n- Evidence: {evidence_links}\n"
                ),
            )
        )


def _subject_directory(
    name: str, scenario_id: str, subject: Mapping[str, Any], variant: Any, stage: Any
) -> str | None:
    """The evidence directory of the subject one assessment judges.

    Producer-sample assessments point at the producer sample; handoff
    assessments point at the plan-stage sample the judgment is about.
    """

    subject_cell = f"{subject.get('profile')}-{subject.get('reasoning_effort')}"
    sample = _sample_index(subject)
    if name in ("handoff", "plan-content"):
        stage_dir = _handoff_stage_dir(variant=variant, stage=stage)
        if stage_dir is None:
            return None
        return f"scenarios/{scenario_id}/{subject_cell}/{stage_dir}/s{sample}"
    return f"scenarios/{scenario_id}/{subject_cell}/s{sample}"


def _collect_per_subject_assessment(
    *,
    name: str,
    title: str,
    group: str,
    records: Sequence[Mapping[str, Any]],
    scenario,
    bundle: Path,
    discovery: Mapping[str, Path],
    artifact_root: Path,
    system_messages: _SystemMessageStore,
    configs: _ConfigStore,
    runs: list[dict[str, Any]],
    files: list[CollectedFile],
    subject_notes: dict[str, list[str]],
) -> None:
    """Collect one assessor run per subject, one shared results page.

    Every sample of every subject cell is its own assessment request, so
    each record collects its own run directory. Assessor runs live under
    the subject's cell subtree (``<cell>/assessment/<stage>/…``) and each
    judged subject accumulates an ``assessment.md`` grade summary one
    level beside its evidence.
    """

    def subject_key(record: Mapping[str, Any]) -> tuple[Any, Any, Any, Any]:
        subject = record.get("subject") or {}
        assessment = record.get("assessment")
        variant = assessment.get("variant") if isinstance(assessment, Mapping) else None
        return (
            variant,
            subject.get("profile"),
            subject.get("reasoning_effort"),
            subject.get("sample_index"),
        )

    # Judgments of one subject keep the frozen dataset's
    # (sample_index, modified) order; a subject judged more than once
    # numbers its judgments so every run renders at its own location.
    judgment_totals = Counter(subject_key(record) for record in records)
    judgment_seen: Counter[tuple[Any, Any, Any, Any]] = Counter()

    scenario_id = scenario.scenario_id
    assessor_name, effort = assessment_cell_or_history(
        _assessment_category(scenario, name), f"{name}-assessment"
    )
    first_run_record: dict[str, Any] | None = None
    first_session_link: str | None = None
    for record in records:
        subject = record["subject"]
        sample_index = subject.get("sample_index")
        assessment = record.get("assessment")
        variant = assessment.get("variant") if isinstance(assessment, Mapping) else None
        stage = assessment.get("stage") if isinstance(assessment, Mapping) else None
        run_dir = _run_dir_for(
            discovery,
            record,
            (
                f"{group}:{scenario_id}:{variant}:"
                f"{subject.get('profile')}:"
                f"{subject.get('reasoning_effort')}:s{sample_index}"
            ),
        )
        judgment_seen[subject_key(record)] += 1
        ordinal = judgment_seen[subject_key(record)]
        numbered = judgment_totals[subject_key(record)] > 1
        variant_segment = f"{variant}/" if variant is not None else ""
        subject_cell = f"{subject.get('profile')}-{subject.get('reasoning_effort')}"
        sample_segment = f"s{sample_index}"
        if numbered:
            sample_segment = f"{sample_segment}/j{ordinal}"
        # Assessor runs sit inside the subject's cell subtree so the
        # judgment and its evidence stay one hop apart in both
        # directions.
        run_prefix = (
            f"scenarios/{scenario_id}/{subject_cell}/assessment/{name}"
            f"/{variant_segment}{sample_segment}".rstrip("/")
        )
        run_record, _ = _collect_run(
            (
                f"{name}-assessment-{subject_cell}-"
                f"{variant + '-' if variant is not None else ''}{sample_segment}"
            ),
            record,
            subdir=None,
            run_dir=run_dir,
            scenario=scenario,
            bundle=bundle,
            profile=assessor_name,
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
            system_message_key=f"{assessor_name}-assessor",
            config_key=f"{assessor_name}-assessor-{effort}",
            config_include_tasks=False,
        )
        if first_run_record is None:
            first_run_record = run_record
            first_session_link = run_prefix
        subject_dir = _subject_directory(name, scenario_id, subject, variant, stage)
        if subject_dir is not None:
            subject_notes.setdefault(subject_dir, []).extend(
                _subject_assessment_note(
                    name=name,
                    assessment=assessment,
                    assessor_session=run_prefix,
                    results_page=f"scenarios/{scenario_id}/assessment/{name}/results.md",
                    page=f"{subject_dir}/assessment.md",
                )
            )
    assert first_run_record is not None
    run_prefix = f"scenarios/{scenario_id}/assessment/{name}"
    results_page = f"{run_prefix}/results.md"
    files.append(
        CollectedFile(
            relative_path=results_page,
            content=_assessment_results_markdown(
                title=title,
                kind=name,
                records=records,
                target_path=f"scenarios/{scenario_id}/target.md",
                assessor={
                    "run_id": first_run_record["run_id"],
                    "model": first_run_record["model"],
                    "reasoning_effort": first_run_record["reasoning_effort"],
                    "config_path": first_run_record["config"],
                    "system_message": first_run_record["system_message"],
                },
                page=results_page,
                first_session_link=first_session_link,
                rubric_note=(
                    "- Rubric: fragmentation uses none/low/medium/high mapped"
                    " to 100/67/33/0; every other dimension uses"
                    " none/partial/present mapped to 100/50/0. An"
                    " assessment's overall success is the equal-weight"
                    " average of the six dimension scores."
                    if name == "task-creation"
                    else (
                        "- Rubric: the assessor scores handoff quality 0-100"
                        " from plan coverage, lost facts, invented scope,"
                        " rediscovery breadth, documentation and testing"
                        " boundaries, and whether the plan is self-contained."
                        if name == "handoff"
                        else (
                            (
                                "- Rubric: every requirement is graded"
                                " (conveyed/partial/missing; the self-containedness"
                                " and proportionality requirements use their own"
                                " scales); non-top grades require a named finding;"
                                " coverage is the share of top grades."
                                if name == "plan-content"
                                else (
                                    "- Rubric: five fidelity dimensions"
                                    " (complete/partial/poor;"
                                    " justified/not_applicable/fabricated;"
                                    " fits/forced/missing); every grade carries"
                                    " {where, quote, why} findings, non-top grades"
                                    " require them, and every response harvests"
                                    " mistakes."
                                    if name == "file-fidelity"
                                    else (
                                        "- Rubric: every top-level section is"
                                        " graded (readable/partial/unreadable)"
                                        " plus whole-file navigation"
                                        " (navigable/partial/confusing), anchored"
                                        " on measured structure facts; findings"
                                        " required for non-top grades; presentation"
                                        " mistakes harvested."
                                        if name == "file-readability"
                                        else "- Rubric: every dimension is a"
                                        " positive"
                                        " completeness grade (complete/partial/poor;"
                                        " justified/not_applicable/fabricated;"
                                        " fits/forced/"
                                        "missing). Grades carry evidence"
                                        " occurrences; no numeric score is derived."
                                    )
                                )
                            )
                        )
                    )
                ),
            ),
        )
    )


def _subject_assessment_note(
    *,
    name: str,
    assessment: Mapping[str, Any] | None,
    assessor_session: str,
    results_page: str,
    page: str,
) -> list[str]:
    """One judgment's summary rows for its subject's ``assessment.md``."""

    if not isinstance(assessment, Mapping):
        return []
    lines = [f"## {name} assessment"]
    variant = assessment.get("variant")
    stage = assessment.get("stage")
    scope = " · ".join(str(item) for item in (variant, stage) if item is not None)
    if scope:
        lines.append(f"- Scope: {scope}")
    if name == "task-quality":
        dimensions = assessment.get("dimensions") or {}
        for dim_name, dim in sorted(dimensions.items()):
            grade = dim.get("grade") if isinstance(dim, Mapping) else None
            lines.append(f"- {dim_name}: **{grade}**")
        task_kind = assessment.get("task_kind")
        if task_kind:
            lines.append(f"- Assessed task kind: {task_kind}")
    elif name == "handoff":
        score = assessment.get("handoff_quality_score")
        lines.append(f"- Handoff quality score: **{score}**")
        for field in ("plan_coverage", "broad_rediscovery", "task_self_contained"):
            value = assessment.get(field)
            if value is not None:
                lines.append(f"- {field}: {value}")
    elif name == "plan-content":
        coverage = assessment.get("coverage")
        if coverage is not None:
            lines.append(f"- Top-grade coverage: **{coverage:.0%}**")
        requirements = assessment.get("requirements") or {}
        for requirement_id, entry in sorted(requirements.items()):
            if not isinstance(entry, Mapping):
                continue
            lines.append(f"- {requirement_id}: **{entry.get('grade')}**")
        missed = assessment.get("missed_requirements") or []
        for item in missed:
            lines.append(f"- Missed requirement: {item}")
    elif name == "file-fidelity":
        dimensions = assessment.get("dimensions") or {}
        for dim_name, dim in sorted(dimensions.items()):
            if not isinstance(dim, Mapping):
                continue
            findings = dim.get("findings") or []
            lines.append(
                f"- {dim_name}: **{dim.get('grade')}**" f" ({len(findings)} findings)"
            )
        mistakes = assessment.get("mistakes") or []
        lines.append(f"- Mistakes harvested: {len(mistakes)}")
    elif name == "file-readability":
        sections = assessment.get("sections") or {}
        for title, entry in sorted(sections.items()):
            if not isinstance(entry, Mapping):
                continue
            lines.append(f"- {title}: **{entry.get('grade')}**")
        navigation = assessment.get("navigation") or {}
        if isinstance(navigation, Mapping):
            lines.append(f"- Navigation: **{navigation.get('grade')}**")
        mistakes = assessment.get("mistakes") or []
        lines.append(f"- Mistakes harvested: {len(mistakes)}")
    else:
        overall = assessment.get("overall_success_percentage")
        metrics = assessment.get("quality_metrics") or {}
        if overall is not None:
            lines.append(f"- Overall success: **{overall:g}%**")
        for dim_name, metric in sorted(metrics.items()):
            status = metric.get("status") if isinstance(metric, Mapping) else None
            lines.append(f"- {dim_name}: {status}")
    summary = assessment.get("summary")
    if isinstance(summary, str) and summary.strip():
        lines.append(f"- Summary: {summary}")
    lines.append(
        "- Assessor session:"
        f" [`session.md`]({_link(f'{assessor_session}/session.md', page)})"
    )
    lines.append(f"- Full results: [`results.md`]({_link(results_page, page)})")
    return lines


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
    bundle: Path,
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
    assessor_name, effort = assessment_cell("handoff", "task-creation-assessment")
    run_record, _ = _collect_run(
        f"{name}-assessment",
        record,
        subdir=None,
        run_dir=run_dir,
        scenario=scenario,
        bundle=bundle,
        profile=assessor_name,
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
        system_message_key=f"{assessor_name}-assessor",
        config_key=f"{assessor_name}-assessor-{effort}",
        config_include_tasks=False,
    )
    results_page = f"{run_prefix}/results.md"
    files.append(
        CollectedFile(
            relative_path=results_page,
            content=_assessment_results_markdown(
                title=title,
                kind=name,
                records=[record],
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
                    else (
                        "- Rubric: the assessor scores handoff quality 0-100"
                        " from plan coverage, lost facts, invented scope,"
                        " rediscovery breadth, documentation and testing"
                        " boundaries, and whether the plan is self-contained."
                        if name == "handoff"
                        else (
                            (
                                "- Rubric: every requirement is graded"
                                " (conveyed/partial/missing; the self-containedness"
                                " and proportionality requirements use their own"
                                " scales); non-top grades require a named finding;"
                                " coverage is the share of top grades."
                                if name == "plan-content"
                                else (
                                    "- Rubric: five fidelity dimensions"
                                    " (complete/partial/poor;"
                                    " justified/not_applicable/fabricated;"
                                    " fits/forced/missing); every grade carries"
                                    " {where, quote, why} findings, non-top grades"
                                    " require them, and every response harvests"
                                    " mistakes."
                                    if name == "file-fidelity"
                                    else (
                                        "- Rubric: every top-level section is"
                                        " graded (readable/partial/unreadable)"
                                        " plus whole-file navigation"
                                        " (navigable/partial/confusing), anchored"
                                        " on measured structure facts; findings"
                                        " required for non-top grades; presentation"
                                        " mistakes harvested."
                                        if name == "file-readability"
                                        else "- Rubric: every dimension is a"
                                        " positive"
                                        " completeness grade (complete/partial/poor;"
                                        " justified/not_applicable/fabricated;"
                                        " fits/forced/"
                                        "missing). Grades carry evidence"
                                        " occurrences; no numeric score is derived."
                                    )
                                )
                            )
                        )
                    )
                ),
            ),
        )
    )


def _assessment_results_markdown(
    *,
    title: str,
    kind: str,
    records: Sequence[Mapping[str, Any]],
    target_path: str,
    assessor: Mapping[str, Any],
    page: str,
    rubric_note: str,
    first_session_link: str | None = None,
) -> str:
    system_message = assessor.get("system_message") or {}
    config_link = _link(assessor["config_path"], page)
    transcript_link = (
        f"[session.md]({_link(f'{first_session_link}/session.md', page)})"
        if first_session_link
        else "[session.md](session.md)"
    )
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
            f"- First judgment's full transcript: {transcript_link} — includes"
            " the exact prompt and the raw response; every judgment's"
            " transcript lives beside its subject"
            f" (`<cell>/assessment/{kind}/…`)",
            f"- Reviewed target: [{target_path.split('/')[-2]}]"
            f"({_link(target_path, page)})",
            rubric_note,
            "",
            "## Judgments",
            "",
        ]
    )
    for record in records:
        for profile, effort, sample_index, assessment in _iter_judgments(record):
            # The judgment schema follows the assessment kind, not field
            # presence: task-creation responses legitimately carry a
            # handoff_quality_score field because the prompt's JSON shape
            # includes it.
            if kind == "handoff":
                lines.extend(
                    _handoff_judgment_markdown(
                        assessment,
                        profile=profile,
                        effort=effort,
                        sample_index=sample_index,
                    )
                )
            elif kind == "task-quality":
                lines.extend(
                    _quality_judgment_markdown(
                        assessment,
                        profile=profile,
                        effort=effort,
                        sample_index=sample_index,
                    )
                )
            elif kind == "plan-content":
                lines.extend(
                    _plan_content_judgment_markdown(
                        assessment,
                        profile=profile,
                        effort=effort,
                        sample_index=sample_index,
                    )
                )
            elif kind == "file-fidelity":
                lines.extend(
                    _file_fidelity_judgment_markdown(
                        assessment,
                        profile=profile,
                        effort=effort,
                        sample_index=sample_index,
                    )
                )
            elif kind == "file-readability":
                lines.extend(
                    _file_readability_judgment_markdown(
                        assessment,
                        profile=profile,
                        effort=effort,
                        sample_index=sample_index,
                    )
                )
            else:
                lines.extend(
                    _judgment_markdown(
                        assessment,
                        profile=profile,
                        effort=effort,
                        sample_index=sample_index,
                    )
                )
            lines.append("")
        invalid = record.get("invalid_producer_records") or []
        if invalid:
            lines.extend(["## Excluded records", ""])
            for item in invalid:
                producer = item.get("producer") or {}
                reasons = "; ".join(str(r) for r in item.get("invalid_reasons", ()))
                lines.append(
                    f"- {producer.get('profile')}"
                    f" {producer.get('reasoning_effort')}: {reasons}"
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
    plan_target = target.get("plan_target") or {}
    required = plan_target.get("required_content") or []
    if required:
        lines.extend(["", "**Plan content requirements**", ""])
        for item in required:
            derived = item.get("derived_from") or []
            suffix = (
                f" (from {', '.join(str(source) for source in derived)})"
                if derived
                else ""
            )
            lines.append(f"- {item.get('id')}: {item.get('content')}{suffix}")
    return lines


def _assessment_category(scenario, name: str) -> str:
    """The category whose configuration declares an assessment stage."""

    return scenario.category


def _quality_judgment_markdown(
    assessment: Mapping[str, Any],
    *,
    profile: Any = None,
    effort: Any = None,
    sample_index: int | None = None,
) -> list[str]:
    heading = f"### {profile} · {effort} — task kind {assessment.get('task_kind')}"
    if sample_index is not None:
        heading += f" (sample {sample_index})"
    lines = [heading, "", "| Dimension | Grade | Occurrences |", "|---|---|---:|"]
    dimensions = assessment.get("dimensions") or {}
    for dimension, grades in QUALITY_GRADES.items():
        item = dimensions.get(dimension) or {}
        occurrences = item.get("occurrences") or []
        lines.append(f"| {dimension} | {item.get('grade')} | {len(occurrences)} |")
    lines.extend(["", assessment.get("summary") or "", ""])
    for dimension, grades in QUALITY_GRADES.items():
        item = dimensions.get(dimension) or {}
        for occurrence in item.get("occurrences") or []:
            description = occurrence.get("description")
            if description:
                lines.append(f"- {dimension}: {description}")
    return lines


def _plan_content_judgment_markdown(
    assessment: Mapping[str, Any],
    *,
    profile: Any = None,
    effort: Any = None,
    sample_index: int | None = None,
) -> list[str]:
    heading = (
        f"### {profile} · {effort} — {assessment.get('variant')}"
        f" ({assessment.get('stage')})"
    )
    if sample_index is not None:
        heading += f" (sample {sample_index})"
    coverage = assessment.get("coverage")
    coverage_text = "—" if coverage is None else f"{coverage:.0%}"
    lines = [
        heading,
        "",
        f"Top-grade coverage: {coverage_text}",
        "",
        "| Requirement | Grade | Finding |",
        "|---|---|---|",
    ]
    for requirement_id, entry in sorted((assessment.get("requirements") or {}).items()):
        if not isinstance(entry, Mapping):
            continue
        finding = str(entry.get("finding") or "").replace("|", "\\|")
        finding = finding.replace("`", "'")
        lines.append(f"| {requirement_id} | {entry.get('grade')} | {finding} |")
    missed = assessment.get("missed_requirements") or []
    if missed:
        lines.extend(["", "**Content the requirement layers missed**", ""])
        lines.extend(f"- {item}" for item in missed)
    summary = assessment.get("summary")
    if isinstance(summary, str) and summary.strip():
        lines.extend(["", summary, ""])
    return lines


def _plain_finding_text(value: Any) -> str:
    """A model-written prose field rendered as safe plain text."""

    return " ".join(str(value or "").replace("`", "'").split())


def _inline_snippet(value: Any, limit: int = 80) -> str:
    """A model-written string as safe inline code.

    Backticks and line breaks would break the code span, so they are
    removed; the snippet stays a verbatim prefix of the finding.
    """

    cleaned = str(value or "").replace("`", "'").split()
    joined = " ".join(cleaned)
    return joined[:limit]


def _file_fidelity_judgment_markdown(
    assessment: Mapping[str, Any],
    *,
    profile: Any = None,
    effort: Any = None,
    sample_index: int | None = None,
) -> list[str]:
    heading = f"### {profile} · {effort}"
    if sample_index is not None:
        heading += f" (sample {sample_index})"
    lines = [
        heading,
        "",
        "| Dimension | Grade | Findings |",
        "|---|---|---:|",
    ]
    dimensions = assessment.get("dimensions") or {}
    for dimension in (
        "plan_design_completeness",
        "durable_context_preservation",
        "section_appropriateness",
        "plan_justification",
        "task_kind_fit",
    ):
        item = dimensions.get(dimension) or {}
        findings = item.get("findings") or []
        lines.append(f"| {dimension} | {item.get('grade')} | {len(findings)} |")
    lines.extend(["", "**Findings**", ""])
    for dimension, item in sorted((dimensions or {}).items()):
        if not isinstance(item, Mapping):
            continue
        for finding in item.get("findings") or []:
            if isinstance(finding, Mapping):
                lines.append(
                    f"- {dimension} — {_inline_snippet(finding.get('where'))}:"
                    f" {_plain_finding_text(finding.get('why'))}"
                    f" (`{_inline_snippet(finding.get('quote'))}`)"
                )
    mistakes = assessment.get("mistakes") or []
    if mistakes:
        lines.extend(["", "**Mistakes**", ""])
        for mistake in mistakes:
            if isinstance(mistake, Mapping):
                lines.append(
                    f"- {_inline_snippet(mistake.get('where'))}:"
                    f" {_plain_finding_text(mistake.get('why'))}"
                    f" (`{_inline_snippet(mistake.get('quote'))}`)"
                )
    summary = assessment.get("summary")
    if isinstance(summary, str) and summary.strip():
        lines.extend(["", summary, ""])
    return lines


def _file_readability_judgment_markdown(
    assessment: Mapping[str, Any],
    *,
    profile: Any = None,
    effort: Any = None,
    sample_index: int | None = None,
) -> list[str]:
    heading = f"### {profile} · {effort}"
    if sample_index is not None:
        heading += f" (sample {sample_index})"
    lines = [
        heading,
        "",
        "| Section | Grade | Findings |",
        "|---|---|---:|",
    ]
    sections = assessment.get("sections") or {}
    for title, entry in sections.items():
        if not isinstance(entry, Mapping):
            continue
        findings = entry.get("findings") or []
        lines.append(f"| {title} | {entry.get('grade')} | {len(findings)} |")
    navigation = assessment.get("navigation") or {}
    if isinstance(navigation, Mapping):
        nav_findings = navigation.get("findings") or []
        lines.append(
            f"| _navigation_ | {navigation.get('grade')} | {len(nav_findings)} |"
        )
    lines.extend(["", "**Findings**", ""])
    for title, entry in sorted(sections.items()):
        if not isinstance(entry, Mapping):
            continue
        for finding in entry.get("findings") or []:
            if isinstance(finding, Mapping):
                lines.append(
                    f"- {title} — {_inline_snippet(finding.get('where'))}:"
                    f" {_plain_finding_text(finding.get('why'))}"
                    f" (`{_inline_snippet(finding.get('quote'))}`)"
                )
    if isinstance(navigation, Mapping):
        for finding in navigation.get("findings") or []:
            if isinstance(finding, Mapping):
                lines.append(
                    f"- navigation — {_inline_snippet(finding.get('where'))}:"
                    f" {_plain_finding_text(finding.get('why'))}"
                    f" (`{_inline_snippet(finding.get('quote'))}`)"
                )
    mistakes = assessment.get("mistakes") or []
    if mistakes:
        lines.extend(["", "**Mistakes**", ""])
        for mistake in mistakes:
            if isinstance(mistake, Mapping):
                lines.append(
                    f"- {_inline_snippet(mistake.get('where'))}:"
                    f" {_plain_finding_text(mistake.get('why'))}"
                    f" (`{_inline_snippet(mistake.get('quote'))}`)"
                )
    summary = assessment.get("summary")
    if isinstance(summary, str) and summary.strip():
        lines.extend(["", summary, ""])
    return lines


def _judgment_markdown(
    assessment: Mapping[str, Any],
    *,
    profile: Any = None,
    effort: Any = None,
    sample_index: int | None = None,
) -> list[str]:
    producer = assessment.get("producer") or {}
    metrics = assessment.get("quality_metrics") or {}
    heading = (
        f"### {profile or producer.get('profile')}"
        f" · {effort or producer.get('reasoning_effort')}"
        f" — overall {assessment.get('overall_success_percentage')}"
    )
    if sample_index is not None:
        heading += f" (sample {sample_index})"
    lines = [
        heading,
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
            lines.append(f"- **{dimension}**: {occurrence.get('description')}{suffix}")
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


def _handoff_judgment_markdown(
    assessment: Mapping[str, Any],
    *,
    profile: Any = None,
    effort: Any = None,
    sample_index: int | None = None,
) -> list[str]:
    producer = assessment.get("producer") or {}
    heading = (
        f"### {profile or producer.get('profile')}"
        f" · {effort or producer.get('reasoning_effort')}"
        f" ({assessment.get('variant')}, {assessment.get('stage')})"
        f" — handoff quality {assessment.get('handoff_quality_score')}"
    )
    if sample_index is not None:
        heading += f" (sample {sample_index})"
    lines = [
        heading,
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


def _handoff_stage_dir(*, variant: Any, stage: Any) -> str | None:
    """Map one handoff judgment to the stage directory it is about."""

    if stage == "same-agent":
        return "continuation"
    return {
        "retain": "plan-retain",
        "omit": "plan-omit",
        "incomplete": "control",
        "generated-task": "generated-plan",
        "generated-file": "generated-plan",
    }.get(variant)


def _iter_judgments(
    record: Mapping[str, Any],
) -> Iterable[tuple[Any, Any, int | None, Mapping[str, Any]]]:
    """Yield (profile, effort, sample_index, judgment) for both schemas.

    Historical batched records carry a list of judgments, each echoing
    its producer; per-subject records carry one judgment with the
    subject mapping held by the record.
    """

    assessment = record.get("assessment")
    if not isinstance(assessment, Mapping):
        return
    batch = assessment.get("assessments")
    if isinstance(batch, list):
        for judgment in batch:
            if not isinstance(judgment, Mapping):
                continue
            producer = judgment.get("producer") or {}
            yield (
                producer.get("profile"),
                producer.get("reasoning_effort"),
                None,
                judgment,
            )
        return
    subject = record.get("subject") or {}
    yield (
        subject.get("profile"),
        subject.get("reasoning_effort"),
        subject.get("sample_index"),
        assessment,
    )


def _assessment_details(frozen: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Project per-assessment judgment details for the matrix views.

    The cohort aggregates explain *which* assessments produced them; these
    rows carry the individual judgment values, the path of the readable
    rendering, and the run or stage directory each judgment is about.
    """

    task_creation: list[dict[str, Any]] = []
    for record in frozen.get("semantic_records", ()):
        scenario_id = record.get("scenario_id")
        for profile, effort, sample_index, assessment in _iter_judgments(record):
            metrics = assessment.get("quality_metrics") or {}
            cell = f"{profile}-{effort}"
            task_creation.append(
                {
                    "kind": "task-creation",
                    "scenario_id": scenario_id,
                    "profile": profile,
                    "reasoning_effort": effort,
                    "sample_index": sample_index,
                    "overall_success_percentage": assessment.get(
                        "overall_success_percentage"
                    ),
                    "dimensions": {
                        name: {
                            "status": (metrics.get(name) or {}).get("status"),
                            "score": (metrics.get(name) or {}).get("score"),
                        }
                        for name in QUALITY_DIMENSIONS
                    },
                    "run_path": (
                        f"scenarios/{scenario_id}/{cell}"
                        f"/s{0 if sample_index is None else sample_index}"
                    ),
                    "results_path": (
                        f"scenarios/{scenario_id}"
                        "/assessment/task-creation/results.md"
                    ),
                }
            )
    task_quality: list[dict[str, Any]] = []
    for record in frozen.get("quality_records", ()):
        scenario_id = record.get("scenario_id")
        for profile, effort, sample_index, assessment in _iter_judgments(record):
            dimensions = assessment.get("dimensions") or {}
            cell = f"{profile}-{effort}"
            task_quality.append(
                {
                    "kind": "task-quality",
                    "scenario_id": scenario_id,
                    "profile": profile,
                    "reasoning_effort": effort,
                    "sample_index": sample_index,
                    "task_kind": assessment.get("task_kind"),
                    "dimensions": {
                        name: (dimensions.get(name) or {}).get("grade")
                        for name in QUALITY_GRADES
                    },
                    "run_path": (
                        f"scenarios/{scenario_id}/{cell}"
                        f"/s{0 if sample_index is None else sample_index}"
                    ),
                    "results_path": (
                        f"scenarios/{scenario_id}" "/assessment/task-quality/results.md"
                    ),
                }
            )
    plan_content: list[dict[str, Any]] = []
    for record in frozen.get("plan_content_records", ()):
        scenario_id = record.get("scenario_id")
        subject = record.get("subject") or {}
        assessment = record.get("assessment") or {}
        cell = f"{subject.get('profile')}-{subject.get('reasoning_effort')}"
        sample_index = subject.get("sample_index")
        stage_dir = _handoff_stage_dir(
            variant=assessment.get("variant"), stage=assessment.get("stage")
        )
        sample_dir = f"s{0 if sample_index is None else sample_index}"
        run_path = (
            f"scenarios/{scenario_id}/{cell}/{stage_dir}/{sample_dir}"
            if stage_dir
            else f"scenarios/{scenario_id}/{cell}/{sample_dir}"
        )
        plan_content.append(
            {
                "kind": "plan-content",
                "scenario_id": scenario_id,
                "variant": assessment.get("variant"),
                "stage": assessment.get("stage"),
                "profile": subject.get("profile"),
                "reasoning_effort": subject.get("reasoning_effort"),
                "sample_index": sample_index,
                "coverage": assessment.get("coverage"),
                "requirements": {
                    requirement_id: (entry or {}).get("grade")
                    for requirement_id, entry in (
                        assessment.get("requirements") or {}
                    ).items()
                },
                "missed_requirement_count": len(
                    assessment.get("missed_requirements") or ()
                ),
                "run_path": run_path,
                "results_path": (
                    f"scenarios/{scenario_id}/assessment/plan-content/results.md"
                ),
            }
        )
    file_fidelity: list[dict[str, Any]] = []
    for record in frozen.get("file_fidelity_records", ()):
        scenario_id = record.get("scenario_id")
        subject = record.get("subject") or {}
        assessment = record.get("assessment") or {}
        cell = f"{subject.get('profile')}-{subject.get('reasoning_effort')}"
        sample_index = subject.get("sample_index")
        file_fidelity.append(
            {
                "kind": "file-fidelity",
                "scenario_id": scenario_id,
                "profile": subject.get("profile"),
                "reasoning_effort": subject.get("reasoning_effort"),
                "sample_index": sample_index,
                "dimensions": {
                    name: (entry or {}).get("grade")
                    for name, entry in (assessment.get("dimensions") or {}).items()
                },
                "mistake_count": len(assessment.get("mistakes") or ()),
                "run_path": (
                    f"scenarios/{scenario_id}/{cell}"
                    f"/s{0 if sample_index is None else sample_index}"
                ),
                "results_path": (
                    f"scenarios/{scenario_id}/assessment/file-fidelity/results.md"
                ),
            }
        )
    file_readability: list[dict[str, Any]] = []
    for record in frozen.get("file_readability_records", ()):
        scenario_id = record.get("scenario_id")
        subject = record.get("subject") or {}
        assessment = record.get("assessment") or {}
        cell = f"{subject.get('profile')}-{subject.get('reasoning_effort')}"
        sample_index = subject.get("sample_index")
        file_readability.append(
            {
                "kind": "file-readability",
                "scenario_id": scenario_id,
                "profile": subject.get("profile"),
                "reasoning_effort": subject.get("reasoning_effort"),
                "sample_index": sample_index,
                "sections": {
                    title: (entry or {}).get("grade")
                    for title, entry in (assessment.get("sections") or {}).items()
                },
                "navigation": (assessment.get("navigation") or {}).get("grade"),
                "mistake_count": len(assessment.get("mistakes") or ()),
                "run_path": (
                    f"scenarios/{scenario_id}/{cell}"
                    f"/s{0 if sample_index is None else sample_index}"
                ),
                "results_path": (
                    f"scenarios/{scenario_id}/assessment/file-readability/results.md"
                ),
            }
        )
    handoff: list[dict[str, Any]] = []
    for record in frozen.get("handoff_semantic_records", ()):
        scenario_id = record.get("scenario_id")
        for profile, effort, sample_index, assessment in _iter_judgments(record):
            cell = f"{profile}-{effort}"
            stage_dir = _handoff_stage_dir(
                variant=assessment.get("variant"), stage=assessment.get("stage")
            )
            sample_dir = f"s{0 if sample_index is None else sample_index}"
            run_path = (
                f"scenarios/{scenario_id}/{cell}/{stage_dir}/{sample_dir}"
                if stage_dir
                else f"scenarios/{scenario_id}/{cell}/{sample_dir}"
            )
            handoff.append(
                {
                    "kind": "handoff",
                    "scenario_id": scenario_id,
                    "variant": assessment.get("variant"),
                    "stage": assessment.get("stage"),
                    "profile": profile,
                    "reasoning_effort": effort,
                    "sample_index": sample_index,
                    "handoff_quality_score": assessment.get("handoff_quality_score"),
                    "plan_coverage": assessment.get("plan_coverage"),
                    "task_self_contained": assessment.get("task_self_contained"),
                    "broad_rediscovery": assessment.get("broad_rediscovery"),
                    "documentation_boundary": assessment.get("documentation_boundary"),
                    "testing_boundary": assessment.get("testing_boundary"),
                    "run_path": run_path,
                    "results_path": (
                        f"scenarios/{scenario_id}/assessment/handoff/results.md"
                    ),
                }
            )
    task_creation.sort(
        key=lambda row: (
            row["scenario_id"] or "",
            row["profile"] or "",
            row["reasoning_effort"] or "",
        )
    )
    handoff.sort(
        key=lambda row: (
            row["scenario_id"] or "",
            row["variant"] or "",
            row["stage"] or "",
            row["profile"] or "",
            row["reasoning_effort"] or "",
        )
    )
    plan_content.sort(
        key=lambda row: (
            row["scenario_id"] or "",
            row["variant"] or "",
            row["stage"] or "",
            row["profile"] or "",
            row["reasoning_effort"] or "",
        )
    )
    for rows in (file_fidelity, file_readability):
        rows.sort(
            key=lambda row: (
                row["scenario_id"] or "",
                row["profile"] or "",
                row["reasoning_effort"] or "",
            )
        )
    return (
        task_creation
        + handoff
        + task_quality
        + plan_content
        + file_fidelity
        + file_readability
    )


def _build_index_views(records: PackageRecords) -> list[GeneratedView]:
    aggregate = records.collected_json("aggregate.json")
    identity = dict(records.identity)
    lines = [
        f"# {identity.get('label', 'Task-guidance evaluation')} result package",
        "",
        f"- Dataset: `{identity.get('dataset_id')}`",
    ]
    selection = _selection_fields(aggregate)
    if "attempts" in selection:
        lines.extend(
            [
                f"- Producer attempt: `{aggregate['attempts']['producer']}`",
                f"- Handoff attempt: `{aggregate['attempts']['handoff']}`",
                f"- Semantic attempt: `{aggregate['attempts']['semantic']}`",
            ]
        )
    else:
        lines.append(
            "- Run labels: " + ", ".join(f"`{item}`" for item in selection["labels"])
        )
    lines.extend(
        [
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
    )
    scenario_ids = sorted(
        {
            path.split("/")[1]
            for path in records.collected_paths
            if path.startswith("scenarios/")
        }
    )
    for scenario_id in scenario_ids:
        results = (
            " · [results](scenarios/{scenario_id}/results.md)".format(
                scenario_id=scenario_id
            )
            if f"scenarios/{scenario_id}/results.md" in records.collected_paths
            else ""
        )
        lines.append(f"- [`{scenario_id}`](scenarios/{scenario_id}/index.md){results}")
    lines.extend(
        [
            "",
            "## Known limitations",
            "",
            "- Historical GLM runs saved no provider usage metadata; their"
            " usage and estimated cost remain unknown.",
            "- GPT same-agent continuation runs recorded no compiled-message"
            " hash; their delivered instructions are inherited from the"
            " producer run's verified message instead of reconstructed"
            " independently.",
            "- Session transcripts omit full tool-result content and"
            " encrypted reasoning; concise failure excerpts are retained.",
        ]
    )
    return [
        GeneratedView(relative_path="index.md", content="\n".join(lines) + "\n"),
        GeneratedView(
            relative_path="matrix.md",
            content=_matrix_markdown(records, aggregate),
        ),
    ]


def _matrix_markdown(records: PackageRecords, aggregate: Mapping[str, Any]) -> str:
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
    summary = render_summary(
        {
            "label": aggregate["label"],
            "labels": aggregate.get("labels"),
            "attempts": aggregate.get("attempts"),
            "status": aggregate["status"],
            "semantic_quality": aggregate["semantic_quality"],
            "producer_records": groups["producer_records"],
            "handoff_records": groups["handoff_records"],
            "same_agent_records": groups["same_agent_records"],
            "provider_blocker_records": aggregate.get("provider_blocker_records", []),
        }
    )
    sections = [summary.rstrip()]
    sections.extend(_matrix_detail_sections(aggregate))
    sections.extend(_per_scenario_section(records))
    return "\n\n".join(sections) + "\n"


def _matrix_detail_sections(aggregate: Mapping[str, Any]) -> list[str]:
    """Explain every cohort row: one detail row per individual judgment."""

    details = aggregate.get("assessment_details", ())
    task_rows = [row for row in details if row.get("kind") == "task-creation"]
    handoff_rows = [row for row in details if row.get("kind") == "handoff"]
    has_samples = any(
        row.get("sample_index") is not None for row in (*task_rows, *handoff_rows)
    )
    sample_header = " Sample |" if has_samples else ""
    sample_rule = "---|" if has_samples else ""
    sections: list[str] = []
    if task_rows:
        header = (
            "| Scenario | Producer | Overall | Fragmentation | Phase-only |"
            " Layer split | Evidence reownership | Dependency safety |"
            " Production crossing | Run | Judgment |" + sample_header
        )
        lines = [
            "## Task-creation semantic detail",
            "",
            "One row per judgment. Each cohort row above is the average of"
            " its rows here; dimension cells read `status (score)`.",
            "",
            header,
            "|---|---|---:|---|---|---|---|---|---|---|---|" + sample_rule,
        ]
        for row in task_rows:
            producer = f"{row.get('profile')} {row.get('reasoning_effort')}".rstrip()
            dimensions = " | ".join(
                _dimension_cell(row.get("dimensions", {}).get(name))
                for name in QUALITY_DIMENSIONS
            )
            overall = row.get("overall_success_percentage")
            overall_text = "—" if overall is None else f"{overall:g}"
            run_path = row.get("run_path") or ""
            run_link = (
                f"[{run_path.rstrip('/').rsplit('/', 1)[-1]}]"
                f"({_link(run_path, 'matrix.md')})"
                if run_path
                else "—"
            )
            sample_cell = f" s{row.get('sample_index')} |" if has_samples else ""
            lines.append(
                f"| `{row.get('scenario_id')}` | {producer} | {overall_text}"
                f" | {dimensions} | {run_link} |"
                f" [results]({_link(row['results_path'], 'matrix.md')}) |" + sample_cell
            )
        sections.append("\n".join(lines))
    if handoff_rows:
        lines = [
            "## Handoff semantic detail",
            "",
            "One row per judgment, across plan variants and stages.",
            "",
            "| Scenario | Variant | Stage | Producer | Handoff quality |"
            " Plan coverage | Self-contained | Broad rediscovery |"
            " Documentation | Testing | Run | Judgment |" + sample_header,
            "|---|---|---|---|---:|---|---|---|---|---|---|---|" + sample_rule,
        ]
        for row in handoff_rows:
            producer = f"{row.get('profile')} {row.get('reasoning_effort')}".rstrip()
            score = row.get("handoff_quality_score")
            score_text = "—" if score is None else f"{score}"
            run_path = row.get("run_path") or ""
            run_link = (
                f"[{run_path.rstrip('/').rsplit('/', 1)[-1]}]"
                f"({_link(run_path, 'matrix.md')})"
                if run_path
                else "—"
            )
            sample_cell = f" s{row.get('sample_index')} |" if has_samples else ""
            lines.append(
                f"| `{row.get('scenario_id')}` | {row.get('variant')}"
                f" | {row.get('stage')} | {producer} | {score_text}"
                f" | {row.get('plan_coverage')}"
                f" | {_yes_no(row.get('task_self_contained'))}"
                f" | {_yes_no(row.get('broad_rediscovery'))}"
                f" | {row.get('documentation_boundary')}"
                f" | {row.get('testing_boundary')} | {run_link} |"
                f" [results]({_link(row['results_path'], 'matrix.md')}) |" + sample_cell
            )
        sections.append("\n".join(lines))
    quality_rows = [row for row in details if row.get("kind") == "task-quality"]
    if quality_rows:
        sections.append(_quality_cohort_section(quality_rows))
        sections.append(_quality_detail_section(quality_rows))
    plan_content_rows = [row for row in details if row.get("kind") == "plan-content"]
    if plan_content_rows:
        sections.append(_plan_content_cohort_section(plan_content_rows))
        sections.append(_plan_content_detail_section(plan_content_rows))
    fidelity_rows = [row for row in details if row.get("kind") == "file-fidelity"]
    if fidelity_rows:
        sections.append(_file_fidelity_cohort_section(fidelity_rows))
        sections.append(_file_fidelity_detail_section(fidelity_rows))
    readability_rows = [row for row in details if row.get("kind") == "file-readability"]
    if readability_rows:
        sections.append(_file_readability_cohort_section(readability_rows))
        sections.append(_file_readability_detail_section(readability_rows))
    return sections


def _plan_content_cohort_section(rows: Sequence[Mapping[str, Any]]) -> str:
    """Per-requirement top-grade shares by plan variant cohort.

    A requirement whose column shows the same value in every cohort —
    or 100% everywhere — is a zero-variance candidate: either every
    plan genuinely conveys it or the rubric cannot distinguish quality
    through it. The judge-validation gate resolves which.
    """

    variants = [
        variant
        for variant in (
            "retain",
            "omit",
            "incomplete",
            "generated-task",
            "generated-file",
        )
        if any(row.get("variant") == variant for row in rows)
    ]
    requirement_ids = sorted(
        {
            requirement_id
            for row in rows
            for requirement_id in (row.get("requirements") or {})
        }
    )

    def _top_share(cohort: Sequence[Mapping[str, Any]], requirement_id: str) -> str:
        grades = [(row.get("requirements") or {}).get(requirement_id) for row in cohort]
        graded = [grade for grade in grades if grade is not None]
        if not graded:
            return "—"
        return f"{100 * sum(1 for grade in graded if grade in ('conveyed', 'self-contained', 'proportionate')) / len(graded):.0f}%"

    def _mean_coverage(cohort: Sequence[Mapping[str, Any]]) -> str:
        coverages = [
            row.get("coverage") for row in cohort if row.get("coverage") is not None
        ]
        return f"{100 * sum(coverages) / len(coverages):.0f}%" if coverages else "—"

    lines = [
        "## Presented-plan content",
        "",
        "Top-grade share per requirement, by the variant of the task file"
        " the presenting agent worked from; `n` is the judged plans.",
        "",
        "| Requirement |" + "".join(f" {variant} |" for variant in variants),
        "|---|" + "---:|" * len(variants),
    ]
    for requirement_id in requirement_ids:
        cells = "".join(
            f" {_top_share([row for row in rows if row.get('variant') == variant], requirement_id)} |"
            for variant in variants
        )
        lines.append(f"| {requirement_id} |{cells}")
    lines.extend(
        [
            "",
            "| Cohort | n | Mean coverage |",
            "|---|---:|---:|",
        ]
    )
    for variant in [*variants, "all"]:
        cohort = [row for row in rows if row.get("variant") == variant]
        label = "All" if variant == "all" else variant
        lines.append(f"| {label} | {len(cohort)} | {_mean_coverage(cohort)} |")
    return "\n".join(lines)


def _plan_content_detail_section(rows: Sequence[Mapping[str, Any]]) -> str:
    """One row per plan-content judgment, linked to its subject."""

    has_samples = any(row.get("sample_index") is not None for row in rows)
    sample_header = " Sample |" if has_samples else ""
    sample_rule = "---|" if has_samples else ""
    lines = [
        "## Presented-plan content detail",
        "",
        "One row per judgment; the subject link opens the judged plan's"
        " grade summary.",
        "",
        "| Scenario | Variant | Producer | Coverage | Non-top requirements |"
        " Missed | Subject | Judgment |" + sample_header,
        "|---|---|---|---:|---|---:|---|---|" + sample_rule,
    ]
    for row in rows:
        producer = f"{row.get('profile')} {row.get('reasoning_effort')}".rstrip()
        coverage = row.get("coverage")
        coverage_text = "—" if coverage is None else f"{coverage:.0%}"
        requirements = row.get("requirements") or {}
        non_top = sorted(
            requirement_id
            for requirement_id, grade in requirements.items()
            if grade is not None
            and grade not in ("conveyed", "self-contained", "proportionate")
        )
        non_top_text = ", ".join(non_top) if non_top else "—"
        missed = row.get("missed_requirement_count")
        missed_text = "—" if missed is None else str(missed)
        run_path = row.get("run_path") or ""
        subject_link = (
            f"[{run_path.rstrip('/').rsplit('/', 1)[-1]}]"
            f"({_link(run_path + '/assessment.md', 'matrix.md')})"
            if run_path
            else "—"
        )
        sample_cell = f" s{row.get('sample_index')} |" if has_samples else ""
        lines.append(
            f"| `{row.get('scenario_id')}` | {row.get('variant')} | {producer}"
            f" | {coverage_text} | {non_top_text} | {missed_text}"
            f" | {subject_link}"
            f" | [results]({_link(row['results_path'], 'matrix.md')}) |" + sample_cell
        )
    return "\n".join(lines)


def _FILE_FIDELITY_DIMENSION_LABELS() -> dict[str, str]:
    return {
        "plan_design_completeness": "design",
        "durable_context_preservation": "context",
        "section_appropriateness": "placement",
        "plan_justification": "justification",
        "task_kind_fit": "kind-fit",
    }


def _file_fidelity_cohort_section(rows: Sequence[Mapping[str, Any]]) -> str:
    """Cohort shares of top fidelity grades per dimension."""

    labels = _FILE_FIDELITY_DIMENSION_LABELS()
    cohorts: dict[str, list[Mapping[str, Any]]] = {"All": list(rows)}
    for row in rows:
        model = str(row.get("profile") or "").upper()
        if model:
            cohorts.setdefault(model, []).append(row)
        cohorts.setdefault(
            f"{row.get('profile')} {row.get('reasoning_effort')}".rstrip(), []
        ).append(row)
    model_names = sorted(name for name in cohorts if name in {"GLM", "GPT"})
    ordered = (
        ["All"]
        + model_names
        + sorted(key for key in cohorts if key != "All" and key not in {"GLM", "GPT"})
    )
    lines = [
        "## Task-file fidelity",
        "",
        "Share of top grades (complete / justified / fits) per dimension;"
        " `n` is the judged subjects in the cohort.",
        "",
        "| Cohort | n | Top grades overall |"
        + "".join(f" {label} |" for label in labels.values()),
        "|---|---:|---:|" + "---:|" * len(labels),
    ]
    top_grades = {"complete", "justified", "fits"}
    seen: set[str] = set()
    for name in ordered:
        if name not in cohorts or name in seen:
            continue
        seen.add(name)
        cohort_rows = cohorts[name]
        count = len(cohort_rows)
        per_dimension = {}
        for dim_name in labels:
            values = [
                (row.get("dimensions") or {}).get(dim_name) for row in cohort_rows
            ]
            graded = [value for value in values if value is not None]
            per_dimension[dim_name] = (
                f"{100 * sum(1 for value in graded if value in top_grades) / len(graded):.0f}%"
                if graded
                else "—"
            )
        overall = sum(
            sum(
                1
                for value in (row.get("dimensions") or {}).values()
                if value in top_grades
            )
            for row in cohort_rows
        )
        total = sum(
            len(
                [
                    value
                    for value in (row.get("dimensions") or {}).values()
                    if value is not None
                ]
            )
            for row in cohort_rows
        )
        overall_text = f"{100 * overall / total:.0f}%" if total else "—"
        lines.append(
            f"| {name} | {count} | {overall_text} |"
            + "".join(f" {per_dimension[dim_name]} |" for dim_name in labels)
        )
    mistake_total = sum(row.get("mistake_count") or 0 for row in rows)
    lines.extend(
        [
            "",
            f"Mistakes harvested across all judgments: {mistake_total}.",
        ]
    )
    return "\n".join(lines)


def _file_fidelity_detail_section(rows: Sequence[Mapping[str, Any]]) -> str:
    """One row per fidelity judgment, linked to its subject."""

    has_samples = any(row.get("sample_index") is not None for row in rows)
    sample_header = " Sample |" if has_samples else ""
    sample_rule = "---|" if has_samples else ""
    lines = [
        "## Task-file fidelity detail",
        "",
        "| Scenario | Producer | design | context | placement | justification |"
        " kind-fit | Mistakes | Subject | Judgment |" + sample_header,
        "|---|---|---|---|---|---|---|---:|---|---|" + sample_rule,
    ]
    labels = _FILE_FIDELITY_DIMENSION_LABELS()
    for row in rows:
        producer = f"{row.get('profile')} {row.get('reasoning_effort')}".rstrip()
        dimensions = row.get("dimensions") or {}
        run_path = row.get("run_path") or ""
        subject_link = (
            f"[{run_path.rstrip('/').rsplit('/', 1)[-1]}]"
            f"({_link(run_path + '/assessment.md', 'matrix.md')})"
            if run_path
            else "—"
        )
        sample_cell = f" s{row.get('sample_index')} |" if has_samples else ""
        cells = "".join(f" {dimensions.get(dim_name) or '—'} |" for dim_name in labels)
        lines.append(
            f"| `{row.get('scenario_id')}` | {producer} |{cells}"
            f" {row.get('mistake_count')} | {subject_link}"
            f" | [results]({_link(row['results_path'], 'matrix.md')}) |" + sample_cell
        )
    return "\n".join(lines)


def _file_readability_cohort_section(rows: Sequence[Mapping[str, Any]]) -> str:
    """Cohort shares of readable sections and navigable files."""

    cohorts: dict[str, list[Mapping[str, Any]]] = {"All": list(rows)}
    for row in rows:
        model = str(row.get("profile") or "").upper()
        if model:
            cohorts.setdefault(model, []).append(row)
        cohorts.setdefault(
            f"{row.get('profile')} {row.get('reasoning_effort')}".rstrip(), []
        ).append(row)
    model_names = sorted(name for name in cohorts if name in {"GLM", "GPT"})
    ordered = (
        ["All"]
        + model_names
        + sorted(key for key in cohorts if key != "All" and key not in {"GLM", "GPT"})
    )
    lines = [
        "## Task-file readability",
        "",
        "Share of `readable` section grades, `navigable` whole-file grades,"
        " and harvested presentation mistakes per cohort.",
        "",
        "| Cohort | n | Readable sections | Navigable files | Mistakes |",
        "|---|---:|---:|---:|---:|",
    ]
    seen: set[str] = set()
    for name in ordered:
        if name not in cohorts or name in seen:
            continue
        seen.add(name)
        cohort_rows = cohorts[name]
        section_total = sum(len(row.get("sections") or {}) for row in cohort_rows)
        readable = sum(
            1
            for row in cohort_rows
            for grade in (row.get("sections") or {}).values()
            if grade == "readable"
        )
        navigable = sum(
            1 for row in cohort_rows if row.get("navigation") == "navigable"
        )
        mistakes = sum(row.get("mistake_count") or 0 for row in cohort_rows)
        readable_text = (
            f"{100 * readable / section_total:.0f}%" if section_total else "—"
        )
        navigable_text = (
            f"{100 * navigable / len(cohort_rows):.0f}%" if cohort_rows else "—"
        )
        lines.append(
            f"| {name} | {len(cohort_rows)} | {readable_text}"
            f" | {navigable_text} | {mistakes} |"
        )
    return "\n".join(lines)


def _file_readability_detail_section(rows: Sequence[Mapping[str, Any]]) -> str:
    """One row per readability judgment, linked to its subject."""

    has_samples = any(row.get("sample_index") is not None for row in rows)
    sample_header = " Sample |" if has_samples else ""
    sample_rule = "---|" if has_samples else ""
    lines = [
        "## Task-file readability detail",
        "",
        "| Scenario | Producer | Readable sections | Navigation | Mistakes |"
        " Subject | Judgment |" + sample_header,
        "|---|---|---|---|---:|---|---|" + sample_rule,
    ]
    for row in rows:
        producer = f"{row.get('profile')} {row.get('reasoning_effort')}".rstrip()
        sections = row.get("sections") or {}
        readable = sum(1 for grade in sections.values() if grade == "readable")
        sections_text = f"{readable}/{len(sections)}" if sections else "—"
        run_path = row.get("run_path") or ""
        subject_link = (
            f"[{run_path.rstrip('/').rsplit('/', 1)[-1]}]"
            f"({_link(run_path + '/assessment.md', 'matrix.md')})"
            if run_path
            else "—"
        )
        sample_cell = f" s{row.get('sample_index')} |" if has_samples else ""
        lines.append(
            f"| `{row.get('scenario_id')}` | {producer} | {sections_text}"
            f" | {row.get('navigation') or '—'} | {row.get('mistake_count')}"
            f" | {subject_link}"
            f" | [results]({_link(row['results_path'], 'matrix.md')}) |" + sample_cell
        )
    return "\n".join(lines)


def _quality_top_grades(dimensions: Mapping[str, Any]) -> int:
    top = {"complete", "justified", "fits"}
    return sum(1 for value in dimensions.values() if value in top)


def _quality_cohort_section(rows: Sequence[Mapping[str, Any]]) -> str:
    """Cohort shares of top grades per quality dimension."""

    def cohort_key(row: Mapping[str, Any]) -> str:
        return f"{row.get('profile')} {row.get('reasoning_effort')}".rstrip()

    cohorts: dict[str, list[Mapping[str, Any]]] = {"All": list(rows)}
    for row in rows:
        model = str(row.get("profile") or "").upper()
        if model:
            cohorts.setdefault(model, []).append(row)
    for row in rows:
        cohorts.setdefault(cohort_key(row), []).append(row)
    model_names = sorted(name for name in cohorts if name in {"GLM", "GPT"})
    ordered = (
        ["All"]
        + model_names
        + sorted(key for key in cohorts if key != "All" and key not in {"GLM", "GPT"})
    )
    seen: set[str] = set()
    lines = [
        "## Task-file quality",
        "",
        "Share of top grades (complete / justified / fits) per dimension;"
        " `n` is the judged subjects in the cohort.",
        "",
        "| Cohort | n | Top grades overall |"
        + "".join(f" {label} |" for label in _QUALITY_DIMENSION_LABELS.values()),
        "|---|---:|---:|" + "---:|" * len(_QUALITY_DIMENSION_LABELS),
    ]
    for name in ordered:
        if name not in cohorts or name in seen:
            continue
        seen.add(name)
        cohort_rows = cohorts[name]
        count = len(cohort_rows)
        per_dimension = {}
        for dim_name in _QUALITY_DIMENSION_LABELS:
            values = [
                (row.get("dimensions") or {}).get(dim_name) for row in cohort_rows
            ]
            graded = [value for value in values if value is not None]
            per_dimension[dim_name] = (
                f"{100 * sum(1 for value in graded if value in {'complete', 'justified', 'fits'}) / len(graded):.0f}%"
                if graded
                else "—"
            )
        overall = sum(
            _quality_top_grades(row.get("dimensions") or {}) for row in cohort_rows
        )
        total = sum(
            len(
                [
                    value
                    for value in (row.get("dimensions") or {}).values()
                    if value is not None
                ]
            )
            for row in cohort_rows
        )
        overall_text = f"{100 * overall / total:.0f}%" if total else "—"
        lines.append(
            f"| {name} | {count} | {overall_text} |"
            + "".join(
                f" {per_dimension[dim_name]} |"
                for dim_name in _QUALITY_DIMENSION_LABELS
            )
        )
    return "\n".join(lines)


def _quality_detail_section(rows: Sequence[Mapping[str, Any]]) -> str:
    """One row per quality judgment, linked to its subject's grades."""

    has_samples = any(row.get("sample_index") is not None for row in rows)
    sample_header = " Sample |" if has_samples else ""
    sample_rule = "---|" if has_samples else ""
    lines = [
        "## Task-file quality detail",
        "",
        "One row per judgment; non-top grades are the findings to read.",
        "",
        "| Scenario | Producer | Kind |"
        + "".join(f" {label} |" for label in _QUALITY_DIMENSION_LABELS.values())
        + " Subject |"
        + sample_header,
        "|---|---|---|"
        + "---|" * len(_QUALITY_DIMENSION_LABELS)
        + "---|"
        + sample_rule,
    ]
    for row in rows:
        producer = f"{row.get('profile')} {row.get('reasoning_effort')}".rstrip()
        dimensions = row.get("dimensions") or {}
        run_path = row.get("run_path") or ""
        subject_link = (
            f"[assessment]({_link(f'{run_path}/assessment.md', 'matrix.md')})"
            if run_path
            else "—"
        )
        sample_cell = f" s{row.get('sample_index')} |" if has_samples else ""
        lines.append(
            f"| `{row.get('scenario_id')}` | {producer} | {row.get('task_kind') or '—'} |"
            + "".join(
                f" {dimensions.get(dim_name) or '—'} |"
                for dim_name in _QUALITY_DIMENSION_LABELS
            )
            + f" {subject_link} |"
            + sample_cell
        )
    return "\n".join(lines)


def _dimension_cell(metric: Mapping[str, Any] | None) -> str:
    if not metric:
        return "—"
    status = metric.get("status")
    score = metric.get("score")
    if status is None:
        return "—"
    return f"{status} ({score})" if score is not None else str(status)


def _per_scenario_section(records: PackageRecords) -> list[str]:
    """Link every scenario's results page, cells, and judgments."""

    cells: dict[str, set[str]] = {}
    assessments: dict[str, set[str]] = {}
    for path in records.collected_paths:
        parts = path.split("/")
        if (
            len(parts) == 5
            and parts[0] == "scenarios"
            and parts[3].startswith("s")
            and parts[4] == "run.json"
            and parts[2] != "assessment"
        ):
            cells.setdefault(parts[1], set()).add(parts[2])
        elif (
            len(parts) == 5
            and parts[0] == "scenarios"
            and parts[2] == "assessment"
            and parts[4] == "results.md"
        ):
            assessments.setdefault(parts[1], set()).add(parts[3])
    if not cells and not assessments:
        return []
    lines = [
        "## Per-scenario results",
        "",
        "| Scenario | Numbers | Cells | Task-creation | Handoff | Quality"
        " | Plan content | Fidelity | Readability |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for scenario_id in sorted(set(cells) | set(assessments)):
        cell_links = " · ".join(
            f"[{cell}](scenarios/{scenario_id}/{cell}/index.md)"
            for cell in sorted(cells.get(scenario_id, ()))
        )
        assessment_links = {
            name: f"[results](scenarios/{scenario_id}/assessment/{name}/results.md)"
            for name in sorted(assessments.get(scenario_id, ()))
        }
        numbers_link = (
            f"[results](scenarios/{scenario_id}/results.md)"
            if f"scenarios/{scenario_id}/results.md" in records.collected_paths
            else "—"
        )
        lines.append(
            f"| `{scenario_id}` | {numbers_link} | {cell_links or '—'}"
            f" | {assessment_links.get('task-creation', '—')}"
            f" | {assessment_links.get('handoff', '—')}"
            f" | {assessment_links.get('task-quality', '—')}"
            f" | {assessment_links.get('plan-content', '—')}"
            f" | {assessment_links.get('file-fidelity', '—')}"
            f" | {assessment_links.get('file-readability', '—')} |"
        )
    return ["\n".join(lines)]


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


_STAGE_ORDER = {
    KIND_TASK_CREATION: 0,
    KIND_PLAN_RETAIN: 1,
    KIND_PLAN_OMIT: 2,
    KIND_CONTINUATION: 3,
    KIND_CONTROL: 4,
    KIND_GENERATED_PLAN: 5,
}

_QUALITY_DIMENSION_LABELS = {
    "plan_design_completeness": "design",
    "durable_context_preservation": "context",
    "findability": "findability",
    "section_appropriateness": "placement",
    "plan_justification": "justification",
    "task_kind_fit": "kind-fit",
}


def _scenario_views(records: PackageRecords, scenario_id: str) -> list[GeneratedView]:
    prefix = f"scenarios/{scenario_id}"
    lines = [
        f"# Scenario `{scenario_id}`",
        "",
        "- [Reviewed target](target.md)",
        "- [All numbers for this scenario](results.md)",
        "",
        "## Cells",
        "",
        "| Cell | Runs |",
        "|---|---|",
    ]
    cell_keys = _scenario_cell_keys(records, scenario_id)
    for cell_key in cell_keys:
        runs = _cell_runs(records, scenario_id, cell_key)
        kinds = ", ".join(f"`{run['run']['kind']}`" for run in runs)
        lines.append(f"| [`{cell_key}`]({cell_key}/index.md) | {kinds} |")
    lines.extend(["", "## Assessment summaries", ""])
    for name, title in (
        ("task-creation", "Task-creation semantic assessment"),
        ("handoff", "Handoff semantic assessment"),
        ("task-quality", "Task-file quality assessment"),
    ):
        if f"{prefix}/assessment/{name}/results.md" in records.collected_paths:
            lines.append(
                f"- [{title}](assessment/{name}/results.md) — every judgment;"
                " each judgment's assessor session lives beside its subject"
                f" (`<cell>/assessment/{name}/…`)"
            )
    views = [
        GeneratedView(
            relative_path=f"{prefix}/index.md",
            content="\n".join(lines) + "\n",
        )
    ]
    results_view = _scenario_results_view(records, scenario_id, cell_keys)
    if results_view is not None:
        views.append(results_view)
    for cell_key in cell_keys:
        views.extend(_cell_views(records, scenario_id, cell_key))
    return views


def _scenario_cell_keys(records: PackageRecords, scenario_id: str) -> list[str]:
    """Producer-cell directory names, derived from sample run locations."""

    prefix = f"scenarios/{scenario_id}"
    return sorted(
        {
            path.split("/")[2]
            for path in records.collected_paths
            if path.startswith(f"{prefix}/")
            and len(path.split("/")) >= 5
            and path.split("/")[2] != "assessment"
            and path.split("/")[3].startswith("s")
            and path.endswith("/run.json")
        }
    )


def _cell_runs(
    records: PackageRecords, scenario_id: str, cell_key: str
) -> list[dict[str, Any]]:
    """Every evidence run of one cell: producers and stage samples.

    Each entry carries the run record and the package directory it was
    collected to; assessment runs stay out (they are judgments, not
    evidence).
    """

    prefix = f"scenarios/{scenario_id}/{cell_key}"
    run_paths = [
        path
        for path in records.collected_paths
        if path.startswith(f"{prefix}/")
        and path.endswith("/run.json")
        and "/assessment/" not in path
        and len(path.split("/")) in (5, 6)
    ]
    entries = [
        {"path": path.rsplit("/", 1)[0], "run": records.collected_json(path)}
        for path in sorted(run_paths)
    ]
    entries.sort(
        key=lambda entry: (
            _STAGE_ORDER.get(entry["run"].get("kind"), 99),
            entry["path"],
        )
    )
    return entries


def _fidelity_grades_text(row: Mapping[str, Any] | None) -> str:
    if not row:
        return "—"
    dimensions = row.get("dimensions") or {}
    parts = [
        f"{label} {dimensions.get(name) or '—'}"
        for name, label in (
            ("plan_design_completeness", "design"),
            ("durable_context_preservation", "context"),
            ("task_kind_fit", "kind-fit"),
        )
    ]
    parts.append(f"mistakes {row.get('mistake_count') or 0}")
    return " · ".join(parts)


def _readability_grades_text(row: Mapping[str, Any] | None) -> str:
    if not row:
        return "—"
    sections = row.get("sections") or {}
    readable = sum(1 for grade in sections.values() if grade == "readable")
    navigation = row.get("navigation")
    return (
        f"{readable}/{len(sections)} readable"
        f" · navigation {navigation or '—'}"
        f" · mistakes {row.get('mistake_count') or 0}"
    )


def _scenario_results_view(
    records: PackageRecords, scenario_id: str, cell_keys: Sequence[str]
) -> GeneratedView | None:
    """One page holding every number for one scenario, linking to evidence."""

    aggregate = records.collected_json("aggregate.json")
    details = [
        row
        for row in aggregate.get("assessment_details", ())
        if row.get("scenario_id") == scenario_id
    ]
    page = f"scenarios/{scenario_id}/results.md"
    runs = [
        entry
        for cell_key in cell_keys
        for entry in _cell_runs(records, scenario_id, cell_key)
    ]
    if not runs:
        return None
    by_run_path = {
        (row.get("kind"), row.get("run_path")): row
        for row in details
        if isinstance(row.get("run_path"), str)
    }
    lines = [
        f"# Results — `{scenario_id}`",
        "",
        "- [Scenario index](index.md) · [Reviewed target](target.md) ·"
        " [Quality matrix](../../matrix.md)",
        "",
        "Every number for this scenario, one hop from the evidence it"
        " was computed from.",
        "",
        "## Producer samples",
        "",
        "| Cell | Sample | Status | Task-creation overall | Task-file quality"
        " grades | Fidelity | Readability |",
        "|---|---|---|---|---|---|---|",
    ]
    for entry in runs:
        run = entry["run"]
        if run.get("kind") != KIND_TASK_CREATION:
            continue
        status = "valid" if run.get("valid") else "invalid"
        task_row = by_run_path.get(("task-creation", entry["path"]))
        overall = task_row and task_row.get("overall_success_percentage")
        overall_text = "—" if overall is None else f"{overall:g}%"
        quality_rows = [
            row
            for row in details
            if row.get("kind") == "task-quality"
            and row.get("run_path") == entry["path"]
        ]
        if quality_rows:
            grades = quality_rows[0].get("dimensions") or {}
            quality_text = " · ".join(
                f"{_QUALITY_DIMENSION_LABELS.get(name, name)}"
                f" {grades.get(name) or '—'}"
                for name in _QUALITY_DIMENSION_LABELS
                if name in grades
            )
        else:
            quality_text = "—"
        sample = entry["path"].rsplit("/", 1)[-1]
        cell = entry["path"].split("/")[2]
        link = f"[`{sample}`]({_link(entry['path'] + '/session.md', page)})"
        if f"{entry['path']}/assessment.md" in records.collected_paths:
            link += f" ([assessment]({_link(entry['path'] + '/assessment.md', page)}))"
        if f"{entry['path']}/invalid.md" in records.collected_paths:
            link += f" ([invalid]({_link(entry['path'] + '/invalid.md', page)}))"
        fidelity_row = by_run_path.get(("file-fidelity", entry["path"]))
        fidelity_text = _fidelity_grades_text(fidelity_row)
        readability_row = by_run_path.get(("file-readability", entry["path"]))
        readability_text = _readability_grades_text(readability_row)
        lines.append(
            f"| [`{cell}`]({cell}/index.md) | {link} | {status}"
            f" | {overall_text} | {quality_text} | {fidelity_text}"
            f" | {readability_text} |"
        )
    lines.extend(
        [
            "",
            "## Plan stages",
            "",
            "| Cell | Stage | Sample | Status | Handoff score | Coverage |"
            " Broad rediscovery | Plan content |",
            "|---|---|---|---|---:|---|---|---|",
        ]
    )
    for entry in runs:
        run = entry["run"]
        if run.get("kind") == KIND_TASK_CREATION:
            continue
        status = "valid" if run.get("valid") else "invalid"
        row = by_run_path.get(("handoff", entry["path"]))
        score = row and row.get("handoff_quality_score")
        score_text = "—" if score is None else f"{score}"
        coverage = (row and row.get("plan_coverage")) or "—"
        rediscovery = row and row.get("broad_rediscovery")
        rediscovery_text = "—" if rediscovery is None else str(rediscovery)
        content_row = by_run_path.get(("plan-content", entry["path"]))
        content_coverage = content_row and content_row.get("coverage")
        content_text = "—" if content_coverage is None else f"{content_coverage:.0%}"
        sample = entry["path"].rsplit("/", 1)[-1]
        stage = entry["path"].split("/")[3]
        cell = entry["path"].split("/")[2]
        link = f"[`{sample}`]({_link(entry['path'] + '/session.md', page)})"
        if f"{entry['path']}/assessment.md" in records.collected_paths:
            link += f" ([assessment]({_link(entry['path'] + '/assessment.md', page)}))"
        invalid_note = (
            f" ([invalid]({_link(entry['path'] + '/invalid.md', page)}))"
            if f"{entry['path']}/invalid.md" in records.collected_paths
            else ""
        )
        lines.append(
            f"| [`{cell}`]({cell}/index.md) | `{stage}` | {link}{invalid_note}"
            f" | {status} | {score_text} | {coverage} | {rediscovery_text}"
            f" | {content_text} |"
        )
    return GeneratedView(relative_path=page, content="\n".join(lines) + "\n")


def _cell_views(
    records: PackageRecords, scenario_id: str, cell_key: str
) -> list[GeneratedView]:
    page = f"scenarios/{scenario_id}/{cell_key}/index.md"
    prefix = f"scenarios/{scenario_id}/{cell_key}"
    runs = _cell_runs(records, scenario_id, cell_key)
    producer = runs[0]["run"] if runs else {}
    lines = [
        f"# Cell `{scenario_id}` — `{cell_key}`",
        "",
        f"- Model: `{producer.get('model')}` (profile `{producer.get('provider')}`,"
        f" effort `{producer.get('reasoning_effort')}`)",
        "- [Scenario results](../results.md) — every number for the scenario",
        "",
        "## Runs",
        "",
    ]
    for entry in runs:
        run = entry["run"]
        run_dir = entry["path"]
        status = "valid" if run.get("valid") else "invalid"
        lines.append(f"### `{run['kind']}` — {run_dir.rsplit('/', 1)[-1]} ({status})")
        lines.append("")
        lines.append(
            f"- [Session]({_link(f'{run_dir}/session.md', page)})"
            " — includes the prompt and response"
        )
        if f"{run_dir}/assessment.md" in records.collected_paths:
            lines.append(
                f"- [Assessment]({_link(f'{run_dir}/assessment.md', page)})"
                " — the grades judging this run"
            )
        if f"{run_dir}/invalid.md" in records.collected_paths:
            lines.append(
                f"- [Invalid sample note]({_link(f'{run_dir}/invalid.md', page)})"
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
    assessment_dirs = sorted(
        {
            path[: -len("/session.md")]
            for path in records.collected_paths
            if path.startswith(f"{prefix}/assessment/") and path.endswith("/session.md")
        }
    )
    if assessment_dirs:
        lines.extend(["## Assessor runs", ""])
        lines.append(
            "Judgments of this cell's evidence; grades sit beside the"
            " judged sample as `assessment.md`."
        )
        lines.append("")
        for run_dir in assessment_dirs:
            label = "/".join(run_dir.split("/")[3:])
            lines.append(f"- [`{label}`]({_link(f'{run_dir}/session.md', page)})")
    lines.extend(["", "Assessment summaries:", ""])
    for name, title in (
        ("task-creation", "Task-creation semantic results"),
        ("handoff", "Handoff semantic results"),
        ("task-quality", "Task-file quality results"),
        ("plan-content", "Presented-plan content results"),
        ("file-fidelity", "Task-file fidelity results"),
        ("file-readability", "Task-file readability results"),
    ):
        path = f"scenarios/{scenario_id}/assessment/{name}/results.md"
        if path in records.collected_paths:
            lines.append(f"- [{title}]({_link(path, page)})")
    return [GeneratedView(relative_path=page, content="\n".join(lines) + "\n")]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    scenarios_parser = commands.add_parser(
        "extract-scenarios",
        help="write the scenario definitions export (targets, prompts,"
        " templates, shared inputs, stage inputs)",
    )
    scenarios_parser.add_argument("--output", type=Path, default=SCENARIOS_ROOT)
    scenarios_parser.add_argument(
        "--bundle",
        type=Path,
        default=DEFAULT_BUNDLE,
        help="guidance bundle the shared inputs are generated from",
    )
    scenarios_parser.add_argument(
        "--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT
    )

    collect_parser = commands.add_parser(
        "collect", help="collect a durable result package"
    )
    collect_parser.add_argument(
        "--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT
    )
    collect_parser.add_argument(
        "--frozen",
        type=Path,
        required=True,
        help=(
            "consolidated dataset JSON produced by freeze; the completed"
            " evaluations no longer live in suite fixtures"
        ),
    )
    collect_parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="package directory to write; its name is the package name",
    )
    collect_parser.add_argument(
        "--bundle",
        type=Path,
        default=None,
        help=(
            "guidance bundle used for workspace reconstruction; defaults to"
            " the bundle recorded in the frozen dataset"
        ),
    )
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
        output = extract_scenarios(
            output_dir=args.output.expanduser().resolve(),
            bundle=args.bundle.expanduser().resolve(),
            artifact_root=args.artifact_root.expanduser().resolve(),
        )
        print(output)
        return 0
    if args.command == "collect":
        package = collect(
            package_dir=args.output.expanduser().resolve(),
            artifact_root=args.artifact_root.expanduser().resolve(),
            frozen_path=args.frozen.expanduser().resolve(),
            cells=args.cells,
            reconstruct=not args.no_reconstruction,
            bundle=args.bundle.expanduser().resolve() if args.bundle else None,
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
