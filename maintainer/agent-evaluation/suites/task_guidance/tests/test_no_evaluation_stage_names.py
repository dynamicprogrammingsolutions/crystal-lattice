"""Naming cleanup: no evaluation-stage names in suite code or tests.

The suite's operational vocabulary is the configuration-declared stage
catalog and run labels. The historical evaluation names — the b0/b1
attempt names, the old stage markers, and the deleted parameter
environment variables — must stay out of the code. The remaining
``attempt`` vocabulary is the legacy data-format field names, confined
to the explicit compatibility adapters and the tests that construct
legacy-shape fixtures.
"""

from __future__ import annotations

from pathlib import Path


SUITE_ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve()

# Historical evaluation attempt names and old stage markers.
EVALUATION_NAMES = (
    "b0-v5-r1",
    "b1-v1-r1",
    "b0-metrics1",
    "b1-metrics1",
    "task_guidance_baseline",
    "task_guidance_semantic",
)

# Parameter environment variables deleted with the configuration rework.
DELETED_ENV_VARS = (
    "AGENT_EVAL_RUN_REAL",
    "AGENT_EVAL_ALLOW_HOSTED",
    "AGENT_EVAL_PROFILE",
    "AGENT_EVAL_TASK_SCENARIO",
    "AGENT_EVAL_TASK_EFFORT",
    "AGENT_EVAL_TASK_GUIDANCE_RUN_ATTEMPT",
    "AGENT_EVAL_TASK_HANDOFF_RUN_ATTEMPT",
    "AGENT_EVAL_TASK_GUIDANCE_SEMANTIC_ATTEMPT",
    "AGENT_EVAL_TASK_ALLOW_PARTIAL",
    "AGENT_EVAL_CACHE_NONCE",
    "AGENT_EVAL_MAX_EVENTS",
    "AGENT_EVAL_TASK_DATASET_ID",
)

# The legacy data-format vocabulary is owned by the compatibility
# adapters (historical frozen datasets and records stay readable) and by
# the tests that construct legacy-shape fixtures.
ATTEMPT_VOCABULARY_OWNERS = {
    "results.py",
    "result_package.py",
    "test_results.py",
    "test_result_package.py",
    "test_package_adapter.py",
    "test_configuration.py",
    "test_runner_assembly.py",
}


def _suite_sources() -> list[Path]:
    return sorted(
        path
        for path in SUITE_ROOT.rglob("*.py")
        if path != HERE and "__pycache__" not in path.parts
    )


def test_evaluation_names_are_absent_from_suite_code() -> None:
    for path in _suite_sources():
        text = path.read_text(encoding="utf-8")
        for token in EVALUATION_NAMES:
            assert token not in text, f"{token!r} appears in {path}"


def test_deleted_environment_variables_appear_only_in_the_inertness_test() -> None:
    for path in _suite_sources():
        text = path.read_text(encoding="utf-8")
        for token in DELETED_ENV_VARS:
            if token not in text:
                continue
            assert path.name == "test_collection.py", (
                f"{token!r} appears in {path}; only the legacy-inertness"
                " collection test may name a deleted variable"
            )


def test_attempt_vocabulary_stays_in_the_compatibility_owners() -> None:
    for path in _suite_sources():
        text = path.read_text(encoding="utf-8")
        if "attempt" not in text:
            continue
        assert path.name in ATTEMPT_VOCABULARY_OWNERS, (
            f"{path} uses the legacy attempt vocabulary; the operational"
            " vocabulary is run labels"
        )
