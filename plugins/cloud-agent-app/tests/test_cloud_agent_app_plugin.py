from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List

import pytest

PLUGIN_SRC = Path(__file__).resolve().parents[1] / "src"
if str(PLUGIN_SRC) not in sys.path:
    sys.path.insert(0, str(PLUGIN_SRC))

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_core import Session
from cloud_agent_app import cloud_agent_validation
import cloud_agent_app.cloud_agent_app_plugin as cloud_agent_app_plugin_module
from cloud_agent_app.cloud_agent_container import stage_container_build_context
from cloud_agent_app.cloud_agent_app_plugin import CloudAgentAppPlugin
from cloud_agent_app.cloud_agent_profiles import resolve_cloud_agent_profiles
from cloud_agent_app.cloud_agent_validation import RuntimeImageBuildSpec
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
                        "cloud_setup_script": str(transfer_script),
                        "install_script": str(transfer_script),
                        "compatible_sync_down_profiles": ["test-sync"],
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
                        "mode": "image",
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
    result = subprocess.run(
        [str(script)],
        cwd=str(cwd),
        env={**os.environ, **env},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{script} failed with {result.returncode}: "
            f"{result.stderr or result.stdout}"
        )


def _branch_script_env(
    *,
    workspace: Path,
    transfer_dir: Path,
    session_id: str,
    cloud_workspace_dir: Path | None = None,
) -> Dict[str, str]:
    token = session_id.replace(" ", "-")
    return {
        "LOCAL_WORKSPACE_DIR": str(workspace),
        "CLOUD_WORKSPACE_DIR": str(
            cloud_workspace_dir if cloud_workspace_dir is not None else workspace
        ),
        "TRANSFER_DIR": str(transfer_dir),
        "TRANSFER_STAGE_DIR": str(transfer_dir / ".cloud-agent" / "local-stage"),
        "WORKING_DIR": str(workspace),
        "SESSION_ID": session_id,
        "CLOUD_AGENT_DELEGATED_SNAPSHOT_REF": (
            f"refs/cloud-agent/{token}/delegated-snapshot"
        ),
        "CLOUD_AGENT_CLOUD_FULL_STATE_REF": (
            f"refs/cloud-agent/{token}/cloud-full-state"
        ),
        "CLOUD_AGENT_LOCAL_IMPORT_STATE_REF": (
            f"refs/cloud-agent/{token}/local-import-state"
        ),
        "CLOUD_AGENT_LAST_SYNCED_REF": f"refs/cloud-agent/{token}/last-synced",
        "CLOUD_AGENT_IMPORTED_BRANCH_NAME": f"cloud/{token}/committed",
    }


def test_cloud_start_session_ui_element_maps_current_session_id() -> None:
    elements = {
        element["id"]: element for element in CloudAgentAppPlugin().get_ui_elements({})
    }

    element = elements["cloud_start_session_agent"]
    assert element["id"] == "cloud_start_session_agent"
    assert element["action_id"] == "cloud.start_session_agent"
    assert element["param_map"] == {"session_id": "$session.session_id"}
    assert "condition" not in element

    assert elements["cloud_check_session_agent"]["param_map"] == {
        "session_id": "$session.session_id",
    }
    assert "dialog" not in elements["cloud_check_session_agent"]
    assert elements["cloud_check_session_agent"]["condition"] == {
        "any": [
            {"path": "metadata.cloud_agent.instance_id", "exists": True},
            {"path": "metadata.cloud_agent.operation_ref", "exists": True},
        ]
    }
    assert elements["cloud_sync_down"]["param_map"] == {
        "instance_id": "$session.metadata.cloud_agent.instance_id",
        "session_id": "$session.session_id",
    }
    assert elements["cloud_close_session"]["param_map"] == {
        "instance_id": "$session.metadata.cloud_agent.instance_id",
        "session_id": "$session.session_id",
    }
    assert elements["cloud_close_session"]["dialog"] == {
        "kind": "confirm",
        "title": "Close cloud agent",
        "message": (
            "Close this cloud agent now? Unsynced cloud changes "
            "will be lost unless you synced them previously."
        ),
    }
    assert elements["cloud_detach_session"]["param_map"] == {
        "session_id": "$session.session_id",
    }


def test_cloud_plugin_exposes_validate_cloud_command_binding() -> None:
    plugin = CloudAgentAppPlugin()

    actions = {action["id"]: action for action in plugin.get_actions({})}
    commands = {command["name"]: command for command in plugin.get_commands({})}

    assert "cloud.validate_cloud" in actions
    assert actions["cloud.validate_cloud"]["inputs"] == {
        "workspace_dir": {"type": "string", "required": False},
        "keep_temp_dir": {"type": "boolean", "required": False, "default": False},
        "cache_dir": {"type": "string", "required": False},
        "runtime_build_context": {"type": "string", "required": False},
        "runtime_dockerfile": {"type": "string", "required": False},
    }
    assert commands["validate-cloud"] == {
        "name": "validate-cloud",
        "description": "Validate the current workspace through the shared local-Docker cloud flow.",
        "action_id": "cloud.validate_cloud",
        "args": [
            {
                "name": "workspace_dir",
                "flags": ["--workspace-dir"],
                "help": "Override the local workspace directory for validation.",
            },
            {
                "name": "keep_temp_dir",
                "flags": ["--keep-temp-dir"],
                "help": "Keep the generated transfer, instance, and build-context directories for debugging.",
            },
            {
                "name": "cache_dir",
                "flags": ["--cache-dir"],
                "help": "Bind-mount a stable local cache directory into the validation runtime.",
            },
            {
                "name": "runtime_build_context",
                "flags": ["--runtime-build-context"],
                "help": "Override the Docker build context used when the validation runtime image must be built.",
            },
            {
                "name": "runtime_dockerfile",
                "flags": ["--runtime-dockerfile"],
                "help": "Override the Dockerfile used when the validation runtime image must be built.",
            },
        ],
    }


def test_cloud_start_session_default_wait_timeout_is_short() -> None:
    plugin = CloudAgentAppPlugin()

    assert plugin._start_action_timeout_seconds({}) == 0.0
    assert (
        plugin._start_action_timeout_seconds({"start_action_timeout_seconds": 1}) == 1.0
    )


