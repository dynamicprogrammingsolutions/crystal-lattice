from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Mapping

from agent_eval import AgentEval, Run
from agent_eval.crystal_lattice import (
    CrystalLatticeContext,
    CrystalLatticeEnvironment,
)
from agent_eval.services import RunServices
from agent_eval.workspace import GitWorkspaceFactory, git_workspace


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
PACKAGE_ROOT = REPOSITORY_ROOT / "maintainer" / "agent-evaluation"
SPEC_ROOT = (
    REPOSITORY_ROOT
    / "maintainer"
    / "specifications"
    / "documentation-and-specification-standard"
    / "agent-behavior-verification"
)
DEFAULT_REVISION = "c00d14954a503b96a6e2bbdb90a4c31c8af785e1"
DEFAULT_CONFIG = Path.home() / ".crystal" / "config.json"

CANDIDATE_GUIDANCE_PATHS = (
    "AGENTS.md",
    "docs/development/index.md",
    "docs/development/standards/index.md",
    "docs/development/standards/documentation.md",
    "docs/development/standards/specifications.md",
    "docs/development/repository/index.md",
    "docs/development/repository/documentation.md",
    "docs/development/repository/specifications.md",
    "plugins/AGENTS.md",
    "plugins/docs/AGENTS.md",
)


@dataclass(frozen=True)
class ModelProfile:
    name: str
    agent_id: str
    model: str
    hosted: bool
    auth_mode: str | None = None

    def request_overrides(self, workspace: Path) -> dict[str, object]:
        overrides: dict[str, object] = {
            "model": self.model,
            "working_directory": str(workspace),
            "allowed_paths": [str(workspace)],
            "include_tasks": False,
            "skills_enabled": False,
            "mcp_enabled": False,
            "web_search_enabled": False,
        }
        if self.name == "glm":
            overrides["request_options"] = {"reasoning_effort": "high"}
        if self.auth_mode is not None:
            overrides["auth_mode"] = self.auth_mode
        return overrides


PROFILES = {
    "glm": ModelProfile(
        name="glm",
        agent_id="glm-ollama",
        model="glm-5.2:cloud",
        hosted=False,
    ),
    "gpt": ModelProfile(
        name="gpt",
        agent_id="codex-openai",
        model="gpt-5.6-luna",
        hosted=True,
        auth_mode="chatgpt",
    ),
}


@dataclass(frozen=True)
class GuidanceFile:
    path: str
    sha256: str


@dataclass(frozen=True)
class TurnValue:
    prompt: str
    response: str
    completed: bool
    cancelled: bool
    errors: tuple[str, ...]
    tool_event_count: int
    mutation_count: int
    duration_seconds: float


@dataclass(frozen=True)
class AssertionFinding:
    name: str
    passed: bool
    detail: str


class WorkspaceAwareEnvironment(CrystalLatticeEnvironment):
    """Resolve Crystal Lattice workspace environment at open time."""

    @contextmanager
    def open(
        self,
        *,
        services: RunServices,
        workspace: Path | None,
        parent_snapshot: object | None,
    ) -> Iterator[CrystalLatticeContext]:
        if workspace is None:
            raise ValueError("documentation-standard evaluations require a workspace")
        dynamic = CrystalLatticeEnvironment(
            config_path=self.config_path,
            env_overrides={
                **self.env_overrides,
                "WORKING_DIR": str(workspace),
                "REPO_ROOT": str(workspace),
            },
            config_env=self.config_env,
            core_factory=self.core_factory,
            application_factory=self.application_factory,
            default_agent=self.default_agent,
            request_driver=self.request_driver,
            snapshotter=self.snapshotter,
        )
        with dynamic.open(
            services=services,
            workspace=workspace,
            parent_snapshot=parent_snapshot,
        ) as context:
            yield context


@dataclass(frozen=True)
class ScenarioWorkspaceFactory:
    fixture_id: str
    candidate_guidance: bool
    branch_variant: str = "base"
    revision: str = DEFAULT_REVISION

    def fingerprint(self) -> object:
        return {
            "type": "documentation-standard-scenario",
            "fixture_id": self.fixture_id,
            "candidate_guidance": self.candidate_guidance,
            "guidance_sha256": (
                candidate_guidance_sha256() if self.candidate_guidance else None
            ),
            "branch_variant": self.branch_variant,
            "revision": self.revision,
        }

    def __call__(self, staging_dir: Path) -> Path:
        base = self._base()
        workspace = base(staging_dir)
        apply_fixture(workspace, self.fixture_id, self.branch_variant)
        if self.candidate_guidance:
            copy_candidate_guidance(workspace)
        _commit_fixture(workspace)
        return workspace

    def cleanup(self, workspace: Path) -> None:
        self._base().cleanup(workspace)

    def _base(self) -> GitWorkspaceFactory:
        return git_workspace(
            source=REPOSITORY_ROOT,
            revision=self.revision,
            cache_root=PACKAGE_ROOT / ".repository-cache",
        )


