"""Suite configuration: the JSON manifest plus the pinned runtime configs.

``configuration.json`` is the single declaration of what the evaluation is:
the agents (each with its model, declared efforts, and pinned runtime-config
fixture), the scenario categories with their producer matrices and stage
lists, and the default directories. This module loads that manifest and
resolves the runtime-config fixtures; consumers read the values through it
and must not redefine agent, matrix, stage, or directory values.

The stage catalog — what each stage name means (the workspace a run starts
from, whether it continues an earlier stage, its expansion, and its record
file) — lives in :mod:`stages`; the manifest selects from it.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


SUITE_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = SUITE_ROOT.parents[3]
PACKAGE_ROOT = REPOSITORY_ROOT / "maintainer" / "agent-evaluation"

with (SUITE_ROOT / "configuration.json").open(encoding="utf-8") as _stream:
    CONFIGURATION = json.load(_stream)

SCHEMA_VERSION = CONFIGURATION["schema_version"]
AGENTS = CONFIGURATION["agents"]
CATEGORIES = CONFIGURATION["categories"]

_directories = CONFIGURATION["directories"]
DEFAULT_ARTIFACT_ROOT = REPOSITORY_ROOT / _directories["artifact_root"]
DEFAULT_BUNDLE = REPOSITORY_ROOT / _directories["guidance_bundle"]
GUIDANCE_TARGET = REPOSITORY_ROOT / _directories["guidance_target"]
PACKAGES_ROOT = REPOSITORY_ROOT / _directories["result_packages"]
SCENARIOS_ROOT = REPOSITORY_ROOT / _directories["scenario_export"]


def selected_bundle() -> Path:
    """The guidance bundle under evaluation (directory setting)."""

    raw = os.getenv("AGENT_EVAL_GUIDANCE_BUNDLE", "").strip()
    return Path(raw).expanduser().resolve() if raw else DEFAULT_BUNDLE


def selected_artifact_root() -> Path:
    """The evaluation artifact root (directory setting)."""

    raw = os.getenv("AGENT_EVAL_ARTIFACT_ROOT", "").strip()
    return Path(raw).expanduser() if raw else DEFAULT_ARTIFACT_ROOT


def producer_cells(category: str) -> tuple[tuple[str, str], ...]:
    """The (agent, effort) pairs that produce one scenario category."""

    return tuple(
        (cell["agent"], cell["effort"])
        for cell in CATEGORIES[category]["producer_cells"]
    )


def all_producer_cells() -> tuple[tuple[str, str], ...]:
    """Every distinct (agent, effort) pair, in declaration order."""

    cells: list[tuple[str, str]] = []
    for name in CATEGORIES:
        for pair in producer_cells(name):
            if pair not in cells:
                cells.append(pair)
    return tuple(cells)


def stage_config(category: str, stage: str) -> dict:
    """One stage's declared configuration for a category."""

    return CATEGORIES[category]["stages"][stage]


def plan_variants(category: str) -> tuple[str, ...]:
    """The handoff-plan stage's input variants for a category."""

    return tuple(stage_config(category, "handoff-plan")["variants"])


# Retired assessment stages and the judge declaration they ran with.
# Historical frozen datasets still collect into packages, so their
# assessor provenance stays resolvable after the stage leaves the live
# configuration.
RETIRED_ASSESSMENT_STAGES = {
    "task-quality-assessment": {"agent": "glm", "effort": "max"},
}


def assessment_cell(category: str, stage: str) -> tuple[str, str]:
    """The (agent, effort) one assessment stage declares as its judge."""

    config = stage_config(category, stage)
    return config["agent"], config["effort"]


def assessment_cell_or_history(category: str, stage: str) -> tuple[str, str]:
    """The judge of a live or retired assessment stage.

    Collection of historical packages resolves retired stages through
    the history table; live stages always win.
    """

    try:
        return assessment_cell(category, stage)
    except KeyError:
        config = RETIRED_ASSESSMENT_STAGES.get(stage)
        if config is None:
            raise
        return config["agent"], config["effort"]


def negative_control(category: str) -> dict | None:
    """The category's negative-control designation, if it runs one."""

    return CATEGORIES[category]["stages"].get("negative-control")


def negative_control_designations() -> tuple[dict, ...]:
    """Every declared negative-control designation, across categories."""

    return tuple(
        control
        for name in CATEGORIES
        for control in (negative_control(name),)
        if control is not None
    )


def agent_config_file(agent_name: str, *, artifact_root: Path, version: str) -> Path:
    """Resolve one agent's pinned runtime config for an artifact root.

    The committed fixture is the crystal-lattice config the agent runs
    against; the only applied override is the artifact-local plugin cache
    directory. The resolved file is written under the artifact root so runs
    and exports record exactly the config they used.
    """

    fixture = SUITE_ROOT / AGENTS[agent_name]["config"]
    config = json.loads(fixture.read_text(encoding="utf-8"))
    config["plugin_cache_dir"] = str(
        artifact_root / "plugin-cache" / agent_name / version
    )
    target = artifact_root / "agent-config" / f"{agent_name}-{version}.json"
    rendered = json.dumps(config, indent=2, sort_keys=True) + "\n"
    if not target.exists() or target.read_text(encoding="utf-8") != rendered:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
    return target
