from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


def _load_module_from_path(module_name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _load_runtime_module(repo_root: Path) -> ModuleType:
    runtime_path = (
        repo_root / "cloud-orchestrator" / "runtime" / "python" / "runtime.py"
    )
    return _load_module_from_path("_cloud_runtime_workdir_test_runtime", runtime_path)


def test_initialize_runtime_chdirs_to_workspace_before_agent_application(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    instance_dir = tmp_path / "instance"
    transfer_dir = tmp_path / "transfer"
    workspace_dir = instance_dir / "workspace"
    sessions_dir = instance_dir / "sessions"
    config_path = instance_dir / "config" / "config.json"
    config_assets_dir = instance_dir / "config" / "assets"

    transfer_config = transfer_dir / ".cloud-agent" / "config"
    transfer_config.mkdir(parents=True)
    (transfer_config / "config.json").write_text(
        '{"providers": {}, "agents": {}}',
        encoding="utf-8",
    )
    (transfer_dir / "committed.txt").write_text("project file\n", encoding="utf-8")

    monkeypatch.setenv("CLOUD_AGENT_INSTANCE_DIR", str(instance_dir))
    monkeypatch.setenv("CLOUD_AGENT_WORKSPACE_DIR", str(workspace_dir))
    monkeypatch.setenv("CLOUD_AGENT_SESSIONS_DIR", str(sessions_dir))
    monkeypatch.setenv("CLOUD_AGENT_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("CONFIG_DIR", str(config_assets_dir))
    monkeypatch.setenv("TRANSFER_DIR", str(transfer_dir))

    old_cwd = Path.cwd()
    runtime = _load_runtime_module(repo_root)
    constructed_cwd: list[Path] = []

    class FakeAgentApplication:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            constructed_cwd.append(Path.cwd().resolve())

    monkeypatch.setattr(runtime.cloud_runtime, "AgentApplication", FakeAgentApplication)
    monkeypatch.setattr(runtime.cloud_runtime, "InMemoryEventStore", lambda: object())
    monkeypatch.setattr(
        runtime.cloud_runtime,
        "FilesystemSnapshotSelectionStore",
        lambda _path: object(),
    )

    try:
        runtime._initialize_runtime()
        codex_tools_root = repo_root / "plugins" / "codex-tools" / "src" / "codex_tools"
        apply_patch_runtime = _load_module_from_path(
            "_cloud_runtime_test_apply_patch_runtime",
            codex_tools_root / "apply_patch_runtime.py",
        )
        workdir = _load_module_from_path(
            "_cloud_runtime_test_workdir",
            codex_tools_root / "workdir.py",
        )

        config = {"working_directory": ".", "allowed_paths": ["."]}
        patch_result = apply_patch_runtime.execute_apply_patch_text(
            "*** Begin Patch\n"
            "*** Add File: patched.txt\n"
            "+patched in workspace\n"
            "*** End Patch\n",
            config=config,
        )

        assert workdir.resolve_turn_cwd(config) == str(workspace_dir.resolve())
        assert patch_result["success"] is True
        assert (workspace_dir / "patched.txt").read_text(
            encoding="utf-8"
        ) == "patched in workspace"
    finally:
        os.chdir(old_cwd)
        runtime.server_mod._agent_app = None
        sys.modules.pop(runtime.__name__, None)
        sys.modules.pop("_cloud_runtime_test_apply_patch_runtime", None)
        sys.modules.pop("_cloud_runtime_test_workdir", None)

    assert constructed_cwd == [workspace_dir.resolve()]
    assert (workspace_dir / "committed.txt").read_text(
        encoding="utf-8"
    ) == "project file\n"
    assert runtime._runtime_status_snapshot()["ready"] is True