def test_cloud_start_session_returns_operation_ref_before_background_work(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    transfer_script = _write_script(tmp_path / "transfer.sh")
    config_path = _write_config(tmp_path, transfer_script)
    app = AgentApplication(
        str(config_path), str(tmp_path / "sessions"), event_store=InMemoryEventStore()
    )
    _core, _base_config, session = app.create_session("default")
    plugin = app._app_plugins["cloud"].plugin
    started_threads: list[Any] = []

    class FakeThread:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.args = args
            self.kwargs = kwargs

        def start(self) -> None:
            started_threads.append(self)

    monkeypatch.setattr(
        "cloud_agent_app.cloud_agent_app_plugin.threading.Thread", FakeThread
    )
    monkeypatch.setattr(
        plugin,
        "_post_json",
        lambda *args, **kwargs: pytest.fail("orchestrator called synchronously"),
    )

    result = app.execute_application_action(
        "cloud",
        "cloud.start_session_agent",
        {"session_id": session.session_id},
    )

    assert started_threads
    assert result["state"] == "starting"
    assert result["operation_ref"].startswith(f"cloud-start:{session.session_id}:")
    assert result["display"]["title"] == "Cloud Agent Starting"
    loaded = app.load_session(session.session_id)
    assert loaded is not None
    cloud_agent = (loaded[2].metadata or {})["cloud_agent"]
    assert cloud_agent["operation_ref"] == result["operation_ref"]
    assert cloud_agent["startup_stage"] == "queued"
    assert cloud_agent["state"] == "starting"


def test_cloud_check_status_uses_operation_ref_without_manual_token(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    transfer_script = _write_script(tmp_path / "transfer.sh")
    config_path = _write_config(tmp_path, transfer_script)
    app = AgentApplication(
        str(config_path), str(tmp_path / "sessions"), event_store=InMemoryEventStore()
    )
    _core, _base_config, session = app.create_session("default")
    plugin = app._app_plugins["cloud"].plugin

    class FakeThread:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def start(self) -> None:
            return None

    monkeypatch.setattr(
        "cloud_agent_app.cloud_agent_app_plugin.threading.Thread", FakeThread
    )
    start_result = app.execute_application_action(
        "cloud",
        "cloud.start_session_agent",
        {"session_id": session.session_id},
    )

    status = app.execute_application_action(
        "cloud",
        "cloud.check_session_agent",
        {"session_id": session.session_id},
    )

    assert status["operation_ref"] == start_result["operation_ref"]
    assert start_result["operation_ref"] in status["display"]["body"]
    assert "token" not in json.dumps(status["display"]["actions"])


def test_cloud_check_status_reads_instance_from_session_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transfer_script = _write_script(tmp_path / "transfer.sh")
    config_path = _write_config(tmp_path, transfer_script)
    app = AgentApplication(
        str(config_path), str(tmp_path / "sessions"), event_store=InMemoryEventStore()
    )
    _core, _base_config, session = app.create_session("default")
    plugin = app._app_plugins["cloud"].plugin
    metadata = dict(session.metadata or {})
    metadata["cloud_agent"] = {
        "operation_ref": "cloud-start:s1:test",
        "instance_id": "inst_test",
        "token": "secret-token",
        "state": "starting",
    }
    app.save_session(
        Session(
            session_id=session.session_id,
            messages=session.messages,
            metadata=metadata,
        )
    )

    monkeypatch.setattr(
        plugin,
        "_get_json",
        lambda base_url, path, token=None: {
            "instance_id": "inst_test",
            "session_id": session.session_id,
            "token": "secret-token",
            "state": "running",
            "startup_stage": "ready",
            "connection_id": "conn_test",
        },
    )

    status = app.execute_application_action(
        "cloud",
        "cloud.check_session_agent",
        {"session_id": session.session_id},
    )

    assert status["instance_id"] == "inst_test"
    assert "Instance ID: `inst_test`" in status["display"]["body"]
    assert "secret-token" not in status["display"]["body"]
    refresh = next(
        action
        for action in status["display"]["actions"]
        if action["id"] == "refresh-cloud-agent-status"
    )
    assert refresh["fixed_params"] == {"session_id": session.session_id}


def test_cloud_start_background_operation_updates_session_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    transfer_script = _write_script(tmp_path / "transfer.sh")
    config_path = _write_config(tmp_path, transfer_script)
    app = AgentApplication(
        str(config_path), str(tmp_path / "sessions"), event_store=InMemoryEventStore()
    )
    _core, _base_config, session = app.create_session("default")
    wrapper = app._app_plugins["cloud"]
    plugin = wrapper.plugin
    operation = plugin._cloud_operation_registry(app).create(
        session_id=session.session_id
    )
    operation_ref = operation["operation_ref"]

    monkeypatch.setattr(
        plugin,
        "_create_transfer_keypair",
        lambda transfer_dir: {
            "public_key": "ssh-ed25519 test",
            "private_key_path": transfer_dir / "id_ed25519",
        },
    )
    monkeypatch.setattr(
        plugin, "_run_managed_ssh_adapter", lambda *args, **kwargs: None
    )

    def fake_post_json(base_url, path, payload, token=None):
        if path == "/transfers":
            return {"transfer_id": "transfer_test"}
        if path == "/transfers/transfer_test/ready":
            return {}
        if path == "/instances":
            return {
                "instance_id": "inst_test",
                "session_id": session.session_id,
                "token": "secret-token",
                "state": "starting",
                "startup_stage": "runtime_starting",
                "connection_id": "conn_test",
            }
        raise AssertionError(path)

    monkeypatch.setattr(plugin, "_post_json", fake_post_json)
    monkeypatch.setattr(
        plugin,
        "_wait_for_instance_ready",
        lambda orchestrator_url, instance, state, timeout_seconds=None: {
            **instance,
            "state": "running",
            "startup_stage": "ready",
        },
    )

    plugin._run_start_session_agent_operation(
        app,
        {"session_id": session.session_id},
        wrapper.state,
        operation_ref,
    )

    loaded = app.load_session(session.session_id)
    assert loaded is not None
    cloud_agent = (loaded[2].metadata or {})["cloud_agent"]
    assert cloud_agent["operation_ref"] == operation_ref
    assert cloud_agent["instance_id"] == "inst_test"
    assert cloud_agent["state"] == "running"
    assert cloud_agent["startup_stage"] == "ready"
    assert cloud_agent["connection_id"] == "conn_test"


def test_write_cloud_runtime_scripts_copies_optional_validation_script(
    tmp_path: Path,
) -> None:
    plugin = CloudAgentAppPlugin()
    workspace = tmp_path / "workspace"
    transfer_dir = tmp_path / "transfer"
    workspace.mkdir()
    transfer_dir.mkdir()

    setup = _write_script(tmp_path / "setup", "printf setup > /dev/null\n")
    install = _write_script(tmp_path / "install", "printf install > /dev/null\n")
    validate = _write_script(tmp_path / "validate", "printf validate > /dev/null\n")
    export = _write_script(tmp_path / "export", "printf export > /dev/null\n")
    sync_applied = _write_script(tmp_path / "sync-applied", "printf sync > /dev/null\n")

    plugin._write_cloud_runtime_scripts(
        transfer_dir,
        {
            "cloud_setup_script": str(setup),
            "install_script": str(install),
            "validation_script": str(validate),
            "cloud_export_script": str(export),
            "cloud_mark_synced_script": str(sync_applied),
            "selected_transfer_up_profile": "working-tree-current-state",
            "selected_sync_down_profile": "working-tree-patch",
        },
        workspace,
        session_id="session-1",
    )

    scripts_dir = transfer_dir / ".cloud-agent" / "scripts"
    assert (scripts_dir / "setup").read_text(encoding="utf-8") == setup.read_text(
        encoding="utf-8"
    )
    assert (scripts_dir / "install").read_text(encoding="utf-8") == install.read_text(
        encoding="utf-8"
    )
    assert (scripts_dir / "validate").read_text(encoding="utf-8") == validate.read_text(
        encoding="utf-8"
    )
    assert (scripts_dir / "export").read_text(encoding="utf-8") == export.read_text(
        encoding="utf-8"
    )
    assert (scripts_dir / "sync-applied").read_text(
        encoding="utf-8"
    ) == sync_applied.read_text(encoding="utf-8")
    runtime_env = (scripts_dir / "runtime.env").read_text(encoding="utf-8")
    assert (
        "CLOUD_AGENT_TRANSFER_UP_PROFILE_ID=working-tree-current-state" in runtime_env
    )
    assert "CLOUD_AGENT_SYNC_DOWN_PROFILE_ID=working-tree-patch" in runtime_env


def test_validate_cloud_action_packages_runtime_and_returns_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "sample.txt").write_text("payload\n", encoding="utf-8")
    validate_hook = _write_script(
        workspace / ".cloud-agent" / "validate-cloud",
        'printf "validate hook" > /dev/null\n',
    )
    _write_script(workspace / ".cloud-agent" / "install-cloud")
    transfer_script = _write_script(
        tmp_path / "transfer.py",
        'mkdir -p "${TRANSFER_DIR}"\ncp "${LOCAL_WORKSPACE_DIR}/sample.txt" "${TRANSFER_DIR}/sample.txt"\n',
    )

    config_path = _write_config(tmp_path, transfer_script)
    config_data = json.loads(config_path.read_text(encoding="utf-8"))
    config_data["application"]["cloud_agent"]["transfer_up_profiles"]["test-transfer"][
        "validation_script"
    ] = str(validate_hook)
    config_path.write_text(json.dumps(config_data), encoding="utf-8")
    app = AgentApplication(
        str(config_path), str(tmp_path / "sessions"), event_store=InMemoryEventStore()
    )
    plugin = app._app_plugins["cloud"].plugin
    captured_commands: List[list[str]] = []
    cache_dir = tmp_path / "cache"

    monkeypatch.setattr(
        "cloud_agent_app.cloud_agent_app_plugin.ensure_local_runtime_image",
        lambda runtime_image, runtime_layout, build_context=None, dockerfile=None, selected_config=None, logger=None: {
            "runtime_image": runtime_image,
            "source": "existing",
        },
    )
    monkeypatch.setattr(
        "cloud_agent_app.cloud_agent_app_plugin.reserve_local_port",
        lambda: 18123,
    )

    def fake_run_command(
        command: list[str],
        *,
        cwd: Path,
        logger=None,
        event_name: str = "cloud_validation_command",
        env: dict[str, str] | None = None,
        stream_output: bool = False,
    ):
        captured_commands.append(command)
        return subprocess.CompletedProcess(
            command,
            0,
            stdout="ok",
            stderr="",
        )

    monkeypatch.setattr(
        "cloud_agent_app.cloud_agent_app_plugin.run_command", fake_run_command
    )
    monkeypatch.setattr(
        plugin, "_wait_for_local_runtime_ready", lambda port, state: {"ready": True}
    )
    monkeypatch.setattr(
        plugin,
        "_local_runtime_request",
        lambda method, port, path, payload=None: (
            200,
            {
                "status": "ok",
                "smoke": {"workspace_exists": True},
                "validate": {"status": "ran"},
            },
        ),
    )
    monkeypatch.setattr(plugin, "_docker_logs", lambda container_name: "")
    monkeypatch.setattr(plugin, "_remove_container", lambda container_name: None)

    result = app.execute_application_action(
        "cloud",
        "cloud.validate_cloud",
        {
            "workspace_dir": str(workspace),
            "keep_temp_dir": True,
            "cache_dir": str(cache_dir),
        },
    )

    assert result["status"] == "ok"
    assert result["display"]["title"] == "Cloud Validation Passed"
    assert result["runtime_image"] == "cloud-agent-runtime:latest"
    assert result["cache_dir"] == str(cache_dir.resolve())
    assert captured_commands[0][:3] == ["docker", "run", "-d"]
    assert captured_commands[0][-1] == "cloud-agent-runtime:latest"
    assert f"{cache_dir.resolve()}:/cloud-agent/cache" in captured_commands[0]

    artifacts_dir = Path(result["artifacts_dir"])
    runtime_env = (
        artifacts_dir / "transfer" / ".cloud-agent" / "scripts" / "runtime.env"
    ).read_text(encoding="utf-8")
    assert "CLOUD_AGENT_VALIDATION_SESSION_ID=" in runtime_env
    assert (
        artifacts_dir / "transfer" / ".cloud-agent" / "scripts" / "validate"
    ).read_text(encoding="utf-8") == validate_hook.read_text(encoding="utf-8")
    shutil.rmtree(artifacts_dir, ignore_errors=True)


def test_validate_cloud_action_materializes_source_runtime_image_context_per_request(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "sample.txt").write_text("payload\n", encoding="utf-8")
    _write_script(workspace / ".cloud-agent" / "install-cloud")
    _write_script(workspace / ".cloud-agent" / "validate-cloud")
    transfer_script = _write_script(
        tmp_path / "transfer.py",
        'mkdir -p "${TRANSFER_DIR}"\ncp "${LOCAL_WORKSPACE_DIR}/sample.txt" "${TRANSFER_DIR}/sample.txt"\n',
    )

    config_path = _write_config(tmp_path, transfer_script)
    app = AgentApplication(
        str(config_path), str(tmp_path / "sessions"), event_store=InMemoryEventStore()
    )
    plugin = app._app_plugins["cloud"].plugin
    captured_prepare: dict[str, Path] = {}
    captured_runtime_image: dict[str, Any] = {}

    monkeypatch.setattr(
        "cloud_agent_app.cloud_agent_app_plugin.load_runtime_layout",
        lambda: SimpleNamespace(layout="source"),
    )

    def fake_prepare_source_cloud_runtime_build_context(
        runtime_layout: Any,
        *,
        destination: Path | None = None,
        selected_config: Path | None = None,
        cloud_disabled_plugin_specs: list[str] | None = None,
    ) -> tuple[Path, Path]:
        assert destination is not None
        captured_prepare["destination"] = destination.resolve()
        captured_prepare["selected_config"] = (
            selected_config.resolve() if selected_config is not None else None
        )
        captured_prepare["disabled_specs"] = list(cloud_disabled_plugin_specs or [])
        destination.mkdir(parents=True, exist_ok=True)
        dockerfile = destination / "Dockerfile"
        dockerfile.write_text("FROM scratch\n", encoding="utf-8")
        return destination, dockerfile

    monkeypatch.setattr(
        "cloud_agent_app.cloud_agent_app_plugin.prepare_source_cloud_runtime_build_context",
        fake_prepare_source_cloud_runtime_build_context,
    )

    def fake_ensure_local_runtime_image(
        runtime_image: str,
        runtime_layout: Any,
        build_context: Path | None = None,
        dockerfile: Path | None = None,
        selected_config: Path | None = None,
        logger=None,
    ) -> dict[str, str]:
        captured_runtime_image["runtime_image"] = runtime_image
        captured_runtime_image["build_context"] = (
            build_context.resolve() if build_context is not None else None
        )
        captured_runtime_image["dockerfile"] = (
            dockerfile.resolve() if dockerfile is not None else None
        )
        captured_runtime_image["selected_config"] = (
            selected_config.resolve() if selected_config is not None else None
        )
        return {
            "runtime_image": runtime_image,
            "source": "built",
            "build_context": str(build_context) if build_context is not None else "",
            "dockerfile": str(dockerfile) if dockerfile is not None else "",
        }

    monkeypatch.setattr(
        "cloud_agent_app.cloud_agent_app_plugin.ensure_local_runtime_image",
        fake_ensure_local_runtime_image,
    )
    monkeypatch.setattr(
        "cloud_agent_app.cloud_agent_app_plugin.reserve_local_port",
        lambda: 18123,
    )
    monkeypatch.setattr(
        "cloud_agent_app.cloud_agent_app_plugin.run_command",
        lambda command, *, cwd, logger=None, event_name="cloud_validation_command", env=None, stream_output=False: subprocess.CompletedProcess(
            command,
            0,
            stdout="ok",
            stderr="",
        ),
    )
    monkeypatch.setattr(
        plugin, "_wait_for_local_runtime_ready", lambda port, state: {"ready": True}
    )
    monkeypatch.setattr(
        plugin,
        "_local_runtime_request",
        lambda method, port, path, payload=None: (
            200,
            {
                "status": "ok",
                "smoke": {"workspace_exists": True},
                "validate": {"status": "ran"},
            },
        ),
    )
    monkeypatch.setattr(plugin, "_docker_logs", lambda container_name: "")
    monkeypatch.setattr(plugin, "_remove_container", lambda container_name: None)

    result = app.execute_application_action(
        "cloud",
        "cloud.validate_cloud",
        {
            "workspace_dir": str(workspace),
            "keep_temp_dir": True,
        },
    )

    artifacts_dir = Path(result["artifacts_dir"]).resolve()
    expected_context = artifacts_dir / "runtime-image-build-context"
    assert captured_prepare["destination"] == expected_context
    assert captured_prepare["selected_config"] == config_path.resolve()
    assert captured_prepare["disabled_specs"] == []
    assert captured_runtime_image["runtime_image"] == "cloud-agent-runtime:latest"
    assert captured_runtime_image["build_context"] == expected_context
    assert captured_runtime_image["dockerfile"] == expected_context / "Dockerfile"
    assert captured_runtime_image["selected_config"] == config_path.resolve()
    shutil.rmtree(artifacts_dir, ignore_errors=True)


def test_runtime_image_builds_default_when_digest_label_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = tmp_path / "context"
    context.mkdir()
    dockerfile = context / "Dockerfile"
    dockerfile.write_text("FROM scratch\n", encoding="utf-8")
    (context / "runtime.py").write_text("print('runtime')\n", encoding="utf-8")
    layout = SimpleNamespace(
        cloud_runtime_build_context=context,
        cloud_runtime_dockerfile=dockerfile,
    )
    calls: list[dict[str, Any]] = []

    def fake_run_command(
        command: list[str],
        *,
        cwd: Path,
        logger=None,
        event_name: str = "cloud_validation_command",
        env: dict[str, str] | None = None,
        stream_output: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(
            {
                "command": command,
                "env": env,
                "stream_output": stream_output,
            }
        )
        if command[:3] == ["docker", "image", "inspect"]:
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="built", stderr="")

    monkeypatch.setattr(cloud_agent_validation, "run_command", fake_run_command)

    result = cloud_agent_validation.ensure_local_runtime_image(
        "cloud-agent-runtime:latest",
        runtime_layout=layout,
    )

    build_call = next(
        call for call in calls if call["command"][:2] == ["docker", "build"]
    )
    build_command = build_call["command"]
    assert result["source"] == "built"
    assert result["digest"]
    assert result["digest_tag"].startswith("cloud-agent-runtime:sha-")
    assert "-t" in build_command
    assert "cloud-agent-runtime:latest" in build_command
    assert result["digest_tag"] in build_command
    assert build_call["stream_output"] is True
    assert build_call["env"] == cloud_agent_validation._DOCKER_BUILD_PROGRESS_ENV
    assert (
        f"{cloud_agent_validation.RUNTIME_DIGEST_LABEL}={result['digest']}"
        in build_command
    )


def test_runtime_image_reuses_default_when_digest_label_matches(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = tmp_path / "context"
    context.mkdir()
    dockerfile = context / "Dockerfile"
    dockerfile.write_text("FROM scratch\n", encoding="utf-8")
    (context / "runtime.py").write_text("print('runtime')\n", encoding="utf-8")
    spec = RuntimeImageBuildSpec(context_dir=context, dockerfile=dockerfile)
    digest = cloud_agent_validation.runtime_build_digest(spec)
    layout = SimpleNamespace(
        cloud_runtime_build_context=context,
        cloud_runtime_dockerfile=dockerfile,
    )
    calls: list[dict[str, Any]] = []

    def fake_run_command(
        command: list[str],
        *,
        cwd: Path,
        logger=None,
        event_name: str = "cloud_validation_command",
        env: dict[str, str] | None = None,
        stream_output: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(
            {
                "command": command,
                "env": env,
                "stream_output": stream_output,
            }
        )
        payload = [
            {
                "Config": {
                    "Labels": {cloud_agent_validation.RUNTIME_DIGEST_LABEL: digest}
                }
            }
        ]
        return subprocess.CompletedProcess(
            command, 0, stdout=json.dumps(payload), stderr=""
        )

    monkeypatch.setattr(cloud_agent_validation, "run_command", fake_run_command)

    result = cloud_agent_validation.ensure_local_runtime_image(
        "cloud-agent-runtime:latest",
        runtime_layout=layout,
    )

    assert result["source"] == "existing"
    assert result["digest"] == digest
    assert not any(call["command"][:2] == ["docker", "build"] for call in calls)


def test_runtime_image_missing_custom_without_explicit_build_metadata_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = tmp_path / "context"
    context.mkdir()
    dockerfile = context / "Dockerfile"
    dockerfile.write_text("FROM scratch\n", encoding="utf-8")
    layout = SimpleNamespace(
        cloud_runtime_build_context=context,
        cloud_runtime_dockerfile=dockerfile,
    )

    def fake_run_command(
        command: list[str],
        *,
        cwd: Path,
        logger=None,
        event_name: str = "cloud_validation_command",
        env: dict[str, str] | None = None,
        stream_output: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="")

    monkeypatch.setattr(cloud_agent_validation, "run_command", fake_run_command)

    with pytest.raises(RuntimeError, match="custom-runtime:latest.*not available"):
        cloud_agent_validation.ensure_local_runtime_image(
            "custom-runtime:latest",
            runtime_layout=layout,
        )


def test_runtime_image_builds_custom_with_explicit_build_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = tmp_path / "context"
    context.mkdir()
    dockerfile = context / "Dockerfile"
    dockerfile.write_text("FROM scratch\n", encoding="utf-8")
    layout = SimpleNamespace(
        cloud_runtime_build_context=None,
        cloud_runtime_dockerfile=None,
    )
    calls: list[dict[str, Any]] = []

    def fake_run_command(
        command: list[str],
        *,
        cwd: Path,
        logger=None,
        event_name: str = "cloud_validation_command",
        env: dict[str, str] | None = None,
        stream_output: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(
            {
                "command": command,
                "env": env,
                "stream_output": stream_output,
            }
        )
        if command[:3] == ["docker", "image", "inspect"]:
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="built", stderr="")

    monkeypatch.setattr(cloud_agent_validation, "run_command", fake_run_command)

    result = cloud_agent_validation.ensure_local_runtime_image(
        "custom-runtime:latest",
        runtime_layout=layout,
        build_context=context,
        dockerfile=dockerfile,
    )

    assert result["source"] == "built"
    assert result["digest_tag"].startswith("custom-runtime:sha-")
    build_call = next(
        call for call in calls if call["command"][:2] == ["docker", "build"]
    )
    assert build_call["stream_output"] is True
    assert build_call["env"] == cloud_agent_validation._DOCKER_BUILD_PROGRESS_ENV


def test_staged_container_image_builds_with_streamed_plain_progress(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = tmp_path / "context"
    context.mkdir()
    dockerfile = context / "Dockerfile"
    dockerfile.write_text("FROM scratch\n", encoding="utf-8")
    staged_context = cloud_agent_validation.StagedContainerBuildContext(
        context_dir=context,
        dockerfile=dockerfile,
        dockerfile_relative_path="Dockerfile",
        digest="abc123",
    )
    calls: list[dict[str, Any]] = []

    def fake_run_command(
        command: list[str],
        *,
        cwd: Path,
        logger=None,
        event_name: str = "cloud_validation_command",
        env: dict[str, str] | None = None,
        stream_output: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(
            {
                "command": command,
                "env": env,
                "stream_output": stream_output,
            }
        )
        if command[:3] == ["docker", "image", "inspect"]:
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="built", stderr="")

    monkeypatch.setattr(cloud_agent_validation, "run_command", fake_run_command)

    result = cloud_agent_validation.ensure_local_staged_container_image(
        {
            "image": "profile-runtime:latest",
            "target": "project-runtime",
            "build_args": {"PYTHON_VERSION": "3.12"},
        },
        staged_context=staged_context,
    )

    build_call = next(
        call for call in calls if call["command"][:2] == ["docker", "build"]
    )
    build_command = build_call["command"]
    assert result["source"] == "built"
    assert result["digest"] == "abc123"
    assert build_call["stream_output"] is True
    assert build_call["env"] == cloud_agent_validation._DOCKER_BUILD_PROGRESS_ENV
    assert "--target" in build_command
    assert "project-runtime" in build_command
    assert "--build-arg" in build_command
    assert "PYTHON_VERSION=3.12" in build_command


def test_profile_resolver_selects_default_profiles_and_expands_env_paths(
    tmp_path: Path,
) -> None:
    config_dir = tmp_path / "config"
    workspace = tmp_path / "workspace"
    local_stage = _write_script(config_dir / "cloud-agent" / "local-stage")
    transfer = _write_script(config_dir / "cloud-agent" / "transfer-up")
    setup = _write_script(config_dir / "cloud-agent" / "setup")
    install = _write_script(config_dir / "cloud-agent" / "install")
    validate = _write_script(config_dir / "cloud-agent" / "validate")
    export = _write_script(config_dir / "cloud-agent" / "export")
    apply_down = _write_script(config_dir / "cloud-agent" / "apply-down")

    resolved = resolve_cloud_agent_profiles(
        {
            "default_transfer_up_profile": "working-tree-current-state",
            "default_sync_down_profile": "working-tree-patch",
            "default_container_profile": "default-runtime",
            "transfer_up_profiles": {
                "working-tree-current-state": {
                    "local_stage_script": "${env:CONFIG_DIR}/cloud-agent/local-stage",
                    "local_transfer_script": "${env:CONFIG_DIR}/cloud-agent/transfer-up",
                    "cloud_setup_script": "${env:CONFIG_DIR}/cloud-agent/setup",
                    "install_script": "${env:CONFIG_DIR}/cloud-agent/install",
                    "validation_script": "${env:CONFIG_DIR}/cloud-agent/validate",
                    "compatible_sync_down_profiles": ["working-tree-patch"],
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
                "default-runtime": {
                    "image": "cloud-agent-runtime:latest",
                }
            },
        },
        env={"CONFIG_DIR": str(config_dir), "WORKING_DIR": str(workspace)},
    )

    assert resolved["selected_transfer_up_profile"] == "working-tree-current-state"
    assert resolved["selected_sync_down_profile"] == "working-tree-patch"
    assert resolved["selected_container_profile"] == "default-runtime"
    assert resolved["local_stage_script"] == str(local_stage.resolve())
    assert resolved["local_transfer_script"] == str(transfer.resolve())
    assert resolved["cloud_setup_script"] == str(setup.resolve())
    assert resolved["install_script"] == str(install.resolve())
    assert resolved["validation_script"] == str(validate.resolve())
    assert resolved["cloud_export_script"] == str(export.resolve())
    assert resolved["local_apply_script"] == str(apply_down.resolve())
    assert resolved["cloud_mark_synced_script"] is None
    assert resolved["container"] == {
        "profile_id": "default-runtime",
        "mode": "image",
        "image": "cloud-agent-runtime:latest",
        "cache_mounts": [],
        "mounts": [],
    }


def test_profile_resolver_exposes_dockerfile_container_spec(tmp_path: Path) -> None:
    transfer = _write_script(tmp_path / "transfer")
    setup = _write_script(tmp_path / "setup")
    export = _write_script(tmp_path / "export")
    apply_down = _write_script(tmp_path / "apply-down")

    resolved = resolve_cloud_agent_profiles(
        {
            "default_transfer_up_profile": "current",
            "default_sync_down_profile": "patch",
            "default_container_profile": "runtime",
            "transfer_up_profiles": {
                "current": {
                    "local_transfer_script": str(transfer),
                    "cloud_setup_script": str(setup),
                }
            },
            "sync_down_profiles": {
                "patch": {
                    "cloud_export_script": str(export),
                    "local_apply_script": str(apply_down),
                }
            },
            "container_profiles": {
                "runtime": {
                    "image": "runtime:test",
                    "dockerfile": "runtime/Dockerfile",
                    "context": "runtime",
                    "target": "cloud-agent",
                    "build_args": {"PYTHON_VERSION": "3.12"},
                    "build_assets": [
                        {
                            "source": "frontend/package.json",
                            "target": "assets/frontend/package.json",
                        }
                    ],
                    "cache_mounts": [
                        {
                            "id": "frontend-node-modules",
                            "target": "/cloud-agent/instance/workspace/frontend/node_modules",
                            "scope": "connection",
                        }
                    ],
                    "mounts": [
                        {
                            "id": "ollama-models",
                            "target": "/cloud-agent/cache/ollama",
                            "scope": "profile",
                        }
                    ],
                }
            },
        },
        env={"WORKING_DIR": str(tmp_path), "CONFIG_DIR": str(tmp_path)},
    )

    assert resolved["container"] == {
        "profile_id": "runtime",
        "mode": "dockerfile",
        "image": "runtime:test",
        "dockerfile": "runtime/Dockerfile",
        "dockerfile_path": str((tmp_path / "runtime" / "Dockerfile").resolve()),
        "context": "runtime",
        "context_path": str((tmp_path / "runtime").resolve()),
        "target": "cloud-agent",
        "build_args": {"PYTHON_VERSION": "3.12"},
        "build_assets": [
            {
                "source": "frontend/package.json",
                "source_path": str((tmp_path / "frontend" / "package.json").resolve()),
                "target": "assets/frontend/package.json",
            }
        ],
        "cache_mounts": [
            {
                "id": "frontend-node-modules",
                "target": "/cloud-agent/instance/workspace/frontend/node_modules",
                "scope": "connection",
            }
        ],
        "mounts": [
            {
                "id": "ollama-models",
                "target": "/cloud-agent/cache/ollama",
                "scope": "profile",
            }
        ],
    }


def test_profile_resolver_expands_container_env_paths(tmp_path: Path) -> None:
    transfer = _write_script(tmp_path / "transfer")
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    dockerfile = runtime / "Dockerfile"
    dockerfile.write_text("FROM scratch\n", encoding="utf-8")
    asset = tmp_path / "frontend" / "package.json"
    asset.parent.mkdir()
    asset.write_text("{}", encoding="utf-8")

    resolved = resolve_cloud_agent_profiles(
        {
            "default_transfer_up_profile": "current",
            "default_sync_down_profile": "patch",
            "default_container_profile": "runtime",
            "transfer_up_profiles": {
                "current": {
                    "local_transfer_script": str(transfer),
                    "cloud_setup_script": str(transfer),
                }
            },
            "sync_down_profiles": {
                "patch": {
                    "cloud_export_script": str(transfer),
                    "local_apply_script": str(transfer),
                }
            },
            "container_profiles": {
                "runtime": {
                    "image": "runtime:test",
                    "dockerfile": "${env:WORKING_DIR}/runtime/Dockerfile",
                    "context": "${env:WORKING_DIR}/runtime",
                    "build_assets": [
                        {
                            "source": "${env:WORKING_DIR}/frontend/package.json",
                            "target": "assets/package.json",
                        }
                    ],
                }
            },
        },
        env={"WORKING_DIR": str(tmp_path), "CONFIG_DIR": str(tmp_path)},
    )

    container = resolved["container"]
    assert container["mode"] == "dockerfile"
    assert container["dockerfile_path"] == str(dockerfile.resolve())
    assert container["context_path"] == str(runtime.resolve())
    assert container["build_assets"][0]["source_path"] == str(asset.resolve())


def test_profile_resolver_exposes_list_mode_dockerfile_context(tmp_path: Path) -> None:
    transfer = _write_script(tmp_path / "transfer")
    setup = _write_script(tmp_path / "setup")
    export = _write_script(tmp_path / "export")
    apply_down = _write_script(tmp_path / "apply-down")

    resolved = resolve_cloud_agent_profiles(
        {
            "default_transfer_up_profile": "current",
            "default_sync_down_profile": "patch",
            "default_container_profile": "runtime",
            "transfer_up_profiles": {
                "current": {
                    "local_transfer_script": str(transfer),
                    "cloud_setup_script": str(setup),
                }
            },
            "sync_down_profiles": {
                "patch": {
                    "cloud_export_script": str(export),
                    "local_apply_script": str(apply_down),
                }
            },
            "container_profiles": {
                "runtime": {
                    "image": "runtime:test",
                    "dockerfile": "Dockerfile",
                    "context": [
                        {
                            "source": "runtime/Dockerfile",
                            "target": "Dockerfile",
                        },
                        {
                            "source": "runtime/runtime.py",
                            "target": "runtime.py",
                        },
                    ],
                    "build_assets": [
                        {
                            "source": "frontend/package.json",
                            "target": "assets/frontend/package.json",
                        }
                    ],
                }
            },
        },
        env={"WORKING_DIR": str(tmp_path), "CONFIG_DIR": str(tmp_path)},
    )

    container = resolved["container"]
    assert container["mode"] == "dockerfile"
    assert container["dockerfile"] == "Dockerfile"
    assert "context_path" not in container
    assert "dockerfile_path" not in container
    assert container["context_entries"] == [
        {
            "source": "runtime/Dockerfile",
            "source_path": str((tmp_path / "runtime" / "Dockerfile").resolve()),
            "target": "Dockerfile",
        },
        {
            "source": "runtime/runtime.py",
            "source_path": str((tmp_path / "runtime" / "runtime.py").resolve()),
            "target": "runtime.py",
        },
    ]


def test_cloud_plugin_requires_explicit_container_profile() -> None:
    plugin = CloudAgentAppPlugin()

    with pytest.raises(
        ValueError,
        match="application.cloud_agent.default_container_profile is required",
    ):
        plugin.init(
            {
                "application": {
                    "cloud_agent": {
                        "default_transfer_up_profile": "current",
                        "default_sync_down_profile": "patch",
                        "transfer_up_profiles": {"current": {}},
                        "sync_down_profiles": {"patch": {}},
                    }
                }
            }
        )


def test_prepare_container_build_sources_materializes_runtime_context_in_request_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_context = tmp_path / "runtime-context"
    materialized_context = tmp_path / "materialized-runtime-context"
    config_path = tmp_path / "custom-config.json"
    config_path.write_text("{}", encoding="utf-8")
    captured: dict[str, Path] = {}

    plugin = CloudAgentAppPlugin()
    monkeypatch.setattr(
        cloud_agent_app_plugin_module,
        "load_runtime_layout",
        lambda: SimpleNamespace(
            layout="source",
            env_overrides=lambda: {
                "CLOUD_RUNTIME_BUILD_CONTEXT": str(runtime_context.resolve())
            },
        ),
    )

    def fake_prepare_source_cloud_runtime_build_context(
        runtime_layout: Any,
        *,
        destination: Path | None = None,
        selected_config: Path | None = None,
        cloud_disabled_plugin_specs: list[str] | None = None,
    ) -> tuple[Path, Path]:
        captured["destination"] = destination.resolve() if destination else None
        captured["selected_config"] = (
            selected_config.resolve() if selected_config is not None else None
        )
        captured["disabled_specs"] = list(cloud_disabled_plugin_specs or [])
        return materialized_context, materialized_context / "Dockerfile"

    monkeypatch.setattr(
        cloud_agent_app_plugin_module,
        "prepare_source_cloud_runtime_build_context",
        fake_prepare_source_cloud_runtime_build_context,
    )

    container = {
        "mode": "dockerfile",
        "dockerfile": "Dockerfile",
        "context_entries": [
            {
                "source": "${env:CLOUD_RUNTIME_BUILD_CONTEXT}/python_lib",
                "source_path": str((runtime_context / "python_lib").resolve()),
                "target": "python_lib",
            }
        ],
        "build_assets": [
            {
                "source": "${env:CLOUD_RUNTIME_BUILD_CONTEXT}/plugin_sources",
                "source_path": str((runtime_context / "plugin_sources").resolve()),
                "target": "plugin_sources",
            }
        ],
    }
    rewritten = plugin._prepare_container_build_sources(
        container,
        app=SimpleNamespace(get_config_path=lambda: config_path),
        materialization_dir=materialized_context,
    )

    assert captured["destination"] == materialized_context.resolve()
    assert captured["selected_config"] == config_path.resolve()
    assert captured["disabled_specs"] == []
    assert rewritten["context_entries"][0]["source_path"] == str(
        (materialized_context / "python_lib").resolve()
    )
    assert rewritten["build_assets"][0]["source_path"] == str(
        (materialized_context / "plugin_sources").resolve()
    )
    assert container["context_entries"][0]["source_path"] == str(
        (runtime_context / "python_lib").resolve()
    )


def test_prepare_container_for_orchestrator_sends_sanitized_dockerfile_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_context = tmp_path / "runtime-context"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    plugin = CloudAgentAppPlugin()
    captured_destination: dict[str, Path] = {}

    monkeypatch.setattr(
        plugin,
        "_prepare_container_build_sources",
        lambda container, app=None, materialization_dir=None, cloud_disabled_plugin_specs=None: {
            **container,
            "context_entries": [
                {
                    "source": "${env:CLOUD_RUNTIME_BUILD_CONTEXT}/python_lib",
                    "source_path": str(
                        (tmp_path / "materialized" / "python_lib").resolve()
                    ),
                    "target": "python_lib",
                }
            ],
            "build_assets": [
                {
                    "source": "frontend/package.json",
                    "source_path": str(
                        (workspace / "frontend" / "package.json").resolve()
                    ),
                    "target": "assets/package.json",
                }
            ],
        },
    )

    def fake_stage_container_build_context(
        container: Dict[str, Any],
        *,
        workspace_dir: Path,
        destination_dir: Path,
    ) -> Any:
        captured_destination["path"] = destination_dir.resolve()
        context_dir = destination_dir / "context"
        context_dir.mkdir(parents=True, exist_ok=True)
        dockerfile = context_dir / "Dockerfile"
        dockerfile.write_text("FROM scratch\n", encoding="utf-8")
        return SimpleNamespace(
            context_dir=context_dir,
            dockerfile=dockerfile,
            dockerfile_relative_path="Dockerfile",
            digest="digest123",
        )

    monkeypatch.setattr(
        cloud_agent_app_plugin_module,
        "stage_container_build_context",
        fake_stage_container_build_context,
    )
    monkeypatch.setattr(plugin, "_build_context_exists", lambda *args, **kwargs: True)

    payload = plugin._prepare_container_for_orchestrator(
        SimpleNamespace(get_config_path=lambda: tmp_path / "config.json"),
        {
            "container": {
                "profile_id": "default-runtime",
                "label": "Default runtime",
                "mode": "dockerfile",
                "image": "cloud-agent-runtime:latest",
                "dockerfile": "Dockerfile",
                "context_entries": [
                    {
                        "source": "${env:CLOUD_RUNTIME_BUILD_CONTEXT}/python_lib",
                        "source_path": str((runtime_context / "python_lib").resolve()),
                        "target": "python_lib",
                    }
                ],
                "build_assets": [
                    {
                        "source": "frontend/package.json",
                        "source_path": str(
                            (workspace / "frontend" / "package.json").resolve()
                        ),
                        "target": "assets/package.json",
                    }
                ],
                "cache_mounts": [],
                "mounts": [],
            }
        },
        orchestrator_url="http://orchestrator.test",
        workspace_dir=workspace,
    )

    assert captured_destination["path"].name == "staged"
    assert payload == {
        "profile_id": "default-runtime",
        "label": "Default runtime",
        "mode": "dockerfile",
        "image": "cloud-agent-runtime:latest",
        "dockerfile": "Dockerfile",
        "build_context_digest": "digest123",
        "build_context_ref": {"digest": "digest123"},
        "cache_mounts": [],
        "mounts": [],
    }
    assert "context_entries" not in payload
    assert "build_assets" not in payload


def test_container_build_context_digest_includes_declared_assets(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    runtime = workspace / "runtime"
    runtime.mkdir(parents=True)
    (runtime / "Dockerfile").write_text("FROM scratch\n", encoding="utf-8")
    (runtime / "runtime.txt").write_text("runtime\n", encoding="utf-8")
    (workspace / "frontend").mkdir()
    package_json = workspace / "frontend" / "package.json"
    package_json.write_text('{"name":"one"}\n', encoding="utf-8")

    container = {
        "image": "runtime:test",
        "dockerfile": "runtime/Dockerfile",
        "context": "runtime",
        "build_assets": [
            {
                "source": "frontend/package.json",
                "target": "assets/frontend/package.json",
            }
        ],
    }

    first = stage_container_build_context(
        container,
        workspace_dir=workspace,
        destination_dir=tmp_path / "first",
    )
    package_json.write_text('{"name":"two"}\n', encoding="utf-8")
    second = stage_container_build_context(
        container,
        workspace_dir=workspace,
        destination_dir=tmp_path / "second",
    )

    assert first.digest != second.digest
    assert (first.context_dir / "assets" / "frontend" / "package.json").read_text(
        encoding="utf-8"
    ) == '{"name":"one"}\n'


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
                    "cloud_setup_script": str(install),
                    "install_script": str(install),
                }
            },
            "sync_down_profiles": {
                "patch": {
                    "cloud_export_script": str(export),
                    "local_apply_script": str(base_apply),
                }
            },
            "container_profiles": {
                "runtime": {"mode": "image", "image": "runtime:test"}
            },
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
                        "cloud_setup_script": str(install),
                        "install_script": str(install),
                        "compatible_sync_down_profiles": ["other-patch"],
                    }
                },
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
                "container_profiles": {
                    "runtime": {"mode": "image", "image": "runtime:test"}
                },
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
                        "cloud_setup_script": str(transfer),
                        "install_script": str(transfer),
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
    transfer_up = (
        scripts_root
        / "transfer_up"
        / "working-tree-current-state"
        / "local_transfer_script"
    )
    setup = (
        scripts_root
        / "transfer_up"
        / "working-tree-current-state"
        / "cloud_setup_script"
    )
    export = scripts_root / "sync_down" / "working-tree-patch" / "cloud_export_script"
    mark_synced = (
        scripts_root / "sync_down" / "working-tree-patch" / "cloud_mark_synced_script"
    )
    apply_down = (
        scripts_root / "sync_down" / "working-tree-patch" / "local_apply_script"
    )

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
        setup,
        {
            "CLOUD_WORKSPACE_DIR": str(cloud),
            "TRANSFER_DIR": str(upload),
            "TRANSFER_STAGE_DIR": str(upload / ".cloud-agent" / "local-stage"),
        },
        cwd=cloud,
    )
    (cloud / "chain.txt").write_text("base\nchange1\n", encoding="utf-8")
    sync1 = tmp_path / "sync1"
    sync1.mkdir()
    _run_cloud_profile_script(
        export,
        {
            "CLOUD_WORKSPACE_DIR": str(cloud),
            "TRANSFER_DIR": str(sync1),
            "TRANSFER_STAGE_DIR": str(sync1 / ".cloud-agent" / "local-stage"),
        },
        cwd=cloud,
    )
    _run_cloud_profile_script(
        apply_down,
        {
            "LOCAL_WORKSPACE_DIR": str(local),
            "TRANSFER_DIR": str(sync1),
            "TRANSFER_STAGE_DIR": str(sync1 / ".cloud-agent" / "local-stage"),
        },
        cwd=local,
    )
    _run_cloud_profile_script(
        mark_synced,
        {
            "CLOUD_WORKSPACE_DIR": str(cloud),
            "TRANSFER_DIR": str(sync1),
            "TRANSFER_STAGE_DIR": str(sync1 / ".cloud-agent" / "local-stage"),
        },
        cwd=cloud,
    )

    (cloud / "chain.txt").write_text("base\nchange1\nchange2\n", encoding="utf-8")
    sync2 = tmp_path / "sync2"
    sync2.mkdir()
    _run_cloud_profile_script(
        export,
        {
            "CLOUD_WORKSPACE_DIR": str(cloud),
            "TRANSFER_DIR": str(sync2),
            "TRANSFER_STAGE_DIR": str(sync2 / ".cloud-agent" / "local-stage"),
        },
        cwd=cloud,
    )
    _run_cloud_profile_script(
        apply_down,
        {
            "LOCAL_WORKSPACE_DIR": str(local),
            "TRANSFER_DIR": str(sync2),
            "TRANSFER_STAGE_DIR": str(sync2 / ".cloud-agent" / "local-stage"),
        },
        cwd=local,
    )

    assert (local / "chain.txt").read_text(encoding="utf-8") == (
        "base\nchange1\nchange2\n"
    )


def test_profile_resolver_treats_missing_standard_repo_hooks_as_noops(
    tmp_path: Path,
) -> None:
    transfer = _write_script(tmp_path / "transfer")
    setup = _write_script(tmp_path / "setup")
    export = _write_script(tmp_path / "export")
    apply_down = _write_script(tmp_path / "apply-down")

    resolved = resolve_cloud_agent_profiles(
        {
            "default_transfer_up_profile": "current",
            "default_sync_down_profile": "patch",
            "default_container_profile": "runtime",
            "transfer_up_profiles": {
                "current": {
                    "local_transfer_script": str(transfer),
                    "cloud_setup_script": str(setup),
                }
            },
            "sync_down_profiles": {
                "patch": {
                    "cloud_export_script": str(export),
                    "local_apply_script": str(apply_down),
                }
            },
            "container_profiles": {
                "runtime": {"mode": "image", "image": "runtime:test"}
            },
        },
        env={"WORKING_DIR": str(tmp_path / "workspace"), "CONFIG_DIR": str(tmp_path)},
    )

    assert resolved["local_stage_script"] is None
    assert resolved["install_script"] is None
    assert resolved["validation_script"] is None


def test_profile_resolver_rejects_missing_nonstandard_optional_hook_paths(
    tmp_path: Path,
) -> None:
    transfer = _write_script(tmp_path / "transfer")
    setup = _write_script(tmp_path / "setup")
    export = _write_script(tmp_path / "export")
    apply_down = _write_script(tmp_path / "apply-down")

    with pytest.raises(ValueError, match="install_script did not resolve"):
        resolve_cloud_agent_profiles(
            {
                "default_transfer_up_profile": "current",
                "default_sync_down_profile": "patch",
                "default_container_profile": "runtime",
                "transfer_up_profiles": {
                    "current": {
                        "local_transfer_script": str(transfer),
                        "cloud_setup_script": str(setup),
                        "install_script": str(tmp_path / "missing-install"),
                    }
                },
                "sync_down_profiles": {
                    "patch": {
                        "cloud_export_script": str(export),
                        "local_apply_script": str(apply_down),
                    }
                },
                "container_profiles": {
                    "runtime": {"mode": "image", "image": "runtime:test"}
                },
            },
            env={"WORKING_DIR": str(tmp_path), "CONFIG_DIR": str(tmp_path)},
        )


def test_clean_head_branch_profiles_import_branch_without_touching_local_dirty_state(
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
    transfer_up = scripts_root / "transfer_up" / "clean-head" / "local_transfer_script"
    setup = scripts_root / "transfer_up" / "clean-head" / "cloud_setup_script"
    export = scripts_root / "sync_down" / "branch-import" / "cloud_export_script"
    apply_down = scripts_root / "sync_down" / "branch-import" / "local_apply_script"
    mark_synced = (
        scripts_root / "sync_down" / "branch-import" / "cloud_mark_synced_script"
    )

    local = tmp_path / "local"
    cloud = tmp_path / "cloud"
    local.mkdir()
    cloud.mkdir()
    subprocess.run(["git", "init"], cwd=local, check=True, stdout=subprocess.PIPE)
    subprocess.run(
        ["git", "config", "user.email", "local@example.invalid"], cwd=local, check=True
    )
    subprocess.run(["git", "config", "user.name", "Local Test"], cwd=local, check=True)
    (local / "tracked.txt").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=local, check=True)
    subprocess.run(
        ["git", "commit", "-m", "base"], cwd=local, check=True, stdout=subprocess.PIPE
    )
    (local / "tracked.txt").write_text("local dirty\n", encoding="utf-8")

    upload = tmp_path / "upload"
    upload.mkdir()
    _run_cloud_profile_script(
        transfer_up,
        {"LOCAL_WORKSPACE_DIR": str(local), "TRANSFER_DIR": str(upload)},
        cwd=local,
    )
    env = _branch_script_env(
        workspace=local,
        cloud_workspace_dir=cloud,
        transfer_dir=upload,
        session_id="clean-head",
    )
    _run_cloud_profile_script(setup, env, cwd=cloud)

    assert (cloud / "tracked.txt").read_text(encoding="utf-8") == "base\n"

    subprocess.run(
        ["git", "config", "user.email", "cloud@example.invalid"], cwd=cloud, check=True
    )
    subprocess.run(["git", "config", "user.name", "Cloud Test"], cwd=cloud, check=True)
    (cloud / "tracked.txt").write_text("base\ncloud commit\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=cloud, check=True)
    subprocess.run(
        ["git", "commit", "-m", "cloud commit"],
        cwd=cloud,
        check=True,
        stdout=subprocess.PIPE,
    )

    sync1 = tmp_path / "sync1"
    sync1.mkdir()
    export_env = _branch_script_env(
        workspace=local,
        cloud_workspace_dir=cloud,
        transfer_dir=sync1,
        session_id="clean-head",
    )
    _run_cloud_profile_script(export, export_env, cwd=cloud)
    _run_cloud_profile_script(apply_down, export_env, cwd=local)
    _run_cloud_profile_script(mark_synced, export_env, cwd=cloud)

    assert (local / "tracked.txt").read_text(encoding="utf-8") == "local dirty\n"
    imported = subprocess.run(
        ["git", "show", "cloud/clean-head/committed:tracked.txt"],
        cwd=local,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    assert imported.stdout == "base\ncloud commit\n"
    local_snapshot = subprocess.run(
        ["git", "rev-parse", "refs/cloud-agent/clean-head/local-import-state"],
        cwd=local,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    assert local_snapshot.stdout.strip()


def test_dirty_branch_profiles_preserve_safety_refs_and_incremental_branch_sync(
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
    transfer_up = (
        scripts_root
        / "transfer_up"
        / "working-tree-current-state-branch"
        / "local_transfer_script"
    )
    setup = (
        scripts_root
        / "transfer_up"
        / "working-tree-current-state-branch"
        / "cloud_setup_script"
    )
    export = scripts_root / "sync_down" / "branch-import" / "cloud_export_script"
    apply_down = scripts_root / "sync_down" / "branch-import" / "local_apply_script"
    mark_synced = (
        scripts_root / "sync_down" / "branch-import" / "cloud_mark_synced_script"
    )

    local = tmp_path / "local"
    cloud = tmp_path / "cloud"
    local.mkdir()
    cloud.mkdir()
    subprocess.run(["git", "init"], cwd=local, check=True, stdout=subprocess.PIPE)
    subprocess.run(
        ["git", "config", "user.email", "local@example.invalid"], cwd=local, check=True
    )
    subprocess.run(["git", "config", "user.name", "Local Test"], cwd=local, check=True)
    (local / "a.txt").write_text("base-a\n", encoding="utf-8")
    (local / "b.txt").write_text("base-b\n", encoding="utf-8")
    subprocess.run(["git", "add", "a.txt", "b.txt"], cwd=local, check=True)
    subprocess.run(
        ["git", "commit", "-m", "base"], cwd=local, check=True, stdout=subprocess.PIPE
    )
    (local / "a.txt").write_text("local-a\n", encoding="utf-8")
    (local / "b.txt").write_text("local-b\n", encoding="utf-8")

    upload = tmp_path / "upload-branch"
    upload.mkdir()
    upload_env = _branch_script_env(
        workspace=local,
        cloud_workspace_dir=cloud,
        transfer_dir=upload,
        session_id="dirty-branch",
    )
    _run_cloud_profile_script(transfer_up, upload_env, cwd=local)
    delegated_snapshot = subprocess.run(
        ["git", "show", "refs/cloud-agent/dirty-branch/delegated-snapshot:a.txt"],
        cwd=local,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    assert delegated_snapshot.stdout == "local-a\n"

    _run_cloud_profile_script(setup, upload_env, cwd=cloud)
    assert (cloud / "a.txt").read_text(encoding="utf-8") == "local-a\n"
    assert (cloud / "b.txt").read_text(encoding="utf-8") == "local-b\n"

    subprocess.run(
        ["git", "config", "user.email", "cloud@example.invalid"], cwd=cloud, check=True
    )
    subprocess.run(["git", "config", "user.name", "Cloud Test"], cwd=cloud, check=True)
    (cloud / "b.txt").write_text("cloud-b1\n", encoding="utf-8")
    subprocess.run(["git", "add", "b.txt"], cwd=cloud, check=True)
    subprocess.run(
        ["git", "commit", "-m", "cloud b1"],
        cwd=cloud,
        check=True,
        stdout=subprocess.PIPE,
    )

    sync1 = tmp_path / "branch-sync1"
    sync1.mkdir()
    sync1_env = _branch_script_env(
        workspace=local,
        cloud_workspace_dir=cloud,
        transfer_dir=sync1,
        session_id="dirty-branch",
    )
    _run_cloud_profile_script(export, sync1_env, cwd=cloud)
    _run_cloud_profile_script(apply_down, sync1_env, cwd=local)
    _run_cloud_profile_script(mark_synced, sync1_env, cwd=cloud)

    assert (local / "a.txt").read_text(encoding="utf-8") == "local-a\n"
    assert (local / "b.txt").read_text(encoding="utf-8") == "local-b\n"
    committed_b1 = subprocess.run(
        ["git", "show", "cloud/dirty-branch/committed:b.txt"],
        cwd=local,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    assert committed_b1.stdout == "cloud-b1\n"
    delegated_b = subprocess.run(
        ["git", "show", "refs/cloud-agent/dirty-branch/delegated-snapshot:b.txt"],
        cwd=local,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    assert delegated_b.stdout == "local-b\n"
    cloud_full_b1 = subprocess.run(
        ["git", "show", "refs/cloud-agent/dirty-branch/cloud-full-state:a.txt"],
        cwd=local,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    assert cloud_full_b1.stdout == "local-a\n"
    local_import_b = subprocess.run(
        ["git", "show", "refs/cloud-agent/dirty-branch/local-import-state:b.txt"],
        cwd=local,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    assert local_import_b.stdout == "local-b\n"

    (cloud / "b.txt").write_text("cloud-b2\n", encoding="utf-8")
    subprocess.run(["git", "add", "b.txt"], cwd=cloud, check=True)
    subprocess.run(
        ["git", "commit", "-m", "cloud b2"],
        cwd=cloud,
        check=True,
        stdout=subprocess.PIPE,
    )
    (cloud / "a.txt").write_text("local-a\ncloud residual\n", encoding="utf-8")

    sync2 = tmp_path / "branch-sync2"
    sync2.mkdir()
    sync2_env = _branch_script_env(
        workspace=local,
        cloud_workspace_dir=cloud,
        transfer_dir=sync2,
        session_id="dirty-branch",
    )
    _run_cloud_profile_script(export, sync2_env, cwd=cloud)
    _run_cloud_profile_script(apply_down, sync2_env, cwd=local)

    committed_b2 = subprocess.run(
        ["git", "show", "cloud/dirty-branch/committed:b.txt"],
        cwd=local,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    assert committed_b2.stdout == "cloud-b2\n"
    cloud_full_a2 = subprocess.run(
        ["git", "show", "refs/cloud-agent/dirty-branch/cloud-full-state:a.txt"],
        cwd=local,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    assert cloud_full_a2.stdout == "local-a\ncloud residual\n"


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
    adapter_script = _write_script(tmp_path / "adapter", "exit 0\n")

    config_path = _write_config(tmp_path, transfer_script)
    config_data = json.loads(config_path.read_text(encoding="utf-8"))
    cloud_agent = config_data["application"]["cloud_agent"]
    managed_ssh = cloud_agent.setdefault("managed_ssh", {})
    managed_ssh["adapter_script"] = str(adapter_script)
    config_path.write_text(json.dumps(config_data), encoding="utf-8")
    app = AgentApplication(
        str(config_path), str(tmp_path / "sessions"), event_store=InMemoryEventStore()
    )
    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "hello cloud", {}, config=base_config)
    app.save_session(session)

    calls: List[Dict[str, Any]] = []

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

    monkeypatch.setattr("cloud_agent_app.cloud_agent_app_plugin.urlopen", fake_urlopen)
    plugin = app._app_plugins["cloud"].plugin
    monkeypatch.setattr(
        plugin, "_write_runtime_config_transfer", lambda *args, **kwargs: {}
    )

    class _InlineThread:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self._target = kwargs["target"]
            self._args = kwargs.get("args", ())

        def start(self) -> None:
            self._target(*self._args)

    monkeypatch.setattr(
        "cloud_agent_app.cloud_agent_app_plugin.threading.Thread", _InlineThread
    )

    result = app.execute_application_action(
        "cloud",
        "cloud.start_session_agent",
        {"session_id": session.session_id},
    )

    assert result["operation_ref"].startswith(f"cloud-start:{session.session_id}:")
    display = result["display"]
    assert display["title"] == "Cloud Agent Starting"
    assert calls[0]["url"] == "http://orchestrator.test/transfers"
    assert "public_key" in calls[0]["body"]
    assert "public_host" not in calls[0]["body"]
    assert calls[2]["body"]["session_id"] == session.session_id
    assert calls[2]["body"]["transfer_ref"] == {"transfer_id": "tr_test"}
    assert calls[2]["body"]["container"] == {
        "profile_id": "test-runtime",
        "mode": "image",
        "image": "cloud-agent-runtime:latest",
        "cache_mounts": [],
        "mounts": [],
    }
    assert calls[2]["body"]["connection_ref"]["reuse"] is True
    assert calls[2]["body"]["connection_ref"]["connection_key"].startswith(
        "cloud-agent-app:"
    )
    assert result["mutations"]["updated_session_ids"] == [session.session_id]
    assert result["ui_effects"]["reload_session_ids"] == [session.session_id]

    _core, _base_config, updated_session = app.load_session(session.session_id)
    cloud_agent = updated_session.metadata["cloud_agent"]
    assert cloud_agent["connection_id"] == "conn_test"
    assert cloud_agent["instance_id"] == "inst_test"
    assert cloud_agent["session_id"] == session.session_id
    assert cloud_agent["state"] == "running"
    assert cloud_agent["token"] == "tok_test"
    assert cloud_agent["connection_link"].startswith("crystal-lattice-cloud://connect?")

    captured = json.loads(env_capture.read_text(encoding="utf-8"))
    assert captured["LOCAL_WORKSPACE_DIR"] == str(workspace.resolve())
    assert captured["CLOUD_WORKSPACE_DIR"] == CLOUD_WORKSPACE_DIR
    assert captured["TRANSFER_DIR"]
    app.close()


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


def test_session_fork_clears_cloud_agent_metadata(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    transfer_script = _write_script(tmp_path / "transfer.py")

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
                    "state": "running",
                },
            },
        )
    )

    _core, _base_config, stored = app.load_session(session.session_id)
    _fork_core, _fork_base, forked = app.fork_session(
        core,
        stored,
        base_config,
        upto_index=len(stored.messages) - 1,
        new_session_id="forked-session",
    )

    assert "cloud_agent" not in (forked.metadata or {})


def test_detach_session_clears_cloud_metadata(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    transfer_script = _write_script(tmp_path / "transfer.py")

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
                    "state": "failed",
                },
            },
        )
    )

    result = app.execute_application_action(
        "cloud",
        "cloud.detach_session",
        {"session_id": session.session_id},
    )

    assert result["status"] == "ok"
    assert result["ui_effects"]["reload_session_ids"] == [session.session_id]
    _core, _base_config, updated_session = app.load_session(session.session_id)
    assert "cloud_agent" not in updated_session.metadata


def test_close_session_does_not_sync_before_closing_and_clears_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    transfer_script = _write_script(tmp_path / "transfer.py")

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
                    "instance_id": "inst_running",
                    "session_id": session.session_id,
                    "state": "running",
                },
            },
        )
    )

    plugin = CloudAgentAppPlugin()

    monkeypatch.setattr(
        plugin,
        "_sync_down",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("sync_down should not run for failed instances")
        ),
    )

    calls: List[str] = []

    def fake_post_json(
        base_url: str, path: str, payload: Dict[str, Any], *, token: Any = None
    ) -> Dict[str, Any]:
        calls.append(path)
        assert path == "/instances/inst_running/close"
        return {
            "instance_id": "inst_running",
            "session_id": session.session_id,
            "state": "closed",
        }

    monkeypatch.setattr(plugin, "_post_json", fake_post_json)

    result = plugin._close_session(
        app,
        {"instance_id": "inst_running", "session_id": session.session_id},
        {"orchestrator_url": "http://orchestrator.test"},
    )

    assert result["status"] == "ok"
    assert "sync_down" not in result
    assert result["display"]["body"] == (
        "The cloud runtime was closed. Unsynced cloud changes were not copied back locally."
    )
    assert calls == ["/instances/inst_running/close"]
    _core, _base_config, updated_session = app.load_session(session.session_id)
    assert "cloud_agent" not in updated_session.metadata
    assert updated_session.metadata["cloud_agent_last_runtime"]["was_cloud"] is True
    assert (
        updated_session.metadata["cloud_agent_last_runtime"]["current_workdir"]
        == CLOUD_WORKSPACE_DIR
    )


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
    assert manifest["included_excluded"] == []


