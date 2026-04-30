from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict

from fastapi import HTTPException, Response

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_app.sessions import FilesystemSnapshotSelectionStore
from agent_terminal_app import server as server_mod


app = server_mod.app


def instance_dir() -> Path:
    return Path(os.environ.get("CLOUD_AGENT_INSTANCE_DIR", "/cloud-agent/instance"))


def workspace_dir() -> Path:
    return Path(
        os.environ.get("CLOUD_AGENT_WORKSPACE_DIR")
        or os.environ.get("CLOUD_WORKSPACE_DIR")
        or instance_dir() / "workspace"
    )


def sessions_dir() -> Path:
    return Path(
        os.environ.get("CLOUD_AGENT_SESSIONS_DIR")
        or os.environ.get("SESSION_DIR")
        or instance_dir() / "sessions"
    )


def config_path() -> Path:
    return Path(
        os.environ.get("CLOUD_AGENT_CONFIG_PATH")
        or instance_dir() / "config" / "config.json"
    )


def config_assets_dir() -> Path:
    return Path(os.environ.get("CONFIG_DIR") or instance_dir() / "config" / "assets")


def transfer_dir() -> Path:
    return Path(os.environ.get("TRANSFER_DIR", "/transfer"))


def scripts_dir() -> Path:
    return instance_dir() / "scripts"


def export_transfer_dir() -> Path:
    return instance_dir() / "transfer" / "export"


def _copytree_contents(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.mkdir(parents=True, exist_ok=True)
    for child in src.iterdir():
        target = dst / child.name
        if child.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(child, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(child, target)


def _load_dotenv_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] == '"':
            value = bytes(value[1:-1], "utf-8").decode("unicode_escape")
        os.environ[key] = value


def _load_runtime_env(root: Path) -> None:
    env_root = root / "env"
    _load_dotenv_file(env_root / "runtime.env")
    env_dir = env_root / "runtime.env.d"
    if env_dir.is_dir():
        for path in sorted(env_dir.glob("*.env")):
            _load_dotenv_file(path)


def _install_canonical_env() -> None:
    os.environ["CLOUD_AGENT_INSTANCE_DIR"] = str(instance_dir())
    os.environ["CLOUD_AGENT_WORKSPACE_DIR"] = str(workspace_dir())
    os.environ["CLOUD_AGENT_SESSIONS_DIR"] = str(sessions_dir())
    os.environ["CLOUD_AGENT_CONFIG_PATH"] = str(config_path())
    os.environ["CONFIG_DIR"] = str(config_assets_dir())
    os.environ["WORKING_DIR"] = str(workspace_dir())
    os.environ.setdefault("CLOUD_WORKSPACE_DIR", str(workspace_dir()))
    os.environ.setdefault("SESSION_DIR", str(sessions_dir()))


def _copy_workspace_from_transfer(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.mkdir(parents=True, exist_ok=True)
    for child in src.iterdir():
        if child.name == ".cloud-agent":
            continue
        target = dst / child.name
        if child.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(child, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(child, target)


def _bootstrap_from_transfer() -> None:
    state_dir = instance_dir() / "state"
    marker = state_dir / ".cloud-agent-runtime-ready"
    state_dir.mkdir(parents=True, exist_ok=True)
    workspace_dir().mkdir(parents=True, exist_ok=True)
    sessions_dir().mkdir(parents=True, exist_ok=True)
    config_path().parent.mkdir(parents=True, exist_ok=True)
    config_assets_dir().mkdir(parents=True, exist_ok=True)

    if marker.exists():
        _load_runtime_env(instance_dir())
        _install_canonical_env()
        return

    unpacked = transfer_dir()
    _copy_workspace_from_transfer(unpacked, workspace_dir())

    cloud_root = unpacked / ".cloud-agent"
    transferred_sessions = cloud_root / "sessions"
    if transferred_sessions.exists():
        _copytree_contents(transferred_sessions, sessions_dir())

    transferred_config = cloud_root / "config" / "config.json"
    if transferred_config.exists():
        shutil.copy2(transferred_config, config_path())
    transferred_assets = cloud_root / "config" / "assets"
    if transferred_assets.exists():
        _copytree_contents(transferred_assets, config_assets_dir())
    transferred_env = cloud_root / "env"
    if transferred_env.exists():
        _copytree_contents(transferred_env, instance_dir() / "env")
    transferred_scripts = cloud_root / "scripts"
    if transferred_scripts.exists():
        _copytree_contents(transferred_scripts, scripts_dir())

    _load_runtime_env(instance_dir())
    _install_canonical_env()

    setup_script = scripts_dir() / "setup"
    if setup_script.exists():
        import subprocess

        subprocess.run(
            [str(setup_script)],
            cwd=str(workspace_dir()),
            env={
                **os.environ,
                "CLOUD_WORKSPACE_DIR": str(workspace_dir()),
                "TRANSFER_DIR": str(unpacked),
            },
            check=True,
        )

    marker.write_text(str(time.time()), encoding="utf-8")


@app.on_event("startup")
def startup() -> None:
    _bootstrap_from_transfer()
    server_mod._agent_app = AgentApplication(
        str(config_path()),
        str(sessions_dir()),
        event_store=InMemoryEventStore(),
        snapshot_selection_store=FilesystemSnapshotSelectionStore(
            sessions_dir() / ".snapshots"
        ),
        env_overrides={
            "CONFIG_DIR": str(config_assets_dir()),
            "WORKING_DIR": str(workspace_dir()),
            "BUILTIN_PLUGINS": os.environ.get(
                "BUILTIN_PLUGINS", "/opt/ai-agent-platform/plugins"
            ),
        },
    )


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "cloud-agent-runtime",
        "agent_application": server_mod._agent_app is not None,
    }


@app.post("/cloud-agent/workspace/files")
def write_workspace_file(payload: Dict[str, Any]) -> Dict[str, Any]:
    rel = str(payload.get("path") or "")
    if rel.startswith("/") or ".." in Path(rel).parts:
        raise HTTPException(status_code=400, detail="invalid path")
    target = workspace_dir() / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(str(payload.get("content") or ""), encoding="utf-8")
    return {"path": rel}


@app.get("/cloud-agent/workspace/files/{file_path:path}")
def read_workspace_file(file_path: str) -> Dict[str, Any]:
    if file_path.startswith("/") or ".." in Path(file_path).parts:
        raise HTTPException(status_code=400, detail="invalid path")
    target = workspace_dir() / file_path
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="file not found")
    return {"path": file_path, "content": target.read_text(encoding="utf-8")}


@app.get("/cloud-agent/config-assets/files/{file_path:path}")
def read_config_asset(file_path: str) -> Dict[str, Any]:
    if file_path.startswith("/") or ".." in Path(file_path).parts:
        raise HTTPException(status_code=400, detail="invalid path")
    target = config_assets_dir() / file_path
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="file not found")
    return {"path": file_path, "content": target.read_text(encoding="utf-8")}


