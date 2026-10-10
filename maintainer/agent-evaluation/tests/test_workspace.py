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
        assert (
            second.workspace.joinpath("tracked.txt").read_text(encoding="utf-8")
            == "cached change\n"
        )
        assert (
            second.workspace.joinpath("untracked.txt").read_text(encoding="utf-8")
            == "cached untracked\n"
        )
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


def test_path_workspace_inside_parent_repo_has_no_ambient_git_fingerprint(
    tmp_path: Path,
) -> None:
    """A bare path workspace must not adopt the surrounding repo's HEAD.

    Continuation runs pass the parent run's workspace (a plain path
    inside the evaluation artifact tree, which itself lives inside a
    larger git checkout). Embedding that ambient repo's HEAD or status
    in the prepared-workspace fingerprint rotates the execution-cache
    key on every commit in the surrounding checkout, so identical
    requests never replay across invocations. Only a repository whose
    root is the workspace itself counts as a git workspace.
    """

    from agent_eval.workspace import prepare_workspace

    # A parent repo with a commit, and a nested plain workspace dir.
    parent = tmp_path / "parent-repo"
    (parent / "nested").mkdir(parents=True)
    subprocess.run(["git", "-C", str(parent), "init", "-q"], check=True)
    subprocess.run(
        ["git", "-C", str(parent), "commit", "--allow-empty", "-m", "base"],
        check=True,
        env={
            **__import__("os").environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.invalid",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.invalid",
        },
    )
    workspace = parent / "nested"
    (workspace / "file.txt").write_text("content", encoding="utf-8")

    prepared = prepare_workspace(workspace, run_dir=tmp_path / "run")

    assert prepared.git_root is None
    assert prepared.fingerprint is not None
    assert prepared.fingerprint["path_kind"] == "directory"
    assert prepared.fingerprint["revision"] is None
    # A fresh commit in the ambient repo must not change the fingerprint.
    subprocess.run(
        ["git", "-C", str(parent), "commit", "--allow-empty", "-m", "next"],
        check=True,
        env={
            **__import__("os").environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.invalid",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.invalid",
        },
    )
    prepared_again = prepare_workspace(workspace, run_dir=tmp_path / "run2")
    assert prepared_again.fingerprint == prepared.fingerprint
