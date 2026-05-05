from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List

import pytest

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from cloud_agent_app.cloud_agent_app_plugin import CloudAgentAppPlugin
from cloud_agent_app.cloud_agent_profiles import resolve_cloud_agent_profiles
from cloud_agent_app.cloud_agent_transfer import (
    CLOUD_WORKSPACE_DIR,
    CLOUD_PLUGIN_CACHE_DIR,
    build_portable_config,
    copy_config_assets,
    scan_env_placeholders,
    write_runtime_env,
)


def _plugin_path() -> str:
    return str(Path(__file__).resolve().parents[1])


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _write_config(tmp_path: Path, transfer_script: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {"echo": {"provider": "echo_openai_like", "model": "test-model"}},
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            f"path:{_plugin_path()}",
        ],
        "agents": {"default": {"provider": "echo"}},
        "application": {
            "cloud_agent": {
                "orchestrator_url": "http://orchestrator.test",
                "workspace_dir": str(tmp_path / "workspace"),
                "transfer_method": "managed_ssh",
                "default_transfer_up_profile": "test-transfer",
                "default_sync_down_profile": "test-sync",
                "default_container_profile": "test-runtime",
                "transfer_up_profiles": {
                    "test-transfer": {
                        "local_transfer_script": str(transfer_script),
                        "install_profile": "test-install",
                        "compatible_sync_down_profiles": ["test-sync"],
                    }
                },
                "install_profiles": {
                    "test-install": {
                        "cloud_install_script": str(transfer_script),
                    }
                },
                "sync_down_profiles": {
                    "test-sync": {
                        "cloud_export_script": str(transfer_script),
                        "local_apply_script": str(transfer_script),
                        "compatible_transfer_up_profiles": ["test-transfer"],
                    }
                },
                "container_profiles": {
                    "test-runtime": {
                        "image": "cloud-agent-runtime:latest",
                    }
                },
                "config_assets": {
                    "include_config_dir": True,
                    "exclude": [".plugin_cache"],
                    "max_top_level_entry_bytes": 1024 * 1024,
                },
            }
        },
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _write_script(path: Path, body: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"#!/usr/bin/env bash\nset -euo pipefail\n{body}", encoding="utf-8")
    path.chmod(0o755)
    return path


