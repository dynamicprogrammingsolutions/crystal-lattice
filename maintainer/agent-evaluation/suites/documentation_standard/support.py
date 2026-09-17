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
from typing import Any, Iterator, Mapping, cast

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
BASELINE_GUIDANCE_REVISION = "3a62b6fc"
ORIGINAL_DEVELOP_GUIDANCE_REVISION = "f81f36326b58268297ba59c1cacbcda604257c27"
FOLLOWUP_BASELINE_GUIDANCE_REVISION = (
    "cdeb50a7df92820e487c466b030ea8f5f6dcb993"
)
GUIDANCE_INJECTION_VERSION = "v6"
PROFILE_CONFIG_VERSION = "v8"
DEFAULT_CONFIG = Path.home() / ".crystal" / "config.json"
PLUGIN_RUNTIME_CONSTRAINTS = PACKAGE_ROOT / "constraints" / "plugin-runtime.txt"
FIXTURE_REVISIONS = {
    "js-single-file-tool": "v4",
    "report-export": "v3",
    "mobile-composer": "v1",
    "event-retry": "v5",
    "batch-sync": "v2",
    "path-policy": "v3",
    "slug-utils": "v3",
    "label-utils": "v3",
    "sync-engine": "v3",
    "requirement-scope": "v1",
    "testing-strategy": "v1",
    "requirement-quality-batch": "v1",
    "requirement-quality-timeout": "v1",
    "requirement-quality-output": "v1",
    "requirement-quality-eleventy": "v1",
    "requirement-quality-fastapi": "v1",
    "requirement-quality-flask-vue": "v1",
    "requirement-quality-judge": "v1",
}
SYNTHETIC_SRC_CONFTEST = """import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
"""

