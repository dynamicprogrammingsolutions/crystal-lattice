"""Run-model layer mechanism tests: labels, identity, samples, retries."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

import pytest

from agent_eval import AgentEval, Run
from agent_eval.runner import (
    RunModel,
    generate_run_label,
    publish_when_no_provider_errors,
    request_identity,
)

from fixtures.run_model_scenario import EchoEnvironment, EchoValue


def _identity(**components: Any) -> str:
    return request_identity(
        namespace="run-model-tests",
        version="v1",
        components=components,
    )


def _provenance(run: Run[Any]) -> Mapping[str, Any]:
    return json.loads(
        run.artifact_dir.joinpath("records", "run-model.json").read_text(
            encoding="utf-8"
        )
    )


class TestRunLabels:
    def test_generated_labels_are_unique_and_shaped(self) -> None:
        labels = [generate_run_label() for _ in range(8)]

        assert len(set(labels)) == 8
        for label in labels:
            assert re.fullmatch(r"r-\d{8}-\d{6}-[0-9a-f]{4}", label)

    def test_explicit_label_is_used_and_auto_label_is_generated(
        self, tmp_path: Path
    ) -> None:
        environment = EchoEnvironment(agent="alpha")
        with AgentEval(
            default_environment=environment,
            artifact_root=tmp_path / "artifacts",
            cache_root=tmp_path / "cache",
        ) as evaluation:
            explicit = RunModel(evaluation, label="batch-a")
            auto = RunModel(evaluation)

        assert explicit.label == "batch-a"
        assert re.fullmatch(r"r-\d{8}-\d{6}-[0-9a-f]{4}", auto.label)


class TestRequestIdentity:
    def test_identity_is_component_order_independent(self) -> None:
        first = _identity(agent="alpha", effort="low", prompt="p")
        second = _identity(prompt="p", effort="low", agent="alpha")

        assert first == second

    def test_identity_changes_when_any_component_changes(self) -> None:
        base = _identity(agent="alpha", effort="low", prompt="p")

        assert base != _identity(agent="alpha", effort="high", prompt="p")
        assert base != _identity(agent="beta", effort="low", prompt="p")
        assert base != _identity(agent="alpha", effort="low", prompt="q")
        assert base != request_identity(
            namespace="other-namespace",
            version="v1",
            components={"agent": "alpha", "effort": "low", "prompt": "p"},
        )
        assert base != request_identity(
            namespace="run-model-tests",
            version="v2",
            components={"agent": "alpha", "effort": "low", "prompt": "p"},
        )

    def test_label_is_structurally_absent_from_the_identity(self) -> None:
        # The identity composition takes no label argument at all, so a
        # label can never leak into the cache key.
        import inspect

        parameters = inspect.signature(request_identity).parameters

        assert "label" not in parameters
        assert "attempt" not in parameters


class TestRunModelExecution:
    def test_label_never_changes_the_cache_key(self, tmp_path: Path) -> None:
        environment = EchoEnvironment(agent="alpha")
        with AgentEval(
            default_environment=environment,
            artifact_root=tmp_path / "artifacts",
            cache_root=tmp_path / "cache",
        ) as evaluation:
            first_model = RunModel(evaluation, label="batch-a")
            second_model = RunModel(evaluation, label="batch-b")
            identity = _identity(
                stage="produce", agent="alpha", scenario="s", effort="low"
            )

            first = first_model.run(
                "produce",
                lambda context: context.respond("prompt"),
                identity=identity,
            )
            second = second_model.run(
                "produce",
                lambda context: context.respond("prompt"),
                identity=identity,
            )

        assert first.cache_hit is False
        assert second.cache_hit is True
        assert environment.request_count == 1

    def test_provenance_record_is_written_per_run(self, tmp_path: Path) -> None:
        environment = EchoEnvironment(agent="alpha")
        with AgentEval(
            default_environment=environment,
            artifact_root=tmp_path / "artifacts",
            cache_root=tmp_path / "cache",
        ) as evaluation:
            model = RunModel(evaluation, label="batch-a")
            identity = _identity(stage="produce", agent="alpha")
            run = model.run(
                "produce",
                lambda context: context.respond("prompt"),
                identity=identity,
            )

        provenance = _provenance(run)

        assert provenance["label"] == "batch-a"
        assert provenance["identity"] == identity
        assert provenance["cache_hit"] is False
        assert provenance["sample_index"] == 0
        assert provenance["run_id"] == run.run_id

    def test_fresh_reexecutes_a_successful_request(self, tmp_path: Path) -> None:
        environment = EchoEnvironment(agent="alpha")
        with AgentEval(
            default_environment=environment,
            artifact_root=tmp_path / "artifacts",
            cache_root=tmp_path / "cache",
        ) as evaluation:
            model = RunModel(evaluation, label="batch-a")
            identity = _identity(stage="produce", agent="alpha")

            first = model.run(
                "produce",
                lambda context: context.respond("prompt"),
                identity=identity,
            )
            fresh = model.run(
                "produce",
                lambda context: context.respond("prompt"),
                identity=identity,
                fresh=True,
            )
            replay = model.run(
                "produce",
                lambda context: context.respond("prompt"),
                identity=identity,
            )

        assert first.cache_hit is False
        assert fresh.cache_hit is False
        assert replay.cache_hit is True
        assert environment.request_count == 2
        assert fresh.value.request_count == 2

    def test_samples_execute_the_request_n_times(self, tmp_path: Path) -> None:
        environment = EchoEnvironment(agent="alpha")
        with AgentEval(
            default_environment=environment,
            artifact_root=tmp_path / "artifacts",
            cache_root=tmp_path / "cache",
        ) as evaluation:
            model = RunModel(evaluation, label="batch-a")
            identity = _identity(stage="produce", agent="alpha")

            runs = model.run_samples(
                "produce",
                lambda context: context.respond("prompt"),
                identity=identity,
                count=3,
            )

        assert len(runs) == 3
        assert environment.request_count == 3
        assert [run.value.request_count for run in runs] == [1, 2, 3]
        assert all(run.cache_hit is False for run in runs)
        assert [_provenance(run)["sample_index"] for run in runs] == [0, 1, 2]

    def test_sample_count_must_be_positive(self, tmp_path: Path) -> None:
        environment = EchoEnvironment(agent="alpha")
        with AgentEval(
            default_environment=environment,
            artifact_root=tmp_path / "artifacts",
            cache_root=tmp_path / "cache",
        ) as evaluation:
            model = RunModel(evaluation, label="batch-a")

            with pytest.raises(ValueError):
                model.run_samples(
                    "produce",
                    lambda context: context.respond("prompt"),
                    identity=_identity(stage="produce", agent="alpha"),
                    count=0,
                )


class TestProviderFailureRetries:
    def test_provider_error_values_are_not_cached_and_retry_naturally(
        self, tmp_path: Path
    ) -> None:
        environment = EchoEnvironment(agent="alpha", failures=("insufficient quota",))
        with AgentEval(
            default_environment=environment,
            artifact_root=tmp_path / "artifacts",
            cache_root=tmp_path / "cache",
        ) as evaluation:
            model = RunModel(evaluation, label="batch-a")
            identity = _identity(stage="produce", agent="alpha")

            failed = model.run(
                "produce",
                lambda context: context.respond("prompt"),
                identity=identity,
            )
            retried = model.run(
                "produce",
                lambda context: context.respond("prompt"),
                identity=identity,
            )
            replay = model.run(
                "produce",
                lambda context: context.respond("prompt"),
                identity=identity,
            )

        assert failed.error is None
        assert failed.value.errors == ("insufficient quota",)
        assert failed.cache_hit is False
        assert retried.cache_hit is False
        assert retried.value.errors == ()
        assert replay.cache_hit is True
        assert environment.request_count == 2

    def test_publish_predicate_helper_covers_value_shapes(self, tmp_path: Path) -> None:
        clean = EchoValue("p", "r", True, (), 1)
        failing = EchoValue("p", "", False, ("insufficient quota",), 1)

        assert publish_when_no_provider_errors(_run_with(clean)) is True
        assert publish_when_no_provider_errors(_run_with(failing)) is False
        assert publish_when_no_provider_errors(_run_with({"errors": ()})) is True
        assert publish_when_no_provider_errors(_run_with({"errors": ["boom"]})) is False
        assert publish_when_no_provider_errors(_run_with({"unrelated": 1})) is True


def _run_with(value: object) -> Run[object]:
    """Minimal Run stand-in carrying only the value the helper inspects."""

    return Run(
        run_id="r",
        name="n",
        value=value,
        snapshot=None,
        environment={},
        environment_fingerprint={},
        workspace=None,
        workspace_fingerprint=None,
        changed_paths=(),
        artifact_dir=Path("."),
        error=None,
        cache_hit=False,
        parent_run_id=None,
        snapshot_sha256=None,
    )


def test_run_model_layer_is_environment_neutral() -> None:
    # The layer must stay importable without the crystal-lattice adapter.
    import os
    import subprocess
    import sys

    source_root = Path(__file__).resolve().parents[1] / "src"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import agent_eval.runner; "
                "assert 'agent_eval.crystal_lattice' not in sys.modules"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PYTHONPATH": str(source_root),
        },
    )
    assert result.returncode == 0, result.stderr