@dataclass(frozen=True)
class ParentWorkspaceFactory:
    parent_workspace: Path
    fixture_id: str
    branch_variant: str

    def fingerprint(self) -> object:
        return {
            "type": "documentation-standard-parent-fork",
            "parent": _workspace_content_sha256(self.parent_workspace),
            "fixture_id": self.fixture_id,
            "branch_variant": self.branch_variant,
            "guidance_sha256": candidate_guidance_sha256(),
        }

    def __call__(self, staging_dir: Path) -> Path:
        base = ScenarioWorkspaceFactory(
            fixture_id=self.fixture_id,
            candidate_guidance=False,
            branch_variant="base",
        )
        workspace = base(staging_dir)
        _copy_workspace_contents(self.parent_workspace, workspace)
        copy_candidate_guidance(workspace)
        _commit_fixture(workspace)
        return workspace

    def cleanup(self, workspace: Path) -> None:
        ScenarioWorkspaceFactory(
            fixture_id=self.fixture_id,
            candidate_guidance=False,
        ).cleanup(workspace)


class DocumentationEvaluationHarness:
    def __init__(self, profile: ModelProfile) -> None:
        config_path = Path(
            os.getenv("AGENT_EVAL_CONFIG", str(DEFAULT_CONFIG))
        ).expanduser()
        if not config_path.is_file():
            raise FileNotFoundError(f"Crystal Lattice config missing: {config_path}")
        artifact_root = Path(
            os.getenv(
                "AGENT_EVAL_ARTIFACT_ROOT",
                str(REPOSITORY_ROOT / "tmp" / "agent-evaluation" / "documentation-standard"),
            )
        ).expanduser()
        environment = WorkspaceAwareEnvironment.from_config(
            config_path,
            environment={
                "CONFIG_DIR": str(config_path.parent),
                "CHATGPT_TEST_STATE_DIR": str(config_path.parent),
                "OLLAMA_OPENAI_BASE_URL": os.getenv(
                    "OLLAMA_OPENAI_BASE_URL",
                    "http://localhost:11434/v1",
                ),
            },
        )
        self.profile = profile
        self.evaluation = AgentEval(
            default_environment=environment,
            artifact_root=artifact_root / profile.name,
            cache_root=artifact_root / "cache" / profile.name,
        )
        self._runs: dict[str, Run[TurnValue]] = {}

    def close(self) -> None:
        self.evaluation.close()

    def seed(
        self,
        *,
        seed_id: str,
        spec_file: str,
        fixture_id: str,
    ) -> Run[TurnValue]:
        key = f"seed:{seed_id}"
        if key in self._runs:
            return self._runs[key]
        prompt = extract_blockquote(SPEC_ROOT / spec_file, "## Exact seed prompt")
        workspace = ScenarioWorkspaceFactory(
            fixture_id=fixture_id,
            candidate_guidance=False,
        )
        strategy_version = "v5" if self.profile.name == "gpt" else "v4"
        run = self.evaluation.run(
            seed_id,
            lambda context: self._turn(context, prompt, guidance=()),
            workspace=workspace,
            cache_key=(
                f"documentation-standard:{self.profile.name}:{seed_id}:"
                f"{_sha256_text(prompt)}:{strategy_version}"
            ),
        )
        self._runs[key] = run
        return run

    def branch(
        self,
        *,
        test_id: str,
        spec_file: str,
        parent: Run[TurnValue],
        fixture_id: str,
        branch_variant: str = "base",
        prompt_heading: str = "## Exact user prompt",
        cache: bool = True,
    ) -> Run[TurnValue]:
        key = f"branch:{test_id}:{branch_variant}"
        if key in self._runs:
            return self._runs[key]
        prompt = extract_blockquote(SPEC_ROOT / spec_file, prompt_heading)
        workspace = ScenarioWorkspaceFactory(
            fixture_id=fixture_id,
            candidate_guidance=True,
            branch_variant=branch_variant,
        )
        guidance = candidate_guidance_files()
        cache_key = None
        if cache:
            cache_key = (
                f"documentation-standard:{self.profile.name}:{test_id}:"
                f"{candidate_guidance_sha256()}:{_sha256_text(prompt)}:"
                f"{branch_variant}:v1"
            )
        run = self.evaluation.run(
            test_id,
            lambda context: self._turn(context, prompt, guidance=guidance),
            continue_from=parent,
            workspace=workspace,
            cache_key=cache_key,
        )
        self._runs[key] = run
        return run

    def branch_from_parent_workspace(
        self,
        *,
        test_id: str,
        spec_file: str,
        parent: Run[TurnValue],
        fixture_id: str,
        branch_variant: str,
        prompt_heading: str = "## Exact user prompt",
    ) -> Run[TurnValue]:
        key = f"parent-branch:{test_id}:{branch_variant}:{prompt_heading}"
        if key in self._runs:
            return self._runs[key]
        if parent.workspace is None:
            raise ValueError("parent run has no workspace")
        prompt = extract_blockquote(SPEC_ROOT / spec_file, prompt_heading)
        workspace = ParentWorkspaceFactory(
            parent_workspace=parent.workspace,
            fixture_id=fixture_id,
            branch_variant=branch_variant,
        )
        run = self.evaluation.run(
            test_id,
            lambda context: self._turn(
                context,
                prompt,
                guidance=candidate_guidance_files(),
            ),
            continue_from=parent,
            workspace=workspace,
            cache_key=(
                f"documentation-standard:{self.profile.name}:{test_id}:"
                f"{parent.snapshot_sha256}:{candidate_guidance_sha256()}:"
                f"{_sha256_text(prompt)}:v1"
            ),
        )
        self._runs[key] = run
        return run

    def _turn(
        self,
        context: CrystalLatticeContext,
        prompt: str,
        *,
        guidance: tuple[GuidanceFile, ...],
    ) -> TurnValue:
        if context.workspace is None:
            raise ValueError("missing evaluation workspace")
        if context.session_or_none is None:
            context.start(self.profile.agent_id)
        context.config.update(self.profile.request_overrides(context.workspace))
        context.services.record(
            "documentation_standard.profile",
            {
                "name": self.profile.name,
                "agent_id": self.profile.agent_id,
                "model": self.profile.model,
                "hosted": self.profile.hosted,
                "auth_mode": self.profile.auth_mode,
            },
        )
        context.services.record(
            "documentation_standard.prompt",
            {
                "text": prompt,
                "sha256": _sha256_text(prompt),
            },
        )
        context.services.record(
            "documentation_standard.guidance",
            [item.__dict__ for item in guidance],
        )
        context.add_message("user", prompt)
        raw_max_events = os.getenv("AGENT_EVAL_MAX_EVENTS")
        max_events = int(raw_max_events) if raw_max_events else None
        max_tool_calls = int(os.getenv("AGENT_EVAL_MAX_TOOL_CALLS", "30"))
        completed_tool_calls: set[str] = set()

        def observe_tool_results(event: Mapping[str, object]) -> None:
            completed_tool_calls.update(completed_tool_call_ids(event))

        outcome = context.request(
            stream=True,
            max_events=max_events,
            observers=(observe_tool_results,),
            stop_when=lambda progress: (
                len(completed_tool_calls) >= max_tool_calls
            ),
        )
        context.services.record(
            "documentation_standard.completed_tool_calls",
            {
                "count": len(completed_tool_calls),
                "ids": sorted(completed_tool_calls),
                "budget": max_tool_calls,
            },
        )
        return TurnValue(
            prompt=prompt,
            response=outcome.final_response,
            completed=outcome.completed,
            cancelled=outcome.cancelled,
            errors=outcome.error_messages,
            tool_event_count=outcome.tool_event_count,
            mutation_count=outcome.mutation_count,
            duration_seconds=outcome.duration_seconds,
        )


