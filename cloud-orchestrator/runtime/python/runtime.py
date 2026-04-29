from __future__ import annotations

import json
import os
import shutil
import tarfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Response


app = FastAPI(title="Cloud Agent Runtime")


def workspace_dir() -> Path:
    return Path(os.environ.get("CLOUD_WORKSPACE_DIR", "/workspace"))


def transfer_dir() -> Path:
    return Path(os.environ.get("TRANSFER_DIR", "/transfer"))


def session_dir() -> Path:
    return Path(os.environ.get("SESSION_DIR", "/sessions"))


def _safe_extract_tar(tar: tarfile.TarFile, target: Path) -> None:
    target_resolved = target.resolve()
    for member in tar.getmembers():
        member_target = (target / member.name).resolve()
        if target_resolved not in [member_target, *member_target.parents]:
            raise RuntimeError(f"unsafe tar path: {member.name}")
    tar.extractall(target)


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


def _bootstrap_from_transfer() -> None:
    marker = workspace_dir() / ".cloud-agent-runtime-ready"
    if marker.exists():
        return

    workspace_dir().mkdir(parents=True, exist_ok=True)
    session_dir().mkdir(parents=True, exist_ok=True)
    unpacked = Path("/tmp/cloud-agent-transfer")
    if unpacked.exists():
        shutil.rmtree(unpacked)
    unpacked.mkdir(parents=True, exist_ok=True)

    bundle = transfer_dir() / "bundle.tar.gz"
    if bundle.exists():
        with tarfile.open(bundle, "r:gz") as tar:
            _safe_extract_tar(tar, unpacked)
    elif transfer_dir().exists():
        _copytree_contents(transfer_dir(), unpacked)

    _copytree_contents(unpacked / "workspace", workspace_dir())

    transferred_sessions = unpacked / ".cloud-agent" / "sessions"
    if transferred_sessions.exists():
        for path in transferred_sessions.glob("*.json"):
            shutil.copy2(path, session_dir() / path.name)

    setup_script = unpacked / ".cloud-agent" / "setup-cloud"
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


def _session_path(session_id: str) -> Path:
    if "/" in session_id or "\\" in session_id or session_id in {"", ".", ".."}:
        raise HTTPException(status_code=400, detail="invalid session id")
    return session_dir() / f"{session_id}.json"


def _load_session(session_id: str) -> Dict[str, Any]:
    path = _session_path(session_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="session not found")
    return json.loads(path.read_text(encoding="utf-8"))


def _save_session(session: Dict[str, Any]) -> None:
    session_id = str(session.get("session_id") or "")
    path = _session_path(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(session, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "healthy", "service": "cloud-agent-runtime"}


@app.get("/api/data")
def api_data() -> Dict[str, Any]:
    return {"message": "Cloud agent runtime", "status": "connected"}


@app.get("/api/hello")
def api_hello() -> Dict[str, Any]:
    return {"message": "Hello from cloud agent runtime"}


@app.get("/sessions")
def list_sessions(limit: Optional[int] = None) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []
    for path in sorted(session_dir().glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        raw = json.loads(path.read_text(encoding="utf-8"))
        preview = ""
        for msg in raw.get("messages") or []:
            if msg.get("role") == "user":
                preview = " ".join(str(msg.get("content") or "").split())[:80]
                break
        items.append(
            {
                "session_id": raw.get("session_id") or path.stem,
                "modified": path.stat().st_mtime,
                "preview": preview,
                "metadata": raw.get("metadata") or {},
                "pinned": False,
            }
        )
    return {"sessions": items[:limit] if isinstance(limit, int) and limit >= 0 else items}


@app.get("/sessions/{session_id}/messages")
def list_messages(session_id: str, start: Optional[int] = None, end: Optional[int] = None) -> Dict[str, Any]:
    session = _load_session(session_id)
    messages = session.get("messages") or []
    selected = messages[slice(start, end)]
    offset = start or 0
    return {
        "messages": [
            {"index": offset + idx, "message": msg}
            for idx, msg in enumerate(selected)
        ],
        "cursor_event_id": None,
        "active_request_id": None,
        "readonly": False,
        "snapshot_id": None,
    }


@app.post("/sessions/{session_id}/messages")
def append_message(session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    session = _load_session(session_id)
    messages = list(session.get("messages") or [])
    messages.append(
        {
            "role": payload.get("role", "user"),
            "content": payload.get("content", ""),
            "metadata": payload.get("metadata") or {},
        }
    )
    session["messages"] = messages
    _save_session(session)
    return {"session": session}


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


@app.get("/cloud-agent/sessions/{session_id}/export")
def export_session(session_id: str) -> Response:
    return Response(
        content=_session_path(session_id).read_text(encoding="utf-8"),
        media_type="application/json",
    )