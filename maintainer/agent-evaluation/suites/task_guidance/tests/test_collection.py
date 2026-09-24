"""Collection checks: the live matrix is exactly the configuration.

The collected live evaluation — the ``agent_eval``-marked stage drivers
under ``evaluation/`` — must be exactly the configuration-derived matrix,
nothing more and nothing less, regardless of legacy environment
variables, and ``-k`` must slice it correctly. A bare pytest invocation
over the whole suite collects the machinery tests and no live
evaluation at all (the repo-wide default deselection).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from ..evaluation.matrix import (
    handoff_assessment_cases,
    handoff_plan_cases,
    negative_control_cases,
    continuation_cases,
    task_creation_assessment_cases,
    task_creation_cases,
)


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
SUITE_ROOT = Path(__file__).resolve().parents[1]
EVALUATION_ROOT = SUITE_ROOT / "evaluation"


def _expected_ids() -> set[str]:
    return {
        *(f"test_task_creation[{case.id}]" for case in task_creation_cases()),
        *(f"test_handoff_plan[{case.id}]" for case in handoff_plan_cases()),
        *(f"test_continuation[{case.id}]" for case in continuation_cases()),
        *(f"test_negative_control[{case.id}]" for case in negative_control_cases()),
        *(
            f"test_task_creation_assessment[{case.id}]"
            for case in task_creation_assessment_cases()
        ),
        *(f"test_handoff_assessment[{case.id}]" for case in handoff_assessment_cases()),
    }


def _collect(
    *args: str,
    target: Path = EVALUATION_ROOT,
    env: dict[str, str] | None = None,
) -> set[str]:
    environment = dict(os.environ)
    if env:
        environment.update(env)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(target),
            "--collect-only",
            "-q",
            *args,
        ],
        capture_output=True,
        text=True,
        cwd=PACKAGE_ROOT,
        env=environment,
    )
    assert result.returncode in (0, 4, 5), result.stderr
    ids = set()
    for line in result.stdout.splitlines():
        if "::" not in line or "[" not in line:
            continue
        ids.add(line.rsplit("::", 1)[1].strip())
    return ids


def test_collect_only_lists_exactly_the_configuration_matrix() -> None:
    assert _collect("-m", "agent_eval") == _expected_ids()


def test_bare_pytest_collects_no_live_tests() -> None:
    collected = _collect(target=SUITE_ROOT)
    assert collected
    assert not collected & _expected_ids()


def test_legacy_environment_variables_do_not_change_collection() -> None:
    legacy = {
        "AGENT_EVAL_PROFILE": "gpt",
        "AGENT_EVAL_TASK_SCENARIO": "tg01-eleventy-archive-handoff",
        "AGENT_EVAL_TASK_EFFORT": "high",
        "AGENT_EVAL_TASK_GUIDANCE_RUN_ATTEMPT": "legacy-r1",
        "AGENT_EVAL_TASK_HANDOFF_RUN_ATTEMPT": "legacy-h1",
        "AGENT_EVAL_TASK_GUIDANCE_SEMANTIC_ATTEMPT": "legacy-m1",
        "AGENT_EVAL_TASK_ALLOW_PARTIAL": "1",
        "AGENT_EVAL_RUN_REAL": "1",
        "AGENT_EVAL_ALLOW_HOSTED": "1",
        "AGENT_EVAL_TASK_DATASET_ID": "legacy-dataset",
    }
    assert _collect("-m", "agent_eval", env=legacy) == _expected_ids()


def test_k_slices_select_cells() -> None:
    glm_ids = {
        test_id
        for test_id in _expected_ids()
        if "-glm-" in test_id or test_id.endswith("-glm")
    }
    assert _collect("-m", "agent_eval", "-k", "glm") == glm_ids

    one_scenario = {
        test_id
        for test_id in _expected_ids()
        if "tg01-eleventy-archive-handoff" in test_id
    }
    assert (
        _collect("-m", "agent_eval", "-k", "tg01-eleventy-archive-handoff")
        == one_scenario
    )

    retain_only = {test_id for test_id in _expected_ids() if "-retain-" in test_id}
    assert _collect("-m", "agent_eval", "-k", "retain") == retain_only
