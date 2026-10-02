from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest

from agent_app.application_future import AgentApplication
from agent_app import plugin_cache


def _app(tmp_path: Path, plugins: list[object] | None = None) -> AgentApplication:
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "plugins": plugins or [],
                "plugin_policy": {"allow_bash_tools": True},
            }
        ),
        encoding="utf-8",
    )
    return AgentApplication(config, tmp_path / "sessions")


def test_application_reclaims_legacy_revisions_and_managed_pip_cache(tmp_path: Path) -> None:
    root = tmp_path / ".plugin_cache"
    cache = root / "plugins"
    for path in (
        cache / "old@rev",
        cache / "node" / "old@rev",
        cache / "bash" / "old@rev",
        cache / "src" / "plugin_clone_abandoned",
        cache / ".abandoned@rev.tmp",
        root / "pip" / "http-v2",
    ):
        path.mkdir(parents=True)
        (path / "data").write_text("old", encoding="utf-8")
    old_clone = cache / "src" / "plugin_clone_abandoned"
    os.utime(old_clone, (time.time() - 90000, time.time() - 90000))
    temp_install = cache / ".abandoned@rev.tmp"
    os.utime(temp_install, (time.time() - 90000, time.time() - 90000))
    lock_file = cache / ".locks" / "old@rev.lock"
    lock_file.parent.mkdir()
    lock_file.touch()
    external = tmp_path / "my-pip-cache"
    external.mkdir()
    (external / "keep").write_text("yes", encoding="utf-8")

    app = _app(tmp_path)
    try:
        assert not (cache / "old@rev").exists()
        assert not (cache / "node" / "old@rev").exists()
        assert not (cache / "bash" / "old@rev").exists()
        assert not old_clone.exists()
        assert not temp_install.exists()
        assert not lock_file.exists()
        assert not (root / "pip").exists()
        assert (external / "keep").exists()
    finally:
        app.close()


def test_live_process_lease_protects_plugin_during_other_application_startup(
    tmp_path: Path,
) -> None:
    cache = tmp_path / ".plugin_cache" / "plugins"
    tool = Path(__file__).parent / "fixtures" / "bash_tools" / "read_line_range.bash"
    script = """
import json, sys
from pathlib import Path
from agent_app.plugin_manager import PluginManager
mgr = PluginManager(cache_dir=Path(sys.argv[1]), policy={"allow_bash_tools": True})
result = mgr.resolve_all([{"bash_tool": {"file": sys.argv[2]}}])
assert not result.errors, result.errors
path = next((Path(sys.argv[1]) / "bash").glob("*@*"))
print(json.dumps({"path": str(path), "name": result.classes[0].name}), flush=True)
sys.stdin.readline()
assert path.is_file() is False and (path / Path(sys.argv[2]).name).is_file()
mgr.close()
"""
    child = subprocess.Popen(
        [sys.executable, "-c", script, str(cache), str(tool)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join(
                [str(Path(__file__).resolve().parents[1]), os.environ.get("PYTHONPATH", "")]
            ),
        },
    )
    try:
        assert child.stdout is not None
        line = child.stdout.readline()
        assert line, child.stderr.read() if child.stderr else ""
        details = json.loads(line)
        selected = Path(details["path"])
        assert details["name"] == "read_line_range"
        lease = next((cache.parent / ".plugins.cache_control" / "leases").glob("*.json"))
        data = json.loads(lease.read_text(encoding="utf-8"))
        data["expires_at"] = 0
        lease.write_text(json.dumps(data), encoding="utf-8")

        app = _app(tmp_path)
        app.close()
        assert selected.is_dir()
        assert child.stdin is not None
        child.stdin.write("\n")
        child.stdin.flush()
        assert child.wait(timeout=10) == 0, child.stderr.read() if child.stderr else ""

        app = _app(tmp_path)
        app.close()
        assert not selected.exists()
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=10)


