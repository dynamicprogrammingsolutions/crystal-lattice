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
from pathlib import Path
import uuid
from typing import Any, Dict, Optional

import pytest

from agent_app.application_future import AgentApplication

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


def _fixtures_root() -> Path:
    return Path(__file__).parent / "fixtures"


def _repo_files_root() -> Path:
    return _fixtures_root() / "repo_files"


def _assert_tool_results_include(events: list[Dict[str, Any]], expected_tools: set[str]) -> None:
    tool_result_events = [ev for ev in events if ev.get("type") == "tool_results"]
    assert tool_result_events, "expected tool_results events"
    tool_msgs: list[Dict[str, Any]] = []
    for ev in tool_result_events:
        tool_msgs.extend(ev.get("messages") or [])
    tool_names = {m.get("metadata", {}).get("tool_name") for m in tool_msgs}
    missing = expected_tools - tool_names
    assert not missing, f"missing tool results for: {sorted(missing)} (saw {sorted(tool_names)})"


def _run_read_write_scenario(app: AgentApplication, *, label: str) -> None:
    write_path = str(REPO_TMP_DIR / f"e2e_{label}_write_{uuid.uuid4().hex}.txt")
    desired = f"HELLO_FROM_E2E_{label.upper()}"

    core, base_config, session = app.create_session("default")
    session_id = session.session_id
    session = core.add_message(session, "system", "You are helpful. Always use tools and follow instructions exactly.")
    session = core.add_message(session, "user", _compose_read_write_prompt(write_path, write_path, desired))
    app.save_session(session)

    events = _collect_events(app, session_id, stream=False, overrides=None, print_stream=False)
    _assert_tool_results_include(events, {"write_file", "read_file"})


def _copy_repo_file(rel_path: str, *, dest: Path) -> None:
    src = _repo_files_root() / rel_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


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

    _run_read_write_scenario(app, label="localpath")


@pytest.mark.ollama
def test_agent_application_with_localpath_plugins_entries_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ensure_model: None
) -> None:
    """E2E: local path + entries list (dict spec) + mapping-by-kind."""

    env = _make_local_env(tmp_path)
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    config_path = _resolve_config_path("localpath_entries_plugins.json")
    session_root = tmp_path / "sessions_local_entries"
    app = AgentApplication(str(config_path), str(session_root))
    _run_read_write_scenario(app, label="local_entries")


@pytest.mark.ollama
def test_agent_application_with_localpath_plugins_module_only_descriptor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ensure_model: None
) -> None:
    """E2E: local path + module-only spec using agent_plugin.json descriptor."""

    env = _make_local_env(tmp_path)

    desc_root = tmp_path / "dev_plugins_desc"
    pkg_dir = desc_root / "dev_plugins"
    shutil.copytree(Path(env["DEV_PLUGINS_DIR"]) / "dev_plugins", pkg_dir, dirs_exist_ok=True)
    _copy_repo_file("dev_plugins/extra_tool.py", dest=pkg_dir / "extra_tool.py")
    _copy_repo_file("dev_plugins/agent_plugin.json", dest=desc_root / "agent_plugin.json")
    _copy_repo_file("setup_with_descriptor.py", dest=desc_root / "setup.py")

    env["DEV_PLUGINS_DESC_DIR"] = str(desc_root)
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    # Sanity-check: module-only + descriptor should exclude ExtraTool.
    from agent_app.plugin_manager import PluginManager

    mgr = PluginManager(cache_dir=Path(env["PLUGIN_CACHE_DIR"]))
    core_kinds, _apps, errs = mgr.load_plugins(
        [{"spec": f"path:{env['DEV_PLUGINS_DESC_DIR']}::dev_plugins", "kind": None}]
    )
    assert errs == []
    tool_class_names = {cls.__name__ for cls in core_kinds.get("tools", [])}
    assert tool_class_names == {"FileReaderTool", "FileWriterTool"}

    config_path = _resolve_config_path("localpath_module_only_plugins.json")
    session_root = tmp_path / "sessions_local_module_only"
    app = AgentApplication(str(config_path), str(session_root))
    _run_read_write_scenario(app, label="local_module_only")


@pytest.mark.ollama
def test_agent_application_with_localpath_plugins_canonical_items(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ensure_model: None
) -> None:
    """E2E: local path referenced via canonical items with explicit kinds."""

    env = _make_local_env(tmp_path)
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    config_path = _resolve_config_path("localpath_canonical_plugins.json")
    session_root = tmp_path / "sessions_local_canonical"
    app = AgentApplication(str(config_path), str(session_root))
    _run_read_write_scenario(app, label="local_canonical")


