from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from cloud_agent_app.cloud_agent_app_plugin import CloudAgentAppPlugin
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
                "local_transfer_script": str(transfer_script),
                "cloud_export_script": str(transfer_script),
                "local_apply_script": str(transfer_script),
                "transfer_method": "managed_ssh",
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
    assert calls[2]["body"] == {
        "session_id": session.session_id,
        "transfer_ref": {"transfer_id": "tr_test"},
    }
    assert adapter_calls[0]["direction"] == "upload"

    captured = json.loads(env_capture.read_text(encoding="utf-8"))
    assert captured["LOCAL_WORKSPACE_DIR"] == str(workspace.resolve())
    assert captured["CLOUD_WORKSPACE_DIR"] == CLOUD_WORKSPACE_DIR
    assert captured["TRANSFER_DIR"]


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