def selected_profile() -> ModelProfile:
    name = os.getenv("AGENT_EVAL_PROFILE", "").strip().lower()
    if name not in PROFILES:
        raise ValueError(
            "AGENT_EVAL_PROFILE must be one of: " + ", ".join(sorted(PROFILES))
        )
    return PROFILES[name]


def enforce_real_model_gate(profile: ModelProfile) -> None:
    if os.getenv("AGENT_EVAL_RUN_REAL") != "1":
        raise RuntimeError("set AGENT_EVAL_RUN_REAL=1 to execute real-model tests")
    if profile.hosted and os.getenv("AGENT_EVAL_ALLOW_HOSTED") != "1":
        raise RuntimeError(
            "set AGENT_EVAL_ALLOW_HOSTED=1 to execute hosted ChatGPT tests"
        )


def extract_blockquote(path: Path, heading: str) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        start = lines.index(heading) + 1
    except ValueError as exc:
        raise ValueError(f"{path} has no heading {heading!r}") from exc
    values: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        if line.startswith(">"):
            value = line[1:]
            if value.startswith(" "):
                value = value[1:]
            values.append(value)
        elif values and not line.strip():
            break
    if not values:
        raise ValueError(f"{path} has no blockquote under {heading!r}")
    return re.sub(r"\s+", " ", " ".join(values)).strip()