def _init_git_repo_from_fixture(src_dir: Path, repo_dir: Path) -> str:
    # Copy only the package directory; keep the repo fixture small/clean.
    shutil.copytree(src_dir / "dev_plugins", repo_dir / "dev_plugins", dirs_exist_ok=True)
    _copy_repo_file("setup_basic.py", dest=repo_dir / "setup.py")
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


def _init_git_repo_from_fixture_with_descriptor(src_dir: Path, repo_dir: Path) -> str:
    """Create a local git repo with a root plugin descriptor and an extra tool."""

    shutil.copytree(src_dir / "dev_plugins", repo_dir / "dev_plugins", dirs_exist_ok=True)
    pkg_dir = repo_dir / "dev_plugins"
    _copy_repo_file("dev_plugins/extra_tool.py", dest=pkg_dir / "extra_tool.py")
    _copy_repo_file("dev_plugins/agent_plugin.json", dest=repo_dir / "agent_plugin.json")
    _copy_repo_file("setup_with_descriptor.py", dest=repo_dir / "setup.py")
    subprocess.check_call(["git", "init"], cwd=str(repo_dir))
    subprocess.check_call(["git", "add", "."], cwd=str(repo_dir))
    subprocess.check_call(
        [
            "git",
            "-c",
            "user.email=test@example.com",
            "-c",
            "user.name=Test User",
            "commit",
            "-m",
            "init",
        ],
        cwd=str(repo_dir),
    )
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

    _run_read_write_scenario(app, label="git")


@pytest.mark.ollama
def test_agent_application_with_git_plugins_entries_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ensure_model: None
) -> None:
    """E2E: git installer + entries list dict spec."""

    env = _make_local_env(tmp_path)
    repo_dir = tmp_path / "dev_plugins_repo_entries"
    _init_git_repo_from_fixture(Path(env["DEV_PLUGINS_DIR"]), repo_dir)
    env["DEV_PLUGINS_GIT_DIR"] = str(repo_dir)
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    config_path = _resolve_config_path("git_entries_plugins.json")
    session_root = tmp_path / "sessions_git_entries"
    app = AgentApplication(str(config_path), str(session_root))
    _run_read_write_scenario(app, label="git_entries")


@pytest.mark.ollama
def test_agent_application_with_git_plugins_module_only_descriptor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ensure_model: None
) -> None:
    """E2E: git installer + module-only spec using agent_plugin.json descriptor."""

    env = _make_local_env(tmp_path)
    repo_dir = tmp_path / "dev_plugins_repo_module_only"
    _init_git_repo_from_fixture_with_descriptor(Path(env["DEV_PLUGINS_DIR"]), repo_dir)
    env["DEV_PLUGINS_GIT_DIR"] = str(repo_dir)
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    from agent_app.plugin_manager import PluginManager

    mgr = PluginManager(cache_dir=Path(env["PLUGIN_CACHE_DIR"]))
    core_kinds, _apps, errs = mgr.load_plugins(
        [{"spec": f"git+{env['DEV_PLUGINS_GIT_DIR']}::dev_plugins", "kind": None}]
    )
    assert errs == []
    tool_class_names = {cls.__name__ for cls in core_kinds.get("tools", [])}
    assert tool_class_names == {"FileReaderTool", "FileWriterTool"}

    config_path = _resolve_config_path("git_module_only_plugins.json")
    session_root = tmp_path / "sessions_git_module_only"
    app = AgentApplication(str(config_path), str(session_root))
    _run_read_write_scenario(app, label="git_module_only")


@pytest.mark.ollama
def test_agent_application_with_git_plugins_canonical_items(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ensure_model: None
) -> None:
    """E2E: git installer referenced via canonical items with explicit kinds."""

    env = _make_local_env(tmp_path)
    repo_dir = tmp_path / "dev_plugins_repo_canonical"
    _init_git_repo_from_fixture(Path(env["DEV_PLUGINS_DIR"]), repo_dir)
    env["DEV_PLUGINS_GIT_DIR"] = str(repo_dir)
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    config_path = _resolve_config_path("git_canonical_plugins.json")
    session_root = tmp_path / "sessions_git_canonical"
    app = AgentApplication(str(config_path), str(session_root))
    _run_read_write_scenario(app, label="git_canonical")