LEGACY_GUIDANCE_PATHS = (
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

CURRENT_GUIDANCE_PATHS = (
    "AGENTS.md",
    "docs/development/index.md",
    "docs/development/documentation.md",
    "docs/development/crystal-lattice-documentation.md",
    "plugins/AGENTS.md",
    "plugins/docs/AGENTS.md",
)

CANDIDATE_GUIDANCE_PATHS = CURRENT_GUIDANCE_PATHS


@dataclass(frozen=True)
class ModelProfile:
    name: str
    agent_id: str
    model: str
    hosted: bool
    auth_mode: str | None = None
    plugin_fragments: tuple[str, ...] = ()

    def request_overrides(
        self,
        workspace: Path,
        *,
        reasoning_effort: str | None = None,
    ) -> dict[str, object]:
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
            overrides["request_options"] = {
                "reasoning_effort": reasoning_effort or "high"
            }
        elif reasoning_effort is not None:
            overrides["reasoning_effort"] = reasoning_effort
        if self.auth_mode is not None:
            overrides["auth_mode"] = self.auth_mode
        return overrides


PROFILES = {
    "glm": ModelProfile(
        name="glm",
        agent_id="glm-ollama",
        model="glm-5.3-flash:cloud",
        hosted=False,
        plugin_fragments=(
            "/codex-tools",
            "/feature-request-options",
            "/feature-system-message",
            "/reference-openai-compatible-provider",
        ),
    ),
    "gpt": ModelProfile(
        name="gpt",
        agent_id="codex-openai",
        model="gpt-5.6-luna",
        hosted=True,
        auth_mode="chatgpt",
        plugin_fragments=(
            "/codex-tools",
            "/feature-request-options",
            "/feature-system-message",
            "/openai_responses",
            "/chatgpt-auth-app",
        ),
    ),
}

EVALUATION_TOOL_PLUGINS = (
    "plugins.file_reader_tool.FileReaderTool",
    "plugins.file_writer_tool.FileWriterTool",
    "codex_tools.shell_tool.ShellArrayTool",
)
GUIDANCE_FEATURE_PLUGIN = (
    "suites.documentation_standard.guidance_feature."
    "DocumentationStandardGuidanceFeature"
)
GUIDANCE_CONFIG_KEY = "_documentation_standard_guidance"


@dataclass(frozen=True)
class GuidanceFile:
    path: str
    sha256: str


@dataclass(frozen=True)
class GuidanceSource:
    name: str
    root: Path = REPOSITORY_ROOT
    revision: str | None = None
    paths: tuple[str, ...] = CURRENT_GUIDANCE_PATHS
    content_overrides: tuple[tuple[str, bytes], ...] = ()

    def read_bytes(self, relative: str) -> bytes:
        for path, content in self.content_overrides:
            if path == relative:
                return content
        if self.revision is None:
            return self.root.joinpath(relative).read_bytes()
        result = subprocess.run(
            ["git", "show", f"{self.revision}:{relative}"],
            cwd=self.root,
            check=False,
            capture_output=True,
        )
        if result.returncode != 0:
            message = result.stderr.decode("utf-8", errors="replace").strip()
            raise ValueError(
                f"cannot read guidance {relative!r} from {self.revision}: {message}"
            )
        return result.stdout

    def files(self) -> tuple[GuidanceFile, ...]:
        return tuple(
            GuidanceFile(
                path=relative,
                sha256=hashlib.sha256(self.read_bytes(relative)).hexdigest(),
            )
            for relative in self.paths
        )

    def sha256(self) -> str:
        payload = json.dumps(
            [item.__dict__ for item in self.files()],
            sort_keys=True,
            separators=(",", ":"),
        )
        return _sha256_text(payload)

    def copy_to(self, workspace: Path) -> None:
        for relative in self.paths:
            target = workspace / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(self.read_bytes(relative))

    def metadata(self) -> dict[str, object]:
        return {
            "name": self.name,
            "revision": self.revision,
            "sha256": self.sha256(),
            "files": [item.__dict__ for item in self.files()],
            "content_override_paths": [
                path for path, _ in self.content_overrides
            ],
            "injection_version": GUIDANCE_INJECTION_VERSION,
        }

    def context_message(
        self,
        paths: tuple[str, ...] | None = None,
    ) -> str:
        selected_paths = paths or self.paths
        lines = [
            "Repository guidance for the next task follows.",
            "Treat it as project instructions, not as the task itself.",
            "Each section is the exact content of the named repository file.",
        ]
        for relative in selected_paths:
            if relative not in self.paths:
                raise ValueError(f"unsupported guidance instruction path: {relative}")
            content = self.read_bytes(relative).decode("utf-8")
            lines.extend(
                (
                    "",
                    f'<repository-guidance path="{relative}">',
                    content,
                    "</repository-guidance>",
                )
            )
        return "\n".join(lines)


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
    guidance_name: str | None = None
    guidance_revision: str | None = None
    guidance_sha256: str | None = None
    guidance_injected: bool = False


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
    guidance: GuidanceSource | None = None

    def fingerprint(self) -> object:
        guidance = self._guidance()
        return {
            "type": "documentation-standard-scenario",
            "fixture_id": self.fixture_id,
            "fixture_revision": fixture_revision(self.fixture_id),
            "candidate_guidance": self.candidate_guidance,
            "guidance_name": guidance.name if guidance is not None else None,
            "guidance_revision": guidance.revision if guidance is not None else None,
            "guidance_sha256": guidance.sha256() if guidance is not None else None,
            "branch_variant": self.branch_variant,
            "revision": self.revision,
        }

    def __call__(self, staging_dir: Path) -> Path:
        base = self._base()
        workspace = base(staging_dir)
        apply_fixture(workspace, self.fixture_id, self.branch_variant)
        guidance = self._guidance()
        if guidance is not None:
            guidance.copy_to(workspace)
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

    def _guidance(self) -> GuidanceSource | None:
        if not self.candidate_guidance:
            return None
        return self.guidance or candidate_guidance_source()


@dataclass(frozen=True)
class ParentWorkspaceFactory:
    parent_workspace: Path
    fixture_id: str
    branch_variant: str
    guidance: GuidanceSource

    def fingerprint(self) -> object:
        return {
            "type": "documentation-standard-parent-fork",
            "parent": _workspace_content_sha256(self.parent_workspace),
            "fixture_id": self.fixture_id,
            "fixture_revision": fixture_revision(self.fixture_id),
            "branch_variant": self.branch_variant,
            "guidance_name": self.guidance.name,
            "guidance_revision": self.guidance.revision,
            "guidance_sha256": self.guidance.sha256(),
        }

    def __call__(self, staging_dir: Path) -> Path:
        base = ScenarioWorkspaceFactory(
            fixture_id=self.fixture_id,
            candidate_guidance=False,
            branch_variant="base",
        )
        workspace = base(staging_dir)
        _copy_workspace_contents(self.parent_workspace, workspace)
        self.guidance.copy_to(workspace)
        _commit_fixture(workspace)
        return workspace

    def cleanup(self, workspace: Path) -> None:
        ScenarioWorkspaceFactory(
            fixture_id=self.fixture_id,
            candidate_guidance=False,
        ).cleanup(workspace)


class DocumentationEvaluationHarness:
    def __init__(
        self,
        profile: ModelProfile,
        *,
        guidance: GuidanceSource | None = None,
    ) -> None:
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
        projected_config = _project_config_for_profile(
            config_path,
            artifact_root=artifact_root,
            profile=profile,
        )
        environment = WorkspaceAwareEnvironment.from_config(
            projected_config,
            environment={
                "CONFIG_DIR": str(config_path.parent),
                "CHATGPT_TEST_STATE_DIR": str(config_path.parent),
                "BUILTIN_PLUGINS": str(REPOSITORY_ROOT / "plugins"),
                "PIP_CONSTRAINT": str(PLUGIN_RUNTIME_CONSTRAINTS),
                "OLLAMA_OPENAI_BASE_URL": os.getenv(
                    "OLLAMA_OPENAI_BASE_URL",
                    "http://localhost:11434/v1",
                ),
            },
        )
        self.profile = profile
        self.guidance = guidance or selected_guidance_source()
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
        strategy_version = f"profile-{PROFILE_CONFIG_VERSION}"
        run = self.evaluation.run(
            seed_id,
            lambda context: self._turn(context, prompt, guidance=None),
            workspace=workspace,
            cache_key=(
                f"documentation-standard:{self.profile.name}:{seed_id}:"
                f"{_sha256_text(prompt)}:{fixture_revision(fixture_id)}:"
                f"{strategy_version}"
            ),
        )
        self._runs[key] = run
        return run

    def fresh_scenario(
        self,
        *,
        test_id: str,
        spec_file: str,
        fixture_id: str,
        reasoning_effort: str,
        cache_variant: str,
        prompt_heading: str = "## Exact user prompt",
        guidance_instruction_paths: tuple[str, ...] | None = None,
    ) -> Run[TurnValue]:
        instruction_paths = guidance_instruction_paths or self.guidance.paths
        key = (
            f"fresh:{test_id}:{reasoning_effort}:{cache_variant}:"
            f"{prompt_heading}:{_sha256_text(json.dumps(instruction_paths))}"
        )
        if key in self._runs:
            return self._runs[key]
        prompt = extract_blockquote(SPEC_ROOT / spec_file, prompt_heading)
        workspace = ScenarioWorkspaceFactory(
            fixture_id=fixture_id,
            candidate_guidance=True,
            guidance=self.guidance,
        )
        cache_key = (
            f"documentation-standard:{self.profile.name}:{test_id}:"
            f"{self.guidance.name}:{self.guidance.sha256()}:"
            f"{_sha256_text(prompt)}:{fixture_revision(fixture_id)}:"
            f"{GUIDANCE_INJECTION_VERSION}:{PROFILE_CONFIG_VERSION}:"
            f"{_sha256_text(json.dumps(instruction_paths))}:"
            f"{reasoning_effort}:{cache_variant}"
        )
        run = self.evaluation.run(
            test_id,
            lambda context: self._turn(
                context,
                prompt,
                guidance=self.guidance,
                inject_guidance=True,
                guidance_instruction_paths=instruction_paths,
                reasoning_effort=reasoning_effort,
            ),
            workspace=workspace,
            cache_key=cache_key,
        )
        self._runs[key] = run
        return run

    def fresh_prompt(
        self,
        *,
        test_id: str,
        prompt: str,
        reasoning_effort: str,
        cache_variant: str,
        fixture_id: str = "requirement-quality-judge",
    ) -> Run[TurnValue]:
        key = (
            f"fresh-prompt:{test_id}:{reasoning_effort}:{cache_variant}:"
            f"{_sha256_text(prompt)}"
        )
        if key in self._runs:
            return self._runs[key]
        workspace = ScenarioWorkspaceFactory(
            fixture_id=fixture_id,
            candidate_guidance=False,
        )
        cache_key = (
            f"documentation-standard:{self.profile.name}:{test_id}:"
            f"{_sha256_text(prompt)}:{fixture_revision(fixture_id)}:"
            f"{PROFILE_CONFIG_VERSION}:{reasoning_effort}:{cache_variant}"
        )
        run = self.evaluation.run(
            test_id,
            lambda context: self._turn(
                context,
                prompt,
                guidance=None,
                inject_guidance=False,
                reasoning_effort=reasoning_effort,
            ),
            workspace=workspace,
            cache_key=cache_key,
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
        guidance_instruction_paths: tuple[str, ...] | None = None,
        reasoning_effort: str | None = None,
    ) -> Run[TurnValue]:
        effort_key = reasoning_effort or "default"
        key = f"branch:{test_id}:{branch_variant}:{effort_key}"
        if key in self._runs:
            return self._runs[key]
        prompt = extract_blockquote(SPEC_ROOT / spec_file, prompt_heading)
        cache_variant = os.getenv("AGENT_EVAL_BRANCH_CACHE_VARIANT", "").strip()
        workspace = ScenarioWorkspaceFactory(
            fixture_id=fixture_id,
            candidate_guidance=True,
            branch_variant=branch_variant,
            guidance=self.guidance,
        )
        cache_key = None
        if cache:
            cache_variant_suffix = f":{cache_variant}" if cache_variant else ""
            instruction_paths = (
                guidance_instruction_paths or self.guidance.paths
            )
            cache_key = (
                f"documentation-standard:{self.profile.name}:{test_id}:"
                f"{self.guidance.name}:{self.guidance.sha256()}:"
                f"{_sha256_text(prompt)}:"
                f"{branch_variant}:{fixture_revision(fixture_id)}:"
                f"{GUIDANCE_INJECTION_VERSION}:{PROFILE_CONFIG_VERSION}:"
                f"{_sha256_text(json.dumps(instruction_paths))}:"
                f"{effort_key}"
                f"{cache_variant_suffix}"
            )
        run = self.evaluation.run(
            test_id,
            lambda context: self._turn(
                context,
                prompt,
                guidance=self.guidance,
                inject_guidance=True,
                guidance_instruction_paths=guidance_instruction_paths,
                reasoning_effort=reasoning_effort,
            ),
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
            guidance=self.guidance,
        )
        run = self.evaluation.run(
            test_id,
            lambda context: self._turn(
                context,
                prompt,
                guidance=self.guidance,
                inject_guidance=False,
            ),
            continue_from=parent,
            workspace=workspace,
            cache_key=(
                f"documentation-standard:{self.profile.name}:{test_id}:"
                f"{parent.snapshot_sha256}:{self.guidance.name}:"
                f"{self.guidance.sha256()}:"
                f"{_sha256_text(prompt)}:{fixture_revision(fixture_id)}:"
                f"{GUIDANCE_INJECTION_VERSION}:{PROFILE_CONFIG_VERSION}"
            ),
        )
        self._runs[key] = run
        return run

    def _turn(
        self,
        context: CrystalLatticeContext,
        prompt: str,
        *,
        guidance: GuidanceSource | None,
        inject_guidance: bool = False,
        guidance_instruction_paths: tuple[str, ...] | None = None,
        reasoning_effort: str | None = None,
    ) -> TurnValue:
        if context.workspace is None:
            raise ValueError("missing evaluation workspace")
        if context.session_or_none is None:
            context.start(self.profile.agent_id)
        context.config.update(
            self.profile.request_overrides(
                context.workspace,
                reasoning_effort=reasoning_effort,
            )
        )
        context.services.record(
            "documentation_standard.profile",
            {
                "name": self.profile.name,
                "agent_id": self.profile.agent_id,
                "model": self.profile.model,
                "hosted": self.profile.hosted,
                "auth_mode": self.profile.auth_mode,
                "reasoning_effort": reasoning_effort or (
                    "high" if self.profile.name == "glm" else None
                ),
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
            guidance.metadata() if guidance is not None else None,
        )
        injected_paths = (
            guidance_instruction_paths or guidance.paths
            if guidance is not None and inject_guidance
            else ()
        )
        if guidance is not None and inject_guidance:
            guidance_message = guidance.context_message(injected_paths)
            if self.profile.auth_mode == "chatgpt":
                context.config[GUIDANCE_CONFIG_KEY] = guidance_message
                injection_strategy = "late_feature_endpoint_instructions"
                injection_role = "instructions"
                injection_position: int | str = "post_compilation"
            else:
                effective_config = context.effective_config()
                session = context.core.add_message(
                    context.session,
                    "system",
                    guidance_message,
                    None,
                    cast(dict[str, Any], effective_config),
                    after_index=-1,
                )
                session = context.application.save_session(session)
                context.replace_runtime(
                    core=context.core,
                    base_config=context.base_config,
                    session=session,
                )
                injection_strategy = "leading_message"
                injection_role = "system"
                injection_position = 0
        else:
            injection_strategy = None
            injection_role = None
            injection_position = None
        context.services.record(
            "documentation_standard.guidance_injection",
            {
                "injected": guidance is not None and inject_guidance,
                "version": GUIDANCE_INJECTION_VERSION,
                "strategy": injection_strategy,
                "role": injection_role,
                "position": injection_position,
                "paths": list(injected_paths),
            },
        )
        context.services.record(
            "documentation_standard.branch_cache_variant",
            os.getenv("AGENT_EVAL_BRANCH_CACHE_VARIANT", "").strip() or "default",
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
            guidance_name=guidance.name if guidance is not None else None,
            guidance_revision=guidance.revision if guidance is not None else None,
            guidance_sha256=guidance.sha256() if guidance is not None else None,
            guidance_injected=guidance is not None and inject_guidance,
        )


def selected_profile() -> ModelProfile:
    name = os.getenv("AGENT_EVAL_PROFILE", "").strip().lower()
    if name not in PROFILES:
        raise ValueError(
            "AGENT_EVAL_PROFILE must be one of: " + ", ".join(sorted(PROFILES))
        )
    return PROFILES[name]


def candidate_guidance_source() -> GuidanceSource:
    return GuidanceSource(name="candidate", paths=CURRENT_GUIDANCE_PATHS)


def baseline_guidance_source() -> GuidanceSource:
    return GuidanceSource(
        name="baseline",
        revision=BASELINE_GUIDANCE_REVISION,
        paths=LEGACY_GUIDANCE_PATHS,
    )


def original_develop_guidance_source() -> GuidanceSource:
    return GuidanceSource(
        name="develop",
        revision=ORIGINAL_DEVELOP_GUIDANCE_REVISION,
        paths=LEGACY_GUIDANCE_PATHS,
    )


def followup_baseline_guidance_source() -> GuidanceSource:
    return GuidanceSource(
        name="followup-baseline",
        revision=FOLLOWUP_BASELINE_GUIDANCE_REVISION,
        paths=CURRENT_GUIDANCE_PATHS,
    )


def selected_guidance_source() -> GuidanceSource:
    name = os.getenv("AGENT_EVAL_GUIDANCE_VARIANT", "candidate").strip()
    if name == "candidate":
        return candidate_guidance_source()
    if name == "baseline":
        return baseline_guidance_source()
    if name == "develop":
        return original_develop_guidance_source()
    if name == "followup-baseline":
        return followup_baseline_guidance_source()
    raw_root = os.getenv("AGENT_EVAL_GUIDANCE_DIR")
    if not raw_root:
        raise ValueError(
            "custom AGENT_EVAL_GUIDANCE_VARIANT requires AGENT_EVAL_GUIDANCE_DIR"
        )
    root = Path(raw_root).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"guidance directory missing: {root}")
    return GuidanceSource(name=name, root=root)


def enforce_real_model_gate(profile: ModelProfile) -> None:
    if os.getenv("AGENT_EVAL_RUN_REAL") != "1":
        raise RuntimeError("set AGENT_EVAL_RUN_REAL=1 to execute real-model tests")
    if profile.hosted and os.getenv("AGENT_EVAL_ALLOW_HOSTED") != "1":
        raise RuntimeError(
            "set AGENT_EVAL_ALLOW_HOSTED=1 to execute hosted ChatGPT tests"
        )
    if profile.name == "glm":
        result = subprocess.run(
            ["ollama", "show", profile.model],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise RuntimeError(
                f"Ollama cannot resolve configured model {profile.model!r}: {detail}"
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
    return candidate_guidance_source().files()


def candidate_guidance_sha256() -> str:
    return candidate_guidance_source().sha256()


def copy_candidate_guidance(workspace: Path) -> None:
    candidate_guidance_source().copy_to(workspace)


def record_review(
    run: Run[TurnValue],
    *,
    spec_file: str,
    findings: tuple[AssertionFinding, ...],
) -> None:
    spec_path = SPEC_ROOT / spec_file
    human_questions = extract_section(spec_path, "## Human review")
    value = run.value
    prompt = value.prompt if value is not None else "(Run failed before prompt execution.)"
    response = value.response if value is not None else "(No assistant response.)"
    guidance_name = value.guidance_name if value is not None else None
    guidance_revision = value.guidance_revision if value is not None else None
    guidance_sha256 = value.guidance_sha256 if value is not None else None
    guidance_injected = value.guidance_injected if value is not None else False
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
        f"- Guidance variant: `{guidance_name or 'none'}`",
        f"- Guidance revision: `{guidance_revision or 'working-tree'}`",
        f"- Guidance SHA-256: `{guidance_sha256 or 'none'}`",
        f"- Guidance injected: `{guidance_injected}`",
        "",
        "## Prompt",
        "",
        prompt,
        "",
        "## Response",
        "",
        response or "(No assistant response.)",
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
            "prompt": prompt,
            "response": response,
            "changed_paths": run.changed_paths,
            "findings": [finding.__dict__ for finding in findings],
            "guidance": {
                "name": guidance_name,
                "revision": guidance_revision,
                "sha256": guidance_sha256,
                "injected": guidance_injected,
            },
        },
    )


def assert_findings(findings: tuple[AssertionFinding, ...]) -> None:
    failures = [finding for finding in findings if not finding.passed]
    if failures:
        rendered = "\n".join(f"- {item.name}: {item.detail}" for item in failures)
        raise AssertionError(f"documentation-standard findings failed:\n{rendered}")


def basic_run_findings(run: Run[TurnValue]) -> tuple[AssertionFinding, ...]:
    if run.value is None:
        error = run.error
        detail = (
            f"{error.phase}: {error.type}: {error.message}"
            if error is not None
            else "run produced no value and no structured error"
        )
        return (
            AssertionFinding("run completed", False, detail),
            AssertionFinding("assistant response", False, "run produced no value"),
            AssertionFinding("provider errors", False, detail),
        )
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


def require_run_value(run: Run[TurnValue]) -> TurnValue:
    if run.value is not None:
        return run.value
    error = run.error
    if error is None:
        raise AssertionError("evaluation run produced no value and no structured error")
    raise AssertionError(
        "evaluation setup failed before scenario assertions: "
        f"{error.phase}: {error.type}: {error.message}"
    )


def _project_config_for_profile(
    source: Path,
    *,
    artifact_root: Path,
    profile: ModelProfile,
) -> Path:
    raw = json.loads(source.read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"Crystal Lattice config must contain an object: {source}")
    agents = raw.get("agents")
    if not isinstance(agents, dict):
        raise ValueError(f"Crystal Lattice config has no agents mapping: {source}")
    selected = agents.get(profile.agent_id)
    if not isinstance(selected, dict):
        raise KeyError(
            f"Crystal Lattice config has no selected agent {profile.agent_id!r}: "
            f"{source}"
        )
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    plugins = raw.get("plugins")
    if not isinstance(plugins, list):
        raise ValueError(f"Crystal Lattice config has no plugins list: {source}")
    selected_plugins = [
        item
        for item in plugins
        if (
            isinstance(item, str)
            and (
                not item.startswith(("path:", "bash:", "node:"))
                or any(fragment in item for fragment in profile.plugin_fragments)
            )
        )
    ]
    for agent in agents.values():
        if not isinstance(agent, dict):
            continue
        agent_plugins = agent.get("plugins")
        if not isinstance(agent_plugins, list):
            continue
        for item in agent_plugins:
            if (
                isinstance(item, str)
                and item.startswith(("path:", "bash:", "node:"))
                and any(fragment in item for fragment in profile.plugin_fragments)
                and item not in selected_plugins
            ):
                selected_plugins.append(item)
    missing_fragments = [
        fragment
        for fragment in profile.plugin_fragments
        if not any(
            isinstance(item, str) and fragment in item for item in selected_plugins
        )
    ]
    if missing_fragments:
        raise ValueError(
            f"Crystal Lattice config is missing profile plugins "
            f"{missing_fragments!r}: {source}"
        )
    projected_agent = {
        **selected,
        "shell_tool_mode": "shell",
        "plugins": [GUIDANCE_FEATURE_PLUGIN, *EVALUATION_TOOL_PLUGINS],
    }
    projection = {
        **raw,
        "agents": {profile.agent_id: projected_agent},
        "plugins": selected_plugins,
        "plugin_cache_dir": str(
            artifact_root
            / "plugin-cache"
            / profile.name
            / f"{source_sha[:16]}-{PROFILE_CONFIG_VERSION}"
        ),
    }
    config_root = artifact_root / "config"
    config_root.mkdir(parents=True, exist_ok=True)
    target = (
        config_root
        / f"{profile.name}-{source_sha[:16]}-{PROFILE_CONFIG_VERSION}.json"
    )
    rendered = json.dumps(projection, indent=2, sort_keys=True) + "\n"
    if not target.exists() or target.read_text() != rendered:
        target.write_text(rendered)
    return target


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
    elif fixture_id == "requirement-scope":
        _fixture_requirement_scope(workspace, branch_variant)
    elif fixture_id == "testing-strategy":
        _fixture_testing_strategy(workspace, branch_variant)
    elif fixture_id == "requirement-quality-batch":
        _fixture_requirement_quality_batch(workspace, branch_variant)
    elif fixture_id == "requirement-quality-timeout":
        _fixture_requirement_quality_timeout(workspace, branch_variant)
    elif fixture_id == "requirement-quality-output":
        _fixture_requirement_quality_output(workspace, branch_variant)
    elif fixture_id == "requirement-quality-eleventy":
        _fixture_requirement_quality_eleventy(workspace, branch_variant)
    elif fixture_id == "requirement-quality-fastapi":
        _fixture_requirement_quality_fastapi(workspace, branch_variant)
    elif fixture_id == "requirement-quality-flask-vue":
        _fixture_requirement_quality_flask_vue(workspace, branch_variant)
    elif fixture_id == "requirement-quality-judge":
        _fixture_requirement_quality_judge(workspace, branch_variant)
    else:
        raise KeyError(f"unknown fixture: {fixture_id}")


def fixture_revision(fixture_id: str) -> str:
    try:
        return FIXTURE_REVISIONS[fixture_id]
    except KeyError as error:
        raise KeyError(f"unknown fixture: {fixture_id}") from error


def _fixture_js_single_file_tool(workspace: Path, branch_variant: str) -> None:
    _focus_js_single_file_tool_workspace(workspace)
    readme = workspace / "plugins/js-single-file-tool/README.md"
    if "## Verify npm" not in readme.read_text(encoding="utf-8"):
        readme.write_text(
            readme.read_text(encoding="utf-8")
            + "\n## Verify npm\n\n```bash\nnpm --vesion\n```\n",
            encoding="utf-8",
        )
    if branch_variant in {"generated-typo", "generated-typo-failing-generator"}:
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
        if branch_variant == "generated-typo-failing-generator":
            generator = workspace / "docs_site/scripts/prepare_mkdocs_site.py"
            generator.parent.mkdir(parents=True, exist_ok=True)
            generator.write_text(
                "import sys\n\n"
                "print('missing dependency: mkdocs-material-extensions', "
                "file=sys.stderr)\n"
                "raise SystemExit(2)\n",
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
            ".gitignore": """__pycache__/
*.pyc
.pytest_cache/
""",
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
            "packages/report-export-sdk/tests/conftest.py": SYNTHETIC_SRC_CONFTEST,
            "packages/report-export-sdk/tests/test_report_export.py": """from report_export import export_rows


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
            ".gitignore": """__pycache__/
*.pyc
.pytest_cache/
""",
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


def publish(event):
    return {"status": "published", "event": event}
""",
            "packages/event-sdk/tests/conftest.py": SYNTHETIC_SRC_CONFTEST,
            "packages/event-sdk/tests/test_events.py": """from events import retry_state


def test_retry_state():
    assert retry_state(1) == "retrying"
    assert retry_state(3) == "failed"


def test_publish_returns_published_event():
    from events import publish

    assert publish({"type": "created"}) == {
        "status": "published",
        "event": {"type": "created"},
    }
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
    if branch_variant in {"approved-task", "approved-task-single-decisions"}:
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
        if branch_variant == "approved-task-single-decisions":
            files["tasks/batch-offline-sync.md"] += """
Record material decisions in one `decisions.md` file. Do not create a
`decisions/` directory or separate decision-record files.
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
            ".gitignore": """__pycache__/
*.pyc
.pytest_cache/
""",
            "packages/path-policy/README.md": """# path-policy

`normalize_path("~/file", home=...)` resolves against the supplied home.
""",
            "packages/path-policy/src/path_policy.py": """from pathlib import Path


def normalize_path(value, *, home, cwd):
    if value.startswith("~/"):
        return str(Path(cwd) / value[2:])
    return str(Path(cwd) / value)
""",
            "packages/path-policy/tests/conftest.py": SYNTHETIC_SRC_CONFTEST,
            "packages/path-policy/tests/test_path_policy.py": """from path_policy import normalize_path


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
            ".gitignore": """__pycache__/
*.pyc
.pytest_cache/
""",
            "packages/slug-utils/README.md": """# slug-utils

Internal slug and cache helpers.
""",
            "packages/slug-utils/src/slug_cache.py": """def remove_expired(paths, *, unlink):
    for path in paths:
        unlink(path)
""",
            "packages/slug-utils/tests/conftest.py": SYNTHETIC_SRC_CONFTEST,
            "packages/slug-utils/tests/test_slug_cache.py": """from slug_cache import remove_expired


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
            ".gitignore": """__pycache__/
*.pyc
.pytest_cache/
""",
            "packages/label-utils/README.md": """# label-utils

`normalize_label(value)` preserves surrounding whitespace.
""",
            "packages/label-utils/src/labels.py": """def normalize_label(value):
    return value
""",
            "packages/label-utils/tests/conftest.py": SYNTHETIC_SRC_CONFTEST,
            "packages/label-utils/tests/test_labels.py": """from labels import normalize_label


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
            ".gitignore": """__pycache__/
*.pyc
.pytest_cache/
""",
            "packages/sync-engine/README.md": """# sync-engine

Sync v2 currently supports Phase 1 local change capture.
""",
            "packages/sync-engine/src/sync.py": """def capture_local(change):
    return {"captured": change}
""",
            "packages/sync-engine/tests/conftest.py": SYNTHETIC_SRC_CONFTEST,
            "packages/sync-engine/tests/test_sync.py": """from sync import capture_local


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


def _fixture_requirement_scope(workspace: Path, branch_variant: str) -> None:
    if branch_variant != "base":
        raise KeyError(f"unknown requirement-scope variant: {branch_variant}")
    _write_synthetic_fixture(
        workspace,
        {
            "packages/offline-queue/README.md": """# offline-queue

`enqueue(item)` appends one item to the local in-memory queue.
""",
            "packages/offline-queue/src/queue.py": """class Queue:
    def __init__(self):
        self.items = []

    def enqueue(self, item):
        self.items.append(item)
""",
            "packages/offline-queue/docs/development/index.md": """# Offline queue development

No batch-enqueue specification exists.
""",
            "tasks/offline-queue-batch-enqueue.md": """# Offline queue batch enqueue

Status: Approved

## Required outcomes

- Add a target for `enqueue_batch(items, max_items=100)`.
- Preserve item order and existing single-item `enqueue` behavior.
- Reject an empty batch.
- Reject more than `max_items` before changing the queue.
- Create live requirements for the target.

Create the specification and requirements only. Do not implement the change.

## Ideas for possible later work

The following ideas are not approved by this task:

- encryption at rest;
- telemetry dashboards;
- adaptive compression;
- cloud replication.
""",
        },
    )


def _fixture_testing_strategy(workspace: Path, branch_variant: str) -> None:
    files = {
        "plugins/ui-options/README.md": """# ui-options

Provides capability-dependent configuration options.
""",
        "plugins/ui-options/src/options.py": """def advanced_option(capabilities):
    if "advanced" not in capabilities:
        return None
    return {
        "id": "advanced",
        "type": "toggle",
        "label": "Advanced",
        "visible": True,
        "_debug_origin": "ui-options",
        "_construction_order": 4,
    }
""",
        "plugins/ui-options/tests/test_options.py": """from options import advanced_option


def test_advanced_option_is_absent_without_capability():
    assert advanced_option(set()) is None
""",
        "plugins/ui-options/docs/development/specifications/option-visibility/index.md": """# Option visibility

The advanced option is absent when the `advanced` capability is unavailable.
When available, consumers receive an option identified as `advanced` with the
label `Advanced`.

The complete mapping, private metadata, key order, and helper-call structure
are not public or persisted interfaces.
""",
        "application/python/example_api/options.py": """from options import advanced_option


def get_options(capabilities):
    option = advanced_option(capabilities)
    return {"options": [] if option is None else [option]}
""",
        "packages/frontend-sdk/src/options.ts": """export function visibleOptions(
  payload: {options: Array<{id: string; label: string; visible?: boolean}>},
) {
  return payload.options.filter(option => option.visible !== false);
}
""",
        "docs/development/specifications/option-delivery/index.md": """# Option delivery

The public options endpoint returns capability-appropriate options. The
production frontend adapter presents the returned visible options without
provider- or plugin-specific types.
""",
    }
    if branch_variant == "local-option":
        files["tasks/ui-options-local-testing.md"] = """# Local option visibility testing

Status: Approved

Prepare the testing strategy for implementing the option-visibility target in
`plugins/ui-options`. Do not implement the change or edit test code.
"""
    elif branch_variant == "cross-layer":
        files["tasks/ui-options-delivery-testing.md"] = """# Option delivery testing

Status: Approved

Prepare the testing strategy for the existing cross-package option-delivery
target. It spans the plugin, public options endpoint, and production frontend
adapter. Do not implement the change or edit test code.
"""
    elif branch_variant != "base":
        raise KeyError(f"unknown testing-strategy variant: {branch_variant}")
    _write_synthetic_fixture(workspace, files)


def _fixture_requirement_quality_batch(
    workspace: Path,
    branch_variant: str,
) -> None:
    if branch_variant != "base":
        raise KeyError(
            f"unknown requirement-quality-batch variant: {branch_variant}"
        )
    _write_synthetic_fixture(
        workspace,
        {
            "packages/offline-queue/README.md": """# offline-queue

`Queue.enqueue(item)` appends one item to the local in-memory queue.
""",
            "packages/offline-queue/src/queue.py": """class Queue:
    def __init__(self):
        self.items = []

    def enqueue(self, item):
        self.items.append(item)
""",
            "packages/offline-queue/docs/development/index.md": """# Offline queue development

No batch-enqueue specification exists.
""",
        },
    )


def _fixture_requirement_quality_timeout(
    workspace: Path,
    branch_variant: str,
) -> None:
    if branch_variant != "base":
        raise KeyError(
            f"unknown requirement-quality-timeout variant: {branch_variant}"
        )
    _write_synthetic_fixture(
        workspace,
        {
            "packages/request-client/README.md": """# request-client

Create `Client(transport, timeout=30)` and call `fetch(url)`. The configured
timeout is used for every request.
""",
            "packages/request-client/src/client.py": """class Client:
    def __init__(self, transport, timeout=30):
        self.transport = transport
        self.timeout = timeout

    def fetch(self, url):
        return self.transport(url, timeout=self.timeout)
""",
            "packages/request-client/docs/development/index.md": """# Request client development

No per-request timeout specification exists.
""",
        },
    )


def _fixture_requirement_quality_output(
    workspace: Path,
    branch_variant: str,
) -> None:
    if branch_variant != "base":
        raise KeyError(
            f"unknown requirement-quality-output variant: {branch_variant}"
        )
    _write_synthetic_fixture(
        workspace,
        {
            "packages/report-cli/README.md": """# report-cli

Run `report-cli` to print the JSON report to standard output.
""",
            "packages/report-cli/src/report_cli.py": """import json


def render_report(rows):
    return json.dumps({"rows": rows}, indent=2, sort_keys=True)


def main(rows):
    print(render_report(rows))
    return 0
""",
            "packages/report-cli/docs/development/index.md": """# Report CLI development

No output-file specification exists.
""",
        },
    )


def _fixture_requirement_quality_eleventy(
    workspace: Path,
    branch_variant: str,
) -> None:
    if branch_variant != "base":
        raise KeyError(
            f"unknown requirement-quality-eleventy variant: {branch_variant}"
        )
    _write_synthetic_fixture(
        workspace,
        {
            "UPSTREAM.md": """# Upstream source

This compact evaluation fixture is adapted from Eleventy Base Blog.

- Repository: https://github.com/11ty/eleventy-base-blog
- Revision: 26b26106d7fbb30b7b40d9ef52589d10ddbcb462
- License: MIT
""",
            "README.md": """# Eleventy Base Blog

A performance-focused static blog starter. Production output is pre-rendered
and uses no client-side JavaScript.

The generated site includes a home page, complete blog archive, tag pages,
feed, sitemap, and previous/next links between individual posts.
""",
            "package.json": """{
  "name": "eleventy-base-blog",
  "version": "9.0.0",
  "type": "module",
  "scripts": {
    "build": "npx @11ty/eleventy",
    "benchmark": "cross-env DEBUG=Eleventy:Benchmark* npx @11ty/eleventy"
  }
}
""",
            "_includes/postslist.njk": """<ol reversed class="postlist">
{%- for post in postslist | reverse %}
  <li>
    <a href="{{ post.url }}">{{ post.data.title }}</a>
    <time datetime="{{ post.date | htmlDateString }}">{{ post.date | readableDate }}</time>
  </li>
{%- endfor %}
</ol>
""",
            "content/blog.njk": """---js
const eleventyNavigation = {
  key: "Archive",
  order: 2
};
---
<h1>Archive</h1>

{% set postslist = collections.posts %}
{% include "postslist.njk" %}
""",
            "content/index.njk": """---js
const numberOfLatestPostsToShow = 3;
---
{% set postslist = collections.posts | head(-1 * numberOfLatestPostsToShow) %}
{% include "postslist.njk" %}
""",
            "content/tag-pages.njk": """---js
const pagination = {
  data: "collections",
  size: 1,
  alias: "tag",
  filter: ["all", "posts"],
};
---
<h1>Tagged “{{ tag }}”</h1>
{% set postslist = collections[tag] %}
{% include "postslist.njk" %}
""",
            "content/sitemap.xml.njk": """---
permalink: /sitemap.xml
layout: false
---
<urlset>
{%- for page in collections.all %}
  <url><loc>{{ page.url | htmlBaseUrl(metadata.url) }}</loc></url>
{%- endfor %}
</urlset>
""",
            "_includes/layouts/post.njk": """<h1>{{ title }}</h1>
{{ content | safe }}

{% set previousPost = collections.posts | getPreviousCollectionItem %}
{% set nextPost = collections.posts | getNextCollectionItem %}
""",
            "eleventy.config.js": """export default async function(eleventyConfig) {
  eleventyConfig.addPlugin(feedPlugin, {
    outputPath: "/feed/feed.xml",
    collection: { name: "posts", limit: 10 },
  });
}
""",
            "docs/development/index.md": """# Development

The project has no archive-pagination specification.
""",
        },
    )


def _fixture_requirement_quality_fastapi(
    workspace: Path,
    branch_variant: str,
) -> None:
    if branch_variant != "base":
        raise KeyError(
            f"unknown requirement-quality-fastapi variant: {branch_variant}"
        )
    _write_synthetic_fixture(
        workspace,
        {
            "UPSTREAM.md": """# Upstream source

This compact evaluation fixture is adapted from FastAPI CRUD Async.

- Repository: https://github.com/testdrivenio/fastapi-crud-async
- Revision: 4fa7ae952ece61e228135285de1b6a5ff65a1dc8
- License: MIT
""",
            "README.md": """# FastAPI CRUD Async

An asynchronous public notes REST API with create, list, read, update, and
delete routes. `GET /notes/` currently returns every note as a plain JSON
array.
""",
            "src/app/api/models.py": """from pydantic import BaseModel, Field


class NoteSchema(BaseModel):
    title: str = Field(..., min_length=3, max_length=50)
    description: str = Field(..., min_length=3, max_length=50)


class NoteDB(NoteSchema):
    id: int
""",
            "src/app/api/crud.py": """from app.db import database, notes


async def get_all():
    query = notes.select()
    return await database.fetch_all(query=query)
""",
            "src/app/api/notes.py": """from typing import List

from fastapi import APIRouter, HTTPException, Path

from app.api import crud
from app.api.models import NoteDB, NoteSchema

router = APIRouter()


@router.get("/", response_model=List[NoteDB])
async def read_all_notes():
    return await crud.get_all()


@router.get("/{id}/", response_model=NoteDB)
async def read_note(id: int = Path(..., gt=0)):
    note = await crud.get(id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.post("/", response_model=NoteDB, status_code=201)
async def create_note(payload: NoteSchema):
    note_id = await crud.post(payload)
    return {"id": note_id, **payload.model_dump()}


@router.put("/{id}/", response_model=NoteDB)
async def update_note(payload: NoteSchema, id: int = Path(..., gt=0)):
    return await crud.put(id, payload)


@router.delete("/{id}/", response_model=NoteDB)
async def delete_note(id: int = Path(..., gt=0)):
    return await crud.delete(id)
""",
            "src/tests/test_notes.py": """def test_read_all_notes(test_app, monkeypatch):
    test_data = [
        {"title": "first", "description": "one", "id": 1},
        {"title": "second", "description": "two", "id": 2},
    ]

    async def mock_get_all():
        return test_data

    monkeypatch.setattr(crud, "get_all", mock_get_all)
    response = test_app.get("/notes/")
    assert response.status_code == 200
    assert response.json() == test_data
""",
            "docs/development/index.md": """# Development

The project has no notes-pagination specification.
""",
        },
    )


def _fixture_requirement_quality_flask_vue(
    workspace: Path,
    branch_variant: str,
) -> None:
    if branch_variant != "base":
        raise KeyError(
            f"unknown requirement-quality-flask-vue variant: {branch_variant}"
        )
    _write_synthetic_fixture(
        workspace,
        {
            "UPSTREAM.md": """# Upstream source

This compact evaluation fixture is adapted from Flask-Vue CRUD.

- Repository: https://github.com/testdrivenio/flask-vue-crud
- Revision: be91da59a10d07384537c2f76f4505eb344d1682
- License: MIT
""",
            "README.md": """# Flask-Vue CRUD

A user-facing Vue single-page Books application backed by a Flask JSON API.
The table displays title, author, and read status. The client reloads all
books after add, update, and delete operations.
""",
            "server/app.py": """from flask import Flask, jsonify, request


app = Flask(__name__)
BOOKS = [
    {"id": "1", "title": "On the Road", "author": "Jack Kerouac", "read": True},
    {"id": "2", "title": "Green Eggs and Ham", "author": "Dr. Seuss", "read": False},
]


@app.route("/books", methods=["GET", "POST"])
def all_books():
    response = {"status": "success"}
    if request.method == "POST":
        BOOKS.append(request.get_json())
        response["message"] = "Book added!"
    else:
        response["books"] = BOOKS
    return jsonify(response)


@app.route("/books/<book_id>", methods=["PUT", "DELETE"])
def single_book(book_id):
    return jsonify({"status": "success"})
""",
            "client/src/components/Books.vue": """<template>
  <main>
    <h1>Books</h1>
    <table>
      <tr v-for="book in books" :key="book.id">
        <td>{{ book.title }}</td>
        <td>{{ book.author }}</td>
        <td>{{ book.read ? "Yes" : "No" }}</td>
      </tr>
    </table>
  </main>
</template>

<script>
import axios from "axios";

export default {
  data() {
    return {
      books: [],
    };
  },
  methods: {
    getBooks() {
      axios.get("http://localhost:5001/books").then((res) => {
        this.books = res.data.books;
      });
    },
    addBook(payload) {
      axios.post("http://localhost:5001/books", payload).then(this.getBooks);
    },
    updateBook(payload, id) {
      axios.put(`http://localhost:5001/books/${id}`, payload).then(this.getBooks);
    },
    removeBook(id) {
      axios.delete(`http://localhost:5001/books/${id}`).then(this.getBooks);
    },
  },
  created() {
    this.getBooks();
  },
};
</script>
""",
            "docs/development/index.md": """# Development

The project has no book-filter specification.
""",
        },
    )


def _fixture_requirement_quality_judge(
    workspace: Path,
    branch_variant: str,
) -> None:
    if branch_variant != "base":
        raise KeyError(
            f"unknown requirement-quality-judge variant: {branch_variant}"
        )
    _write_synthetic_fixture(
        workspace,
        {
            "README.md": """# Requirement-quality semantic evaluation

This isolated workspace is used only to obtain a structured semantic
assessment from the model. The complete assessment input is in the user
message. Do not inspect or modify repository files.
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
    _git(workspace, "add", "-A")
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Agent Evaluation",
        "GIT_AUTHOR_EMAIL": "agent-eval@example.invalid",
        "GIT_COMMITTER_NAME": "Agent Evaluation",
        "GIT_COMMITTER_EMAIL": "agent-eval@example.invalid",
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
    return tuple(
        sorted(
            set(
                re.findall(
                    r"DOC(?:GEN|REP|GUIDE|LOCAL|AGENT|VAL)-\d{3}",
                    text,
                )
            )
        )
    )