@app.get("/cloud-agent/sessions/{session_id}/export")
def export_session(session_id: str) -> Response:
    if "/" in session_id or "\\" in session_id or session_id in {"", ".", ".."}:
        raise HTTPException(status_code=400, detail="invalid session id")
    path = sessions_dir() / f"{session_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="session not found")
    return Response(
        content=path.read_text(encoding="utf-8"), media_type="application/json"
    )


@app.post("/cloud-agent/runtime/export")
def export_runtime_workspace() -> Dict[str, Any]:
    export_dir = export_transfer_dir()
    if export_dir.exists():
        shutil.rmtree(export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)

    export_script = scripts_dir() / "export"
    if not export_script.exists():
        raise HTTPException(status_code=409, detail="cloud export script is not configured")

    import subprocess

    subprocess.run(
        [str(export_script)],
        cwd=str(workspace_dir()),
        env={
            **os.environ,
            "CLOUD_WORKSPACE_DIR": str(workspace_dir()),
            "TRANSFER_DIR": str(export_dir),
        },
        check=True,
    )
    return {"status": "ok", "transfer_dir": str(export_dir)}


@app.get("/cloud-agent/runtime/manifest")
def runtime_manifest() -> Dict[str, Any]:
    path = instance_dir() / "transfer" / ".cloud-agent" / "manifest.json"
    fallback = transfer_dir() / ".cloud-agent" / "manifest.json"
    for candidate in (path, fallback):
        if candidate.exists():
            return json.loads(candidate.read_text(encoding="utf-8"))
    return {}
