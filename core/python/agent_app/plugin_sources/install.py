from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Protocol

import json
import shutil
import subprocess
import sys


class PluginInstallError(Exception):
    def __init__(self, *, detail: str, path: str) -> None:
        super().__init__(detail)
        self.detail = detail
        self.path = path


@dataclass(frozen=True)
class InstallRequest:
    cache_dir: Path
    safe_id: str
    revision: str
    project_dir: Path
    policy: Mapping[str, Any]
    metadata: Dict[str, Any]


class InstallStrategy(Protocol):
    def ensure_installed(self, request: InstallRequest) -> Path:
        """Ensure the project is installed into the cache and importable."""


class PipTargetInstallStrategy:
    """Install an on-disk project into a cache dir via `pip install --target`.

    This strategy owns:
    - Cache directory naming and atomic temp-dir swap
    - pip invocation (`pip_args`, `install_deps: false` -> `--no-deps`)
    - Writing `plugin_metadata.json`
    - `sys.path` activation (core-first append)
    """

    def ensure_installed(self, request: InstallRequest) -> Path:  # type: ignore[override]
        cache_dir = request.cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)

        install_dir = cache_dir / f"{request.safe_id}@{request.revision}"
        if install_dir.exists():
            self._activate_sys_path(install_dir)
            return install_dir

        temp_dir = cache_dir / f".{request.safe_id}@{request.revision}.tmp"
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True, exist_ok=True)

        pip_args: List[str] = list(request.policy.get("pip_args") or [])
        install_deps = bool(request.policy.get("install_deps", True))

        cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--target",
            str(temp_dir),
            *([] if install_deps else ["--no-deps"]),
            str(request.project_dir),
            *pip_args,
        ]

        try:
            subprocess.check_call(cmd)
            meta = dict(request.metadata)
            meta.setdefault("id", request.safe_id)
            meta.setdefault("installed_at", datetime.utcnow().isoformat() + "Z")
            (temp_dir / "plugin_metadata.json").write_text(json.dumps(meta), encoding="utf-8")
            temp_dir.replace(install_dir)
        except Exception as exc:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise PluginInstallError(detail=f"pip install failed: {exc}", path=str(request.project_dir))

        self._activate_sys_path(install_dir)
        return install_dir

    def _activate_sys_path(self, install_dir: Path) -> None:
        value = str(install_dir)
        if value not in sys.path:
            sys.path.append(value)
