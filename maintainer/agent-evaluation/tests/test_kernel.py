from __future__ import annotations

import json
import inspect
import os
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, cast

import pytest

from agent_eval import (
    AgentEval,
    EvidenceVisibility,
    RunFailedError,
    RunServices,
)

from replay import ReplayContext, ReplayEnvironment


@dataclass(frozen=True)
class CustomSnapshot:
    position: int
    callback: object


class CustomSnapshotEnvironment(ReplayEnvironment):
    def snapshot(self, context: ReplayContext) -> object:
        return CustomSnapshot(position=context.position, callback=lambda: None)

    def serialize_snapshot(self, snapshot: object) -> bytes:
        assert isinstance(snapshot, CustomSnapshot)
        return str(snapshot.position).encode("ascii")

    def deserialize_snapshot(self, data: bytes) -> object:
        return CustomSnapshot(position=int(data.decode("ascii")), callback=lambda: None)

    @contextmanager
    def open(
        self,
        *,
        services: RunServices,
        workspace: Path | None,
        parent_snapshot: object | None,
    ) -> Iterator[ReplayContext]:
        self.open_count += 1
        position = (
            parent_snapshot.position
            if isinstance(parent_snapshot, CustomSnapshot)
            else 0
        )
        yield ReplayContext(
            services=services,
            responses=list(self.responses),
            position=position,
        )


class OpenFailureEnvironment(ReplayEnvironment):
    @contextmanager
    def open(
        self,
        *,
        services: RunServices,
        workspace: Path | None,
        parent_snapshot: object | None,
    ) -> Iterator[ReplayContext]:
        raise RuntimeError("environment did not open")
        yield ReplayContext(services=services, responses=[])  # pragma: no cover


def evaluator(
    tmp_path: Path,
    environment: ReplayEnvironment,
) -> AgentEval:
    return AgentEval(
        default_environment=environment,
        artifact_root=tmp_path / "artifacts",
        cache_root=tmp_path / "cache",
    )


def test_program_returns_arbitrary_value_and_writes_artifacts(
    tmp_path: Path,
) -> None:
    environment = ReplayEnvironment(["answer"])
    with evaluator(tmp_path, environment) as evaluation:
        def program(context):
            response = context.next_response("question")
            context.services.record(
                "custom.metadata",
                {"api_token": "do-not-render", "visible": "yes"},
            )
            return {"response": response, "score": 4}

        run = evaluation.run("arbitrary-value", program)

        assert run.value == {"response": "answer", "score": 4}
        assert run.environment == {
            "responses_consumed": 1,
            "responses_remaining": 0,
        }
        assert run.error is None
        assert run.snapshot is not None
        assert run.artifact_dir.joinpath("result.md").is_file()
        assert run.artifact_dir.joinpath("result.json").is_file()
        assert run.artifact_dir.joinpath("raw/evidence.json").is_file()
        result = json.loads(
            run.artifact_dir.joinpath("result.json").read_text(encoding="utf-8")
        )
        custom = next(
            item for item in result["evidence"] if item["kind"] == "custom.metadata"
        )
        assert custom["value"]["api_token"] == "<redacted>"
        assert "answer" in run.canonical_text()
        record = run.record("post-run-score", {"score": 4})
        assert record.is_file()


def test_public_run_signature_stays_minimal() -> None:
    signature = inspect.signature(AgentEval.run)
    assert tuple(signature.parameters) == (
        "self",
        "name",
        "program",
        "environment",
        "continue_from",
        "workspace",
        "cache_key",
        "cache_read",
        "cache_publish",
    )


def test_program_can_perform_multiple_environment_operations(
    tmp_path: Path,
) -> None:
    environment = ReplayEnvironment(["first", "second"])
    with evaluator(tmp_path, environment) as evaluation:
        def program(context):
            return (
                context.next_response("one"),
                context.next_response("two"),
            )

        run = evaluation.run("multiple-operations", program)

    assert run.value == ("first", "second")
    observation = cast(dict[str, object], run.environment)
    assert observation["responses_consumed"] == 2


def test_per_run_environment_replaces_default(tmp_path: Path) -> None:
    default = ReplayEnvironment(["default"], identity="default")
    alternate = ReplayEnvironment(["alternate"], identity="alternate")
    with evaluator(tmp_path, default) as evaluation:
        run = evaluation.run(
            "alternate",
            lambda context: context.next_response("question"),
            environment=alternate,
        )

    assert run.value == "alternate"
    assert default.open_count == 0
    assert alternate.open_count == 1


def test_continuation_restores_parent_snapshot_without_mutating_parent(
    tmp_path: Path,
) -> None:
    environment = ReplayEnvironment(["first", "second"])
    with evaluator(tmp_path, environment) as evaluation:
        first = evaluation.run(
            "first",
            lambda context: context.next_response("one"),
        )
        parent_snapshot = first.snapshot
        second = evaluation.run(
            "second",
            lambda context: context.next_response("two"),
            continue_from=first,
        )

    assert first.value == "first"
    assert second.value == "second"
    assert first.snapshot == parent_snapshot
    second_observation = cast(dict[str, object], second.environment)
    assert second_observation["responses_consumed"] == 2
    assert second.parent_run_id == first.run_id


def test_parent_without_snapshot_is_an_inspectable_failure(
    tmp_path: Path,
) -> None:
    environment = ReplayEnvironment(["first"], snapshot_enabled=False)
    with evaluator(tmp_path, environment) as evaluation:
        parent = evaluation.run(
            "no-snapshot",
            lambda context: context.next_response("one"),
        )
        child = evaluation.run(
            "child",
            lambda context: "unreachable",
            continue_from=parent,
        )

    assert child.error is not None
    assert child.error.phase == "environment.restore"
    assert child.artifact_dir.joinpath("result.md").is_file()
    with pytest.raises(RunFailedError):
        child.raise_for_error()


