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
import importlib


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
    - `sys.path` activation (latest installed plugin takes precedence)
    """

    def ensure_installed(self, request: InstallRequest) -> Path:  # type: ignore[override]
        bundled_install_dir = self._maybe_activate_bundled_source(request)
        if bundled_install_dir is not None:
            return bundled_install_dir

        cache_dir = request.cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)

        install_dir = cache_dir / f"{request.safe_id}@{request.revision}"
        if install_dir.exists() and self._install_dir_matches_request(install_dir, request):
            self._activate_sys_path(install_dir)
            return install_dir

        with self._install_lock(cache_dir, request.safe_id, request.revision):
            if install_dir.exists() and self._install_dir_matches_request(install_dir, request):
                self._activate_sys_path(install_dir)
                return install_dir
            if install_dir.exists():
                shutil.rmtree(install_dir, ignore_errors=True)

            temp_dir = cache_dir / f".{request.safe_id}@{request.revision}.tmp"
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            temp_dir.mkdir(parents=True, exist_ok=True)

            pip_args: List[str] = list(request.policy.get("pip_args") or [])
            install_deps = bool(request.policy.get("install_deps", True))
            cache_args = self._pip_cache_args(request, pip_args)

            cmd = [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "--target",
                str(temp_dir),
                *cache_args,
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
                raise PluginInstallError(
                    detail=f"pip install failed: {exc}", path=str(request.project_dir)
                )

        self._activate_sys_path(install_dir)
        return install_dir

    @contextmanager
    def _install_lock(self, cache_dir: Path, safe_id: str, revision: str) -> Iterator[None]:
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
        try:
            sys.path.remove(value)
        except ValueError:
            pass
        sys.path.insert(0, value)
        self._evict_stale_modules(install_dir)
        importlib.invalidate_caches()

    def _evict_stale_modules(self, install_dir: Path) -> None:
        top_levels = self._top_level_modules_for_install_dir(install_dir)
        if not top_levels:
            return
        install_dir_resolved = install_dir.resolve()
        prefixes = tuple(f"{name}." for name in top_levels)
        to_remove: list[str] = []
        for module_name, module in list(sys.modules.items()):
            if not (
                module_name in top_levels
                or any(module_name.startswith(prefix) for prefix in prefixes)
            ):
                continue
            module_file = getattr(module, "__file__", None)
            if not isinstance(module_file, str) or not module_file:
                to_remove.append(module_name)
                continue
            try:
                module_path = Path(module_file).resolve()
            except Exception:
                to_remove.append(module_name)
                continue
            try:
                module_path.relative_to(install_dir_resolved)
            except ValueError:
                to_remove.append(module_name)
        for module_name in to_remove:
            sys.modules.pop(module_name, None)

    def _top_level_modules_for_install_dir(self, install_dir: Path) -> set[str]:
        discovered: set[str] = set()
        for top_level_file in install_dir.glob("*.dist-info/top_level.txt"):
            try:
                text = top_level_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for line in text.splitlines():
                name = line.strip()
                if name and name.isidentifier():
                    discovered.add(name)
        if discovered:
            return discovered
        for child in install_dir.iterdir():
            name = child.name
            if child.is_dir():
                if name.endswith((".dist-info", ".data")):
                    continue
                if name.isidentifier():
                    discovered.add(name)
                continue
            if child.is_file() and child.suffix == ".py":
                stem = child.stem
                if stem.isidentifier():
                    discovered.add(stem)
        return discovered

    def _pip_cache_args(self, request: InstallRequest, pip_args: List[str]) -> List[str]:
        if "--no-cache-dir" in pip_args:
            return []
        if any(arg == "--cache-dir" or arg.startswith("--cache-dir=") for arg in pip_args):
            return []

        raw_cache_dir = request.policy.get("pip_cache_dir")
        if not isinstance(raw_cache_dir, str) or not raw_cache_dir.strip():
            return []

        cache_dir = Path(os.path.expanduser(raw_cache_dir))
        if not cache_dir.is_absolute():
            cache_dir = request.cache_dir / cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)
        return ["--cache-dir", str(cache_dir)]

    def _maybe_activate_bundled_source(self, request: InstallRequest) -> Path | None:
        root_raw = request.policy.get("bundled_plugin_root") or os.environ.get("BUILTIN_PLUGINS")
        if not isinstance(root_raw, str) or not root_raw.strip():
            return None

        root = Path(root_raw).expanduser().resolve()
        if root.name != "bundled_plugins":
            return None
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

    def _install_dir_matches_request(
        self,
        install_dir: Path,
        request: InstallRequest,
    ) -> bool:
        metadata_path = install_dir / "plugin_metadata.json"
        if not metadata_path.is_file():
            return False
        try:
            installed = json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception:
            return False
        if not isinstance(installed, dict):
            return False
        for key, value in request.metadata.items():
            if installed.get(key) != value:
                return False
        requested_dep_versions = request.metadata.get("local_dependency_versions")
        if isinstance(requested_dep_versions, dict):
            installed_dep_versions = self._installed_distribution_versions(install_dir)
            for raw_name, raw_version in requested_dep_versions.items():
                if not isinstance(raw_name, str) or not isinstance(raw_version, str):
                    return False
                if installed_dep_versions.get(self._normalize_distribution_name(raw_name)) != raw_version:
                    return False
        return True

    def _installed_distribution_versions(self, install_dir: Path) -> Dict[str, str]:
        versions: Dict[str, str] = {}
        for dist_dir in install_dir.glob("*.dist-info"):
            metadata_path = dist_dir / "METADATA"
            if not metadata_path.is_file():
                continue
            name: str | None = None
            version: str | None = None
            try:
                lines = metadata_path.read_text(encoding="utf-8", errors="ignore").splitlines()
            except Exception:
                continue
            for line in lines:
                if line.startswith("Name: "):
                    name = line[6:].strip()
                elif line.startswith("Version: "):
                    version = line[9:].strip()
                if name and version:
                    break
            if name and version:
                versions[self._normalize_distribution_name(name)] = version
        return versions

    def _normalize_distribution_name(self, name: str) -> str:
        normalized = []
        previous_sep = False
        for ch in name.lower():
            if ch.isalnum():
                normalized.append(ch)
                previous_sep = False
            else:
                if not previous_sep:
                    normalized.append("-")
                    previous_sep = True
        return "".join(normalized).strip("-")