def test_config_assets_copy_can_explicitly_include_excluded_files(
    tmp_path: Path,
) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / ".env").write_text("SECRET=1\n", encoding="utf-8")
    auth_dir = config_dir / "auth"
    auth_dir.mkdir()
    (auth_dir / "chatgpt-auth.json").write_text(
        '{"access_token":"test"}', encoding="utf-8"
    )
    (auth_dir / "do-not-copy.json").write_text('{"secret":"other"}', encoding="utf-8")
    state_dir = config_dir / "state"
    state_dir.mkdir()
    (state_dir / "state.json").write_text("{}", encoding="utf-8")

    target = tmp_path / "assets"
    manifest = copy_config_assets(
        config_dir=config_dir,
        target_dir=target,
        policy={
            "include_config_dir": True,
            "exclude": [".env", "auth", "state"],
            "include_excluded": [".env", "auth/chatgpt-auth.json"],
            "max_top_level_entry_bytes": 1024,
        },
    )

    assert (target / ".env").read_text(encoding="utf-8") == "SECRET=1\n"
    assert (target / "auth" / "chatgpt-auth.json").read_text(
        encoding="utf-8"
    ) == '{"access_token":"test"}'
    assert not (target / "auth" / "do-not-copy.json").exists()
    assert not (target / "state").exists()

    included = {
        (entry["path"], entry["status"]) for entry in manifest["included_excluded"]
    }
    assert (".env", "copied") in included
    assert ("auth/chatgpt-auth.json", "copied") in included

    excluded = {(entry["path"], entry["reason"]) for entry in manifest["excluded"]}
    assert (".env", "exclude_pattern") in excluded
    assert ("auth", "exclude_pattern") in excluded
    assert ("state", "exclude_pattern") in excluded