def test_incompatible_environment_is_rejected_before_open(
    tmp_path: Path,
) -> None:
    first_environment = ReplayEnvironment(["first"], identity="first")
    second_environment = ReplayEnvironment(["second"], identity="second")
    with evaluator(tmp_path, first_environment) as evaluation:
        parent = evaluation.run(
            "parent",
            lambda context: context.next_response("one"),
        )
        child = evaluation.run(
            "child",
            lambda context: "unreachable",
            environment=second_environment,
            continue_from=parent,
        )

    assert child.error is not None
    assert child.error.phase == "environment.restore"
    assert second_environment.open_count == 0


def test_program_failure_preserves_environment_and_traceback(
    tmp_path: Path,
) -> None:
    environment = ReplayEnvironment(["unused"])
    with evaluator(tmp_path, environment) as evaluation:
        def fail(context):
            context.services.record("before.failure", {"ok": True})
            raise RuntimeError("planned failure")

        run = evaluation.run("failure", fail)

    assert run.error is not None
    assert run.error.phase == "program"
    assert run.error.type == "RuntimeError"
    observation = cast(dict[str, object], run.environment)
    assert observation["responses_consumed"] == 0
    assert run.error.traceback_artifact is not None
    assert run.artifact_dir.joinpath(run.error.traceback_artifact).is_file()
    assert "planned failure" in run.canonical_text()


def test_cache_publish_predicate_prevents_publication(tmp_path: Path) -> None:
    environment = ReplayEnvironment(["first", "second"])
    with evaluator(tmp_path, environment) as evaluation:
        evaluation.run(
            "unpublishable",
            lambda context: context.next_response("question"),
            cache_key="predicate-v1",
            cache_publish=lambda run: False,
        )
        second = evaluation.run(
            "unpublishable",
            lambda context: context.next_response("question"),
            cache_key="predicate-v1",
            cache_publish=lambda run: False,
        )

    assert second.cache_hit is False
    assert environment.open_count == 2


def test_cache_read_false_reexecutes_but_still_publishes(tmp_path: Path) -> None:
    environment = ReplayEnvironment(["first", "second"])
    with evaluator(tmp_path, environment) as evaluation:
        evaluation.run(
            "fresh",
            lambda context: context.next_response("question"),
            cache_key="fresh-v1",
        )
        fresh = evaluation.run(
            "fresh",
            lambda context: context.next_response("question"),
            cache_key="fresh-v1",
            cache_read=False,
        )
        replay = evaluation.run(
            "fresh",
            lambda context: "unreachable",
            cache_key="fresh-v1",
        )

    assert fresh.cache_hit is False
    assert replay.cache_hit is True
    assert environment.open_count == 2


def test_generic_import_does_not_load_crystal_lattice_packages() -> None:
    source_root = Path(__file__).resolve().parents[1] / "src"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import agent_eval; "
                "assert 'agent_app' not in sys.modules; "
                "assert 'agent_core' not in sys.modules"
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


def test_unpicklable_value_uses_raw_text_fallback(
    tmp_path: Path,
) -> None:
    environment = ReplayEnvironment(["unused"])
    lock = __import__("threading").RLock()
    with evaluator(tmp_path, environment) as evaluation:
        run = evaluation.run("unpicklable", lambda context: lock)

    assert run.error is None
    assert run.value is lock
    assert run.artifact_dir.joinpath("raw/environment/value.txt").is_file()


def test_internal_evidence_is_not_persisted(
    tmp_path: Path,
) -> None:
    environment = ReplayEnvironment(["answer"])
    with evaluator(tmp_path, environment) as evaluation:
        def program(context):
            context.services.record(
                "visible.raw",
                "retained",
                visibility=EvidenceVisibility.RAW,
            )
            context.services.record(
                "private.internal",
                "run-local",
                visibility=EvidenceVisibility.INTERNAL,
            )
            return context.next_response("question")

        run = evaluation.run("evidence-visibility", program)

    raw_evidence = run.artifact_dir.joinpath("raw/evidence.json").read_text(
        encoding="utf-8"
    )
    assert "visible.raw" in raw_evidence
    assert "private.internal" not in raw_evidence


def test_environment_open_failure_is_preserved(tmp_path: Path) -> None:
    environment = OpenFailureEnvironment([])
    with evaluator(tmp_path, environment) as evaluation:
        run = evaluation.run("open-failure", lambda context: "unreachable")

    assert run.error is not None
    assert run.error.phase == "environment.open_or_close"
    assert "environment did not open" in run.canonical_text()


def test_environment_can_supply_custom_snapshot_serialization(
    tmp_path: Path,
) -> None:
    environment = CustomSnapshotEnvironment(["first", "second"])
    with evaluator(tmp_path, environment) as evaluation:
        first = evaluation.run(
            "custom-snapshot",
            lambda context: context.next_response("one"),
            cache_key="custom-snapshot-v1",
        )
        cached = evaluation.run(
            "custom-snapshot",
            lambda context: "unreachable",
            cache_key="custom-snapshot-v1",
        )
        second = evaluation.run(
            "custom-snapshot-child",
            lambda context: context.next_response("two"),
            continue_from=cached,
        )

    assert first.error is None
    assert cached.cache_hit is True
    assert isinstance(cached.snapshot, CustomSnapshot)
    assert second.value == "second"