def extract_section(path: Path, heading: str) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        start = lines.index(heading) + 1
    except ValueError as exc:
        raise ValueError(f"{path} has no heading {heading!r}") from exc
    values: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        values.append(line)
    return "\n".join(values).strip()


def candidate_guidance_files() -> tuple[GuidanceFile, ...]:
    return tuple(
        GuidanceFile(
            path=relative,
            sha256=hashlib.sha256(
                REPOSITORY_ROOT.joinpath(relative).read_bytes()
            ).hexdigest(),
        )
        for relative in CANDIDATE_GUIDANCE_PATHS
    )


def candidate_guidance_sha256() -> str:
    payload = json.dumps(
        [item.__dict__ for item in candidate_guidance_files()],
        sort_keys=True,
        separators=(",", ":"),
    )
    return _sha256_text(payload)


def copy_candidate_guidance(workspace: Path) -> None:
    for relative in CANDIDATE_GUIDANCE_PATHS:
        source = REPOSITORY_ROOT / relative
        target = workspace / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def record_review(
    run: Run[TurnValue],
    *,
    spec_file: str,
    findings: tuple[AssertionFinding, ...],
) -> None:
    spec_path = SPEC_ROOT / spec_file
    human_questions = extract_section(spec_path, "## Human review")
    run.record(
        "assertions.json",
        [finding.__dict__ for finding in findings],
    )
    lines = [
        f"# Documentation-standard review: {run.name}",
        "",
        f"- Profile: `{json.dumps(run.environment_fingerprint, sort_keys=True)}`",
        f"- Parent run: `{run.parent_run_id or 'none'}`",
        f"- Snapshot: `{run.snapshot_sha256 or 'none'}`",
        "",
        "## Prompt",
        "",
        run.value.prompt,
        "",
        "## Response",
        "",
        run.value.response or "(No assistant response.)",
        "",
        "## Changed paths",
        "",
    ]
    lines.extend(f"- `{path}`" for path in run.changed_paths)
    if not run.changed_paths:
        lines.append("None.")
    lines.extend(["", "## Deterministic findings", ""])
    lines.extend(
        f"- {'PASS' if finding.passed else 'FAIL'} — {finding.name}: {finding.detail}"
        for finding in findings
    )
    lines.extend(["", "## Human-review questions", "", human_questions, ""])
    run.record("manual-review.md", "\n".join(lines))
    run.record(
        "semantic-assessment-input.json",
        {
            "requirements": _requirement_ids(spec_path),
            "prompt": run.value.prompt,
            "response": run.value.response,
            "changed_paths": run.changed_paths,
            "findings": [finding.__dict__ for finding in findings],
            "guidance_sha256": candidate_guidance_sha256(),
        },
    )


def assert_findings(findings: tuple[AssertionFinding, ...]) -> None:
    failures = [finding for finding in findings if not finding.passed]
    if failures:
        rendered = "\n".join(f"- {item.name}: {item.detail}" for item in failures)
        raise AssertionError(f"documentation-standard findings failed:\n{rendered}")


def basic_run_findings(run: Run[TurnValue]) -> tuple[AssertionFinding, ...]:
    return (
        AssertionFinding(
            "run completed",
            run.error is None and run.value.completed,
            (
                "completed"
                if run.error is None and run.value.completed
                else f"error={run.error!r}, outcome_errors={run.value.errors!r}"
            ),
        ),
        AssertionFinding(
            "assistant response",
            bool(run.value.response.strip()),
            f"{len(run.value.response)} characters",
        ),
        AssertionFinding(
            "provider errors",
            not run.value.errors,
            repr(run.value.errors),
        ),
    )


def completed_tool_call_ids(event: Mapping[str, object]) -> tuple[str, ...]:
    if event.get("type") not in {"tool_results", "tool_result"}:
        return ()
    messages = event.get("messages")
    values = messages if isinstance(messages, list) else [event]
    ids: list[str] = []
    for index, value in enumerate(values):
        if not isinstance(value, Mapping):
            continue
        metadata = value.get("metadata")
        metadata_value = metadata if isinstance(metadata, Mapping) else {}
        raw_id = (
            metadata_value.get("tool_call_id")
            or value.get("tool_call_id")
            or value.get("tool_use_id")
        )
        if isinstance(raw_id, str) and raw_id:
            ids.append(raw_id)
        else:
            rendered = json.dumps(value, default=str)
            ids.append(f"anonymous:{index}:{_sha256_text(rendered)}")
    return tuple(ids)