def test_config_assets_include_excluded_reports_missing_unsafe_and_size_limit(
    tmp_path: Path,
) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / ".env").write_text("SECRET=1\n", encoding="utf-8")
    (config_dir / ".env.large").write_text("x" * 20, encoding="utf-8")

    target = tmp_path / "assets"
    manifest = copy_config_assets(
        config_dir=config_dir,
        target_dir=target,
        policy={
            "include_config_dir": True,
            "exclude": [".env", ".env.*"],
            "include_excluded": [
                ".env",
                ".env.large",
                ".env.missing",
                "../outside",
                "/absolute",
            ],
            "max_top_level_entry_bytes": 10,
        },
    )

    assert (target / ".env").exists()
    assert not (target / ".env.large").exists()

    included = manifest["included_excluded"]
    assert {"path": ".env", "status": "copied", "bytes": 9} in included
    assert any(
        entry["path"] == ".env.large"
        and entry["status"] == "skipped"
        and entry["reason"] == "size_limit"
        for entry in included
    )
    assert {"path": ".env.missing", "status": "missing"} in included
    assert {
        "path": "../outside",
        "status": "rejected",
        "reason": "unsafe_path",
    } in included
    assert {
        "path": "/absolute",
        "status": "rejected",
        "reason": "unsafe_path",
    } in included


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