def test_selected_install_is_kept_when_application_sweeps(tmp_path: Path) -> None:
    tool = Path(__file__).parent / "fixtures" / "bash_tools" / "read_line_range.bash"
    app = _app(tmp_path, [{"bash_tool": {"file": str(tool)}}])
    try:
        cache = tmp_path / ".plugin_cache" / "plugins"
        selected = next((cache / "bash").glob("*@*"))
        old = cache / "bash" / "unused@rev"
        old.mkdir()
        app2 = _app(tmp_path)
        try:
            assert selected.is_dir()
            assert not old.exists()
        finally:
            app2.close()
    finally:
        app.close()


def test_crashed_owner_is_reclaimed_after_lease_expiry(tmp_path: Path) -> None:
    cache = tmp_path / ".plugin_cache" / "plugins"
    install = cache / "bash" / "crashed@rev"
    install.mkdir(parents=True)
    (install / "tool.bash").write_text("#!/bin/bash\n", encoding="utf-8")
    script = """
import sys
from pathlib import Path
from agent_app.plugin_cache import PluginCache
owner = PluginCache(Path(sys.argv[1]))
owner.claim(Path(sys.argv[2]))
print("READY", flush=True)
sys.stdin.readline()
"""
    child = subprocess.Popen(
        [sys.executable, "-c", script, str(cache), str(install)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join(
                [str(Path(__file__).resolve().parents[1]), os.environ.get("PYTHONPATH", "")]
            ),
        },
    )
    try:
        assert child.stdout is not None
        assert child.stdout.readline().strip() == "READY"
        child.kill()
        child.wait(timeout=10)
        lease = next((cache.parent / ".plugins.cache_control" / "leases").glob("*.json"))
        data = json.loads(lease.read_text(encoding="utf-8"))
        data["expires_at"] = 0
        lease.write_text(json.dumps(data), encoding="utf-8")
        app = _app(tmp_path)
        app.close()
        assert not install.exists()
        assert not lease.exists()
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=10)


def test_live_owner_refreshes_lease_until_close(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(plugin_cache, "HEARTBEAT_SECONDS", 0.02)
    owner = plugin_cache.PluginCache(tmp_path / "plugins")
    try:
        first = json.loads(owner.lease_path.read_text(encoding="utf-8"))["expires_at"]
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            refreshed = json.loads(owner.lease_path.read_text(encoding="utf-8"))["expires_at"]
            if refreshed > first:
                break
            time.sleep(0.01)
        assert refreshed > first
    finally:
        owner.close()
    assert not owner.lease_path.exists()


@pytest.mark.parametrize("via_pip_args", [False, True])
def test_explicit_pip_cache_is_not_cleaned(tmp_path: Path, via_pip_args: bool) -> None:
    pip_cache = tmp_path / "pip"
    if via_pip_args:
        pip_cache = tmp_path / ".plugin_cache" / "pip"
    pip_cache.mkdir(parents=True)
    (pip_cache / "keep").write_text("yes", encoding="utf-8")
    config = tmp_path / "config.json"
    policy = (
        {"pip_args": ["--cache-dir", str(pip_cache)]}
        if via_pip_args
        else {"pip_cache_dir": str(pip_cache)}
    )
    config.write_text(
        json.dumps({"plugin_policy": policy}),
        encoding="utf-8",
    )
    app = AgentApplication(config, tmp_path / "sessions")
    try:
        assert (pip_cache / "keep").read_text(encoding="utf-8") == "yes"
    finally:
        app.close()


@pytest.mark.skipif(shutil.which("node") is None, reason="node executable unavailable")
def test_node_tool_can_run_after_another_application_sweeps(tmp_path: Path) -> None:
    tool = tmp_path / "tool.js"
    tool.write_text("export default { name: 'cached_node_tool' };\n", encoding="utf-8")
    cache = tmp_path / ".plugin_cache" / "plugins"
    script = """
import json, sys
from pathlib import Path
from agent_app.plugin_manager import PluginManager
mgr = PluginManager(cache_dir=Path(sys.argv[1]))
res = mgr.resolve_all([{"node_tool": {"file": sys.argv[2], "id": "cached_node_tool"}}])
assert not res.errors, res.errors
path = next((Path(sys.argv[1]) / "node").glob("*@*"))
print(json.dumps({"path": str(path), "name": res.classes[0].name}), flush=True)
sys.stdin.readline()
from subprocess import check_output
assert check_output(["node", "--input-type=module", "-e",
    "import x from " + repr((path / "tool.js").as_uri()) + "; console.log(x.name)"]).decode().strip() == "cached_node_tool"
mgr.close()
"""
    child = subprocess.Popen(
        [sys.executable, "-c", script, str(cache), str(tool)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join(
                [str(Path(__file__).resolve().parents[1]), os.environ.get("PYTHONPATH", "")]
            ),
        },
    )
    try:
        assert child.stdout is not None
        line = child.stdout.readline()
        assert line, child.stderr.read() if child.stderr else ""
        details = json.loads(line)
        selected = Path(details["path"])
        assert details["name"] == "cached_node_tool"
        app = _app(tmp_path)
        app.close()
        assert selected.is_dir()
        assert child.stdin is not None
        child.stdin.write("\n")
        child.stdin.flush()
        assert child.wait(timeout=10) == 0, child.stderr.read() if child.stderr else ""
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=10)


