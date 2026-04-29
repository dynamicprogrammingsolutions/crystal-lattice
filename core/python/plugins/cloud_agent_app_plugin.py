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
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen


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
        application = app_config.get("application") if isinstance(app_config, dict) else {}
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

    def _start_session_agent(self, app: Any, params: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        orchestrator_url = self._required_config(state, "orchestrator_url")
        session_id = params["session_id"]
        loaded = app.load_session(session_id)
        if loaded is None:
            raise KeyError(f"Session {session_id!r} not found")
        core, _base_config, session = loaded

        workspace_dir = self._workspace_dir(params, state)
        cloud_workspace_dir = str(state.get("cloud_workspace_dir") or "/workspace")

        with tempfile.TemporaryDirectory(prefix="cloud-agent-transfer-") as transfer_tmp:
            transfer_dir = Path(transfer_tmp)
            transfer_env = {
                "LOCAL_WORKSPACE_DIR": str(workspace_dir),
                "CLOUD_WORKSPACE_DIR": cloud_workspace_dir,
                "TRANSFER_DIR": str(transfer_dir),
            }
            if isinstance(state.get("transfer_script"), str) and str(state.get("transfer_script")).strip():
                self._run_script(state.get("transfer_script"), transfer_env, cwd=workspace_dir)
            else:
                self._copy_workspace_to_transfer(workspace_dir, transfer_dir)
            self._write_session_export(transfer_dir, session_id, core.export_session(session))

            transfer = self._post_json(
                orchestrator_url,
                "/transfers",
                {
                    "direction": "upload",
                    "method": state.get("transfer_method", "managed_ssh"),
                    "public_host": state.get("transfer_public_host"),
                    "public_key": state.get("transfer_public_key"),
                },
                token=state.get("orchestrator_token"),
            )

            transfer_id = str(transfer["transfer_id"])
            if not self._run_optional_upload_script(state, transfer, transfer_dir, workspace_dir, cloud_workspace_dir):
                self._upload_transfer_bundle(
                    orchestrator_url,
                    transfer_id,
                    transfer_dir,
                    token=state.get("orchestrator_token"),
                )
            self._post_json(orchestrator_url, f"/transfers/{transfer_id}/ready", {}, token=state.get("orchestrator_token"))

            instance = self._post_json(
                orchestrator_url,
                "/instances",
                {
                    "session_id": session_id,
                    "transfer_ref": {"transfer_id": transfer_id},
                    "cloud_workspace_dir": cloud_workspace_dir,
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

    def _sync_down(self, params: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        orchestrator_url = self._required_config(state, "orchestrator_url")
        workspace_dir = self._workspace_dir(params, state)
        cloud_workspace_dir = str(state.get("cloud_workspace_dir") or "/workspace")
        instance_id = params["instance_id"]

        with tempfile.TemporaryDirectory(prefix="cloud-agent-sync-down-") as transfer_tmp:
            transfer_dir = Path(transfer_tmp)
            transfer = self._post_json(
                orchestrator_url,
                "/transfers",
                {"direction": "download", "method": state.get("transfer_method", "managed_ssh")},
                token=state.get("orchestrator_token"),
            )
            transfer_id = str(transfer["transfer_id"])
            export_result = self._post_json(
                orchestrator_url,
                f"/instances/{instance_id}/export",
                {"transfer_ref": {"transfer_id": transfer_id}},
                token=state.get("orchestrator_token"),
            )
            if not self._run_optional_download_script(state, transfer, transfer_dir, workspace_dir, cloud_workspace_dir):
                self._download_transfer_bundle(
                    orchestrator_url,
                    transfer_id,
                    transfer_dir,
                    token=state.get("orchestrator_token"),
                )
            if isinstance(state.get("apply_script"), str) and str(state.get("apply_script")).strip():
                self._run_script(
                    state.get("apply_script"),
                    {
                        "LOCAL_WORKSPACE_DIR": str(workspace_dir),
                        "CLOUD_WORKSPACE_DIR": cloud_workspace_dir,
                        "TRANSFER_DIR": str(transfer_dir),
                    },
                    cwd=workspace_dir,
                )
            else:
                self._copytree_contents(transfer_dir, workspace_dir)
        return {"status": "ok", "instance_id": instance_id, "export": export_result}

    def _close_session(self, app: Any, params: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        orchestrator_url = self._required_config(state, "orchestrator_url")
        instance_id = params["instance_id"]
        result = self._post_json(
            orchestrator_url,
            f"/instances/{instance_id}/close",
            {},
            token=state.get("orchestrator_token"),
        )
        session_payload = result.get("session")
        session_id = params.get("session_id") or result.get("session_id")
        if isinstance(session_payload, str) and isinstance(session_id, str) and session_id:
            loaded = app.load_session(session_id)
            if loaded is not None:
                core, _base_config, _old = loaded
                app.save_session(core.import_session(session_payload))
        return {"status": "ok", "instance_id": instance_id, "close": result}

    def _required_config(self, state: Dict[str, Any], key: str) -> str:
        value = state.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"application.cloud_agent.{key} is required")
        return value.rstrip("/")

    def _workspace_dir(self, params: Dict[str, Any], state: Dict[str, Any]) -> Path:
        raw = params.get("workspace_dir") or state.get("workspace_dir") or os.getcwd()
        return Path(str(raw)).expanduser().resolve()

    def _run_optional_upload_script(
        self,
        state: Dict[str, Any],
        transfer: Dict[str, Any],
        transfer_dir: Path,
        workspace_dir: Path,
        cloud_workspace_dir: str,
    ) -> bool:
        raw_path = state.get("upload_script")
        if not isinstance(raw_path, str) or not raw_path.strip():
            return False
        self._run_script(
            raw_path,
            {
                "LOCAL_WORKSPACE_DIR": str(workspace_dir),
                "CLOUD_WORKSPACE_DIR": cloud_workspace_dir,
                "TRANSFER_DIR": str(transfer_dir),
                "TRANSFER_ID": str(transfer.get("transfer_id") or ""),
                "TRANSFER_ENDPOINT": json.dumps(transfer.get("endpoint") or {}),
            },
            cwd=workspace_dir,
        )
        return True

    def _run_optional_download_script(
        self,
        state: Dict[str, Any],
        transfer: Dict[str, Any],
        transfer_dir: Path,
        workspace_dir: Path,
        cloud_workspace_dir: str,
    ) -> bool:
        raw_path = state.get("download_script")
        if not isinstance(raw_path, str) or not raw_path.strip():
            return False
        self._run_script(
            raw_path,
            {
                "LOCAL_WORKSPACE_DIR": str(workspace_dir),
                "CLOUD_WORKSPACE_DIR": cloud_workspace_dir,
                "TRANSFER_DIR": str(transfer_dir),
                "TRANSFER_ID": str(transfer.get("transfer_id") or ""),
                "TRANSFER_ENDPOINT": json.dumps(transfer.get("endpoint") or {}),
            },
            cwd=workspace_dir,
        )
        return True

    def _run_script(self, raw_path: Any, env: Dict[str, str], *, cwd: Path) -> None:
        if not isinstance(raw_path, str) or not raw_path.strip():
            return
        script = Path(raw_path).expanduser()
        if not script.is_absolute():
            script = cwd / script
        subprocess.run(
            [str(script)],
            cwd=str(cwd),
            env={**os.environ, **env},
            check=True,
        )

    def _write_session_export(self, transfer_dir: Path, session_id: str, payload: str) -> None:
        session_dir = transfer_dir / ".cloud-agent" / "sessions"
        session_dir.mkdir(parents=True, exist_ok=True)
        (session_dir / f"{session_id}.json").write_text(payload, encoding="utf-8")

    def _copy_workspace_to_transfer(self, workspace_dir: Path, transfer_dir: Path) -> None:
        workspace_target = transfer_dir / "workspace"
        workspace_target.mkdir(parents=True, exist_ok=True)
        for child in workspace_dir.iterdir():
            if child.name == ".cloud-agent":
                continue
            target = workspace_target / child.name
            if child.is_dir():
                shutil.copytree(child, target, dirs_exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(child, target)

    def _upload_transfer_bundle(
        self,
        orchestrator_url: str,
        transfer_id: str,
        transfer_dir: Path,
        *,
        token: Any = None,
    ) -> Dict[str, Any]:
        archive_path = transfer_dir.parent / f"{transfer_id}.tar.gz"
        try:
            with tarfile.open(archive_path, "w:gz") as archive:
                for child in transfer_dir.iterdir():
                    archive.add(child, arcname=child.name)
            headers = {"content-type": "application/gzip"}
            if isinstance(token, str) and token:
                headers["authorization"] = f"Bearer {token}"
            request = Request(
                f"{orchestrator_url.rstrip('/')}/transfers/{transfer_id}/upload",
                data=archive_path.read_bytes(),
                headers=headers,
                method="PUT",
            )
            with urlopen(request, timeout=60) as response:
                parsed = json.loads(response.read().decode("utf-8"))
            return parsed if isinstance(parsed, dict) else {}
        finally:
            archive_path.unlink(missing_ok=True)

    def _download_transfer_bundle(
        self,
        orchestrator_url: str,
        transfer_id: str,
        transfer_dir: Path,
        *,
        token: Any = None,
    ) -> None:
        headers = {}
        if isinstance(token, str) and token:
            headers["authorization"] = f"Bearer {token}"
        request = Request(
            f"{orchestrator_url.rstrip('/')}/transfers/{transfer_id}/download",
            headers=headers,
            method="GET",
        )
        archive_path = transfer_dir.parent / f"{transfer_id}.download.tar.gz"
        try:
            with urlopen(request, timeout=60) as response:
                archive_path.write_bytes(response.read())
            with tarfile.open(archive_path, "r:gz") as archive:
                archive.extractall(transfer_dir)
        finally:
            archive_path.unlink(missing_ok=True)

    def _copytree_contents(self, source: Path, destination: Path) -> None:
        for child in source.iterdir():
            target = destination / child.name
            if child.is_dir():
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(child, target)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(child, target)

    def _post_json(self, base_url: str, path: str, payload: Dict[str, Any], *, token: Any = None) -> Dict[str, Any]:
        body = json.dumps({k: v for k, v in payload.items() if v is not None}).encode("utf-8")
        headers = {"content-type": "application/json"}
        if isinstance(token, str) and token:
            headers["authorization"] = f"Bearer {token}"
        request = Request(base_url.rstrip("/") + path, data=body, headers=headers, method="POST")
        with urlopen(request, timeout=30) as response:
            parsed = json.loads(response.read().decode("utf-8"))
        return parsed if isinstance(parsed, dict) else {}

    def _cloud_link(self, *, orchestrator_url: str, instance_id: str, session_id: str, token: str) -> str:
        return "crystal-lattice-cloud://connect?" + urlencode(
            {
                "orchestrator": orchestrator_url,
                "instance_id": instance_id,
                "session_id": session_id,
                "token": token,
            }
        )


__all__ = ["CloudAgentAppPlugin"]