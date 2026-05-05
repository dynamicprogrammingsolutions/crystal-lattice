from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

import hashlib
import os
import subprocess

from agent_core.utils import get_logger

from .descriptor import read_descriptor
from .importing import import_dotted_class
from .install import InstallRequest, InstallStrategy, PipTargetInstallStrategy, PluginInstallError
from .types import PluginContext, PluginResolution


class LocalPathRepoSource:
    """Resolve local plugin repositories.

    Supported specs:
      - Descriptor-driven (recommended): "path:/abs/or/rel"
      - Explicit entry: {"path": "/abs/or/rel", "entry": "pkg.module.Class", "subdirectory": "optional"}
      - Explicit descriptor-driven: {"path": "/abs/or/rel"} (requires agent_plugin.json)
    """

    def __init__(self, *, installer: InstallStrategy | None = None) -> None:
        self._installer = installer or PipTargetInstallStrategy()

    def supports(self, spec: Any) -> bool:
        if isinstance(spec, str):
            return spec.strip().startswith("path:")
        if isinstance(spec, dict):
            return isinstance(spec.get("path"), str)
        return False

    def resolve(self, spec: Any, ctx: PluginContext) -> PluginResolution:
        logger = get_logger("PluginManager")

        parsed_path: Optional[str]
        explicit_entry: Optional[str] = None
        explicit_subdir: Optional[str] = None

        if isinstance(spec, str):
            if "::" in spec:
                return PluginResolution(classes=[], errors=[{
                    "type": "plugin_path_invalid",
                    "detail": "Local path specs no longer support '::' forms; use a dict with 'entry'",
                    "path": spec,
                }])
            parsed_path = spec.split(":", 1)[1]
        elif isinstance(spec, dict):
            parsed_path = spec.get("path")
            if isinstance(spec.get("entry"), str):
                explicit_entry = str(spec.get("entry"))
            if isinstance(spec.get("subdirectory"), str) and str(spec.get("subdirectory")).strip():
                explicit_subdir = str(spec.get("subdirectory")).strip()
        else:
            return PluginResolution(classes=[], errors=[{
                "type": "plugin_path_invalid",
                "detail": "Local path spec must be a string or dict",
                "path": spec,
            }])

        if not isinstance(parsed_path, str) or not parsed_path.strip():
            return PluginResolution(classes=[], errors=[{
                "type": "plugin_path_invalid",
                "detail": "Local path spec must include a non-empty path",
                "path": spec,
            }])

        base = self._resolve_base_dir(parsed_path, ctx.policy)
        if not base.exists():
            return PluginResolution(classes=[], errors=[{
                "type": "plugin_path_invalid",
                "detail": f"Local path {str(base)!r} does not exist",
                "path": parsed_path,
            }])

        descriptor = None
        descriptor_err = None
        if explicit_entry is None:
            descriptor, descriptor_err = read_descriptor(base)
            if descriptor_err is not None or descriptor is None:
                return PluginResolution(classes=[], errors=[descriptor_err or {
                    "type": "plugin_descriptor_invalid",
                    "detail": "Invalid agent_plugin.json",
                    "path": str(base),
                }])

        entries = [explicit_entry] if explicit_entry is not None else list(descriptor.entries)
        subdir = explicit_subdir
        if subdir is None and descriptor is not None:
            subdir = descriptor.subdirectory

        project_dir = (base / subdir).resolve() if isinstance(subdir, str) else base
        if not project_dir.is_dir():
            return PluginResolution(classes=[], errors=[{
                "type": "plugin_path_invalid",
                "detail": f"Project directory {str(project_dir)!r} does not exist",
                "path": str(project_dir),
            }])
        if not self._is_installable_project(project_dir):
            return PluginResolution(classes=[], errors=[{
                "type": "plugin_install_error",
                "detail": "Local path plugins must be pip-installable (pyproject.toml or setup.py)",
                "path": str(project_dir),
            }])

        cache_dir = ctx.cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)

        git_fp = self._fingerprint_git(base, project_dir)
        fp = git_fp or self._fingerprint_files(project_dir)
        revision = hashlib.sha256(fp.encode("utf-8", errors="ignore")).hexdigest()
        safe_id = base.name or "plugin"

        metadata: Dict[str, Any] = {
            "path": str(base),
            "project_dir": str(project_dir),
            "entry": entries[0] if len(entries) == 1 else None,
        }
        if git_fp and git_fp.startswith("git:"):
            parts = git_fp.split(":", 3)
            # Back-compat: older fingerprints were "git:<commit>:<status_hash>".
            # New fingerprints include a scope: "git:<commit>:<status_hash>:<scope>".
            if len(parts) >= 3:
                _tag, commit, status_hash = parts[:3]
                metadata["commit"] = commit
                metadata["status_hash"] = status_hash
            if len(parts) == 4:
                metadata["scope"] = parts[3]

        src_root = cache_dir / "src"
        src_root.mkdir(parents=True, exist_ok=True)
        try:
            install_dir = self._installer.ensure_installed(
                InstallRequest(
                    cache_dir=cache_dir,
                    safe_id=safe_id,
                    revision=revision,
                    project_dir=project_dir,
                    policy=ctx.policy,
                    metadata=metadata,
                )
            )
        except PluginInstallError as exc:
            return PluginResolution(classes=[], errors=[{
                "type": "plugin_install_error",
                "detail": exc.detail,
                "path": exc.path,
            }])
        except Exception as exc:
            return PluginResolution(classes=[], errors=[{
                "type": "plugin_install_error",
                "detail": f"install failed: {exc}",
                "path": str(project_dir),
            }])

        logger.info("plugin_local_resolved", path=str(base), install_dir=str(install_dir))

        classes: List[type] = []
        errors: List[Dict[str, Any]] = []
        for entry in entries:
            cls, err = import_dotted_class(entry)
            if err is not None or cls is None:
                errors.append(err or {"type": "plugin_import_error", "detail": "unknown", "path": entry})
                continue
            classes.append(cls)

        return PluginResolution(classes=classes, errors=errors)

    def _resolve_base_dir(self, path: str, policy: Mapping[str, Any]) -> Path:
        base_dir = policy.get("base_dir")
        base_path = Path(os.path.expanduser(path))
        if not base_path.is_absolute() and isinstance(base_dir, str) and base_dir:
            base_path = Path(base_dir) / base_path
        return base_path.resolve()

    def _is_installable_project(self, project_dir: Path) -> bool:
        return (project_dir / "pyproject.toml").is_file() or (project_dir / "setup.py").is_file()

    def _fingerprint_git(self, base: Path, project_dir: Path) -> Optional[str]:
        """Return a git-based fingerprint scoped to the plugin project directory.

        The goal is that unrelated commits elsewhere in the repository do not
        trigger a reinstall.

        Fingerprint format:
          - clean: "git:<commit>:<state_hash>:<scope>"
          - dirty: "git:<commit>:<state_hash>:<scope>"

        Where:
          - <commit> is the last commit that touched <scope>
          - <state_hash> is:
              - a hash of `git status --porcelain` output scoped to <scope> for clean trees
              - a hash of both the scoped porcelain status and the project file fingerprint
                for dirty trees, so edits within already-dirty files still change the revision
          - <scope> is the repo-relative directory ("." for repo root)
        """

        try:
            repo_root = subprocess.check_output(
                ["git", "-C", str(base), "rev-parse", "--show-toplevel"],
                stderr=subprocess.DEVNULL,
            ).decode().strip()
        except Exception:
            return None

        repo_root_path = Path(repo_root)
        try:
            scope_path = project_dir.resolve().relative_to(repo_root_path.resolve())
        except Exception:
            return None

        scope = "." if str(scope_path) == "." else str(scope_path)

        try:
            commit = subprocess.check_output(
                ["git", "-C", str(repo_root_path), "rev-list", "-1", "HEAD", "--", scope]
            ).decode().strip()
            if not commit:
                return None
        except Exception:
            return None

        try:
            status = subprocess.check_output(
                ["git", "-C", str(repo_root_path), "status", "--porcelain", "--", scope]
            ).decode()
        except Exception:
            status = ""

        status_hash = hashlib.sha256(status.encode("utf-8", errors="ignore")).hexdigest()
        if status.strip():
            project_hash = self._fingerprint_files(project_dir)
            combined = f"{status_hash}:{project_hash}"
            state_hash = hashlib.sha256(
                combined.encode("utf-8", errors="ignore")
            ).hexdigest()
        else:
            state_hash = status_hash
        return f"git:{commit}:{state_hash}:{scope}"

    def _fingerprint_files(self, project_dir: Path) -> str:
        hasher = hashlib.sha256()

        def _ignore_dir(name: str) -> bool:
            return name in {
                ".git",
                "__pycache__",
                ".pytest_cache",
                ".mypy_cache",
                "build",
                "dist",
                ".venv",
                "venv",
            } or name.endswith(".egg-info")

        for root, dirs, files in os.walk(project_dir):
            dirs[:] = [d for d in dirs if not _ignore_dir(d)]
            rel_root = os.path.relpath(root, project_dir)
            for filename in sorted(files):
                if filename.endswith(".pyc"):
                    continue
                full = Path(root) / filename
                try:
                    st = full.stat()
                except Exception:
                    continue
                rel = str(Path(rel_root) / filename)
                hasher.update(rel.encode("utf-8", errors="ignore"))
                hasher.update(str(getattr(st, "st_mtime_ns", int(st.st_mtime * 1e9))).encode("utf-8"))
                hasher.update(str(st.st_size).encode("utf-8"))
        return hasher.hexdigest()
