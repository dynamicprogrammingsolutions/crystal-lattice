"""E2E tests that verify plugin loading via LocalPathSource and GitInstallerSource
using a permanent fixture directory with two tool plugins (file_reader, file_writer)
and an AgentApplication configured with Ollama + tools + reasoning.

These tests mirror the application-layer Ollama tools integration tests but load
tools from a local path and from a local git repository to exercise the plugin
manager/loaders.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
import uuid
from typing import Any, Dict, Optional

import pytest

from agent_app.application_future import AgentApplication
from agent_core import Session
from agent_core.utils import get_logger


logger = get_logger("test")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OPENAI_BASE_URL = f"{OLLAMA_HOST}/v1"
MODEL_TOOLS = os.getenv("OLLAMA_MODEL_TOOLS", "qwen3:0.6b")

REPO_TMP_DIR = Path(__file__).resolve().parents[3] / "tmp"
REPO_TMP_DIR.mkdir(parents=True, exist_ok=True)


def _which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def _run(cmd: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)


@pytest.fixture(scope="module")
def ensure_model() -> None:
    """Ensure that Ollama and the tools-capable model are available, else skip."""

    if _which("ollama") is None:
        pytest.skip("ollama is not installed; skipping e2e plugin tests with Ollama")
    try:
        _run(["ollama", "ps"], timeout=30)
    except Exception:
        pytest.skip("ollama command unavailable or not responding; skipping")

    try:
        cp = _run(["ollama", "pull", MODEL_TOOLS], timeout=1200)
        if cp.returncode != 0:
            msg = cp.stderr.decode("utf-8", errors="ignore")
            pytest.skip(f"failed to pull model {MODEL_TOOLS}: {msg}")
    except Exception as e:  # pragma: no cover - environment dependent
        pytest.skip(f"could not pull model {MODEL_TOOLS}: {e}")


def _resolve_config_path(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / "configs" / name


def _collect_events(
    app: AgentApplication,
    session_id: str,
    *,
    stream: bool,
    overrides: Optional[Dict[str, Any]] = None,
    print_stream: bool = False,
) -> list[Dict[str, Any]]:
    ctx = app.load_session(session_id)
    assert ctx is not None, "session must exist"
    core, base_config, session = ctx
    events: list[Dict[str, Any]] = []
    for ev in app.send_request(core, session, base_config, overrides or {}, stream=stream):
        events.append(ev)
        if print_stream and ev["type"] == "partial":
            msg = ev.get("message", {})
            print(msg.get("content", ""), end="", flush=True)
    return events


def _compose_read_write_prompt(write_path: str, read_path: str, content: str) -> str:
    return (
        "Perform two tool actions in order: first write, then read.\n"
        "1) Use write_file to write the exact text below to the file path provided.\n"
        f"   - file_path: {write_path}\n"
        f"   - content: {content}\n"
        "2) Then use read_file to read the exact same file path.\n"
        "3) Finally, answer with the file's content.\n"
        "You MUST use the tools; do not guess or skip steps."
    )



def _make_local_env(tmp_path: Path) -> Dict[str, str]:
    env = dict(os.environ)
    env["PLUGIN_CACHE_DIR"] = str(tmp_path / "plugin_cache")
    # Must be the parent directory that contains the 'dev_plugins' package
    env["DEV_PLUGINS_DIR"] = str(Path(__file__).parent / "fixtures")
    env["OPENAI_BASE_URL"] = OPENAI_BASE_URL
    env["OLLAMA_MODEL_TOOLS"] = MODEL_TOOLS
    env["REPO_TMP_DIR"] = str(REPO_TMP_DIR)
    return env


@pytest.mark.ollama
def test_agent_application_with_localpath_plugins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ensure_model: None) -> None:
    """Verify loading dev plugins via LocalPathSource and execute a read-file scenario."""

    env = _make_local_env(tmp_path)
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    # Sanity-check: manager loads dev tools from LocalPathSource into 'tools' kind
    from agent_app.plugin_manager import PluginManager
    mgr = PluginManager(cache_dir=Path(env["PLUGIN_CACHE_DIR"]))
    canonical_tools = [
        {"spec": f"path:{env['DEV_PLUGINS_DIR']}::dev_plugins.file_reader_tool.FileReaderTool", "kind": None},
        {"spec": f"path:{env['DEV_PLUGINS_DIR']}::dev_plugins.file_writer_tool.FileWriterTool", "kind": None},
    ]
    core_kinds, app_classes, errs = mgr.load_plugins(canonical_tools)
    assert errs == []
    assert len(core_kinds.get("tools", [])) == 2

    config_path = _resolve_config_path("localpath_plugins.json")
    session_root = tmp_path / "sessions_local"
    app = AgentApplication(str(config_path), str(session_root))

    # Prepare paths and desired content for the tool sequence
    write_path = str(REPO_TMP_DIR / f"e2e_local_write_{uuid.uuid4().hex}.txt")
    read_path = write_path
    desired = "HELLO_FROM_E2E_LOCALPATH"

    try:
        core, base_config, session = app.create_session("default")
        session_id = session.session_id
        session = core.add_message(session, "system", "You are helpful. Always use tools and follow instructions exactly.")
        session = core.add_message(session, "user", _compose_read_write_prompt(write_path, read_path, desired))
        app.save_session(session)

        events = _collect_events(app, session_id, stream=False, overrides=None, print_stream=False)
        # Assert tool executions observed
        tool_result_events = [ev for ev in events if ev.get("type") == "tool_results"]
        assert tool_result_events, "expected tool_results events"
        tool_msgs: list[Dict[str, Any]] = []
        for ev in tool_result_events:
            tool_msgs.extend(ev.get("messages") or [])
        tool_names = [m.get("metadata", {}).get("tool_name") for m in tool_msgs]
        assert "write_file" in tool_names, f"expected write_file in tool_results, saw {tool_names}"
        assert "read_file" in tool_names, f"expected read_file in tool_results, saw {tool_names}"
    finally:
        pass


def _init_git_repo_from_fixture(src_dir: Path, repo_dir: Path) -> str:
    # Copy fixture tree
    shutil.copytree(src_dir, repo_dir, dirs_exist_ok=True)
    # Minimal setup.py to allow pip install of the package `dev_plugins`
    (repo_dir / "setup.py").write_text(
        "from setuptools import setup\nsetup(name='dev_plugins', version='0.0.1', packages=['dev_plugins'])",
        encoding="utf-8",
    )
    subprocess.check_call(["git", "init"], cwd=str(repo_dir))
    subprocess.check_call(["git", "add", "."], cwd=str(repo_dir))
    subprocess.check_call([
        "git",
        "-c",
        "user.email=test@example.com",
        "-c",
        "user.name=Test User",
        "commit",
        "-m",
        "init",
    ], cwd=str(repo_dir))
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(repo_dir)).decode().strip()
    return commit


@pytest.mark.ollama
def test_agent_application_with_git_plugins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ensure_model: None) -> None:
    """Verify loading dev plugins via GitInstallerSource and execute a read-file scenario."""

    env = _make_local_env(tmp_path)
    repo_dir = tmp_path / "dev_plugins_repo"
    commit = _init_git_repo_from_fixture(Path(env["DEV_PLUGINS_DIR"]), repo_dir)
    env["DEV_PLUGINS_GIT_DIR"] = str(repo_dir)
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    # Sanity-check: manager loads dev tools from GitInstallerSource into 'tools' kind
    from agent_app.plugin_manager import PluginManager as _PM
    mgr2 = _PM(cache_dir=Path(env["PLUGIN_CACHE_DIR"]))
    canonical_git = [
        {"spec": f"git+{env['DEV_PLUGINS_GIT_DIR']}::dev_plugins.file_reader_tool.FileReaderTool", "kind": None},
        {"spec": f"git+{env['DEV_PLUGINS_GIT_DIR']}::dev_plugins.file_writer_tool.FileWriterTool", "kind": None},
    ]
    core_kinds_git, app_classes_git, errs_git = mgr2.load_plugins(canonical_git)
    assert errs_git == []
    assert len(core_kinds_git.get("tools", [])) == 2

    config_path = _resolve_config_path("git_plugins.json")
    session_root = tmp_path / "sessions_git"
    app = AgentApplication(str(config_path), str(session_root))

    write_path = str(REPO_TMP_DIR / f"e2e_git_write_{uuid.uuid4().hex}.txt")
    read_path = write_path
    desired = "HELLO_FROM_E2E_GIT"

    try:
        core, base_config, session = app.create_session("default")
        session_id = session.session_id
        session = core.add_message(session, "system", "You are helpful. Always use tools and follow instructions exactly.")
        session = core.add_message(session, "user", _compose_read_write_prompt(write_path, read_path, desired))
        app.save_session(session)

        events = _collect_events(app, session_id, stream=False, overrides=None, print_stream=False)
        tool_result_events = [ev for ev in events if ev.get("type") == "tool_results"]
        assert tool_result_events, "expected tool_results events"
        tool_msgs: list[Dict[str, Any]] = []
        for ev in tool_result_events:
            tool_msgs.extend(ev.get("messages") or [])
        tool_names = [m.get("metadata", {}).get("tool_name") for m in tool_msgs]
        assert "write_file" in tool_names, f"expected write_file in tool_results, saw {tool_names}"
        assert "read_file" in tool_names, f"expected read_file in tool_results, saw {tool_names}"
    finally:
        pass
