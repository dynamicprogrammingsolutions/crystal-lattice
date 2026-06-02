"""Application plugin for starting and managing cloud agent sessions.

The plugin intentionally keeps file-transfer semantics outside the
orchestrator. Project scripts decide what goes into ``TRANSFER_DIR`` and the
configured transfer adapter decides how that directory reaches the cloud host.
"""

from __future__ import annotations

import json
import os
import hashlib
import re
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from agent_core.utils import get_logger
from agent_core.types import Session
from agent_terminal_app.runtime_layout import load_runtime_layout

from .cloud_agent_profiles import resolve_cloud_agent_profiles
from .cloud_agent_transfer import (
    CLOUD_CACHE_DIR,
    CLOUD_WORKSPACE_DIR,
    prepare_cloud_transfer,
)
from .cloud_agent_validation import (
    ensure_local_runtime_image,
    reserve_local_port,
    run_command,
)


DEFAULT_TRANSFER_METHOD = "managed_ssh"
RESERVED_CLOUD_AGENT_DIR = ".cloud-agent"
CLOUD_AGENT_METADATA_KEY = "cloud_agent"
CLOUD_AGENT_LAST_RUNTIME_KEY = "cloud_agent_last_runtime"
DEFAULT_START_ACTION_TIMEOUT_SECONDS = 0.0
DEFAULT_IMPORTED_BRANCH_PREFIX = "cloud"
CLOUD_AGENT_OPERATION_STORE_KEY = "cloud_agent_operations"
_log = get_logger("cloud_agent_app")