def file_text(run: Run[TurnValue], relative: str) -> str:
    if run.workspace is None:
        raise ValueError("run has no workspace")
    return run.workspace.joinpath(relative).read_text(encoding="utf-8")


def file_exists(run: Run[TurnValue], relative: str) -> bool:
    if run.workspace is None:
        raise ValueError("run has no workspace")
    return run.workspace.joinpath(relative).exists()


def matching_paths(run: Run[TurnValue], prefix: str) -> tuple[str, ...]:
    if run.workspace is None:
        raise ValueError("run has no workspace")
    root = run.workspace / prefix
    if not root.exists():
        return ()
    return tuple(
        sorted(
            str(path.relative_to(run.workspace))
            for path in root.rglob("*")
            if path.is_file()
        )
    )


def apply_fixture(workspace: Path, fixture_id: str, branch_variant: str) -> None:
    if fixture_id == "js-single-file-tool":
        _fixture_js_single_file_tool(workspace, branch_variant)
    elif fixture_id == "report-export":
        _fixture_report_export(workspace, branch_variant)
    elif fixture_id == "mobile-composer":
        _fixture_mobile_composer(workspace, branch_variant)
    elif fixture_id == "event-retry":
        _fixture_event_retry(workspace, branch_variant)
    elif fixture_id == "batch-sync":
        _fixture_batch_sync(workspace, branch_variant)
    elif fixture_id == "path-policy":
        _fixture_path_policy(workspace, branch_variant)
    elif fixture_id == "slug-utils":
        _fixture_slug_utils(workspace, branch_variant)
    elif fixture_id == "label-utils":
        _fixture_label_utils(workspace, branch_variant)
    elif fixture_id == "sync-engine":
        _fixture_sync_engine(workspace, branch_variant)
    else:
        raise KeyError(f"unknown fixture: {fixture_id}")


