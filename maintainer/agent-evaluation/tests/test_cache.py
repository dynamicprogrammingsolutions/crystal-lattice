from __future__ import annotations

import multiprocessing
from pathlib import Path

from agent_eval import AgentEval

from replay import ReplayEnvironment


def _concurrent_cache_worker(root: str, marker: str) -> None:
    base = Path(root)
    environment = ReplayEnvironment(["cached"])
    with AgentEval(
        default_environment=environment,
        artifact_root=base / "artifacts",
        cache_root=base / "cache",
    ) as evaluation:
        def program(context):
            with Path(marker).open("a", encoding="utf-8") as handle:
                handle.write("executed\n")
            return context.next_response("question")

        run = evaluation.run(
            "concurrent",
            program,
            cache_key="concurrent-v1",
        )
        run.raise_for_error()


def test_cache_hit_does_not_execute_environment_or_program(
    tmp_path: Path,
) -> None:
    environment = ReplayEnvironment(["cached"])
    with AgentEval(
        default_environment=environment,
        artifact_root=tmp_path / "artifacts",
        cache_root=tmp_path / "cache",
    ) as evaluation:
        def first_program(context):
            context.services.record_artifact(
                "seed-note",
                "preserved from the executed run",
            )
            return context.next_response("question")

        first = evaluation.run(
            "cached",
            first_program,
            cache_key="cached-v1",
        )

        def must_not_run(_context):
            raise AssertionError("cache hit executed the program")

        second = evaluation.run(
            "cached",
            must_not_run,
            cache_key="cached-v1",
        )

    assert first.cache_hit is False
    assert second.cache_hit is True
    assert second.value == "cached"
    assert environment.open_count == 1
    assert second.artifact_dir.joinpath("result.md").is_file()
    assert second.artifact_dir.joinpath("records/seed-note.md").is_file()
    result = second.artifact_dir.joinpath("result.json").read_text(
        encoding="utf-8"
    )
    assert "replay.prompt" in result
    assert "cache.hit" in result


def test_corrupt_cache_entry_is_reported_in_run_artifacts(
    tmp_path: Path,
) -> None:
    environment = ReplayEnvironment(["cached"])
    with AgentEval(
        default_environment=environment,
        artifact_root=tmp_path / "artifacts",
        cache_root=tmp_path / "cache",
    ) as evaluation:
        evaluation.run(
            "cached",
            lambda context: context.next_response("question"),
            cache_key="cached-v1",
        )
        entry = next((tmp_path / "cache" / "entries").iterdir())
        entry.joinpath("value.pkl").write_bytes(b"not a pickle")

        corrupted = evaluation.run(
            "cached",
            lambda context: "unreachable",
            cache_key="cached-v1",
        )

    assert corrupted.error is not None
    assert corrupted.error.phase == "cache.load"
    assert "corrupt" in corrupted.error.message


def test_incomplete_cache_entry_is_rejected(tmp_path: Path) -> None:
    environment = ReplayEnvironment(["cached"])
    evaluation = AgentEval(
        default_environment=environment,
        artifact_root=tmp_path / "artifacts",
        cache_root=tmp_path / "cache",
    )
    assert evaluation.cache is not None
    key = evaluation.cache.key(
        caller_key="cached-v1",
        environment_fingerprint=environment.fingerprint(),
        workspace_fingerprint=None,
        parent_snapshot_sha256=None,
    )
    incomplete = tmp_path / "cache" / "entries" / key
    incomplete.mkdir(parents=True)
    try:
        run = evaluation.run(
            "cached",
            lambda context: "unreachable",
            cache_key="cached-v1",
        )
    finally:
        evaluation.close()

    assert run.error is not None
    assert run.error.phase == "cache.load"
    assert "incomplete" in run.error.message


def test_cache_lock_allows_only_one_concurrent_execution(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "executions.txt"
    context = multiprocessing.get_context("spawn")
    processes = [
        context.Process(
            target=_concurrent_cache_worker,
            args=(str(tmp_path), str(marker)),
        )
        for _ in range(2)
    ]
    for process in processes:
        process.start()
    for process in processes:
        process.join(timeout=30)
        assert process.exitcode == 0

    assert marker.read_text(encoding="utf-8").splitlines() == ["executed"]
    entries = list((tmp_path / "cache" / "entries").iterdir())
    assert len(entries) == 1
    assert entries[0].joinpath("complete").is_file()
    assert not any(
        path.name.startswith(".") and ".tmp-" in path.name
        for path in (tmp_path / "cache" / "entries").iterdir()
    )