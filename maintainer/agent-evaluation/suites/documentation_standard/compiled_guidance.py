from __future__ import annotations

import os
import hashlib
from typing import Any

from maintainer.guidance import CompilationResult, compile_guidance

from .requirement_quality import RequirementQualityScenario
from .support import GuidanceSource, REPOSITORY_ROOT


DEFAULT_BUNDLE = "maintainer/guidance/current"


def selected_bundle() -> str:
    return os.getenv(
        "AGENT_EVAL_GUIDANCE_BUNDLE",
        DEFAULT_BUNDLE,
    ).strip()


def selected_target() -> str:
    value = os.getenv("AGENT_EVAL_GUIDANCE_TARGET", "").strip()
    if not value:
        raise ValueError(
            "AGENT_EVAL_GUIDANCE_TARGET must name the consuming "
            "repository's target-template directory"
        )
    return value


def compile_scenario_guidance(
    scenario: RequirementQualityScenario,
    *,
    bundle: str | None = None,
    target: str | None = None,
) -> CompilationResult:
    del scenario
    return compile_guidance(
        bundle=bundle or selected_bundle(),
        target=target or selected_target(),
        base_directory=REPOSITORY_ROOT,
    )


def guidance_source(
    result: CompilationResult,
    *,
    mode: str,
) -> GuidanceSource:
    if mode not in {"root-only", "task"}:
        raise ValueError(f"unknown compiled-guidance mode: {mode}")
    paths = (
        ("AGENTS.md",)
        if mode == "root-only"
        else ("AGENTS.md", "agents/TASKS-v7.md")
    )
    if "AGENTS.md" not in result.outputs:
        raise ValueError(
            "compiled consuming-project target lacks AGENTS.md"
        )
    overrides = [("AGENTS.md", result.outputs["AGENTS.md"])]
    if mode == "task":
        overrides.append(
            (
                "agents/TASKS-v7.md",
                (REPOSITORY_ROOT / "agents/TASKS-v7.md").read_bytes(),
            )
        )
    return GuidanceSource(
        name=(
            f"compiled-{result.bundle_id}-{result.target_id}-{mode}-"
            f"{result.lock['compilation_sha256'][:12]}"
        ),
        paths=paths,
        content_overrides=tuple(overrides),
    )


def dataset_identity(
    result: CompilationResult,
    *,
    mode: str,
) -> tuple[str, str]:
    digest = str(result.lock["compilation_sha256"])[:12]
    dataset_id = (
        f"compiled-guidance-{result.bundle_id}-{mode}-{digest}-20260917"
    )
    test_prefix = f"requirement-compiled-{result.bundle_id}-{mode}"
    return dataset_id, test_prefix


def compilation_evidence(
    result: CompilationResult,
    *,
    mode: str = "root-only",
) -> dict[str, Any]:
    value = dict(result.lock)
    if mode == "task":
        task_guidance = (
            REPOSITORY_ROOT / "agents/TASKS-v7.md"
        ).read_bytes()
        value["task_guidance"] = {
            "path": "agents/TASKS-v7.md",
            "sha256": hashlib.sha256(task_guidance).hexdigest(),
            "delivery": "crystal-lattice-runtime-config",
        }
    return value