def _fixture_js_single_file_tool(workspace: Path, branch_variant: str) -> None:
    _focus_js_single_file_tool_workspace(workspace)
    if branch_variant == "generated-typo":
        readme = workspace / "plugins/js-single-file-tool/README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8")
            + "\n## Helper installation\n\n```bash\npip instal example-package\n```\n",
            encoding="utf-8",
        )
        prepared = (
            workspace
            / "docs_site/prepared/plugins/js-single-file-tool/index.md"
        )
        prepared.parent.mkdir(parents=True, exist_ok=True)
        prepared.write_text(
            "<!-- generated from plugins/js-single-file-tool/README.md -->\n\n"
            + readme.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    elif branch_variant != "base":
        raise KeyError(f"unknown branch variant: {branch_variant}")


def _fixture_report_export(workspace: Path, branch_variant: str) -> None:
    if branch_variant != "base":
        raise KeyError(f"unknown report-export variant: {branch_variant}")
    _write_synthetic_fixture(
        workspace,
        {
            "packages/report-export-sdk/README.md": """# report-export-sdk

Exports rows to an in-memory report. `export_rows(rows)` currently accepts any
number of rows.

## Verify

```bash
pytest packages/report-export-sdk/tests -q
```
""",
            "packages/report-export-sdk/src/report_export.py": """def export_rows(rows):
    return list(rows)
""",
            "packages/report-export-sdk/tests/test_report_export.py": """from packages.report_export_sdk.src.report_export import export_rows


def test_export_rows_preserves_rows():
    assert export_rows([1, 2]) == [1, 2]
""",
            "packages/report-export-sdk/docs/development/index.md": """# Development

- [Export limits](specifications/export-limits/index.md)
""",
            "packages/report-export-sdk/docs/development/specifications/export-limits/index.md": """# Export limits

Owner: `packages/report-export-sdk`

- [Product specification](product-spec.md)
- [Technical specification](technical-spec.md)
- [Requirements](requirements.md)
""",
            "packages/report-export-sdk/docs/development/specifications/export-limits/product-spec.md": """# Product specification

The export API returns all supplied rows. The current target does not define a
row-count limit.
""",
            "packages/report-export-sdk/docs/development/specifications/export-limits/technical-spec.md": """# Technical specification

`export_rows(rows)` materializes and returns the supplied iterable.
""",
            "packages/report-export-sdk/docs/development/specifications/export-limits/requirements.md": """# Requirements

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| EXPORT-001 | Export preserves supplied rows. | Implemented | Automated | Documented | `src/report_export.py`; `tests/test_report_export.py`; `README.md` |
""",
            "tasks/report-export-max-rows.md": """# Report export maximum rows

Status: Approved

## Requirements checklist

- [ ] `export_rows` accepts optional `max_rows`.
- [ ] Omitted or `None` preserves unlimited compatibility.
- [ ] A positive limit permits `len(rows) <= max_rows`.
- [ ] Exceeding the limit raises `ValueError` before returning output.
- [ ] Target specification, live requirements, tests, and current README stay
  consistent.

Implementation is approved. A separate specification version is not requested.
""",
        },
    )


def _fixture_mobile_composer(workspace: Path, branch_variant: str) -> None:
    if branch_variant != "base":
        raise KeyError(f"unknown mobile-composer variant: {branch_variant}")
    _write_synthetic_fixture(
        workspace,
        {
            "packages/conversation-contract/docs/development/specifications/composer/index.md": """# Portable composer contract

Owner: `packages/conversation-contract`

- [Product specification](product-spec.md)
- [Requirements](requirements.md)
""",
            "packages/conversation-contract/docs/development/specifications/composer/product-spec.md": """# Product specification

All clients submit non-empty text messages through a composer. Portable
behavior covers message validity and submission, not platform layout.
""",
            "packages/conversation-contract/docs/development/specifications/composer/requirements.md": """# Requirements

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| COMPOSER-001 | Clients submit non-empty text. | Implemented | Automated | Documented | Existing clients |
""",
            "mobile/example-app/src/Composer.tsx": """export function Composer() {
  return null;
}
""",
            "mobile/example-app/docs/development/index.md": """# Mobile development

The app implements the portable composer contract.
""",
            "tasks/mobile-composer-ux.md": """# Mobile composer UX

Status: Approved

## Requirements checklist

- [ ] Define a mobile-only multiline composer refinement.
- [ ] Specify keyboard avoidance, send-button placement, and accessibility
  labels.
- [ ] Link the portable composer contract instead of copying it.
- [ ] Create requirements with implementation and verification pending.

Create the specification only. Do not implement the UI.
""",
        },
    )


def _fixture_event_retry(workspace: Path, branch_variant: str) -> None:
    if branch_variant != "base":
        raise KeyError(f"unknown event-retry variant: {branch_variant}")
    _write_synthetic_fixture(
        workspace,
        {
            "packages/event-sdk/README.md": """# event-sdk

SDK for publishing events.

- [User documentation](docs/index.md)
""",
            "packages/event-sdk/docs/index.md": """# Event SDK documentation

- [Publishing events](publishing.md)
""",
            "packages/event-sdk/docs/publishing.md": """# Publishing events

Call `publish(event)`. Transient delivery failures are retried automatically.
""",
            "packages/event-sdk/src/events.py": """def retry_state(attempt, max_attempts=3):
    if attempt >= max_attempts:
        return "failed"
    return "retrying"
""",
            "packages/event-sdk/tests/test_events.py": """from packages.event_sdk.src.events import retry_state


def test_retry_state():
    assert retry_state(1) == "retrying"
    assert retry_state(3) == "failed"
""",
            "packages/event-sdk/docs/development/specifications/event-lifecycle/index.md": """# Event lifecycle

- [Technical specification](technical-spec.md)
- [Requirements](requirements.md)
""",
            "packages/event-sdk/docs/development/specifications/event-lifecycle/technical-spec.md": """# Technical specification

Implemented target: transient delivery failures move through retrying and then
failed after the configured attempt limit.

Target-only behavior: a future `replay_failed()` API may replay persisted
failed events. It is not implemented.
""",
            "packages/event-sdk/docs/development/specifications/event-lifecycle/requirements.md": """# Requirements

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| EVENT-001 | Transient failures retry to the configured limit. | Implemented | Automated | Partial | `src/events.py`; `tests/test_events.py` |
| EVENT-002 | Failed events can be replayed. | Not started | Unverified | Pending | Target only |
""",
        },
    )


def _fixture_batch_sync(workspace: Path, branch_variant: str) -> None:
    files = {
        "packages/batch-sdk/README.md": """# batch-sdk

Submits online batches through the shared transport contract.
""",
        "packages/batch-sdk/src/batch.py": """def submit_batch(items):
    return {"submitted": len(items)}
""",
        "packages/batch-sdk/docs/development/index.md": """# Batch SDK development

No offline synchronization specification exists.
""",
        "packages/transport-contract/docs/development/specifications/transport/index.md": """# Transport contract

Defines request delivery, retryable transport errors, and idempotency keys.
""",
        "packages/persistence-contract/docs/development/specifications/persistence/index.md": """# Persistence contract

Defines durable record encoding, schema migration, and recovery boundaries.
""",
    }
    if branch_variant == "approved-task":
        files["tasks/batch-offline-sync.md"] = """# Batch offline synchronization

Status: Approved

## Requirements checklist

- [ ] Create a substantial package-owned offline synchronization specification.
- [ ] Include conflict resolution, persisted queue migration, compatibility,
  and recovery.
- [ ] Link transport and persistence contracts without copying them.
- [ ] Add stable requirements beginning not implemented and unverified.

Specification and requirements are authorized. Do not implement the protocol.
"""
    elif branch_variant != "base":
        raise KeyError(f"unknown batch-sync variant: {branch_variant}")
    _write_synthetic_fixture(workspace, files)


def _fixture_path_policy(workspace: Path, branch_variant: str) -> None:
    if branch_variant != "base":
        raise KeyError(f"unknown path-policy variant: {branch_variant}")
    _write_synthetic_fixture(
        workspace,
        {
            "packages/path-policy/README.md": """# path-policy

`normalize_path("~/file", home=...)` resolves against the supplied home.
""",
            "packages/path-policy/src/path_policy.py": """from pathlib import Path


def normalize_path(value, *, home, cwd):
    if value.startswith("~/"):
        return str(Path(cwd) / value[2:])
    return str(Path(cwd) / value)
""",
            "packages/path-policy/tests/test_path_policy.py": """from packages.path_policy.src.path_policy import normalize_path


def test_relative_path_uses_cwd():
    assert normalize_path("file", home="/home/a", cwd="/work") == "/work/file"
""",
            "packages/path-policy/docs/development/specifications/path-normalization/index.md": """# Path normalization

- [Technical specification](technical-spec.md)
- [Requirements](requirements.md)
""",
            "packages/path-policy/docs/development/specifications/path-normalization/technical-spec.md": """# Technical specification

Home-relative paths beginning `~/` resolve against the supplied user home.
Ordinary relative paths resolve against the current working directory.
""",
            "packages/path-policy/docs/development/specifications/path-normalization/requirements.md": """# Requirements

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| PATH-001 | `~/` resolves against user home. | Implemented | Unverified | Documented | `README.md`; regression missing |
""",
            "tasks/path-policy-home-relative-bug.md": """# Home-relative path bug

Status: Approved

`normalize_path("~/file", home="/home/a", cwd="/work")` incorrectly returns
`/work/file`. Fix the implementation, add regression coverage, and update live
evidence. The existing target specification is correct.
""",
        },
    )


def _fixture_slug_utils(workspace: Path, branch_variant: str) -> None:
    if branch_variant != "base":
        raise KeyError(f"unknown slug-utils variant: {branch_variant}")
    _write_synthetic_fixture(
        workspace,
        {
            "packages/slug-utils/README.md": """# slug-utils

Internal slug and cache helpers.
""",
            "packages/slug-utils/src/slug_cache.py": """def remove_expired(paths, *, unlink):
    for path in paths:
        unlink(path)
""",
            "packages/slug-utils/tests/test_slug_cache.py": """from packages.slug_utils.src.slug_cache import remove_expired


def test_remove_expired_deletes_paths():
    deleted = []
    remove_expired(["a"], unlink=deleted.append)
    assert deleted == ["a"]
""",
        },
    )


def _fixture_label_utils(workspace: Path, branch_variant: str) -> None:
    if branch_variant != "base":
        raise KeyError(f"unknown label-utils variant: {branch_variant}")
    _write_synthetic_fixture(
        workspace,
        {
            "packages/label-utils/README.md": """# label-utils

`normalize_label(value)` preserves surrounding whitespace.
""",
            "packages/label-utils/src/labels.py": """def normalize_label(value):
    return value
""",
            "packages/label-utils/tests/test_labels.py": """from packages.label_utils.src.labels import normalize_label


def test_normalize_label_preserves_value():
    assert normalize_label("  name  ") == "  name  "
""",
            "packages/label-utils/docs/development/index.md": """# Label development

- [Label normalization](specifications/label-normalization/index.md)
""",
            "packages/label-utils/docs/development/specifications/label-normalization/index.md": """# Label normalization

- [Technical specification](technical-spec.md)
- [Requirements](requirements.md)
""",
            "packages/label-utils/docs/development/specifications/label-normalization/technical-spec.md": """# Technical specification

`normalize_label(value, trim_whitespace=False)` preserves whitespace by
default. When enabled, `trim_whitespace=True` strips leading and trailing
whitespace.
""",
            "packages/label-utils/docs/development/specifications/label-normalization/requirements.md": """# Requirements

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| LABEL-001 | Optional whitespace trimming is supported. | Not started | Unverified | Pending | Target specification |
""",
        },
    )


def _fixture_sync_engine(workspace: Path, branch_variant: str) -> None:
    if branch_variant != "base":
        raise KeyError(f"unknown sync-engine variant: {branch_variant}")
    _write_synthetic_fixture(
        workspace,
        {
            "packages/sync-engine/README.md": """# sync-engine

Sync v2 currently supports Phase 1 local change capture.
""",
            "packages/sync-engine/src/sync.py": """def capture_local(change):
    return {"captured": change}
""",
            "packages/sync-engine/tests/test_sync.py": """from packages.sync_engine.src.sync import capture_local


def test_capture_local():
    assert capture_local("x") == {"captured": "x"}
""",
            "packages/sync-engine/docs/development/specifications/sync-v2/index.md": """# Sync v2

## Temporary progress

Active task: `tasks/sync-v2.md`

- `SYNC-001`: verified
- `SYNC-002`: approved next phase
- `SYNC-003`: later target

- [Product specification](product-spec.md)
- [Technical specification](technical-spec.md)
- [Requirements](requirements.md)
""",
            "packages/sync-engine/docs/development/specifications/sync-v2/product-spec.md": """# Product specification

Phase 1 captures local changes. Phase 2 uploads queued changes with stable
idempotency keys. Phase 3 resolves concurrent remote conflicts.
""",
            "packages/sync-engine/docs/development/specifications/sync-v2/technical-spec.md": """# Technical specification

Phase 2 adds `queue_upload(change, idempotency_key)` and rejects empty keys.
Phase 3 conflict resolution remains target-only.
""",
            "packages/sync-engine/docs/development/specifications/sync-v2/requirements.md": """# Requirements

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| SYNC-001 | Capture local changes. | Implemented | Automated | Documented | Phase 1 |
| SYNC-002 | Queue uploads with idempotency keys. | Not started | Unverified | Pending | Phase 2 |
| SYNC-003 | Resolve concurrent conflicts. | Not started | Unverified | Pending | Phase 3 |
""",
            "tasks/sync-v2.md": """# Sync v2

Status: Approved

Phase 1 is complete. Implement and verify Phase 2 in the next commit. Leave
Phase 3 pending and keep temporary progress until all phases are verified.
""",
        },
    )


def _write_synthetic_fixture(
    workspace: Path,
    files: Mapping[str, str],
) -> None:
    for path in workspace.iterdir():
        if path.name == ".git":
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    neutral_agents = """# Evaluation fixture

This is a small repository fixture. Inspect the files named by the task and
report or implement only the requested scope.
"""
    values = {"AGENTS.md": neutral_agents, **dict(files)}
    for relative, content in values.items():
        target = workspace / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content.rstrip() + "\n", encoding="utf-8")