class CloudAgentOperationRegistry:
    """Process-local registry for cloud startup operations."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._operations: Dict[str, Dict[str, Any]] = {}

    def create(self, *, session_id: str) -> Dict[str, Any]:
        operation_ref = f"cloud-start:{session_id}:{uuid.uuid4().hex}"
        operation = {
            "operation_ref": operation_ref,
            "session_id": session_id,
            "state": "starting",
            "startup_stage": "queued",
            "created_at": time.time(),
            "updated_at": time.time(),
        }
        with self._lock:
            self._operations[operation_ref] = operation
        return dict(operation)

    def update(self, operation_ref: str, **updates: Any) -> Dict[str, Any]:
        with self._lock:
            current = dict(self._operations.get(operation_ref) or {})
            current.update(updates)
            current["operation_ref"] = operation_ref
            current["updated_at"] = time.time()
            self._operations[operation_ref] = current
            return dict(current)

    def get(self, operation_ref: str) -> Dict[str, Any] | None:
        with self._lock:
            operation = self._operations.get(operation_ref)
            return dict(operation) if isinstance(operation, dict) else None


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
        if not isinstance(cloud, dict):
            return {}
        return resolve_cloud_agent_profiles(cloud)

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
                "id": "cloud.check_session_agent",
                "label": "Check cloud agent status",
                "description": "Check whether a cloud agent runtime is ready.",
                "inputs": {
                    "instance_id": {"type": "string", "required": False},
                    "session_id": {"type": "string", "required": True},
                    "token": {"type": "string", "required": False},
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
            {
                "id": "cloud.detach_session",
                "label": "Detach cloud instance",
                "description": "Remove the attached cloud instance from the local session without changing the remote instance.",
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                },
            },
            {
                "id": "cloud.validate_cloud",
                "label": "Validate cloud workspace",
                "description": "Run the local-Docker cloud validation flow for the current workspace.",
                "inputs": {
                    "workspace_dir": {"type": "string", "required": False},
                    "keep_temp_dir": {
                        "type": "boolean",
                        "required": False,
                        "default": False,
                    },
                    "cache_dir": {"type": "string", "required": False},
                    "runtime_build_context": {"type": "string", "required": False},
                    "runtime_dockerfile": {"type": "string", "required": False},
                },
            },
            {
                "id": "cloud.clear_forked_session_attachment",
                "label": "Clear cloud attachment on fork",
                "description": "Internal lifecycle action that removes cloud attachment metadata from forked sessions.",
                "inputs": {},
                "trigger": "session_fork",
            },
        ]

    def get_commands(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
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
        ]

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        has_cloud_agent = {
            "any": [
                {
                    "path": f"metadata.{CLOUD_AGENT_METADATA_KEY}.instance_id",
                    "exists": True,
                },
                {
                    "path": f"metadata.{CLOUD_AGENT_METADATA_KEY}.operation_ref",
                    "exists": True,
                },
            ]
        }
        has_cloud_instance = {
            "path": f"metadata.{CLOUD_AGENT_METADATA_KEY}.instance_id",
            "exists": True,
        }
        return [
            {
                "ui_type": "session_action",
                "id": "cloud_start_session_agent",
                "label": "Start cloud agent",
                "action_id": "cloud.start_session_agent",
                "param_map": {"session_id": "$session.session_id"},
            },
            {
                "ui_type": "session_action",
                "id": "cloud_check_session_agent",
                "label": "Check cloud status",
                "action_id": "cloud.check_session_agent",
                "param_map": {
                    "session_id": "$session.session_id",
                },
                "condition": has_cloud_agent,
            },
            {
                "ui_type": "session_action",
                "id": "cloud_sync_down",
                "label": "Sync cloud changes",
                "action_id": "cloud.sync_down",
                "param_map": {
                    "instance_id": "$session.metadata.cloud_agent.instance_id",
                    "session_id": "$session.session_id",
                },
                "condition": has_cloud_instance,
            },
            {
                "ui_type": "session_action",
                "id": "cloud_close_session",
                "label": "Close cloud agent",
                "action_id": "cloud.close_session",
                "param_map": {
                    "instance_id": "$session.metadata.cloud_agent.instance_id",
                    "session_id": "$session.session_id",
                },
                "dialog": {
                    "kind": "confirm",
                    "title": "Close cloud agent",
                    "message": (
                        "Close this cloud agent now? Unsynced cloud changes "
                        "will be lost unless you synced them previously."
                    ),
                },
                "condition": has_cloud_instance,
            },
            {
                "ui_type": "session_action",
                "id": "cloud_detach_session",
                "label": "Detach cloud instance",
                "action_id": "cloud.detach_session",
                "param_map": {
                    "session_id": "$session.session_id",
                },
                "condition": has_cloud_agent,
            },
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
            return self._sync_down(app, params, state)
        if action_id == "cloud.check_session_agent":
            return self._check_session_agent(app, params, state)
        if action_id == "cloud.close_session":
            return self._close_session(app, params, state)
        if action_id == "cloud.detach_session":
            return self._detach_session(app, params)
        if action_id == "cloud.validate_cloud":
            return self._validate_cloud(app, params, state)
        if action_id == "cloud.clear_forked_session_attachment":
            return self._clear_forked_session_attachment(context)
        raise KeyError(f"Unknown cloud action {action_id!r}")

    def _start_session_agent(
        self, app: Any, params: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        orchestrator_url = self._required_config(state, "orchestrator_url")
        session_id = params["session_id"]
        loaded = app.load_session(session_id)
        if loaded is None:
            raise KeyError(f"Session {session_id!r} not found")
        self._workspace_dir(params, state)
        self._required_script_config(
            state, "local_transfer_script", legacy_key="transfer_script"
        )

        registry = self._cloud_operation_registry(app)
        operation = registry.create(session_id=session_id)
        operation_ref = str(operation["operation_ref"])
        self._save_cloud_agent_metadata(
            app,
            session_id,
            {
                "operation_ref": operation_ref,
                "orchestrator_url": orchestrator_url,
                "session_id": session_id,
                "state": "starting",
                "startup_stage": "queued",
                "operation_started_at": operation["created_at"],
            },
        )

        worker = threading.Thread(
            target=self._run_start_session_agent_operation,
            name=f"cloud-agent-start-{session_id}",
            args=(app, dict(params), dict(state), operation_ref),
            daemon=True,
        )
        worker.start()
        return self._with_session_reload(
            self._cloud_operation_result(
                orchestrator_url=orchestrator_url,
                session_id=session_id,
                operation_ref=operation_ref,
                state="starting",
                startup_stage="queued",
            ),
            session_id,
        )

    def _run_start_session_agent_operation(
        self,
        app: Any,
        params: Dict[str, Any],
        state: Dict[str, Any],
        operation_ref: str,
    ) -> None:
        session_id = str(params["session_id"])
        orchestrator_url = self._required_config(state, "orchestrator_url")
        registry = self._cloud_operation_registry(app)
        try:
            self._update_cloud_operation(
                app,
                session_id,
                operation_ref,
                state="starting",
                startup_stage="preparing_transfer",
            )
            loaded = app.load_session(session_id)
            if loaded is None:
                raise KeyError(f"Session {session_id!r} not found")
            core, _base_config, session = loaded
            metadata = session.metadata if isinstance(session.metadata, dict) else {}
            selected_agent_id = metadata.get("agent_id")
            if not isinstance(selected_agent_id, str) or not selected_agent_id.strip():
                selected_agent_id = None

            workspace_dir = self._workspace_dir(params, state)
            cloud_workspace_dir = CLOUD_WORKSPACE_DIR
            local_stage_script = state.get("local_stage_script")
            local_transfer_script = self._required_script_config(
                state, "local_transfer_script", legacy_key="transfer_script"
            )

            with tempfile.TemporaryDirectory(
                prefix="cloud-agent-transfer-"
            ) as transfer_tmp:
                transfer_dir = Path(transfer_tmp)
                self._transfer_stage_dir(transfer_dir).mkdir(
                    parents=True, exist_ok=True
                )
                transfer_env = self._script_env(
                    app=app,
                    state=state,
                    workspace_dir=workspace_dir,
                    cloud_workspace_dir=cloud_workspace_dir,
                    transfer_dir=transfer_dir,
                    session_id=session_id,
                )
                self._update_cloud_operation(
                    app,
                    session_id,
                    operation_ref,
                    state="starting",
                    startup_stage="local_stage",
                )
                self._run_script(local_stage_script, transfer_env, cwd=workspace_dir)
                self._update_cloud_operation(
                    app,
                    session_id,
                    operation_ref,
                    state="starting",
                    startup_stage="local_transfer",
                )
                self._run_script(local_transfer_script, transfer_env, cwd=workspace_dir)
                self._write_session_export(
                    transfer_dir, session_id, core.export_session(session)
                )
                self._write_runtime_config_transfer(
                    app,
                    transfer_dir,
                    state,
                    selected_agent_id=selected_agent_id,
                )
                self._write_cloud_runtime_scripts(
                    transfer_dir,
                    state,
                    workspace_dir,
                    session_id=session_id,
                )

                key_paths = self._create_transfer_keypair(transfer_dir)

                self._update_cloud_operation(
                    app,
                    session_id,
                    operation_ref,
                    state="starting",
                    startup_stage="creating_transfer",
                )
                transfer = self._post_json(
                    orchestrator_url,
                    "/transfers",
                    self._transfer_create_payload(
                        state, direction="upload", public_key=key_paths["public_key"]
                    ),
                    token=state.get("orchestrator_token"),
                )

                transfer_id = str(transfer["transfer_id"])
                self._update_cloud_operation(
                    app,
                    session_id,
                    operation_ref,
                    state="starting",
                    startup_stage="uploading_transfer",
                    transfer_id=transfer_id,
                )
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

                self._update_cloud_operation(
                    app,
                    session_id,
                    operation_ref,
                    state="starting",
                    startup_stage="creating_instance",
                    transfer_id=transfer_id,
                )
                instance = self._post_json(
                    orchestrator_url,
                    "/instances",
                    {
                        "connection_ref": {
                            "connection_key": self._connection_key(
                                app, state, workspace_dir=workspace_dir
                            ),
                            "reuse": True,
                            "metadata": {"source": "cloud-agent-app"},
                        },
                        "session_id": session_id,
                        "transfer_ref": {"transfer_id": transfer_id},
                        "runtime_image": state.get("runtime_image"),
                    },
                    token=state.get("orchestrator_token"),
                )

            if "token" not in instance and registry.get(operation_ref):
                operation = registry.get(operation_ref) or {}
                if "token" in operation:
                    instance["token"] = operation["token"]
            token = str(instance.get("token") or "")
            link = self._cloud_link(
                orchestrator_url=orchestrator_url,
                connection_id=instance.get("connection_id"),
                instance_id=str(instance["instance_id"]),
                session_id=session_id,
                token=token,
            )
            self._update_cloud_operation(
                app,
                session_id,
                operation_ref,
                state=str(instance.get("state") or "starting"),
                startup_stage=str(instance.get("startup_stage") or "instance_created"),
                instance_id=str(instance["instance_id"]),
                connection_id=instance.get("connection_id"),
                token=token,
                connection_link=link,
            )
            self._save_cloud_agent_metadata(
                app,
                session_id,
                self._cloud_agent_metadata(
                    orchestrator_url=orchestrator_url,
                    instance={**instance, "token": token},
                    session_id=session_id,
                    token=token,
                    link=link,
                    operation_ref=operation_ref,
                ),
            )

            instance = self._wait_for_instance_ready(
                orchestrator_url,
                {**instance, "token": token},
                state,
                timeout_seconds=self._startup_poll_timeout_seconds(state),
            )
            token = str(instance.get("token") or token)
            link = self._cloud_link(
                orchestrator_url=orchestrator_url,
                connection_id=instance.get("connection_id"),
                instance_id=str(instance["instance_id"]),
                session_id=session_id,
                token=token,
            )
            self._update_cloud_operation(
                app,
                session_id,
                operation_ref,
                state=str(instance.get("state") or "starting"),
                startup_stage=str(instance.get("startup_stage") or "ready"),
                instance_id=str(instance["instance_id"]),
                connection_id=instance.get("connection_id"),
                token=token,
                connection_link=link,
            )
            self._save_cloud_agent_metadata(
                app,
                session_id,
                self._cloud_agent_metadata(
                    orchestrator_url=orchestrator_url,
                    instance={**instance, "token": token},
                    session_id=session_id,
                    token=token,
                    link=link,
                    operation_ref=operation_ref,
                ),
            )
        except Exception as exc:
            _log.exception(
                "cloud_start_operation_failed",
                session_id=session_id,
                operation_ref=operation_ref,
            )
            self._update_cloud_operation(
                app,
                session_id,
                operation_ref,
                state="failed",
                startup_stage="failed",
                startup_error=exc.__class__.__name__,
                startup_error_detail=str(exc),
            )

    def _check_session_agent(
        self, app: Any, params: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        orchestrator_url = self._required_config(state, "orchestrator_url")
        session_id = str(params.get("session_id") or "")
        loaded = app.load_session(session_id) if session_id else None
        session_metadata: Dict[str, Any] = {}
        cloud_agent: Dict[str, Any] = {}
        if loaded is not None:
            _core, _base_config, session = loaded
            session_metadata = (
                session.metadata if isinstance(session.metadata, dict) else {}
            )
            cloud_agent = session_metadata.get(CLOUD_AGENT_METADATA_KEY)
            cloud_agent = cloud_agent if isinstance(cloud_agent, dict) else {}
        instance_id = str(
            params.get("instance_id") or cloud_agent.get("instance_id") or ""
        )
        if not instance_id:
            operation_ref = str(cloud_agent.get("operation_ref") or "")
            registry = self._cloud_operation_registry(app)
            operation = registry.get(operation_ref) if operation_ref else None
            result = self._cloud_operation_result(
                orchestrator_url=orchestrator_url,
                session_id=session_id,
                operation_ref=operation_ref,
                state=str(
                    (operation or {}).get("state")
                    or cloud_agent.get("state")
                    or "starting"
                ),
                startup_stage=str(
                    (operation or {}).get("startup_stage")
                    or cloud_agent.get("startup_stage")
                    or "queued"
                ),
                startup_error=(operation or {}).get("startup_error")
                or cloud_agent.get("startup_error"),
                startup_error_detail=(operation or {}).get("startup_error_detail")
                or cloud_agent.get("startup_error_detail"),
            )
            return self._with_session_reload(result, session_id)

        instance = self._get_json(
            orchestrator_url,
            f"/instances/{instance_id}",
            token=state.get("orchestrator_token"),
        )
        session_id = session_id or str(instance.get("session_id") or "")
        token = str(
            cloud_agent.get("token")
            or params.get("token")
            or instance.get("token")
            or ""
        )
        link = (
            self._cloud_link(
                orchestrator_url=orchestrator_url,
                connection_id=instance.get("connection_id"),
                instance_id=instance_id,
                session_id=session_id,
                token=token,
            )
            if session_id and token
            else None
        )
        result = self._cloud_connection_result(
            orchestrator_url=orchestrator_url,
            instance=instance,
            session_id=session_id,
            token=token,
            link=link,
        )
        if session_id:
            self._save_cloud_agent_metadata(
                app,
                session_id,
                self._cloud_agent_metadata(
                    orchestrator_url=orchestrator_url,
                    instance=instance,
                    session_id=session_id,
                    token=token,
                    link=link,
                    operation_ref=(
                        str(cloud_agent.get("operation_ref"))
                        if cloud_agent.get("operation_ref")
                        else None
                    ),
                ),
            )
        return self._with_session_reload(result, session_id)

    def _sync_down(
        self, app: Any, params: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        orchestrator_url = self._required_config(state, "orchestrator_url")
        workspace_dir = self._workspace_dir(params, state)
        cloud_workspace_dir = CLOUD_WORKSPACE_DIR
        instance_id = str(params["instance_id"])
        session_id = str(params.get("session_id") or "")
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
                self._transfer_create_payload(
                    state, direction="download", public_key=key_paths["public_key"]
                ),
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
                    self._script_env(
                        app=app,
                        state=state,
                        workspace_dir=workspace_dir,
                        cloud_workspace_dir=cloud_workspace_dir,
                        transfer_dir=transfer_dir,
                        session_id=session_id,
                    ),
                    cwd=workspace_dir,
                )
                if state.get("cloud_mark_synced_script"):
                    self._post_json(
                        orchestrator_url,
                        f"/instances/{instance_id}/sync-applied",
                        {},
                        token=state.get("orchestrator_token"),
                    )
            finally:
                self._delete_transfer(
                    orchestrator_url,
                    transfer_id,
                    token=state.get("orchestrator_token"),
                )
        if session_id:
            self._save_cloud_agent_metadata(
                app,
                session_id,
                {
                    "instance_id": instance_id,
                    "session_id": session_id,
                    "orchestrator_url": orchestrator_url,
                    "state": "running",
                    "last_synced_at": time.time(),
                },
            )
        return self._with_session_reload(
            {
                "status": "ok",
                "instance_id": instance_id,
                "export": export_result,
                "display": {
                    "format": "markdown",
                    "title": "Cloud Changes Synced",
                    "body": "Cloud workspace changes were applied locally.",
                    "variant": "success",
                },
            },
            session_id,
        )

    def _close_session(
        self, app: Any, params: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        orchestrator_url = self._required_config(state, "orchestrator_url")
        instance_id = str(params["instance_id"])
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
        if isinstance(session_id, str) and session_id:
            self._save_last_cloud_runtime_metadata(app, session_id)
            self._clear_cloud_agent_metadata(app, session_id)
        return self._with_session_reload(
            {
                "status": "ok",
                "instance_id": instance_id,
                "close": result,
                "display": {
                    "format": "markdown",
                    "title": "Cloud Agent Closed",
                    "body": "The cloud runtime was closed. Unsynced cloud changes were not copied back locally.",
                    "variant": "success",
                },
            },
            session_id if isinstance(session_id, str) else "",
        )

    def _detach_session(self, app: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        session_id = str(params["session_id"])
        self._clear_cloud_agent_metadata(app, session_id)
        return self._with_session_reload(
            {
                "status": "ok",
                "session_id": session_id,
                "display": {
                    "format": "markdown",
                    "title": "Cloud Instance Detached",
                    "body": "The local session no longer has an attached cloud instance. The remote instance was not changed.",
                    "variant": "success",
                },
            },
            session_id,
        )

    def _clear_forked_session_attachment(
        self, context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not isinstance(context, dict):
            return {}
        session_payload = context.get("session")
        if not isinstance(session_payload, dict):
            return {}
        session = Session.from_dict(session_payload)
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        if CLOUD_AGENT_METADATA_KEY not in metadata:
            return {}
        next_metadata = dict(metadata)
        next_metadata.pop(CLOUD_AGENT_METADATA_KEY, None)
        return {
            "session": Session(
                session_id=session.session_id,
                messages=session.messages,
                metadata=next_metadata,
            )
        }

    def _cloud_operation_registry(self, app: Any) -> CloudAgentOperationRegistry:
        get_runtime_store = getattr(app, "get_runtime_store", None)
        if not callable(get_runtime_store):
            return CloudAgentOperationRegistry()
        store = get_runtime_store()
        get_or_create = getattr(store, "get_or_create", None)
        if callable(get_or_create):
            return get_or_create(
                CLOUD_AGENT_OPERATION_STORE_KEY, CloudAgentOperationRegistry
            )
        existing = (
            store.get(CLOUD_AGENT_OPERATION_STORE_KEY)
            if hasattr(store, "get")
            else None
        )
        if isinstance(existing, CloudAgentOperationRegistry):
            return existing
        registry = CloudAgentOperationRegistry()
        if hasattr(store, "set"):
            store.set(CLOUD_AGENT_OPERATION_STORE_KEY, registry)
        return registry

    def _update_cloud_operation(
        self,
        app: Any,
        session_id: str,
        operation_ref: str,
        **updates: Any,
    ) -> Dict[str, Any]:
        registry = self._cloud_operation_registry(app)
        operation = registry.update(operation_ref, session_id=session_id, **updates)
        metadata_update = {
            key: value
            for key, value in operation.items()
            if key
            in {
                "operation_ref",
                "session_id",
                "state",
                "startup_stage",
                "startup_error",
                "startup_error_detail",
                "transfer_id",
                "instance_id",
                "connection_id",
                "connection_link",
            }
            and value is not None
        }
        self._save_cloud_agent_metadata(app, session_id, metadata_update)
        return operation

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

    def _validation_cache_dir(
        self, params: Dict[str, Any], *, workspace_dir: Path
    ) -> Path | None:
        raw = params.get("cache_dir")
        return self._optional_validation_path(raw, workspace_dir=workspace_dir)

    def _optional_validation_path(
        self, raw: Any, *, workspace_dir: Path
    ) -> Path | None:
        if not isinstance(raw, str) or not raw.strip():
            return None
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = workspace_dir / path
        return path.resolve()

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
            raise ValueError(
                "Only application.cloud_agent.transfer_method=managed_ssh is supported"
            )
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

    def _transfer_create_payload(
        self, state: Dict[str, Any], *, direction: str, public_key: str
    ) -> Dict[str, Any]:
        payload = {
            "direction": direction,
            "method": state.get("transfer_method", DEFAULT_TRANSFER_METHOD),
            "public_key": public_key,
        }
        public_host = state.get("transfer_public_host")
        if isinstance(public_host, str) and public_host.strip():
            payload["public_host"] = public_host
        return payload

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
        _log.info(
            "cloud_script_start",
            script=str(script),
            cwd=str(cwd),
        )
        started_at = time.monotonic()
        result = subprocess.run(
            [str(script)],
            cwd=str(cwd),
            env={**os.environ, **env},
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        duration = round(time.monotonic() - started_at, 3)
        _log.info(
            "cloud_script_complete",
            script=str(script),
            cwd=str(cwd),
            returncode=result.returncode,
            duration_seconds=duration,
            stdout_preview=(result.stdout or "")[:400],
            stderr_preview=(result.stderr or "")[:400],
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
        self,
        app: Any,
        transfer_dir: Path,
        state: Dict[str, Any],
        *,
        selected_agent_id: Optional[str] = None,
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
            selected_agent_id=(
                selected_agent_id
                if state.get("optimize_runtime_config", True) is not False
                else None
            ),
        )

    def _write_cloud_runtime_scripts(
        self,
        transfer_dir: Path,
        state: Dict[str, Any],
        workspace_dir: Path,
        *,
        session_id: str,
    ) -> None:
        scripts_dir = transfer_dir / RESERVED_CLOUD_AGENT_DIR / "scripts"
        for key, target_name in (
            ("cloud_setup_script", "setup"),
            ("install_script", "install"),
            ("validation_script", "validate"),
            ("cloud_export_script", "export"),
            ("cloud_mark_synced_script", "sync-applied"),
        ):
            raw = state.get(key)
            if not isinstance(raw, str) or not raw.strip():
                continue
            source = Path(raw).expanduser()
            if not source.is_absolute():
                source = workspace_dir / source
            if not source.is_file():
                raise FileNotFoundError(
                    f"application.cloud_agent.{key} not found: {source}"
                )
            scripts_dir.mkdir(parents=True, exist_ok=True)
            target = scripts_dir / target_name
            shutil.copy2(source, target)
            target.chmod(target.stat().st_mode | 0o700)

        runtime_env = self._cloud_runtime_script_env(
            state=state,
            workspace_dir=workspace_dir,
            transfer_dir=transfer_dir,
            session_id=session_id,
        )
        if runtime_env:
            scripts_dir.mkdir(parents=True, exist_ok=True)
            env_path = scripts_dir / "runtime.env"
            env_path.write_text(
                "".join(
                    f"{key}={value}\n" for key, value in sorted(runtime_env.items())
                ),
                encoding="utf-8",
            )
            env_path.chmod(0o600)

    def _build_validation_session(self, app: Any) -> tuple[Any, str, Session]:
        list_agents = getattr(app, "list_agents", None)
        create_session_ephemeral = getattr(app, "create_session_ephemeral", None)
        if not callable(list_agents) or not callable(create_session_ephemeral):
            raise RuntimeError("Cloud validation requires an AgentApplication instance")
        agents = list_agents()
        if not isinstance(agents, list) or not agents:
            raise RuntimeError(
                "Cloud validation requires at least one configured agent"
            )
        agent_id = str(agents[0])
        core, _base_config, session = create_session_ephemeral(agent_id)
        return core, agent_id, session

    def _validate_cloud(
        self, app: Any, params: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        if shutil.which("docker") is None:
            raise RuntimeError(
                "Docker is required for cloud validation but was not found"
            )

        workspace_dir = self._workspace_dir(params, state)
        keep_temp_dir = bool(params.get("keep_temp_dir"))
        cache_dir = self._validation_cache_dir(params, workspace_dir=workspace_dir)
        runtime_build_context = self._optional_validation_path(
            params.get("runtime_build_context"), workspace_dir=workspace_dir
        )
        runtime_dockerfile = self._optional_validation_path(
            params.get("runtime_dockerfile"), workspace_dir=workspace_dir
        )
        runtime_layout = load_runtime_layout()
        runtime_image = str(state.get("runtime_image") or "").strip()
        if not runtime_image:
            raise RuntimeError("Cloud validation requires a configured runtime image")
        local_stage_script = state.get("local_stage_script")
        local_transfer_script = self._required_script_config(
            state, "local_transfer_script", legacy_key="transfer_script"
        )

        core, selected_agent_id, validation_session = self._build_validation_session(
            app
        )
        validation_state = {
            **state,
            "validation_session_id": validation_session.session_id,
        }
        _log.info(
            "cloud_validation_start",
            workspace_dir=str(workspace_dir),
            keep_temp_dir=keep_temp_dir,
            validation_session_id=validation_session.session_id,
            selected_agent_id=selected_agent_id,
            runtime_image=runtime_image,
            cache_dir=str(cache_dir) if cache_dir is not None else None,
            runtime_build_context=(
                str(runtime_build_context)
                if runtime_build_context is not None
                else None
            ),
            runtime_dockerfile=(
                str(runtime_dockerfile) if runtime_dockerfile is not None else None
            ),
        )

        temp_root = Path(tempfile.mkdtemp(prefix="cloud-agent-validate-")).resolve()
        transfer_dir = temp_root / "transfer"
        instance_dir = temp_root / "instance"
        transfer_dir.mkdir(parents=True, exist_ok=True)
        instance_dir.mkdir(parents=True, exist_ok=True)
        port = reserve_local_port()
        container_name = (
            f"cloud-agent-validate-{int(time.time())}-{os.getpid()}".replace("_", "-")
        )
        try:
            _log.info(
                "cloud_validation_prepare_paths",
                temp_root=str(temp_root),
                transfer_dir=str(transfer_dir),
                instance_dir=str(instance_dir),
                local_runtime_port=port,
            )
            self._transfer_stage_dir(transfer_dir).mkdir(parents=True, exist_ok=True)
            if cache_dir is not None:
                cache_dir.mkdir(parents=True, exist_ok=True)
            transfer_env = self._script_env(
                app=app,
                state=validation_state,
                workspace_dir=workspace_dir,
                cloud_workspace_dir=CLOUD_WORKSPACE_DIR,
                transfer_dir=transfer_dir,
                session_id=validation_session.session_id,
            )
            _log.info("cloud_validation_stage_begin", step="local_stage")
            self._run_script(local_stage_script, transfer_env, cwd=workspace_dir)
            _log.info("cloud_validation_stage_begin", step="local_transfer")
            self._run_script(local_transfer_script, transfer_env, cwd=workspace_dir)
            _log.info("cloud_validation_stage_begin", step="session_export")
            self._write_session_export(
                transfer_dir,
                validation_session.session_id,
                core.export_session(validation_session),
            )
            _log.info("cloud_validation_stage_begin", step="runtime_config_transfer")
            self._write_runtime_config_transfer(
                app,
                transfer_dir,
                validation_state,
                selected_agent_id=selected_agent_id,
            )
            _log.info("cloud_validation_stage_begin", step="runtime_script_packaging")
            self._write_cloud_runtime_scripts(
                transfer_dir,
                validation_state,
                workspace_dir,
                session_id=validation_session.session_id,
            )

            image_details = ensure_local_runtime_image(
                runtime_image,
                runtime_layout=runtime_layout,
                build_context=runtime_build_context,
                dockerfile=runtime_dockerfile,
                logger=_log,
            )
            _log.info(
                "cloud_validation_runtime_image_ready",
                runtime_image=runtime_image,
                image_source=image_details.get("source"),
                build_context=image_details.get("build_context"),
                dockerfile=image_details.get("dockerfile"),
                digest=image_details.get("digest"),
                digest_tag=image_details.get("digest_tag"),
            )
            docker_run_command = [
                "docker",
                "run",
                "-d",
                "--name",
                container_name,
                "-p",
                f"127.0.0.1:{port}:8000",
                "-v",
                f"{transfer_dir}:/transfer",
                "-v",
                f"{instance_dir}:/cloud-agent/instance",
            ]
            if cache_dir is not None:
                docker_run_command.extend(
                    [
                        "-v",
                        f"{cache_dir}:{CLOUD_CACHE_DIR}",
                        "-e",
                        f"CLOUD_AGENT_CACHE_DIR={CLOUD_CACHE_DIR}",
                        "-e",
                        f"PIP_CACHE_DIR={CLOUD_CACHE_DIR}/pip",
                        "-e",
                        f"XDG_CACHE_HOME={CLOUD_CACHE_DIR}/xdg",
                    ]
                )
            docker_run_command.append(runtime_image)
            run_result = run_command(
                docker_run_command,
                cwd=workspace_dir,
                logger=_log,
                event_name="cloud_validation_docker_run",
            )
            if run_result.returncode != 0:
                raise RuntimeError(
                    "Failed to start local cloud validation container:\n"
                    + (run_result.stdout or "")
                )

            _log.info(
                "cloud_validation_stage_begin",
                step="runtime_readiness",
                runtime_url=f"http://127.0.0.1:{port}",
                container_name=container_name,
            )
            ready_payload = self._wait_for_local_runtime_ready(port, validation_state)
            _log.info(
                "cloud_validation_stage_begin",
                step="runtime_validate",
                runtime_url=f"http://127.0.0.1:{port}",
            )
            status, validation_payload = self._local_runtime_request(
                "POST",
                port,
                "/cloud-agent/runtime/validate",
                payload={},
            )
            if status != 200:
                raise RuntimeError(self._format_runtime_failure(validation_payload))
            _log.info(
                "cloud_validation_complete",
                workspace_dir=str(workspace_dir),
                runtime_url=f"http://127.0.0.1:{port}",
                validation_status=validation_payload.get("status"),
                validate_step=validation_payload.get("validate"),
            )

            kept_note = ""
            if keep_temp_dir:
                kept_note = f"\nArtifacts kept at `{temp_root}`."

            return {
                "status": "ok",
                "workspace_dir": str(workspace_dir),
                "artifacts_dir": str(temp_root),
                "runtime_url": f"http://127.0.0.1:{port}",
                "runtime_image": runtime_image,
                "cache_dir": str(cache_dir) if cache_dir is not None else None,
                "runtime_ready": ready_payload,
                "validation": validation_payload,
                "display": {
                    "format": "markdown",
                    "title": "Cloud Validation Passed",
                    "body": (
                        f"Cloud validation passed for `{workspace_dir}` using local Docker."
                        f"{kept_note}"
                    ),
                    "variant": "success",
                },
            }
        except Exception as exc:
            detail = str(exc)
            try:
                logs = self._docker_logs(container_name)
            except Exception:
                logs = ""
            if logs:
                detail += f"\n\nContainer logs:\n{logs}"
            raise RuntimeError(detail) from exc
        finally:
            try:
                _log.info(
                    "cloud_validation_cleanup",
                    container_name=container_name,
                    keep_temp_dir=keep_temp_dir,
                    temp_root=str(temp_root),
                )
                self._remove_container(container_name)
            except Exception:
                pass
            if not keep_temp_dir:
                shutil.rmtree(temp_root, ignore_errors=True)

    def _resolved_env(self, app: Any) -> Dict[str, str]:
        get_resolved_env = getattr(app, "get_resolved_env", None)
        if not callable(get_resolved_env):
            return {}
        resolved = get_resolved_env()
        return dict(resolved) if isinstance(resolved, dict) else {}

    def _script_env(
        self,
        *,
        app: Any,
        state: Dict[str, Any],
        workspace_dir: Path,
        cloud_workspace_dir: str,
        transfer_dir: Path,
        session_id: str,
    ) -> Dict[str, str]:
        resolved_env = self._resolved_env(app)
        ref_token = self._ref_safe_token(session_id)
        transfer_stage_dir = self._transfer_stage_dir(transfer_dir)
        branch_prefix = str(
            state.get("imported_branch_prefix") or DEFAULT_IMPORTED_BRANCH_PREFIX
        )
        return {
            **{
                key: str(value)
                for key, value in resolved_env.items()
                if isinstance(key, str) and isinstance(value, str)
            },
            "LOCAL_WORKSPACE_DIR": str(workspace_dir),
            "CLOUD_WORKSPACE_DIR": str(cloud_workspace_dir),
            "TRANSFER_DIR": str(transfer_dir),
            "TRANSFER_STAGE_DIR": str(transfer_stage_dir),
            "WORKING_DIR": str(workspace_dir),
            "SESSION_ID": session_id,
            "CLOUD_AGENT_PROFILE_ID": str(
                state.get("selected_transfer_up_profile")
                or state.get("selected_sync_down_profile")
                or ""
            ),
            "CLOUD_AGENT_TRANSFER_UP_PROFILE_ID": str(
                state.get("selected_transfer_up_profile") or ""
            ),
            "CLOUD_AGENT_SYNC_DOWN_PROFILE_ID": str(
                state.get("selected_sync_down_profile") or ""
            ),
            "CLOUD_AGENT_IMPORTED_BRANCH_NAME": f"{branch_prefix}/{ref_token}/committed",
            "CLOUD_AGENT_DELEGATED_SNAPSHOT_REF": f"refs/cloud-agent/{ref_token}/delegated-snapshot",
            "CLOUD_AGENT_CLOUD_FULL_STATE_REF": f"refs/cloud-agent/{ref_token}/cloud-full-state",
            "CLOUD_AGENT_LOCAL_IMPORT_STATE_REF": f"refs/cloud-agent/{ref_token}/local-import-state",
            "CLOUD_AGENT_LAST_SYNCED_REF": f"refs/cloud-agent/{ref_token}/last-synced",
            "CLOUD_AGENT_VALIDATION_SESSION_ID": str(
                state.get("validation_session_id") or ""
            ),
        }

    def _transfer_stage_dir(self, transfer_dir: Path) -> Path:
        return (transfer_dir / RESERVED_CLOUD_AGENT_DIR / "local-stage").resolve()

    def _cloud_runtime_script_env(
        self,
        *,
        state: Dict[str, Any],
        workspace_dir: Path,
        transfer_dir: Path,
        session_id: str,
    ) -> Dict[str, str]:
        env = self._script_env(
            app=object(),
            state=state,
            workspace_dir=workspace_dir,
            cloud_workspace_dir=CLOUD_WORKSPACE_DIR,
            transfer_dir=transfer_dir,
            session_id=session_id,
        )
        allowed = {
            "SESSION_ID",
            "CLOUD_AGENT_PROFILE_ID",
            "CLOUD_AGENT_TRANSFER_UP_PROFILE_ID",
            "CLOUD_AGENT_SYNC_DOWN_PROFILE_ID",
            "CLOUD_AGENT_VALIDATION_SESSION_ID",
            "CLOUD_AGENT_IMPORTED_BRANCH_NAME",
            "CLOUD_AGENT_DELEGATED_SNAPSHOT_REF",
            "CLOUD_AGENT_CLOUD_FULL_STATE_REF",
            "CLOUD_AGENT_LOCAL_IMPORT_STATE_REF",
            "CLOUD_AGENT_LAST_SYNCED_REF",
        }
        return {key: value for key, value in env.items() if key in allowed}

    def _ref_safe_token(self, value: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9._/-]+", "-", value.strip())
        cleaned = cleaned.strip("./")
        return cleaned or "session"

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
            raise RuntimeError(
                f"POST {path} failed with HTTP {exc.code}: {detail}"
            ) from exc
        return parsed if isinstance(parsed, dict) else {}

    def _get_json(
        self, base_url: str, path: str, *, token: Any = None
    ) -> Dict[str, Any]:
        headers = {}
        if isinstance(token, str) and token:
            headers["authorization"] = f"Bearer {token}"
        request = Request(base_url.rstrip("/") + path, headers=headers, method="GET")
        try:
            with urlopen(request, timeout=30) as response:
                parsed = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"GET {path} failed with HTTP {exc.code}: {detail}"
            ) from exc
        return parsed if isinstance(parsed, dict) else {}

    def _local_runtime_request(
        self,
        method: str,
        port: int,
        path: str,
        *,
        payload: Dict[str, Any] | None = None,
    ) -> tuple[int, Dict[str, Any]]:
        body = (
            json.dumps({k: v for k, v in payload.items() if v is not None}).encode(
                "utf-8"
            )
            if isinstance(payload, dict)
            else None
        )
        headers = {"content-type": "application/json"} if body is not None else {}
        request = Request(
            f"http://127.0.0.1:{port}{path}",
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=5) as response:
                parsed = json.loads(response.read().decode("utf-8"))
                return int(getattr(response, "status", 200)), (
                    parsed if isinstance(parsed, dict) else {}
                )
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(detail)
            except Exception:
                parsed = {"raw": detail}
            return int(exc.code), (
                parsed if isinstance(parsed, dict) else {"raw": detail}
            )

    def _format_runtime_failure(self, payload: Dict[str, Any]) -> str:
        detail = payload.get("detail")
        if isinstance(detail, dict):
            payload = detail
        if payload.get("error") == "script_failed":
            stage = payload.get("stage") or "unknown stage"
            script = payload.get("script") or "unknown script"
            returncode = payload.get("returncode")
            stderr = str(payload.get("stderr") or payload.get("stdout") or "").strip()
            return (
                f"{stage} failed with exit code {returncode} for {script}: "
                f"{stderr or 'no output'}"
            )
        startup_stage = payload.get("startup_stage")
        startup_error = payload.get("startup_error")
        startup_detail = payload.get("startup_error_detail")
        if isinstance(startup_detail, str) and startup_detail.strip():
            try:
                parsed = json.loads(startup_detail)
            except Exception:
                parsed = None
            if isinstance(parsed, dict):
                return self._format_runtime_failure(parsed)
        if startup_stage or startup_error:
            return (
                f"runtime failed during {startup_stage or 'startup'}: "
                f"{startup_detail or startup_error or payload}"
            )
        return str(payload)

    def _wait_for_local_runtime_ready(
        self,
        port: int,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        timeout = self._startup_poll_timeout_seconds(state)
        interval = self._startup_poll_interval_seconds(state)
        deadline = time.monotonic() + timeout
        last_payload: Dict[str, Any] = {}
        last_stage = None
        last_heartbeat = 0.0
        while time.monotonic() < deadline:
            try:
                status, payload = self._local_runtime_request(
                    "GET", port, "/cloud-agent/runtime/ready"
                )
            except Exception:
                time.sleep(interval)
                continue
            last_payload = payload
            stage = payload.get("startup_stage")
            if stage != last_stage:
                _log.info(
                    "cloud_validation_runtime_progress",
                    runtime_url=f"http://127.0.0.1:{port}",
                    startup_stage=stage,
                    status=payload.get("status"),
                )
                last_stage = stage
            now = time.monotonic()
            if now - last_heartbeat >= 5.0:
                _log.info(
                    "cloud_validation_runtime_waiting",
                    runtime_url=f"http://127.0.0.1:{port}",
                    startup_stage=stage,
                    status=payload.get("status"),
                    timeout_seconds=timeout,
                    seconds_remaining=max(0.0, round(deadline - now, 1)),
                )
                last_heartbeat = now
            if status == 200 and payload.get("ready") is True:
                return payload
            if (
                payload.get("status") == "failed"
                or payload.get("startup_stage") == "failed"
            ):
                raise RuntimeError(self._format_runtime_failure(payload))
            time.sleep(interval)
        raise RuntimeError(
            "Timed out waiting for local cloud runtime readiness: "
            f"{self._format_runtime_failure(last_payload) if last_payload else 'no response'}"
        )

    def _docker_logs(self, container_name: str) -> str:
        result = run_command(["docker", "logs", container_name], cwd=Path.cwd())
        return (result.stdout or "").strip()

    def _remove_container(self, container_name: str) -> None:
        run_command(["docker", "rm", "-f", container_name], cwd=Path.cwd())

    def _wait_for_instance_ready(
        self,
        orchestrator_url: str,
        instance: Dict[str, Any],
        state: Dict[str, Any],
        *,
        timeout_seconds: Optional[float] = None,
    ) -> Dict[str, Any]:
        instance_id = str(instance["instance_id"])
        timeout = (
            self._startup_poll_timeout_seconds(state)
            if timeout_seconds is None
            else max(0.0, timeout_seconds)
        )
        interval = self._startup_poll_interval_seconds(state)
        deadline = time.monotonic() + timeout
        current = instance

        while current.get("state") == "starting":
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(interval, remaining))
            current = self._get_json(
                orchestrator_url,
                f"/instances/{instance_id}",
                token=state.get("orchestrator_token"),
            )
            if "token" not in current and "token" in instance:
                current["token"] = instance["token"]

        if "token" not in current and "token" in instance:
            current["token"] = instance["token"]
        return current

    def _startup_poll_timeout_seconds(self, state: Dict[str, Any]) -> float:
        raw = state.get("startup_poll_timeout_seconds")
        if raw is None:
            raw = state.get("startup_wait_timeout_seconds")
        try:
            return max(0.0, float(raw)) if raw is not None else 90.0
        except (TypeError, ValueError):
            return 90.0

    def _start_action_timeout_seconds(self, state: Dict[str, Any]) -> float:
        raw = state.get("start_action_timeout_seconds")
        if raw is None:
            raw = state.get("startup_start_timeout_seconds")
        try:
            return (
                max(0.0, float(raw))
                if raw is not None
                else DEFAULT_START_ACTION_TIMEOUT_SECONDS
            )
        except (TypeError, ValueError):
            return DEFAULT_START_ACTION_TIMEOUT_SECONDS

    def _startup_poll_interval_seconds(self, state: Dict[str, Any]) -> float:
        raw = state.get("startup_poll_interval_seconds")
        try:
            return max(0.25, float(raw)) if raw is not None else 2.0
        except (TypeError, ValueError):
            return 2.0

    def _connection_key(
        self, app: Any, state: Dict[str, Any], *, workspace_dir: Path
    ) -> str:
        configured = state.get("connection_key")
        if isinstance(configured, str) and configured.strip():
            return configured.strip()

        get_config_path = getattr(app, "get_config_path", None)
        config_path = get_config_path() if callable(get_config_path) else ""
        material = json.dumps(
            {
                "config_path": (
                    str(Path(str(config_path)).expanduser().resolve())
                    if config_path
                    else ""
                ),
                "orchestrator_url": str(state.get("orchestrator_url") or ""),
                "workspace_dir": str(workspace_dir),
            },
            sort_keys=True,
        )
        digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]
        return f"cloud-agent-app:{digest}"

    def _cloud_agent_metadata(
        self,
        *,
        orchestrator_url: str,
        instance: Dict[str, Any],
        session_id: str,
        token: str,
        link: Optional[str],
        operation_ref: Optional[str] = None,
    ) -> Dict[str, Any]:
        instance_id = str(instance["instance_id"])
        connection_id = instance.get("connection_id")
        metadata: Dict[str, Any] = {
            "orchestrator_url": orchestrator_url.rstrip("/"),
            "instance_id": instance_id,
            "session_id": session_id,
            "state": str(instance.get("state") or "starting"),
            "status_url": f"{orchestrator_url.rstrip('/')}/instances/{instance_id}",
        }
        if isinstance(connection_id, str) and connection_id:
            metadata["connection_id"] = connection_id
        if token:
            metadata["token"] = token
        if link:
            metadata["connection_link"] = link
        if operation_ref:
            metadata["operation_ref"] = operation_ref
        for key in (
            "startup_stage",
            "startup_error",
            "startup_error_detail",
            "created_at",
            "updated_at",
        ):
            if key in instance:
                metadata[key] = instance[key]
        return metadata

    def _save_cloud_agent_metadata(
        self, app: Any, session_id: str, cloud_agent: Dict[str, Any]
    ) -> None:
        if not session_id:
            return
        loaded = app.load_session(session_id)
        if loaded is None:
            return
        _core, _base_config, session = loaded
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        existing = metadata.get(CLOUD_AGENT_METADATA_KEY)
        existing = existing if isinstance(existing, dict) else {}
        now = time.time()
        next_cloud_agent = {
            **existing,
            **cloud_agent,
            "started_at": existing.get("started_at") or now,
            "updated_at": now,
        }
        self._save_session_metadata(
            app,
            session,
            {**metadata, CLOUD_AGENT_METADATA_KEY: next_cloud_agent},
        )

    def _clear_cloud_agent_metadata(self, app: Any, session_id: str) -> None:
        if not session_id:
            return
        loaded = app.load_session(session_id)
        if loaded is None:
            return
        _core, _base_config, session = loaded
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        if CLOUD_AGENT_METADATA_KEY not in metadata:
            return
        next_metadata = dict(metadata)
        next_metadata.pop(CLOUD_AGENT_METADATA_KEY, None)
        self._save_session_metadata(app, session, next_metadata)

    def _save_last_cloud_runtime_metadata(self, app: Any, session_id: str) -> None:
        if not session_id:
            return
        loaded = app.load_session(session_id)
        if loaded is None:
            return
        _core, _base_config, session = loaded
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        next_metadata = dict(metadata)
        next_metadata[CLOUD_AGENT_LAST_RUNTIME_KEY] = {
            "was_cloud": True,
            "current_workdir": CLOUD_WORKSPACE_DIR,
            "closed_at": time.time(),
        }
        self._save_session_metadata(app, session, next_metadata)

    def _save_session_metadata(
        self, app: Any, session: Any, metadata: Dict[str, Any]
    ) -> None:
        app.save_session(
            session.__class__(
                session_id=session.session_id,
                messages=session.messages,
                metadata=metadata,
            )
        )

    def _with_session_reload(
        self, result: Dict[str, Any], session_id: str
    ) -> Dict[str, Any]:
        if not session_id:
            return result

        next_result = dict(result)
        mutations = (
            dict(next_result.get("mutations"))
            if isinstance(next_result.get("mutations"), dict)
            else {}
        )
        updated_ids = [
            item
            for item in mutations.get("updated_session_ids", [])
            if isinstance(item, str)
        ]
        if session_id not in updated_ids:
            updated_ids.append(session_id)
        mutations.setdefault("created_session_ids", [])
        mutations["updated_session_ids"] = updated_ids
        mutations.setdefault("deleted_session_ids", [])
        next_result["mutations"] = mutations

        ui_effects = (
            dict(next_result.get("ui_effects"))
            if isinstance(next_result.get("ui_effects"), dict)
            else {}
        )
        reload_ids = [
            item
            for item in ui_effects.get("reload_session_ids", [])
            if isinstance(item, str)
        ]
        if session_id not in reload_ids:
            reload_ids.append(session_id)
        ui_effects["reload_session_ids"] = reload_ids
        next_result["ui_effects"] = ui_effects
        return next_result

    def _cloud_operation_result(
        self,
        *,
        orchestrator_url: str,
        session_id: str,
        operation_ref: str,
        state: str,
        startup_stage: str,
        startup_error: Any = None,
        startup_error_detail: Any = None,
    ) -> Dict[str, Any]:
        if state == "failed":
            title = "Cloud Agent Startup Failed"
            variant = "error"
            body = self._failure_body(
                startup_stage, startup_error, startup_error_detail
            )
        else:
            title = "Cloud Agent Starting"
            variant = "warning"
            body = (
                f"The cloud startup operation is in progress. Current stage: "
                f"`{startup_stage or 'queued'}`."
            )
        if operation_ref:
            body += f"\n\nOperation ref: `{operation_ref}`."

        return {
            "status": "ok",
            "state": state,
            "session_id": session_id,
            "operation_ref": operation_ref,
            "display": {
                "format": "markdown",
                "title": title,
                "body": body,
                "variant": variant,
                "actions": [
                    {
                        "kind": "run_action",
                        "id": "refresh-cloud-agent-status",
                        "label": "Refresh status",
                        "plugin": "cloud",
                        "action_id": "cloud.check_session_agent",
                        "action_owner": "application",
                        "fixed_params": {
                            "session_id": session_id,
                        },
                    }
                ],
            },
        }

    def _cloud_connection_result(
        self,
        *,
        orchestrator_url: str,
        instance: Dict[str, Any],
        session_id: str,
        token: str,
        link: Optional[str],
    ) -> Dict[str, Any]:
        state = str(instance.get("state") or "starting")
        connection_id = instance.get("connection_id")
        status_url = (
            f"{orchestrator_url.rstrip('/')}/instances/{instance['instance_id']}"
        )
        startup_stage = instance.get("startup_stage")
        startup_error = instance.get("startup_error")
        startup_detail = instance.get("startup_error_detail")

        if state == "running":
            title = "Cloud Agent Ready"
            variant = "success"
            body = f"The cloud session is ready.\n\nInstance ID: `{instance['instance_id']}`."
        elif state == "failed":
            title = "Cloud Agent Startup Failed"
            variant = "error"
            body = self._failure_body(startup_stage, startup_error, startup_detail)
            body += f"\n\nInstance ID: `{instance['instance_id']}`."
        else:
            title = "Cloud Agent Starting"
            variant = "warning"
            body = (
                f"The cloud runtime is starting. Current stage: "
                f"`{startup_stage or 'starting'}`.\n\n"
                f"Instance ID: `{instance['instance_id']}`."
            )

        actions: List[Dict[str, Any]] = []
        if link:
            actions.append(
                {
                    "kind": "copy_text",
                    "id": "copy-cloud-connection-link",
                    "label": "Copy connection link",
                    "text": link,
                }
            )
        actions.append(
            {
                "kind": "open_url",
                "id": "open-cloud-agent-status",
                "label": "Open status",
                "url": status_url,
            }
        )
        actions.append(
            {
                "kind": "run_action",
                "id": "refresh-cloud-agent-status",
                "label": "Refresh status",
                "plugin": "cloud",
                "action_id": "cloud.check_session_agent",
                "action_owner": "application",
                "fixed_params": {
                    "session_id": session_id,
                },
            }
        )
        if state == "running":
            actions.extend(
                [
                    {
                        "kind": "run_action",
                        "id": "sync-cloud-changes",
                        "label": "Sync cloud changes",
                        "plugin": "cloud",
                        "action_id": "cloud.sync_down",
                        "action_owner": "application",
                        "fixed_params": {
                            "instance_id": instance["instance_id"],
                            "session_id": session_id,
                        },
                    },
                    {
                        "kind": "run_action",
                        "id": "close-cloud-agent",
                        "label": "Close cloud agent",
                        "plugin": "cloud",
                        "action_id": "cloud.close_session",
                        "action_owner": "application",
                        "fixed_params": {
                            "instance_id": instance["instance_id"],
                            "session_id": session_id,
                        },
                    },
                ]
            )

        result: Dict[str, Any] = {
            "state": state,
            "instance_state": state,
            "instance": instance,
            "instance_id": instance["instance_id"],
            "session_id": session_id,
            "connection_link": link,
            "status_url": status_url,
            "display": {
                "format": "markdown",
                "title": title,
                "body": body,
                "variant": variant,
                "actions": actions,
            },
        }
        if isinstance(connection_id, str) and connection_id:
            result["connection_id"] = connection_id
        return result

    def _failure_body(
        self, startup_stage: Any, startup_error: Any, startup_detail: Any
    ) -> str:
        lines = [
            f"Startup stage: `{startup_stage or 'failed'}`.",
            f"Error: `{startup_error or 'runtime_startup_failed'}`.",
        ]
        if isinstance(startup_detail, str) and startup_detail.strip():
            detail = startup_detail.strip()
            if len(detail) > 4000:
                detail = detail[-4000:]
            lines.extend(["", "```text", detail, "```"])
        return "\n".join(lines)

    def _delete_transfer(
        self, base_url: str, transfer_id: str, *, token: Any = None
    ) -> None:
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
        self,
        *,
        orchestrator_url: str,
        instance_id: str,
        session_id: str,
        token: str,
        connection_id: Any = None,
    ) -> str:
        params = {
            "orchestrator": orchestrator_url,
            "instance_id": instance_id,
            "session_id": session_id,
            "token": token,
        }
        if isinstance(connection_id, str) and connection_id:
            params["connection_id"] = connection_id
        return "crystal-lattice-cloud://connect?" + urlencode(params)


__all__ = ["CloudAgentAppPlugin"]