@pytest.mark.integration
def test_python_plugin_stays_importable_across_another_startup(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    package = project / "cacheleasefixture"
    package.mkdir(parents=True)
    (project / "setup.py").write_text(
        "from setuptools import setup\n"
        "setup(name='cacheleasefixture', version='0.1', packages=['cacheleasefixture'])\n",
        encoding="utf-8",
    )
    (package / "__init__.py").write_text(
        "class Plugin:\n"
        "    name = 'cache_lease_fixture'\n"
        "    def init(self, config): return {'alive': True}\n"
        "    def get_tool_schemas(self, state): return []\n",
        encoding="utf-8",
    )
    alternate_project = tmp_path / "alternate" / "project"
    shutil.copytree(project, alternate_project)
    cache = tmp_path / ".plugin_cache" / "plugins"
    script = """
import json, sys
from pathlib import Path
from agent_app.plugin_manager import PluginManager
mgr = PluginManager(cache_dir=Path(sys.argv[1]))
res = mgr.resolve_all([{"path": sys.argv[2], "entry": "cacheleasefixture.Plugin"}])
assert not res.errors, res.errors
cls = res.classes[0]
path = next(Path(sys.argv[1]).glob("project@*"))
print("CACHE_READY:" + json.dumps({"path": str(path), "metadata": json.loads((path / "plugin_metadata.json").read_text())}), flush=True)
sys.stdin.readline()
assert cls().init({}) == {"alive": True}
assert path.is_dir()
mgr.close()
"""
    child = subprocess.Popen(
        [sys.executable, "-c", script, str(cache), str(project)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join(
                [str(Path(__file__).resolve().parents[1]), os.environ.get("PYTHONPATH", "")]
            ),
        },
    )
    try:
        assert child.stdout is not None
        line = next(
            (item for item in child.stdout if item.startswith("CACHE_READY:")),
            "",
        )
        assert line, child.stderr.read() if child.stderr else ""
        details = json.loads(line.removeprefix("CACHE_READY:"))
        selected = Path(details["path"])
        assert not (tmp_path / ".plugin_cache" / "pip").exists()
        app = _app(
            tmp_path,
            [
                {
                    "path": str(alternate_project),
                    "entry": "cacheleasefixture.Plugin",
                }
            ],
        )
        app.close()
        assert selected.is_dir()
        assert child.stdin is not None
        child.stdin.write("\n")
        child.stdin.flush()
        assert child.wait(timeout=10) == 0, child.stderr.read() if child.stderr else ""
        app = _app(tmp_path)
        app.close()
        assert not selected.exists()
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=10)