def _focus_js_single_file_tool_workspace(workspace: Path) -> None:
    keep_root = {".git", "AGENTS.md", "LICENSE", "README.md", "plugins"}
    for path in workspace.iterdir():
        if path.name in keep_root:
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

    plugins = workspace / "plugins"
    keep_plugins = {"AGENTS.md", "docs", "js-single-file-tool"}
    for path in plugins.iterdir():
        if path.name in keep_plugins:
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

    docs = plugins / "docs"
    keep_docs = {
        "AGENTS.md",
        "index.md",
        "node-tool-plugins.md",
        "plugin-packaging-and-loading.md",
        "testing-and-validation.md",
        "tool-interop.md",
        "tool-plugins.md",
    }
    for path in docs.iterdir():
        if path.name in keep_docs:
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def _commit_fixture(workspace: Path) -> None:
    status = _git(workspace, "status", "--short", "--untracked-files=all")
    if not status.strip():
        return
    _git(workspace, "config", "user.name", "Agent Evaluation")
    _git(workspace, "config", "user.email", "agent-eval@example.invalid")
    _git(workspace, "add", "-A")
    env = {
        **os.environ,
        "GIT_AUTHOR_DATE": "2026-08-08T00:00:00+00:00",
        "GIT_COMMITTER_DATE": "2026-08-08T00:00:00+00:00",
    }
    subprocess.run(
        ["git", "commit", "-m", "Prepare documentation evaluation fixture"],
        cwd=workspace,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def _copy_workspace_contents(source: Path, target: Path) -> None:
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        if relative.parts and relative.parts[0] == ".git":
            continue
        destination = target / relative
        if path.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)


def _workspace_content_sha256(workspace: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(workspace.rglob("*")):
        relative = path.relative_to(workspace)
        if relative.parts and relative.parts[0] == ".git":
            continue
        if path.is_file():
            digest.update(relative.as_posix().encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()


def _git(workspace: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _requirement_ids(path: Path) -> tuple[str, ...]:
    text = path.read_text(encoding="utf-8")
    return tuple(sorted(set(re.findall(r"DOCGEN-\d{3}|DOCREP-\d{3}", text))))