def test_portable_config_removes_cloud_disabled_plugin_specs_from_all_plugin_lists() -> (
    None
):
    disabled_spec = "path:${env:BUILTIN_PLUGINS}/session-asset-attachments"
    raw = {
        "plugins": [
            disabled_spec,
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
        ],
        "providers": {
            "kept_provider": {
                "provider": "echo",
                "plugins": [disabled_spec, "plugins.provider_extra"],
            }
        },
        "agents": {
            "selected": {
                "provider": "kept_provider",
                "plugins": [disabled_spec, "plugins.agent_extra"],
            }
        },
    }

    portable, manifest = build_portable_config(
        raw,
        cloud_agent_config={"disabled_plugins": [disabled_spec]},
        selected_agent_id="selected",
    )

    assert portable["plugins"] == [
        "plugins.echo_openai_like_provider.EchoOpenAILikeProvider"
    ]
    assert portable["providers"]["kept_provider"]["plugins"] == [
        "plugins.provider_extra"
    ]
    assert portable["agents"]["selected"]["plugins"] == ["plugins.agent_extra"]
    assert manifest["disabled_plugins"]["requested"] == [disabled_spec]
    assert manifest["disabled_plugins"]["removed"] == [
        {"path": "plugins", "spec": disabled_spec},
        {"path": "providers.kept_provider.plugins", "spec": disabled_spec},
        {"path": "agents.selected.plugins", "spec": disabled_spec},
    ]


