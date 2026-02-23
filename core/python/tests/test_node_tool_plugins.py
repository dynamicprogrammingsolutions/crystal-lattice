from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess

import pytest

from agent_app.application_future import AgentApplication
from agent_app.plugin_manager import PluginManager
from agent_core import AgentCore


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _make_git_js_tool_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "js_tool_repo"
    (repo / "dist").mkdir(parents=True)
    (repo / "package.json").write_text(
        json.dumps(
            {
                "name": "js-git-tool",
                "version": "0.1.0",
                "private": True,
                "type": "module",
                "agent": {"kinds": ["tools"], "tools": [{"id": "js_git_tool", "entry": "dist/index.js"}]},
            }
        ),
        encoding="utf-8",
    )
    (repo / "dist" / "index.js").write_text(
        "export default { name: 'js_git_tool', version: '0.1.0', getToolSchemas() { return [{type:'function', function:{name:'ping', parameters:{type:'object', properties:{}, required:[]}}}]; }, async executeTool(name) { return name === 'ping' ? { success: true, result: 'pong' } : { success: false, error: 'unknown' }; } };\n",
        encoding="utf-8",
    )
    subprocess.check_call(["git", "init"], cwd=str(repo))
    subprocess.check_call(["git", "add", "."], cwd=str(repo))
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
        cwd=str(repo),
    )
    return repo


@pytest.mark.skipif(shutil.which("node") is None, reason="node executable not available")
def test_plugin_manager_resolves_js_echo_tool(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    mgr = PluginManager(cache_dir=cache_dir, policy={"base_dir": str(_repo_root())})

    res = mgr.resolve_all([
        {"node_tool": {"path": "plugins/js-echo-tool"}},
    ])
    assert res.errors == []
    assert len(res.classes) == 1
    cls = res.classes[0]
    assert getattr(cls, "name", None) == "js_echo_tool"

    core = AgentCore()
    core.register_tool(cls)

    schemas = core.get_tool_schemas({})
    assert any((s.get("function") or {}).get("name") == "echo" for s in schemas)


@pytest.mark.skipif(shutil.which("node") is None, reason="node executable not available")
@pytest.mark.skipif(shutil.which("git") is None, reason="git executable not available")
def test_node_tool_git_local_repo_resolves_and_executes(tmp_path: Path) -> None:
    repo = _make_git_js_tool_repo(tmp_path)
    cache_dir = tmp_path / "cache"
    mgr = PluginManager(cache_dir=cache_dir, policy={"base_dir": str(tmp_path)})

    res = mgr.resolve_all([
        {"node_tool": {"git": str(repo)}},
    ])
    assert res.errors == []
    assert len(res.classes) == 1

    core = AgentCore()
    core.register_tool(res.classes[0])
    items = list(
        core.iter_tool_messages(
            [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "ping", "arguments": {}},
                }
            ],
            config={},
        )
    )
    finals = [it for it in items if isinstance(it, dict) and "part" not in it]
    assert len(finals) == 1
    assert "pong" in finals[0].get("content", "")


@pytest.mark.skipif(shutil.which("node") is None, reason="node executable not available")
def test_node_tool_executes_and_streams_with_state_round_trip(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    mgr = PluginManager(cache_dir=cache_dir, policy={"base_dir": str(_repo_root())})
    res = mgr.resolve_all([
        {"node_tool": {"path": "plugins/js-echo-tool"}},
    ])
    assert res.errors == []
    tool_cls = res.classes[0]

    core = AgentCore()
    core.register_tool(tool_cls)

    tool_calls = [
        {
            "id": "call_1",
            "type": "function",
            "function": {"name": "echo", "arguments": {"value": "hi"}},
        },
        {
            "id": "call_2",
            "type": "function",
            "function": {"name": "echo", "arguments": {"value": "bye"}},
        },
    ]

    items = list(core.iter_tool_messages(tool_calls, config={}))
    partials = [it for it in items if isinstance(it, dict) and "part" in it]
    finals = [it for it in items if isinstance(it, dict) and "part" not in it]

    assert len(finals) == 2
    assert partials, "expected partial tool payloads"

    assert "Echo: hi" in finals[0].get("content", "")
    assert "calls=1" in finals[0].get("content", "")
    assert "Echo: bye" in finals[1].get("content", "")
    assert "calls=2" in finals[1].get("content", "")

    md = finals[1].get("metadata") or {}
    assert md.get("tool_plugin") == "js_echo_tool"
    display = md.get("display") or {}
    assert display.get("type") == "text"
    assert "single_line" in display


@pytest.mark.skipif(shutil.which("node") is None, reason="node executable not available")
def test_node_tool_multiple_exports_resolve_and_execute(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    mgr = PluginManager(cache_dir=cache_dir, policy={"base_dir": str(_repo_root())})
    res = mgr.resolve_all([
        {"node_tool": {"path": "plugins/js-multi-tools"}},
    ])
    assert res.errors == []
    assert {getattr(c, "name", "") for c in res.classes} == {"js_echo", "js_reverse"}

    core = AgentCore()
    for cls in res.classes:
        core.register_tool(cls)

    tool_calls = [
        {
            "id": "call_1",
            "type": "function",
            "function": {"name": "echo", "arguments": {"value": "abc"}},
        },
        {
            "id": "call_2",
            "type": "function",
            "function": {"name": "reverse", "arguments": {"value": "abc"}},
        },
    ]
    items = list(core.iter_tool_messages(tool_calls, config={}))
    finals = [it for it in items if isinstance(it, dict) and "part" not in it]
    assert len(finals) == 2
    assert "abc" in finals[0].get("content", "")
    assert "cba" in finals[1].get("content", "")


@pytest.mark.skipif(shutil.which("node") is None, reason="node executable not available")
def test_node_tool_single_file_spec_executes(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    mgr = PluginManager(cache_dir=cache_dir, policy={"base_dir": str(_repo_root())})
    res = mgr.resolve_all([
        {
            "node_tool": {
                "file": "plugins/js-single-file-tool.js",
                "id": "js_single_file_tool",
                "entry": "js-single-file-tool.js",
            }
        },
    ])
    assert res.errors == []
    assert len(res.classes) == 1

    core = AgentCore()
    core.register_tool(res.classes[0])

    tool_calls = [
        {
            "id": "call_1",
            "type": "function",
            "function": {"name": "upper", "arguments": {"value": "hi"}},
        }
    ]
    items = list(core.iter_tool_messages(tool_calls, config={}))
    finals = [it for it in items if isinstance(it, dict) and "part" not in it]
    assert len(finals) == 1
    assert "HI" in finals[0].get("content", "")


@pytest.mark.skipif(shutil.which("node") is None, reason="node executable not available")
def test_agent_application_lists_node_tool_plugin(tmp_path: Path) -> None:
    repo_root = _repo_root()
    config = {
        "plugin_cache_dir": str(tmp_path / "plugin_cache"),
        "plugin_policy": {"base_dir": str(repo_root)},
        "providers": {"dummy": {"provider": "dummy_provider", "model": "test"}},
        "plugins": [
            "tests.dummy_provider.DummyProvider",
            {"node_tool": {"path": "plugins/js-echo-tool"}},
        ],
        "agents": {"default": {"provider": "dummy"}},
    }
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps(config), encoding="utf-8")

    app = AgentApplication(str(cfg_path), str(tmp_path / "sessions"), core_factory=AgentCore)
    ids = [p["id"] for p in app.list_plugins() if p["kind"] == "tools"]
    assert "js_echo_tool" in ids
