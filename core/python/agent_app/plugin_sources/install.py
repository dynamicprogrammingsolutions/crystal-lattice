from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Mapping, Protocol

import fcntl
import json
import os
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
        bundled_install_dir = self._maybe_activate_bundled_source(request)
        if bundled_install_dir is not None:
            return bundled_install_dir

        cache_dir = request.cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)

        install_dir = cache_dir / f"{request.safe_id}@{request.revision}"
        if install_dir.exists():
            self._activate_sys_path(install_dir)
            return install_dir

        with self._install_lock(cache_dir, request.safe_id, request.revision):
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
                (temp_dir / "plugin_metadata.json").write_text(
                    json.dumps(meta), encoding="utf-8"
                )
                temp_dir.replace(install_dir)
            except Exception as exc:
                shutil.rmtree(temp_dir, ignore_errors=True)
                raise PluginInstallError(
                    detail=f"pip install failed: {exc}", path=str(request.project_dir)
                )

        self._activate_sys_path(install_dir)
        return install_dir

    @contextmanager
    def _install_lock(
        self, cache_dir: Path, safe_id: str, revision: str
    ) -> Iterator[None]:
        lock_dir = cache_dir / ".locks"
        lock_dir.mkdir(parents=True, exist_ok=True)
        lock_path = lock_dir / f"{safe_id}@{revision}.lock"
        with lock_path.open("w", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def _activate_sys_path(self, install_dir: Path) -> None:
        value = str(install_dir)
        if value not in sys.path:
            sys.path.append(value)

    def _maybe_activate_bundled_source(self, request: InstallRequest) -> Path | None:
        root_raw = request.policy.get("bundled_plugin_root") or os.environ.get(
            "CRYSTAL_BUNDLED_PLUGIN_ROOT"
        )
        if not isinstance(root_raw, str) or not root_raw.strip():
            return None

        root = Path(root_raw).expanduser().resolve()
        project_dir = request.project_dir.resolve()
        try:
            project_dir.relative_to(root)
        except ValueError:
            return None

        self._activate_bundled_source_tree(root)
        return project_dir

    def _activate_bundled_source_tree(self, root: Path) -> None:
        if not root.is_dir():
            return
        for project in sorted(root.iterdir()):
            if not project.is_dir():
                continue
            src_dir = project / "src"
            if src_dir.is_dir():
                self._activate_sys_path(src_dir)
            elif (project / "pyproject.toml").is_file() or (project / "setup.py").is_file():
                self._activate_sys_path(project)
