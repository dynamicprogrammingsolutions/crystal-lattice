from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def git_repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repository"
    repository.mkdir()
    subprocess.run(["git", "init"], cwd=repository, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Agent Eval Tests"],
        cwd=repository,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "agent-eval@example.invalid"],
        cwd=repository,
        check=True,
    )
    repository.joinpath("tracked.txt").write_text("initial\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repository, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial fixture"],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    return repository
