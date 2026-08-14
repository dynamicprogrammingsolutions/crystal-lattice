from __future__ import annotations

import subprocess
from pathlib import Path

from agent_eval import AgentEval, git_workspace

from replay import ReplayEnvironment


def test_git_workspace_records_changes_and_is_removed_on_close(
    tmp_path: Path,
    git_repository: Path,
) -> None:
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=git_repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    factory = git_workspace(source=git_repository, revision=revision)
    environment = ReplayEnvironment(["done"])
    evaluation = AgentEval(
        default_environment=environment,
        artifact_root=tmp_path / "artifacts",
        cache_root=tmp_path / "cache",
    )

    def modify(context):
        assert context.services.workspace is not None
        context.services.workspace.joinpath("tracked.txt").write_text(
            "changed\n",
            encoding="utf-8",
        )
        context.services.workspace.joinpath("untracked.txt").write_text(
            "new\n",
            encoding="utf-8",
        )
        return context.next_response("modify")

    run = evaluation.run(
        "git-changes",
        modify,
        workspace=factory,
    )
    workspace_path = run.workspace

    assert run.changed_paths == ("tracked.txt", "untracked.txt")
    assert run.artifact_dir.joinpath("raw/workspace/git-diff.patch").is_file()
    assert workspace_path is not None and workspace_path.is_dir()

    evaluation.close()

    assert not workspace_path.exists()


def test_cached_git_run_restores_tracked_and_untracked_changes(
    tmp_path: Path,
    git_repository: Path,
) -> None:
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=git_repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    factory = git_workspace(source=git_repository, revision=revision)
    environment = ReplayEnvironment(["done"])
    with AgentEval(
        default_environment=environment,
        artifact_root=tmp_path / "artifacts",
        cache_root=tmp_path / "cache",
    ) as evaluation:
        def modify(context):
            assert context.services.workspace is not None
            context.services.workspace.joinpath("tracked.txt").write_text(
                "cached change\n",
                encoding="utf-8",
            )
            context.services.workspace.joinpath("untracked.txt").write_text(
                "cached untracked\n",
                encoding="utf-8",
            )
            return context.next_response("modify")

        first = evaluation.run(
            "cached-git",
            modify,
            workspace=factory,
            cache_key="cached-git-v1",
        )
        second = evaluation.run(
            "cached-git",
            lambda context: (_ for _ in ()).throw(
                AssertionError("cache hit executed program")
            ),
            workspace=factory,
            cache_key="cached-git-v1",
        )

        assert second.cache_hit is True
        assert second.workspace is not None
        assert second.workspace.joinpath("tracked.txt").read_text(
            encoding="utf-8"
        ) == "cached change\n"
        assert second.workspace.joinpath("untracked.txt").read_text(
            encoding="utf-8"
        ) == "cached untracked\n"
        assert second.changed_paths == first.changed_paths


def test_existing_path_requires_explicit_workspace_for_continuation(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    environment = ReplayEnvironment(["first", "second"])
    with AgentEval(
        default_environment=environment,
        artifact_root=tmp_path / "artifacts",
    ) as evaluation:
        parent = evaluation.run(
            "parent",
            lambda context: context.next_response("one"),
            workspace=workspace,
        )
        child = evaluation.run(
            "child",
            lambda context: context.next_response("two"),
            continue_from=parent,
        )

    assert child.error is not None
    assert child.error.phase == "workspace.restore"