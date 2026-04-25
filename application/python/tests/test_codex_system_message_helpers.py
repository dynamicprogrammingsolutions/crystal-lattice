from __future__ import annotations

import runpy
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HELPERS_ROOT = (
    REPO_ROOT
    / "application"
    / "python"
    / "agent_terminal_app"
    / "default_config"
    / "system_messages"
    / "helpers"
)


def test_codex_runtime_resolves_relative_working_directory(monkeypatch, tmp_path: Path) -> None:
    workspace = tmp_path / "repo" / "workspace"
    workspace.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)

    namespace = runpy.run_path(
        str(HELPERS_ROOT / "codex_runtime.py"),
        init_globals={"CONFIG": {"working_directory": "repo/workspace"}},
    )

    assert namespace["cwd"] == str(workspace.resolve())
    assert isinstance(namespace["shell"], str)
    assert namespace["shell"]


def test_codex_helpers_render_context_from_effective_working_directory(
    monkeypatch,
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    workspace = repo_root / "workspace"
    workspace.mkdir(parents=True)

    (tmp_path / "AGENTS.md").write_text("process instructions", encoding="utf-8")
    (repo_root / "AGENTS.md").write_text("repo instructions", encoding="utf-8")
    (workspace / "AGENTS.md").write_text("workspace instructions", encoding="utf-8")

    subprocess.run(
        ["git", "init"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )

    monkeypatch.chdir(tmp_path)

    runtime_ns = runpy.run_path(
        str(HELPERS_ROOT / "codex_runtime.py"),
        init_globals={"CONFIG": {"working_directory": "repo/workspace"}},
    )
    project_ns = runpy.run_path(
        str(HELPERS_ROOT / "render_codex_project_instructions.py"),
        init_globals=runtime_ns,
    )
    environment_ns = runpy.run_path(
        str(HELPERS_ROOT / "render_codex_environment_context.py"),
        init_globals=runtime_ns,
    )

    project_text = str(project_ns["SYSTEM_MESSAGE_VALUE"])
    environment_text = str(environment_ns["SYSTEM_MESSAGE_VALUE"])

    assert "workspace instructions" in project_text
    assert "repo instructions" in project_text
    assert "process instructions" not in project_text
    assert f"<cwd>{workspace.resolve()}</cwd>" in environment_text
    assert "<shell>" in environment_text