def _run_cloud_profile_script(script: Path, env: Dict[str, str], *, cwd: Path) -> None:
    subprocess.run(
        [str(script)],
        cwd=str(cwd),
        env={**os.environ, **env},
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_cloud_start_session_ui_element_maps_current_session_id() -> None:
    elements = {
        element["id"]: element for element in CloudAgentAppPlugin().get_ui_elements({})
    }

    element = elements["cloud_start_session_agent"]
    assert element["id"] == "cloud_start_session_agent"
    assert element["action_id"] == "cloud.start_session_agent"
    assert element["param_map"] == {"session_id": "$session.session_id"}
    assert element["condition"] == {
        "not": {"path": "metadata.cloud_agent.instance_id", "exists": True}
    }

    assert elements["cloud_check_session_agent"]["param_map"] == {
        "instance_id": "$session.metadata.cloud_agent.instance_id",
        "session_id": "$session.session_id",
        "token": "$session.metadata.cloud_agent.token",
    }
    assert elements["cloud_sync_down"]["param_map"] == {
        "instance_id": "$session.metadata.cloud_agent.instance_id",
        "session_id": "$session.session_id",
    }
    assert elements["cloud_close_session"]["param_map"] == {
        "instance_id": "$session.metadata.cloud_agent.instance_id",
        "session_id": "$session.session_id",
    }


def test_cloud_start_session_default_wait_timeout_is_short() -> None:
    plugin = CloudAgentAppPlugin()

    assert plugin._start_action_timeout_seconds({}) == 10.0
    assert (
        plugin._start_action_timeout_seconds({"start_action_timeout_seconds": 1}) == 1.0
    )


def test_profile_resolver_selects_default_profiles_and_expands_env_paths(
    tmp_path: Path,
) -> None:
    config_dir = tmp_path / "config"
    workspace = tmp_path / "workspace"
    transfer = _write_script(config_dir / "cloud-agent" / "transfer-up")
    install = _write_script(config_dir / "cloud-agent" / "install")
    export = _write_script(config_dir / "cloud-agent" / "export")
    apply_down = _write_script(config_dir / "cloud-agent" / "apply-down")

    resolved = resolve_cloud_agent_profiles(
        {
            "default_transfer_up_profile": "working-tree-current-state",
            "default_sync_down_profile": "working-tree-patch",
            "default_container_profile": "default-runtime",
            "transfer_up_profiles": {
                "working-tree-current-state": {
                    "local_transfer_script": "${env:CONFIG_DIR}/cloud-agent/transfer-up",
                    "install_profile": "repo-install",
                    "compatible_sync_down_profiles": ["working-tree-patch"],
                }
            },
            "install_profiles": {
                "repo-install": {
                    "cloud_install_script": "${env:CONFIG_DIR}/cloud-agent/install"
                }
            },
            "sync_down_profiles": {
                "working-tree-patch": {
                    "cloud_export_script": "${env:CONFIG_DIR}/cloud-agent/export",
                    "local_apply_script": "${env:CONFIG_DIR}/cloud-agent/apply-down",
                    "compatible_transfer_up_profiles": ["working-tree-current-state"],
                }
            },
            "container_profiles": {
                "default-runtime": {"image": "cloud-agent-runtime:latest"}
            },
        },
        env={"CONFIG_DIR": str(config_dir), "WORKING_DIR": str(workspace)},
    )

    assert resolved["selected_transfer_up_profile"] == "working-tree-current-state"
    assert resolved["selected_install_profile"] == "repo-install"
    assert resolved["selected_sync_down_profile"] == "working-tree-patch"
    assert resolved["selected_container_profile"] == "default-runtime"
    assert resolved["local_transfer_script"] == str(transfer.resolve())
    assert resolved["cloud_setup_script"] == str(install.resolve())
    assert resolved["cloud_export_script"] == str(export.resolve())
    assert resolved["local_apply_script"] == str(apply_down.resolve())
    assert resolved["cloud_mark_synced_script"] is None
    assert resolved["runtime_image"] == "cloud-agent-runtime:latest"


def test_profile_resolver_loads_single_project_config_and_falls_back_to_base_script(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    project_config = workspace / ".cloud-agent" / "cloud-agent.json"
    base_transfer = _write_script(tmp_path / "base-transfer")
    custom_apply = _write_script(workspace / ".cloud-agent" / "scripts" / "apply-down")
    install = _write_script(tmp_path / "install")
    export = _write_script(tmp_path / "export")
    base_apply = _write_script(tmp_path / "base-apply")
    project_config.parent.mkdir(parents=True, exist_ok=True)
    project_config.write_text(
        json.dumps(
            {
                "sync_down_profiles": {
                    "patch": {
                        "local_apply_script": [
                            ".cloud-agent/missing/apply-down",
                            ".cloud-agent/scripts/apply-down",
                        ]
                    }
                },
                "transfer_up_profiles": {
                    "current": {
                        "local_transfer_script": [".cloud-agent/missing/transfer-up"]
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    resolved = resolve_cloud_agent_profiles(
        {
            "default_transfer_up_profile": "current",
            "default_sync_down_profile": "patch",
            "default_container_profile": "runtime",
            "transfer_up_profiles": {
                "current": {
                    "local_transfer_script": str(base_transfer),
                    "install_profile": "install",
                }
            },
            "install_profiles": {"install": {"cloud_install_script": str(install)}},
            "sync_down_profiles": {
                "patch": {
                    "cloud_export_script": str(export),
                    "local_apply_script": str(base_apply),
                }
            },
            "container_profiles": {"runtime": {"image": "runtime:test"}},
        },
        env={"WORKING_DIR": str(workspace), "CONFIG_DIR": str(tmp_path / "config")},
    )

    assert resolved["local_transfer_script"] == str(base_transfer.resolve())
    assert resolved["local_apply_script"] == str(custom_apply.resolve())


def test_profile_resolver_rejects_incompatible_defaults(tmp_path: Path) -> None:
    transfer = _write_script(tmp_path / "transfer")
    install = _write_script(tmp_path / "install")
    export = _write_script(tmp_path / "export")
    apply_down = _write_script(tmp_path / "apply-down")

    with pytest.raises(ValueError, match="not compatible"):
        resolve_cloud_agent_profiles(
            {
                "default_transfer_up_profile": "current",
                "default_sync_down_profile": "patch",
                "default_container_profile": "runtime",
                "transfer_up_profiles": {
                    "current": {
                        "local_transfer_script": str(transfer),
                        "install_profile": "install",
                        "compatible_sync_down_profiles": ["other-patch"],
                    }
                },
                "install_profiles": {"install": {"cloud_install_script": str(install)}},
                "sync_down_profiles": {
                    "patch": {
                        "cloud_export_script": str(export),
                        "local_apply_script": str(apply_down),
                    },
                    "other-patch": {
                        "cloud_export_script": str(export),
                        "local_apply_script": str(apply_down),
                    },
                },
                "container_profiles": {"runtime": {"image": "runtime:test"}},
            },
            env={"WORKING_DIR": str(tmp_path), "CONFIG_DIR": str(tmp_path)},
        )


def test_profile_resolver_rejects_requires_dependency_declarations(
    tmp_path: Path,
) -> None:
    transfer = _write_script(tmp_path / "transfer")

    with pytest.raises(ValueError, match="requires is not supported"):
        resolve_cloud_agent_profiles(
            {
                "default_transfer_up_profile": "current",
                "transfer_up_profiles": {
                    "current": {
                        "local_transfer_script": str(transfer),
                        "install_profile": "install",
                        "requires": {"git": True},
                    }
                },
            },
            env={"WORKING_DIR": str(tmp_path), "CONFIG_DIR": str(tmp_path)},
        )


def test_default_patch_scripts_support_incremental_sync_after_mark_synced(
    tmp_path: Path,
) -> None:
    scripts_root = (
        _repo_root()
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "cloud-agent"
        / "profiles"
    )
    transfer_up = scripts_root / "working-tree-current-state" / "transfer-up"
    install = scripts_root / "repo-install" / "install"
    export = scripts_root / "working-tree-patch" / "export"
    mark_synced = scripts_root / "working-tree-patch" / "mark-synced"
    apply_down = scripts_root / "working-tree-patch" / "apply-down"

    local = tmp_path / "local"
    cloud = tmp_path / "cloud"
    local.mkdir()
    cloud.mkdir()
    subprocess.run(["git", "init"], cwd=local, check=True, stdout=subprocess.PIPE)
    subprocess.run(
        ["git", "config", "user.email", "local@example.invalid"],
        cwd=local,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Local Test"],
        cwd=local,
        check=True,
    )
    (local / "chain.txt").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "chain.txt"], cwd=local, check=True)
    subprocess.run(
        ["git", "commit", "-m", "base"],
        cwd=local,
        check=True,
        stdout=subprocess.PIPE,
    )

    upload = tmp_path / "upload"
    upload.mkdir()
    _run_cloud_profile_script(
        transfer_up,
        {"LOCAL_WORKSPACE_DIR": str(local), "TRANSFER_DIR": str(upload)},
        cwd=local,
    )
    _run_cloud_profile_script(
        install,
        {"CLOUD_WORKSPACE_DIR": str(cloud), "TRANSFER_DIR": str(upload)},
        cwd=cloud,
    )

    (cloud / "chain.txt").write_text("base\nchange1\n", encoding="utf-8")
    sync1 = tmp_path / "sync1"
    sync1.mkdir()
    _run_cloud_profile_script(
        export,
        {"CLOUD_WORKSPACE_DIR": str(cloud), "TRANSFER_DIR": str(sync1)},
        cwd=cloud,
    )
    _run_cloud_profile_script(
        apply_down,
        {"LOCAL_WORKSPACE_DIR": str(local), "TRANSFER_DIR": str(sync1)},
        cwd=local,
    )
    _run_cloud_profile_script(
        mark_synced,
        {"CLOUD_WORKSPACE_DIR": str(cloud)},
        cwd=cloud,
    )

    (cloud / "chain.txt").write_text("base\nchange1\nchange2\n", encoding="utf-8")
    sync2 = tmp_path / "sync2"
    sync2.mkdir()
    _run_cloud_profile_script(
        export,
        {"CLOUD_WORKSPACE_DIR": str(cloud), "TRANSFER_DIR": str(sync2)},
        cwd=cloud,
    )
    _run_cloud_profile_script(
        apply_down,
        {"LOCAL_WORKSPACE_DIR": str(local), "TRANSFER_DIR": str(sync2)},
        cwd=local,
    )

    assert (local / "chain.txt").read_text(encoding="utf-8") == (
        "base\nchange1\nchange2\n"
    )


def test_cloud_start_session_action_runs_transfer_script_and_returns_copy_link(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    env_capture = tmp_path / "env.json"
    transfer_script = tmp_path / "transfer.py"
    transfer_script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import json, os, pathlib",
                f"path = pathlib.Path({str(env_capture)!r})",
                "path.write_text(json.dumps({",
                "  'LOCAL_WORKSPACE_DIR': os.environ.get('LOCAL_WORKSPACE_DIR'),",
                "  'CLOUD_WORKSPACE_DIR': os.environ.get('CLOUD_WORKSPACE_DIR'),",
                "  'TRANSFER_DIR': os.environ.get('TRANSFER_DIR'),",
                "}, sort_keys=True))",
            ]
        ),
        encoding="utf-8",
    )
    transfer_script.chmod(0o755)

    config_path = _write_config(tmp_path, transfer_script)
    app = AgentApplication(
        str(config_path), str(tmp_path / "sessions"), event_store=InMemoryEventStore()
    )
    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "hello cloud", {}, config=base_config)
    app.save_session(session)

    calls: List[Dict[str, Any]] = []
    adapter_calls: List[Dict[str, Any]] = []

    class _Response:
        def __init__(self, payload: Dict[str, Any]) -> None:
            self.payload = payload

        def __enter__(self) -> "_Response":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(self.payload).encode("utf-8")

    def fake_urlopen(request: Any, timeout: float = 30) -> _Response:
        try:
            body = json.loads(request.data.decode("utf-8")) if request.data else {}
        except Exception:
            body = {"binary": True, "length": len(request.data or b"")}
        calls.append(
            {
                "url": request.full_url,
                "body": body,
            }
        )
        if request.full_url.endswith("/transfers"):
            return _Response(
                {
                    "transfer_id": "tr_test",
                    "method": "managed_ssh",
                    "endpoint": {
                        "host": "cloud.example.test",
                        "port": 22000,
                        "username": "transfer",
                        "path": ".",
                        "host_key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestHostKey",
                    },
                }
            )
        if request.full_url.endswith("/transfers/tr_test/ready"):
            return _Response({"transfer_id": "tr_test", "state": "ready"})
        if request.full_url.endswith("/instances"):
            return _Response(
                {
                    "connection_id": "conn_test",
                    "instance_id": "inst_test",
                    "session_id": session.session_id,
                    "state": "running",
                    "token": "tok_test",
                }
            )
        raise AssertionError(f"unexpected URL {request.full_url}")

    def fake_adapter(
        self: CloudAgentAppPlugin,
        state: Dict[str, Any],
        transfer: Dict[str, Any],
        transfer_dir: Path,
        private_key_path: Path,
        *,
        direction: str,
        cwd: Path,
    ) -> None:
        adapter_calls.append(
            {
                "direction": direction,
                "transfer_id": transfer["transfer_id"],
                "transfer_dir": str(transfer_dir),
                "private_key_path": str(private_key_path),
                "cwd": str(cwd),
            }
        )

    monkeypatch.setattr("cloud_agent_app.cloud_agent_app_plugin.urlopen", fake_urlopen)
    monkeypatch.setattr(CloudAgentAppPlugin, "_run_managed_ssh_adapter", fake_adapter)

    result = app.execute_application_action(
        "cloud",
        "cloud.start_session_agent",
        {"session_id": session.session_id},
    )

    assert result["connection_link"].startswith("crystal-lattice-cloud://connect?")
    display = result["display"]
    assert display["actions"][0]["kind"] == "copy_text"
    assert "inst_test" in display["actions"][0]["text"]
    assert calls[0]["url"] == "http://orchestrator.test/transfers"
    assert "public_key" in calls[0]["body"]
    assert "public_host" not in calls[0]["body"]
    assert calls[2]["body"]["session_id"] == session.session_id
    assert calls[2]["body"]["transfer_ref"] == {"transfer_id": "tr_test"}
    assert calls[2]["body"]["runtime_image"] == "cloud-agent-runtime:latest"
    assert calls[2]["body"]["connection_ref"]["reuse"] is True
    assert calls[2]["body"]["connection_ref"]["connection_key"].startswith(
        "cloud-agent-app:"
    )
    assert adapter_calls[0]["direction"] == "upload"
    assert result["mutations"]["updated_session_ids"] == [session.session_id]
    assert result["ui_effects"]["reload_session_ids"] == [session.session_id]

    _core, _base_config, updated_session = app.load_session(session.session_id)
    cloud_agent = updated_session.metadata["cloud_agent"]
    assert cloud_agent["connection_id"] == "conn_test"
    assert cloud_agent["instance_id"] == "inst_test"
    assert cloud_agent["session_id"] == session.session_id
    assert cloud_agent["state"] == "running"
    assert cloud_agent["token"] == "tok_test"
    assert cloud_agent["connection_link"] == result["connection_link"]

    captured = json.loads(env_capture.read_text(encoding="utf-8"))
    assert captured["LOCAL_WORKSPACE_DIR"] == str(workspace.resolve())
    assert captured["CLOUD_WORKSPACE_DIR"] == CLOUD_WORKSPACE_DIR
    assert captured["TRANSFER_DIR"]


def test_cloud_check_session_action_updates_cloud_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    transfer_script = tmp_path / "transfer.py"
    transfer_script.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    transfer_script.chmod(0o755)

    config_path = _write_config(tmp_path, transfer_script)
    app = AgentApplication(
        str(config_path), str(tmp_path / "sessions"), event_store=InMemoryEventStore()
    )
    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "hello cloud", {}, config=base_config)
    app.save_session(
        session.__class__(
            session_id=session.session_id,
            messages=session.messages,
            metadata={
                **session.metadata,
                "cloud_agent": {
                    "instance_id": "inst_test",
                    "session_id": session.session_id,
                    "state": "starting",
                    "token": "tok_test",
                },
            },
        )
    )

    class _Response:
        def __enter__(self) -> "_Response":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(
                {
                    "instance_id": "inst_test",
                    "session_id": session.session_id,
                    "state": "running",
                    "startup_stage": "ready",
                }
            ).encode("utf-8")

    def fake_urlopen(request: Any, timeout: float = 30) -> _Response:
        assert request.full_url == "http://orchestrator.test/instances/inst_test"
        return _Response()

    monkeypatch.setattr("cloud_agent_app.cloud_agent_app_plugin.urlopen", fake_urlopen)

    result = app.execute_application_action(
        "cloud",
        "cloud.check_session_agent",
        {
            "instance_id": "inst_test",
            "session_id": session.session_id,
            "token": "tok_test",
        },
    )

    assert result["state"] == "running"
    assert result["ui_effects"]["reload_session_ids"] == [session.session_id]
    _core, _base_config, updated_session = app.load_session(session.session_id)
    cloud_agent = updated_session.metadata["cloud_agent"]
    assert cloud_agent["state"] == "running"
    assert cloud_agent["startup_stage"] == "ready"
    assert cloud_agent["token"] == "tok_test"


def test_sync_down_marks_cloud_synced_after_local_apply(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    local_apply = _write_script(tmp_path / "apply")
    plugin = CloudAgentAppPlugin()
    calls: List[str] = []

    monkeypatch.setattr(
        plugin,
        "_create_transfer_keypair",
        lambda transfer_dir: {
            "private_key_path": transfer_dir / "key",
            "public_key": "ssh-ed25519 test",
        },
    )
    monkeypatch.setattr(
        plugin,
        "_run_managed_ssh_adapter",
        lambda *args, **kwargs: calls.append("download"),
    )

    def fake_run_script(raw_path: str, env: Dict[str, str], *, cwd: Path) -> None:
        assert raw_path == str(local_apply)
        calls.append("apply")

    monkeypatch.setattr(plugin, "_run_script", fake_run_script)

    def fake_post_json(
        base_url: str, path: str, payload: Dict[str, Any], *, token: Any = None
    ) -> Dict[str, Any]:
        calls.append(path)
        if path == "/transfers":
            return {"transfer_id": "tr_sync", "method": "managed_ssh", "endpoint": {}}
        if path == "/instances/inst_test/export":
            return {"status": "ok"}
        if path == "/instances/inst_test/sync-applied":
            return {"status": "ok"}
        raise AssertionError(path)

    monkeypatch.setattr(plugin, "_post_json", fake_post_json)
    monkeypatch.setattr(plugin, "_delete_transfer", lambda *args, **kwargs: None)

    result = plugin._sync_down(
        app=object(),
        params={"instance_id": "inst_test", "workspace_dir": str(workspace)},
        state={
            "orchestrator_url": "http://orchestrator.test",
            "cloud_export_script": str(tmp_path / "export"),
            "local_apply_script": str(local_apply),
            "cloud_mark_synced_script": str(tmp_path / "mark-synced"),
        },
    )

    assert result["status"] == "ok"
    assert calls == [
        "/transfers",
        "/instances/inst_test/export",
        "download",
        "apply",
        "/instances/inst_test/sync-applied",
    ]


def test_sync_down_does_not_mark_cloud_synced_when_local_apply_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    local_apply = _write_script(tmp_path / "apply")
    plugin = CloudAgentAppPlugin()
    calls: List[str] = []

    monkeypatch.setattr(
        plugin,
        "_create_transfer_keypair",
        lambda transfer_dir: {
            "private_key_path": transfer_dir / "key",
            "public_key": "ssh-ed25519 test",
        },
    )
    monkeypatch.setattr(
        plugin,
        "_run_managed_ssh_adapter",
        lambda *args, **kwargs: calls.append("download"),
    )

    def fake_run_script(raw_path: str, env: Dict[str, str], *, cwd: Path) -> None:
        calls.append("apply")
        raise RuntimeError("apply failed")

    monkeypatch.setattr(plugin, "_run_script", fake_run_script)

    def fake_post_json(
        base_url: str, path: str, payload: Dict[str, Any], *, token: Any = None
    ) -> Dict[str, Any]:
        calls.append(path)
        if path == "/transfers":
            return {"transfer_id": "tr_sync", "method": "managed_ssh", "endpoint": {}}
        if path == "/instances/inst_test/export":
            return {"status": "ok"}
        if path == "/instances/inst_test/sync-applied":
            raise AssertionError("sync-applied should not run after apply failure")
        raise AssertionError(path)

    monkeypatch.setattr(plugin, "_post_json", fake_post_json)
    monkeypatch.setattr(plugin, "_delete_transfer", lambda *args, **kwargs: None)

    with pytest.raises(RuntimeError, match="apply failed"):
        plugin._sync_down(
            app=object(),
            params={"instance_id": "inst_test", "workspace_dir": str(workspace)},
            state={
                "orchestrator_url": "http://orchestrator.test",
                "cloud_export_script": str(tmp_path / "export"),
                "local_apply_script": str(local_apply),
                "cloud_mark_synced_script": str(tmp_path / "mark-synced"),
            },
        )

    assert calls == [
        "/transfers",
        "/instances/inst_test/export",
        "download",
        "apply",
    ]


def test_portable_config_removes_cloud_agent_and_preserves_plugin_owned_paths() -> None:
    raw = {
        "plugin_cache_dir": "${env:CONFIG_DIR}/.plugin_cache/plugins",
        "mixins": {
            "provider_defaults": {
                "working_directory": ".",
                "allowed_paths": [".", "..", "${env:WORKING_DIR}"],
            }
        },
        "application": {
            "tool_output_line_limit": 20,
            "cloud_agent": {
                "orchestrator_url": "${env:CLOUD_ORCHESTRATOR_URL}",
                "orchestrator_token": "${env:CLOUD_ORCHESTRATOR_TOKEN}",
                "workspace_dir": ".",
            },
        },
    }

    portable, manifest = build_portable_config(raw)

    assert portable["plugin_cache_dir"] == CLOUD_PLUGIN_CACHE_DIR
    assert portable["application"] == {"tool_output_line_limit": 20}
    assert portable["mixins"]["provider_defaults"]["working_directory"] == "."
    assert portable["mixins"]["provider_defaults"]["allowed_paths"] == [
        ".",
        "..",
        "${env:WORKING_DIR}",
    ]
    assert {
        "path": "application.cloud_agent",
        "reason": "local_orchestrator_config_removed",
    } in manifest["rewrites"]


def test_portable_config_resolves_mixins_and_keeps_only_selected_agent_provider() -> (
    None
):
    raw = {
        "plugin_cache_dir": "${env:CONFIG_DIR}/.plugin_cache/plugins",
        "mixins": {
            "codex_defaults": {
                "system_message": {
                    "template": "${file:${env:CONFIG_DIR}/system_messages/codex.md}"
                },
                "plugins": ["path:${env:BUILTIN_PLUGINS}/shared-tools"],
            },
            "provider_defaults": {
                "timeout": 300,
            },
        },
        "mixin_policy": {"default_merge": "shallow"},
        "providers": {
            "kept_provider": {
                "mixin_refs": ["provider_defaults"],
                "provider": "kept",
                "api_key": "${env:KEPT_PROVIDER_API_KEY}",
            },
            "removed_provider": {
                "mixin_refs": ["provider_defaults"],
                "provider": "removed",
                "api_key": "${env:REMOVED_PROVIDER_API_KEY}",
            },
        },
        "agents": {
            "selected": {
                "mixin_refs": ["codex_defaults"],
                "provider": "kept_provider",
                "model": "selected-model",
            },
            "other": {
                "provider": "removed_provider",
                "plugins": ["path:${env:BUILTIN_PLUGINS}/other-tools"],
            },
        },
        "application": {"cloud_agent": {"orchestrator_url": "http://local"}},
    }

    portable, manifest = build_portable_config(raw, selected_agent_id="selected")

    assert list(portable["agents"].keys()) == ["selected"]
    assert list(portable["providers"].keys()) == ["kept_provider"]
    assert "mixins" not in portable
    assert "mixin_policy" not in portable
    assert portable["agents"]["selected"]["plugins"] == [
        "path:${env:BUILTIN_PLUGINS}/shared-tools"
    ]
    assert portable["agents"]["selected"]["system_message"]["template"] == (
        "${file:${env:CONFIG_DIR}/system_messages/codex.md}"
    )
    assert portable["providers"]["kept_provider"]["timeout"] == 300
    assert portable["providers"]["kept_provider"]["api_key"] == (
        "${env:KEPT_PROVIDER_API_KEY}"
    )
    assert "removed_provider" not in portable["providers"]
    assert "other" not in portable["agents"]
    assert portable["plugin_cache_dir"] == CLOUD_PLUGIN_CACHE_DIR
    assert manifest["optimization"]["kept_agent_ids"] == ["selected"]
    assert manifest["optimization"]["kept_provider_ids"] == ["kept_provider"]


def test_env_scanner_and_runtime_env_policy_respect_excludes_and_reserved_names(
    tmp_path: Path,
) -> None:
    raw = {
        "providers": {
            "openrouter": {
                "api_key": "${env:OPENROUTER_API_KEY}",
                "base_url": "${env:OPENAI_BASE_URL}",
            }
        },
        "application": {
            "cloud_agent": {"orchestrator_token": "${env:CLOUD_ORCHESTRATOR_TOKEN}"}
        },
        "plugin_cache_dir": "${env:CONFIG_DIR}/.plugin_cache/plugins",
    }
    assert scan_env_placeholders(raw) >= {
        "OPENROUTER_API_KEY",
        "OPENAI_BASE_URL",
        "CLOUD_ORCHESTRATOR_TOKEN",
        "CONFIG_DIR",
    }

    manifest = write_runtime_env(
        raw_config=raw,
        config_dir=tmp_path,
        target_dir=tmp_path / "env",
        policy={
            "include_config_env": True,
            "include": ["EXTRA_RUNTIME_VALUE", "CLOUD_AGENT_CONFIG_PATH"],
            "exclude": ["OPENAI_BASE_URL", "CLOUD_ORCHESTRATOR_TOKEN"],
            "env_files": [],
        },
        env={
            "OPENROUTER_API_KEY": "secret-key",
            "OPENAI_BASE_URL": "https://example.invalid",
            "CLOUD_ORCHESTRATOR_TOKEN": "local-control-secret",
            "CONFIG_DIR": "/local/config",
            "EXTRA_RUNTIME_VALUE": "ok",
            "CLOUD_AGENT_CONFIG_PATH": "/reserved",
        },
    )

    runtime_env = (tmp_path / "env" / "runtime.env").read_text(encoding="utf-8")
    assert "OPENROUTER_API_KEY=secret-key" in runtime_env
    assert "EXTRA_RUNTIME_VALUE=ok" in runtime_env
    assert "OPENAI_BASE_URL" not in runtime_env
    assert "CLOUD_ORCHESTRATOR_TOKEN" not in runtime_env
    assert "CONFIG_DIR" not in runtime_env
    assert "CLOUD_AGENT_CONFIG_PATH" not in runtime_env
    assert manifest["included_names"] == ["EXTRA_RUNTIME_VALUE", "OPENROUTER_API_KEY"]


def test_config_assets_copy_uses_configured_excludes_and_top_level_size_limit(
    tmp_path: Path,
) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "system_messages").mkdir()
    (config_dir / "system_messages" / "prompt.md").write_text("hello", encoding="utf-8")
    (config_dir / ".env").write_text("SECRET=1\n", encoding="utf-8")
    (config_dir / ".plugin_cache").mkdir()
    (config_dir / ".plugin_cache" / "cache.txt").write_text("cache", encoding="utf-8")
    (config_dir / "large.log").write_text("x" * 20, encoding="utf-8")
    large_dir = config_dir / "large_dir"
    large_dir.mkdir()
    (large_dir / "payload.bin").write_text("x" * 21, encoding="utf-8")

    target = tmp_path / "assets"
    manifest = copy_config_assets(
        config_dir=config_dir,
        target_dir=target,
        policy={
            "include_config_dir": True,
            "exclude": [".env", ".plugin_cache"],
            "max_top_level_entry_bytes": 20,
        },
    )

    assert (target / "system_messages" / "prompt.md").read_text(
        encoding="utf-8"
    ) == "hello"
    assert not (target / ".env").exists()
    assert not (target / ".plugin_cache").exists()
    assert not (target / "large_dir").exists()
    excluded = {(entry["path"], entry["reason"]) for entry in manifest["excluded"]}
    assert (".env", "exclude_pattern") in excluded
    assert (".plugin_cache", "exclude_pattern") in excluded
    assert ("large_dir", "size_limit") in excluded


def test_portable_config_preserves_builtin_plugin_path_reference() -> None:
    raw = {
        "plugins": [
            "path:${env:BUILTIN_PLUGINS}/gemini-compaction-feature",
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
        ],
        "agents": {"default": {"provider": "echo"}},
    }

    portable, _manifest = build_portable_config(raw)

    assert (
        portable["plugins"][0]
        == "path:${env:BUILTIN_PLUGINS}/gemini-compaction-feature"
    )
