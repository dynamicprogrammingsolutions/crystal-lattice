from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

import hashlib
import os
import shutil
import subprocess
import tempfile
from urllib.parse import urlsplit

from agent_core.utils import get_logger

from .descriptor import read_descriptor
from .importing import import_dotted_class
from .install import InstallRequest, InstallStrategy, PipTargetInstallStrategy, PluginInstallError
from .types import PluginContext, PluginResolution


class GitRepoSource:
    """Resolve git-based plugin repositories.

    Supported specs:
      - Descriptor-driven (recommended): "git+<url-or-local>[#ref]"
      - Explicit entry: {"git": "<url-or-local>", "ref": "optional", "entry": "pkg.module.Class", "subdirectory": "optional"}
      - Explicit descriptor-driven: {"git": "<url-or-local>", "ref": "optional"} (requires agent_plugin.json)

    Security:
      - Remote URLs require policy `allow_remote: true`.
      - Optional allowlist via `allowed_git_hosts`.
    """

    def __init__(self, *, installer: InstallStrategy | None = None) -> None:
        self._installer = installer or PipTargetInstallStrategy()

    def supports(self, spec: Any) -> bool:
        if isinstance(spec, str):
            return spec.strip().startswith("git+")
        if isinstance(spec, dict):
            return isinstance(spec.get("git"), str)
        return False

    def resolve(self, spec: Any, ctx: PluginContext) -> PluginResolution:
        logger = get_logger("PluginManager")

        url: Optional[str]
        ref: Optional[str] = None
        explicit_entry: Optional[str] = None
        explicit_subdir: Optional[str] = None

        if isinstance(spec, str):
            if "::" in spec:
                return PluginResolution(classes=[], errors=[{
                    "type": "plugin_path_invalid",
                    "detail": "Git specs no longer support '::' forms; use a dict with 'entry'",
                    "path": spec,
                }])
            url_ref = spec.strip()[len("git+") :]
            if "#" in url_ref:
                url, ref = url_ref.split("#", 1)
            else:
                url, ref = url_ref, None
        elif isinstance(spec, dict):
            url = spec.get("git")
            raw_ref = spec.get("ref")
            if isinstance(raw_ref, str) and raw_ref.strip():
                ref = raw_ref.strip()
            if isinstance(spec.get("entry"), str):
                explicit_entry = str(spec.get("entry"))
            if isinstance(spec.get("subdirectory"), str) and str(spec.get("subdirectory")).strip():
                explicit_subdir = str(spec.get("subdirectory")).strip()
        else:
            return PluginResolution(classes=[], errors=[{
                "type": "plugin_path_invalid",
                "detail": "Git spec must be a string or dict",
                "path": spec,
            }])

        if not isinstance(url, str) or not url.strip():
            return PluginResolution(classes=[], errors=[{
                "type": "plugin_path_invalid",
                "detail": "Git spec must include a non-empty URL/path",
                "path": spec,
            }])

        url = self._resolve_local_git_path(url, ctx.policy)
        remote_err = self._enforce_remote_policy(url, ctx.policy)
        if remote_err is not None:
            return PluginResolution(classes=[], errors=[remote_err])

        cache_dir = ctx.cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)
        src_root = cache_dir / "src"
        src_root.mkdir(parents=True, exist_ok=True)

        tmp_clone = Path(tempfile.mkdtemp(prefix="plugin_clone_", dir=str(src_root)))
        try:
            try:
                subprocess.check_call(["git", "clone", url, str(tmp_clone)])
            except Exception as exc:
                return PluginResolution(classes=[], errors=[{
                    "type": "plugin_install_error",
                    "detail": f"git clone failed: {exc}",
                    "path": url,
                }])
            if ref:
                try:
                    subprocess.check_call(["git", "-C", str(tmp_clone), "checkout", ref])
                except Exception as exc:
                    return PluginResolution(classes=[], errors=[{
                        "type": "plugin_install_error",
                        "detail": f"git checkout {ref} failed: {exc}",
                        "path": url,
                    }])

            try:
                commit = subprocess.check_output(["git", "-C", str(tmp_clone), "rev-parse", "HEAD"]).decode().strip()
            except Exception:
                commit = "unknown"

            descriptor = None
            descriptor_err = None
            if explicit_entry is None:
                descriptor, descriptor_err = read_descriptor(tmp_clone)
                if descriptor_err is not None or descriptor is None:
                    return PluginResolution(classes=[], errors=[descriptor_err or {
                        "type": "plugin_descriptor_invalid",
                        "detail": "Invalid agent_plugin.json",
                        "path": str(tmp_clone),
                    }])

            entries = [explicit_entry] if explicit_entry is not None else list(descriptor.entries)
            subdir = explicit_subdir
            if subdir is None and descriptor is not None:
                subdir = descriptor.subdirectory

            project_dir = (tmp_clone / subdir).resolve() if isinstance(subdir, str) else tmp_clone
            if not project_dir.is_dir():
                return PluginResolution(classes=[], errors=[{
                    "type": "plugin_path_invalid",
                    "detail": f"Project directory {str(project_dir)!r} does not exist",
                    "path": str(project_dir),
                }])
            if not self._is_installable_project(project_dir):
                return PluginResolution(classes=[], errors=[{
                    "type": "plugin_install_error",
                    "detail": "Git plugins must be pip-installable (pyproject.toml or setup.py)",
                    "path": str(project_dir),
                }])

            safe_id = self._safe_id(url)

            metadata: Dict[str, Any] = {
                "git": url,
                "ref": ref,
                "commit": commit,
                "project_dir": str(project_dir),
                "entry": entries[0] if len(entries) == 1 else None,
            }

            try:
                install_dir = self._installer.ensure_installed(
                    InstallRequest(
                        cache_dir=cache_dir,
                        safe_id=safe_id,
                        revision=commit,
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

            logger.info("plugin_git_resolved", url=url, commit=commit, install_dir=str(install_dir))

            classes: List[type] = []
            errors: List[Dict[str, Any]] = []
            for entry in entries:
                cls, err = import_dotted_class(entry)
                if err is not None or cls is None:
                    errors.append(err or {"type": "plugin_import_error", "detail": "unknown", "path": entry})
                    continue
                classes.append(cls)
            return PluginResolution(classes=classes, errors=errors)
        finally:
            try:
                shutil.rmtree(tmp_clone, ignore_errors=True)
            except Exception:
                pass

    def _is_installable_project(self, project_dir: Path) -> bool:
        return (project_dir / "pyproject.toml").is_file() or (project_dir / "setup.py").is_file()

    def _safe_id(self, url: str) -> str:
        base = url.rstrip("/").split("/")[-1]
        if base.endswith(".git"):
            base = base[:-4]
        return base or "plugin"

    def _resolve_local_git_path(self, url: str, policy: Mapping[str, Any]) -> str:
        base_dir = policy.get("base_dir")
        is_remote = url.startswith("http://") or url.startswith("https://") or url.startswith("ssh://") or "@" in url
        if is_remote:
            return url
        try:
            url_path = Path(os.path.expanduser(url))
            if not url_path.is_absolute() and isinstance(base_dir, str) and base_dir:
                url_path = Path(base_dir) / url_path
            return str(url_path.resolve())
        except Exception:
            return url

    def _enforce_remote_policy(self, url: str, policy: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
        allow_remote = bool(policy.get("allow_remote", False))
        allowed_hosts = policy.get("allowed_git_hosts") or []
        is_remote = url.startswith("http://") or url.startswith("https://") or url.startswith("ssh://") or "@" in url
        if is_remote and not allow_remote:
            return {
                "type": "plugin_install_error",
                "detail": "Remote git URLs are disabled by policy",
                "path": url,
            }
        if is_remote and allow_remote and allowed_hosts:
            host = None
            if url.startswith("http://") or url.startswith("https://") or url.startswith("ssh://"):
                host = urlsplit(url).hostname
            elif "@" in url and ":" in url:
                host = url.split("@", 1)[1].split(":", 1)[0]
            if host and host not in allowed_hosts:
                return {
                    "type": "plugin_install_error",
                    "detail": f"Git host '{host}' not allowed by policy",
                    "path": url,
                }
        return None