def test_portable_config_cloud_disabled_plugin_specs_do_not_mutate_local_input() -> (
    None
):
    disabled_spec = "path:${env:BUILTIN_PLUGINS}/session-asset-attachments"
    raw = {
        "plugins": [disabled_spec],
        "agents": {"default": {"provider": "echo", "plugins": [disabled_spec]}},
    }

    portable, manifest = build_portable_config(
        raw,
        cloud_agent_config={
            "disabled_plugins": [disabled_spec, "path:${env:BUILTIN_PLUGINS}/missing"]
        },
    )

    assert portable["plugins"] == []
    assert portable["agents"]["default"]["plugins"] == []
    assert raw["plugins"] == [disabled_spec]
    assert raw["agents"]["default"]["plugins"] == [disabled_spec]
    assert manifest["disabled_plugins"]["requested"] == sorted(
        [disabled_spec, "path:${env:BUILTIN_PLUGINS}/missing"]
    )
    assert manifest["disabled_plugins"]["removed"] == [
        {"path": "plugins", "spec": disabled_spec},
        {"path": "agents.default.plugins", "spec": disabled_spec},
    ]


def test_agent_application_cloud_disabled_plugins_support_raw_literals(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    disabled_spec = "path:${env:BUILTIN_PLUGINS}/session-asset-attachments"
    cloud_plugin_path = _plugin_path()
    monkeypatch.setenv("BUILTIN_PLUGINS", str(_repo_root() / "plugins"))
    config = {
        "providers": {
            "echo": {
                "provider": "echo_openai_like",
                "model": "test-model",
            }
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            disabled_spec,
            f"path:{cloud_plugin_path}",
        ],
        "agents": {
            "codex-openai": {
                "provider": "echo",
            }
        },
        "application": {
            "cloud_agent": {
                "orchestrator_url": "http://orchestrator.test",
                "workspace_dir": str(tmp_path / "workspace"),
                "disabled_plugins": [{"$raw": disabled_spec}],
                "default_transfer_up_profile": "test-transfer",
                "default_sync_down_profile": "test-sync",
                "default_container_profile": "test-runtime",
                "transfer_up_profiles": {
                    "test-transfer": {
                        "local_transfer_script": str(
                            _write_script(tmp_path / "transfer")
                        ),
                        "cloud_setup_script": str(_write_script(tmp_path / "setup")),
                        "install_script": str(_write_script(tmp_path / "install")),
                    }
                },
                "sync_down_profiles": {
                    "test-sync": {
                        "cloud_export_script": str(_write_script(tmp_path / "export")),
                        "local_apply_script": str(_write_script(tmp_path / "apply")),
                    }
                },
                "container_profiles": {
                    "test-runtime": {
                        "mode": "image",
                        "image": "cloud-agent-runtime:latest",
                    }
                },
            }
        },
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    app = AgentApplication(
        str(config_path), str(tmp_path / "sessions"), event_store=InMemoryEventStore()
    )
    cloud_state = app._app_plugins["cloud"].state
    portable, manifest = build_portable_config(
        app.get_raw_config(),
        cloud_agent_config=cloud_state,
        selected_agent_id="codex-openai",
    )

    assert cloud_state["disabled_plugins"] == [disabled_spec]
    assert disabled_spec not in portable["plugins"]
    assert manifest["disabled_plugins"]["requested"] == [disabled_spec]
    assert manifest["disabled_plugins"]["removed"] == [
        {"path": "plugins", "spec": disabled_spec}
    ]
