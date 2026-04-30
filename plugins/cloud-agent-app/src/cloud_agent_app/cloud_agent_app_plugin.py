"""Application plugin for starting and managing cloud agent sessions.

The plugin intentionally keeps file-transfer semantics outside the
orchestrator. Project scripts decide what goes into ``TRANSFER_DIR`` and the
configured transfer adapter decides how that directory reaches the cloud host.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .cloud_agent_transfer import CLOUD_WORKSPACE_DIR, prepare_cloud_transfer


DEFAULT_TRANSFER_METHOD = "managed_ssh"
RESERVED_CLOUD_AGENT_DIR = ".cloud-agent"


class CloudAgentAppPlugin:
    name = "cloud"
    version = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "cloud_agent": {
                "type": "object",
                "description": "Cloud agent orchestrator and transfer settings.",
            }
        }

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        application = (
            app_config.get("application") if isinstance(app_config, dict) else {}
        )
        cloud = application.get("cloud_agent") if isinstance(application, dict) else {}
        return dict(cloud) if isinstance(cloud, dict) else {}

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "id": "cloud.start_session_agent",
                "label": "Start cloud agent",
                "description": "Start a cloud agent for a local session and return a copyable cloud connection link.",
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    "workspace_dir": {"type": "string", "required": False},
                },
            },
            {
                "id": "cloud.sync_down",
                "label": "Sync cloud changes",
                "description": "Transfer cloud workspace changes back into the local workspace.",
                "inputs": {
                    "instance_id": {"type": "string", "required": True},
                    "session_id": {"type": "string", "required": False},
                    "workspace_dir": {"type": "string", "required": False},
                },
            },
            {
                "id": "cloud.close_session",
                "label": "Close cloud session",
                "description": "Close a cloud session and overwrite/update the local session with remote state.",
                "inputs": {
                    "instance_id": {"type": "string", "required": True},
                    "session_id": {"type": "string", "required": False},
                    "workspace_dir": {"type": "string", "required": False},
                },
            },
        ]

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "ui_type": "session_action",
                "id": "cloud_start_session_agent",
                "label": "Start cloud agent",
                "action_id": "cloud.start_session_agent",
            }
        ]

    def execute_action(
        self,
        app: Any,
        action_id: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        if action_id == "cloud.start_session_agent":
            return self._start_session_agent(app, params, state)
        if action_id == "cloud.sync_down":
            return self._sync_down(params, state)
        if action_id == "cloud.close_session":
            return self._close_session(app, params, state)
        raise KeyError(f"Unknown cloud action {action_id!r}")

    def _start_session_agent(
        self, app: Any, params: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        orchestrator_url = self._required_config(state, "orchestrator_url")
        session_id = params["session_id"]
        loaded = app.load_session(session_id)
        if loaded is None:
            raise KeyError(f"Session {session_id!r} not found")
        core, _base_config, session = loaded

        workspace_dir = self._workspace_dir(params, state)
        cloud_workspace_dir = CLOUD_WORKSPACE_DIR
        local_transfer_script = self._required_script_config(
            state, "local_transfer_script", legacy_key="transfer_script"
        )

        with tempfile.TemporaryDirectory(
            prefix="cloud-agent-transfer-"
        ) as transfer_tmp:
            transfer_dir = Path(transfer_tmp)
            transfer_env = {
                "LOCAL_WORKSPACE_DIR": str(workspace_dir),
                "CLOUD_WORKSPACE_DIR": cloud_workspace_dir,
                "TRANSFER_DIR": str(transfer_dir),
            }
            self._run_script(local_transfer_script, transfer_env, cwd=workspace_dir)
            self._write_session_export(
                transfer_dir, session_id, core.export_session(session)
            )
            self._write_runtime_config_transfer(app, transfer_dir, state)
            self._write_cloud_runtime_scripts(transfer_dir, state, workspace_dir)

            key_paths = self._create_transfer_keypair(transfer_dir)

            transfer = self._post_json(
                orchestrator_url,
                "/transfers",
                {
                    "direction": "upload",
                    "method": state.get("transfer_method", DEFAULT_TRANSFER_METHOD),
                    "public_host": state.get("transfer_public_host"),
                    "public_key": key_paths["public_key"],
                },
                token=state.get("orchestrator_token"),
            )

            transfer_id = str(transfer["transfer_id"])
            self._run_managed_ssh_adapter(
                state,
                transfer,
                transfer_dir,
                key_paths["private_key_path"],
                direction="upload",
                cwd=workspace_dir,
            )
            self._post_json(
                orchestrator_url,
                f"/transfers/{transfer_id}/ready",
                {},
                token=state.get("orchestrator_token"),
            )

            instance = self._post_json(
                orchestrator_url,
                "/instances",
                {
                    "session_id": session_id,
                    "transfer_ref": {"transfer_id": transfer_id},
                },
                token=state.get("orchestrator_token"),
            )

        link = self._cloud_link(
            orchestrator_url=orchestrator_url,
            instance_id=str(instance["instance_id"]),
            session_id=session_id,
            token=str(instance["token"]),
        )
        return {
            "instance": instance,
            "connection_link": link,
            "display": {
                "format": "markdown",
                "title": "Cloud Agent Ready",
                "body": "The cloud session is ready. Copy the connection link and open it from the mobile app.",
                "variant": "success",
                "actions": [
                    {
                        "kind": "copy_text",
                        "id": "copy-cloud-connection-link",
                        "label": "Copy connection link",
                        "text": link,
                    }
                ],
            },
        }

    def _sync_down(
        self, params: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        orchestrator_url = self._required_config(state, "orchestrator_url")
        workspace_dir = self._workspace_dir(params, state)
        cloud_workspace_dir = CLOUD_WORKSPACE_DIR
        instance_id = params["instance_id"]
        self._required_script_config(state, "cloud_export_script")
        local_apply_script = self._required_script_config(
            state, "local_apply_script", legacy_key="apply_script"
        )

        with tempfile.TemporaryDirectory(
            prefix="cloud-agent-sync-down-"
        ) as transfer_tmp:
            transfer_dir = Path(transfer_tmp)
            key_paths = self._create_transfer_keypair(transfer_dir)
            transfer = self._post_json(
                orchestrator_url,
                "/transfers",
                {
                    "direction": "download",
                    "method": state.get("transfer_method", DEFAULT_TRANSFER_METHOD),
                    "public_key": key_paths["public_key"],
                },
                token=state.get("orchestrator_token"),
            )
            transfer_id = str(transfer["transfer_id"])
            export_result = self._post_json(
                orchestrator_url,
                f"/instances/{instance_id}/export",
                {"transfer_ref": {"transfer_id": transfer_id}},
                token=state.get("orchestrator_token"),
            )
            try:
                self._run_managed_ssh_adapter(
                    state,
                    transfer,
                    transfer_dir,
                    key_paths["private_key_path"],
                    direction="download",
                    cwd=workspace_dir,
                )
                self._run_script(
                    local_apply_script,
                    {
                        "LOCAL_WORKSPACE_DIR": str(workspace_dir),
                        "CLOUD_WORKSPACE_DIR": cloud_workspace_dir,
                        "TRANSFER_DIR": str(transfer_dir),
                    },
                    cwd=workspace_dir,
                )
            finally:
                self._delete_transfer(
                    orchestrator_url,
                    transfer_id,
                    token=state.get("orchestrator_token"),
                )
        return {"status": "ok", "instance_id": instance_id, "export": export_result}

    def _close_session(
        self, app: Any, params: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        orchestrator_url = self._required_config(state, "orchestrator_url")
        instance_id = params["instance_id"]
        sync_result = self._sync_down(params, state)
        result = self._post_json(
            orchestrator_url,
            f"/instances/{instance_id}/close",
            {},
            token=state.get("orchestrator_token"),
        )
        session_payload = result.get("session")
        session_id = params.get("session_id") or result.get("session_id")
        if (
            isinstance(session_payload, str)
            and isinstance(session_id, str)
            and session_id
        ):
            loaded = app.load_session(session_id)
            if loaded is not None:
                core, _base_config, _old = loaded
                app.save_session(core.import_session(session_payload))
        return {
            "status": "ok",
            "instance_id": instance_id,
            "sync_down": sync_result,
            "close": result,
        }

    def _required_config(self, state: Dict[str, Any], key: str) -> str:
        value = state.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"application.cloud_agent.{key} is required")
        return value.rstrip("/")

    def _required_script_config(
        self, state: Dict[str, Any], key: str, *, legacy_key: str | None = None
    ) -> str:
        value = state.get(key)
        if not isinstance(value, str) or not value.strip():
            if legacy_key and isinstance(state.get(legacy_key), str):
                raise ValueError(
                    f"application.cloud_agent.{legacy_key} has been replaced by "
                    f"application.cloud_agent.{key}"
                )
            raise ValueError(f"application.cloud_agent.{key} is required")
        return value

    def _workspace_dir(self, params: Dict[str, Any], state: Dict[str, Any]) -> Path:
        raw = params.get("workspace_dir") or state.get("workspace_dir") or os.getcwd()
        return Path(str(raw)).expanduser().resolve()

    def _run_managed_ssh_adapter(
        self,
        state: Dict[str, Any],
        transfer: Dict[str, Any],
        transfer_dir: Path,
        private_key_path: Path,
        *,
        direction: str,
        cwd: Path,
    ) -> None:
        if str(transfer.get("method") or DEFAULT_TRANSFER_METHOD) != "managed_ssh":
            raise ValueError("Only application.cloud_agent.transfer_method=managed_ssh is supported")
        endpoint = transfer.get("endpoint")
        if not isinstance(endpoint, dict):
            raise ValueError("managed SSH transfer endpoint is missing")
        host = endpoint.get("host")
        port = endpoint.get("port")
        username = endpoint.get("username")
        if not isinstance(host, str) or not host:
            raise ValueError("managed SSH transfer endpoint host is missing")
        if not isinstance(username, str) or not username:
            raise ValueError("managed SSH transfer endpoint username is missing")
        if port is None:
            raise ValueError("managed SSH transfer endpoint port is missing")

        known_hosts = transfer_dir / ".cloud-agent-known-hosts"
        host_key = endpoint.get("host_key")
        if isinstance(host_key, str) and host_key.strip():
            known_hosts.write_text(
                f"[{host}]:{port} {host_key.strip()}\n",
                encoding="utf-8",
            )
        else:
            known_hosts.write_text("", encoding="utf-8")

        managed_ssh = state.get("managed_ssh")
        managed_ssh = managed_ssh if isinstance(managed_ssh, dict) else {}
        adapter_script = managed_ssh.get("adapter_script")
        if not isinstance(adapter_script, str) or not adapter_script.strip():
            adapter_script = str(Path(__file__).with_name("managed_ssh_rsync.sh"))

        env = {
            "TRANSFER_DIRECTION": direction,
            "TRANSFER_DIR": str(transfer_dir),
            "TRANSFER_ID": str(transfer.get("transfer_id") or ""),
            "TRANSFER_SSH_HOST": host,
            "TRANSFER_SSH_PORT": str(port),
            "TRANSFER_SSH_USER": username,
            "TRANSFER_SSH_KEY_PATH": str(private_key_path),
            "TRANSFER_SSH_KNOWN_HOSTS": str(known_hosts),
            "TRANSFER_REMOTE_PATH": str(endpoint.get("path") or "."),
            "SSH_PATH": str(managed_ssh.get("ssh_path") or "ssh"),
            "RSYNC_PATH": str(managed_ssh.get("rsync_path") or "rsync"),
            "RSYNC_EXTRA_ARGS": self._join_shell_args(
                managed_ssh.get("extra_rsync_args")
            ),
        }
        self._run_script(adapter_script, env, cwd=cwd)

    def _join_shell_args(self, value: Any) -> str:
        if not isinstance(value, list):
            return ""
        return " ".join(str(item) for item in value if isinstance(item, str) and item)

    def _run_script(self, raw_path: Any, env: Dict[str, str], *, cwd: Path) -> None:
        if not isinstance(raw_path, str) or not raw_path.strip():
            return
        script = Path(raw_path).expanduser()
        if not script.is_absolute():
            script = cwd / script
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
                f"Script {script} failed with {result.returncode}: "
                f"{result.stderr or result.stdout}"
            )

    def _write_session_export(
        self, transfer_dir: Path, session_id: str, payload: str
    ) -> None:
        session_dir = transfer_dir / ".cloud-agent" / "sessions"
        session_dir.mkdir(parents=True, exist_ok=True)
        (session_dir / f"{session_id}.json").write_text(payload, encoding="utf-8")

    def _write_runtime_config_transfer(
        self, app: Any, transfer_dir: Path, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        get_raw_config = getattr(app, "get_raw_config", None)
        get_config_path = getattr(app, "get_config_path", None)
        get_resolved_env = getattr(app, "get_resolved_env", None)
        if (
            not callable(get_raw_config)
            or not callable(get_config_path)
            or not callable(get_resolved_env)
        ):
            return {}
        return prepare_cloud_transfer(
            raw_config=get_raw_config(),
            config_path=Path(get_config_path()),
            transfer_dir=transfer_dir,
            cloud_agent_config=state,
            env=get_resolved_env(),
        )

    def _write_cloud_runtime_scripts(
        self, transfer_dir: Path, state: Dict[str, Any], workspace_dir: Path
    ) -> None:
        scripts_dir = transfer_dir / RESERVED_CLOUD_AGENT_DIR / "scripts"
        for key, target_name in (
            ("cloud_setup_script", "setup"),
            ("cloud_export_script", "export"),
        ):
            raw = state.get(key)
            if not isinstance(raw, str) or not raw.strip():
                continue
            source = Path(raw).expanduser()
            if not source.is_absolute():
                source = workspace_dir / source
            if not source.is_file():
                raise FileNotFoundError(f"application.cloud_agent.{key} not found: {source}")
            scripts_dir.mkdir(parents=True, exist_ok=True)
            target = scripts_dir / target_name
            shutil.copy2(source, target)
            target.chmod(target.stat().st_mode | 0o700)

    def _create_transfer_keypair(self, transfer_dir: Path) -> Dict[str, Any]:
        key_path = transfer_dir / ".cloud-agent-transfer-key"
        subprocess.run(
            [
                "ssh-keygen",
                "-q",
                "-t",
                "ed25519",
                "-N",
                "",
                "-f",
                str(key_path),
            ],
            check=True,
        )
        private_key = key_path
        public_key = key_path.with_suffix(".pub").read_text(encoding="utf-8").strip()
        private_key.chmod(0o600)
        return {"private_key_path": private_key, "public_key": public_key}

    def _post_json(
        self, base_url: str, path: str, payload: Dict[str, Any], *, token: Any = None
    ) -> Dict[str, Any]:
        body = json.dumps({k: v for k, v in payload.items() if v is not None}).encode(
            "utf-8"
        )
        headers = {"content-type": "application/json"}
        if isinstance(token, str) and token:
            headers["authorization"] = f"Bearer {token}"
        request = Request(
            base_url.rstrip("/") + path, data=body, headers=headers, method="POST"
        )
        try:
            with urlopen(request, timeout=420) as response:
                parsed = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"POST {path} failed with HTTP {exc.code}: {detail}") from exc
        return parsed if isinstance(parsed, dict) else {}

    def _delete_transfer(self, base_url: str, transfer_id: str, *, token: Any = None) -> None:
        headers = {}
        if isinstance(token, str) and token:
            headers["authorization"] = f"Bearer {token}"
        request = Request(
            f"{base_url.rstrip('/')}/transfers/{transfer_id}",
            headers=headers,
            method="DELETE",
        )
        try:
            with urlopen(request, timeout=60):
                return
        except HTTPError:
            return

    def _cloud_link(
        self, *, orchestrator_url: str, instance_id: str, session_id: str, token: str
    ) -> str:
        return "crystal-lattice-cloud://connect?" + urlencode(
            {
                "orchestrator": orchestrator_url,
                "instance_id": instance_id,
                "session_id": session_id,
                "token": token,
            }
        )


__all__ = ["CloudAgentAppPlugin"]
