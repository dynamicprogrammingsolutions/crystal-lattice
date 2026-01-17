from __future__ import annotations

"""Application-level plugin manager and plugin sources.

This module composes core loader interfaces with application-provided policy
and parameters (cache_dir, precedence). It provides concrete sources for:

- Dotted-path imports (no side effects)
- Local path plugins (installed into a cache dir via pip)
- Git plugins (cloned then installed into a cache dir via pip)

The shared install-to-cache behavior is implemented via an install strategy so
it can be replaced independently later.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Protocol, Tuple
import importlib
import hashlib
import os
import sys
import json
import shutil
import subprocess
import tempfile
from datetime import datetime
import pkgutil
import inspect
from urllib.parse import urlsplit
from agent_core.utils import get_logger

from agent_core.plugin.loader import (
    DottedPathSource,
    PluginLoadResult,
    PluginMetadata,
    PluginSource,
    get_plugin_id,
    validate_plugin_for_kind,
)


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
        """Ensure the plugin is installed into the cache and importable."""


class PipTargetInstallStrategy:
    """Install an on-disk project into a cache dir via `pip install --target`.

    This strategy owns:
    - Cache install directory naming and atomic temp-dir swap
    - pip invocation (`pip_args`, `install_deps` -> `--no-deps`)
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
        install_deps = bool(request.policy.get("install_deps", False))
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
        sdir = str(install_dir)
        if sdir not in sys.path:
            sys.path.append(sdir)


class LocalPathSource:
    """Install and load plugin classes from a local directory.

    Supported spec forms:
      - String (single class): ``"path:/abs/or/rel::pkg.module.Class"``
      - Dict (single class): ``{"path": "/abs/or/rel", "entry": "pkg.module.Class"}``
      - Dict (entries list): ``{"path": "/abs/or/rel", "entries": ["pkg.module.ClassA", ...]}``

    Notes:
      - Unlike the earlier "install-free" LocalPath behavior, this source
        now mirrors GitInstallerSource: it performs a local `pip install
        --target ...` into `cache_dir`.
      - The only conceptual difference from the git source is that there is no
        cloning step (the source is already on disk).

    Side effects:
      - Appends the installed cache directory to ``sys.path`` (core-first, not
        prepended).

    See also: docs/plugins/application-config.md
    """

    def __init__(self, *, installer: InstallStrategy | None = None) -> None:
        self._installer = installer or PipTargetInstallStrategy()

    def supports(self, raw_spec: Any) -> bool:  # type: ignore[override]
        if isinstance(raw_spec, str):
            return raw_spec.strip().startswith("path:") and "::" in raw_spec
        if isinstance(raw_spec, dict):
            has_path = isinstance(raw_spec.get("path"), str)
            has_entry = isinstance(raw_spec.get("entry"), str)
            has_entries = isinstance(raw_spec.get("entries"), list)
            return has_path and (has_entry or has_entries)
        return False

    def _safe_id(self, path: Path, explicit_id: Optional[str]) -> str:
        if explicit_id:
            return explicit_id
        return path.name or "plugin"

    def _resolve_base_dir(self, path: str, policy: Mapping[str, Any]) -> Path:
        base_dir = policy.get("base_dir")
        base_path = Path(os.path.expanduser(path))
        if not base_path.is_absolute() and isinstance(base_dir, str) and base_dir:
            base_path = Path(base_dir) / base_path
        return base_path.resolve()

    def _read_descriptor(self, base: Path) -> Dict[str, Any] | None:
        desc_path = base / "agent_plugin.json"
        if not desc_path.is_file():
            return None
        try:
            data = json.loads(desc_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else None
        except Exception:
            return None

    def _project_dir(self, base: Path, raw_spec: Any) -> Path:
        subdir = raw_spec.get("subdirectory") if isinstance(raw_spec, dict) else None
        if not (isinstance(subdir, str) and subdir.strip()):
            desc = self._read_descriptor(base)
            if desc is not None:
                desc_subdir = desc.get("subdirectory")
                if isinstance(desc_subdir, str) and desc_subdir.strip():
                    subdir = desc_subdir
        if isinstance(subdir, str) and subdir.strip():
            return (base / subdir).resolve()
        return base

    def _is_installable_project(self, project_dir: Path) -> bool:
        return (project_dir / "pyproject.toml").is_file() or (project_dir / "setup.py").is_file()

    def _fingerprint_git(self, base: Path) -> Optional[str]:
        try:
            commit = subprocess.check_output(["git", "-C", str(base), "rev-parse", "HEAD"]).decode().strip()
        except Exception:
            return None
        try:
            status = subprocess.check_output(
                ["git", "-C", str(base), "status", "--porcelain", "--", "."]
            ).decode()
        except Exception:
            status = ""
        status_hash = hashlib.sha256(status.encode("utf-8", errors="ignore")).hexdigest()
        return f"git:{commit}:{status_hash}"

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

    def prepare(self, raw_spec: Any, *, cache_dir: Path, policy: Mapping[str, Any]) -> Tuple[Optional[Path], Optional[Dict[str, Any]]]:
        """Install from local path into cache and make it importable."""
        logger = get_logger("PluginManager")
        if isinstance(raw_spec, str):
            left, _, _entry = raw_spec.partition("::")
            path = left.split(":", 1)[1]
        elif isinstance(raw_spec, dict):
            path = str(raw_spec.get("path"))
        else:
            return None, {"type": "plugin_path_invalid", "detail": "LocalPathSource requires string 'path:...::...' or dict with 'path'", "path": raw_spec}
        base = self._resolve_base_dir(path, policy)
        if not base.exists():
            return None, {"type": "plugin_path_invalid", "detail": f"Local path {str(base)!r} does not exist", "path": path}

        project_dir = self._project_dir(base, raw_spec)
        if not project_dir.exists() or not project_dir.is_dir():
            return None, {"type": "plugin_path_invalid", "detail": f"Project directory {str(project_dir)!r} does not exist", "path": str(project_dir)}
        if not self._is_installable_project(project_dir):
            return None, {"type": "plugin_install_error", "detail": "Local path plugins must be pip-installable (pyproject.toml or setup.py)", "path": str(project_dir)}

        cache_dir.mkdir(parents=True, exist_ok=True)
        src_root = cache_dir / "src"
        src_root.mkdir(parents=True, exist_ok=True)

        git_fp = self._fingerprint_git(base)
        fp = git_fp or self._fingerprint_files(project_dir)
        fp_hash = hashlib.sha256(fp.encode("utf-8", errors="ignore")).hexdigest()

        safe_id = self._safe_id(base, raw_spec.get("id") if isinstance(raw_spec, dict) else None)
        expected_install_dir = cache_dir / f"{safe_id}@{fp_hash}"
        already_installed = expected_install_dir.exists()
        if already_installed:
            meta: Dict[str, Any] = {
                "path": str(base),
                "project_dir": str(project_dir),
                "fingerprint": fp,
            }
            if isinstance(git_fp, str) and git_fp.startswith("git:"):
                _tag, commit, status_hash = git_fp.split(":", 2)
                meta["commit"] = commit
                meta["status_hash"] = status_hash
            try:
                install_dir = self._installer.ensure_installed(
                    InstallRequest(
                        cache_dir=cache_dir,
                        safe_id=safe_id,
                        revision=fp_hash,
                        project_dir=project_dir,
                        policy=policy,
                        metadata=meta,
                    )
                )
                return install_dir, None
            except PluginInstallError as exc:
                return None, {"type": "plugin_install_error", "detail": exc.detail, "path": str(project_dir)}

        tmp_copy = Path(tempfile.mkdtemp(prefix="plugin_copy_", dir=str(src_root)))
        try:
            try:
                shutil.copytree(project_dir, tmp_copy, dirs_exist_ok=True)
            except Exception as exc:
                return None, {"type": "plugin_install_error", "detail": f"copy failed: {exc}", "path": str(project_dir)}

            meta: Dict[str, Any] = {
                "path": str(base),
                "project_dir": str(project_dir),
                "fingerprint": fp,
            }
            if isinstance(git_fp, str) and git_fp.startswith("git:"):
                _tag, commit, status_hash = git_fp.split(":", 2)
                meta["commit"] = commit
                meta["status_hash"] = status_hash

            try:
                install_dir = self._installer.ensure_installed(
                    InstallRequest(
                        cache_dir=cache_dir,
                        safe_id=safe_id,
                        revision=fp_hash,
                        project_dir=tmp_copy,
                        policy=policy,
                        metadata=meta,
                    )
                )
            except PluginInstallError as exc:
                return None, {"type": "plugin_install_error", "detail": exc.detail, "path": str(project_dir)}

            logger.info("plugin_local_installed", path=str(base), install_dir=str(install_dir))
            return install_dir, None
        finally:
            try:
                shutil.rmtree(tmp_copy, ignore_errors=True)
            except Exception:
                pass

    def load(self, raw_spec: Any, *, cache_dir: Path, policy: Mapping[str, Any]) -> PluginLoadResult:  # type: ignore[override]
        if isinstance(raw_spec, str):
            left, _, entry = raw_spec.partition("::")
            path = left.split(":", 1)[1]
        elif isinstance(raw_spec, dict):
            path = str(raw_spec.get("path"))
            entry = str(raw_spec.get("entry"))
        else:
            return PluginLoadResult(cls=None, metadata=None, error={
                "type": "plugin_path_invalid",
                "detail": "LocalPathSource requires string 'path:...::module.Class' or dict with 'path' and 'entry'",
                "path": raw_spec,
            })

        base = self._resolve_base_dir(path, policy)
        if not base.exists():
            return PluginLoadResult(cls=None, metadata=None, error={
                "type": "plugin_path_invalid",
                "detail": f"Local path {str(base)!r} does not exist",
                "path": path,
            })

        install_dir, prep_err = self.prepare(raw_spec, cache_dir=cache_dir, policy=policy)
        if prep_err is not None or install_dir is None:
            return PluginLoadResult(cls=None, metadata=None, error=prep_err or {"type": "plugin_install_error", "detail": "install failed", "path": path})

        module_path, sep, attr = entry.rpartition(".")
        if not sep:
            return PluginLoadResult(cls=None, metadata=None, error={
                "type": "plugin_path_invalid",
                "detail": "Invalid entry: expected 'module.Class'",
                "path": entry,
            })
        try:
            module = importlib.import_module(module_path)
            cls = getattr(module, attr)
        except Exception as exc:  # pragma: no cover - import failures surfaced
            return PluginLoadResult(cls=None, metadata=None, error={
                "type": "plugin_import_error",
                "detail": str(exc),
                "path": entry,
            })

        metadata = PluginMetadata(
            id=get_plugin_id(cls),
            kind=None,
            origin=str(install_dir),
            entry=entry,
            raw_spec=raw_spec,
        )
        return PluginLoadResult(cls=cls, metadata=metadata, error=None)


class PluginManager:
    """Compose multiple plugin sources and enforce app-level policy."""

    def __init__(
        self,
        *,
        cache_dir: Path,
        policy: Mapping[str, Any] | None = None,
        loaders: Optional[List[PluginSource]] = None,
    ) -> None:
        self.cache_dir = cache_dir
        self.policy: Mapping[str, Any] = policy or {}
        if loaders is None:
            installer = PipTargetInstallStrategy()
            self.loaders = [
                DottedPathSource(),
                LocalPathSource(installer=installer),
                GitInstallerSource(installer=installer),
            ]
        else:
            self.loaders = loaders

    # ------------------------- loading primitives -------------------------
    def load_one(self, raw_spec: Any, kind: Optional[str] = None) -> PluginLoadResult:
        for loader in self.loaders:
            try:
                if loader.supports(raw_spec):
                    result = loader.load(raw_spec, cache_dir=self.cache_dir, policy=self.policy)
                    if result.cls is not None and kind:
                        err = validate_plugin_for_kind(result.cls, kind)
                        if err is not None:
                            return PluginLoadResult(cls=None, metadata=result.metadata, error=err)
                    return result
            except Exception as exc:  # pragma: no cover - defensive boundary
                return PluginLoadResult(cls=None, metadata=None, error={
                    "type": "plugin_import_error",
                    "detail": str(exc),
                    "path": raw_spec,
                })
        return PluginLoadResult(cls=None, metadata=None, error={
            "type": "plugin_path_invalid",
            "detail": "No loader supports the given spec",
            "path": raw_spec,
        })

    def _find_loader(self, raw_spec: Any) -> Optional[PluginSource]:
        for loader in self.loaders:
            try:
                if loader.supports(raw_spec):
                    return loader
            except Exception:
                continue
        return None

    # ------------------------ canonicalization helper --------------------
    def normalize_plugins(self, plugins_raw: Any) -> List[Dict[str, Any]]:
        """Normalize raw plugin config into canonical list entries.

        Returns:
            List of dicts: ``[{"spec": <string|object>, "kind": <str|None>}, ...]``

        Accepted inputs:
            - Mapping by kind: keys ``providers|extensions|features|tools|application`` with array values.
            - Flat list: strings/objects/canonical items; kind is auto-filled as ``None`` unless present.
            - Single value: wrapped as one canonical item.

        Example:
            >>> mgr.normalize_plugins({"tools": ["path:/p::pkg.mod.Tool"]})
            [{'spec': 'path:/p::pkg.mod.Tool', 'kind': 'tools'}]

        See also: docs/plugins/application-config.md
        """

        canonical: List[Dict[str, Any]] = []
        if plugins_raw is None:
            return canonical
        # Mapping form with per-kind arrays
        if isinstance(plugins_raw, dict):
            for kind in ("providers", "features", "tools", "extensions"):
                entries = plugins_raw.get(kind) or []
                if isinstance(entries, list):
                    for entry in entries:
                        canonical.append({"spec": entry, "kind": kind})
            # Also accept application plugins under mapping for convenience
            entries = plugins_raw.get("application") or plugins_raw.get("application_plugins") or []
            if isinstance(entries, list):
                for entry in entries:
                    canonical.append({"spec": entry, "kind": "application"})
            # If mapping had no known keys, treat as a single spec mapping
            if not canonical and plugins_raw:
                canonical.append({"spec": plugins_raw, "kind": None})
            return canonical

        # Flat list form
        if isinstance(plugins_raw, list):
            for item in plugins_raw:
                if isinstance(item, dict) and "spec" in item:
                    spec = item.get("spec")
                    kind = item.get("kind") if isinstance(item.get("kind"), str) else None
                    canonical.append({"spec": spec, "kind": kind})
                else:
                    canonical.append({"spec": item, "kind": None})
            return canonical

        # Single value
        canonical.append({"spec": plugins_raw, "kind": None})
        return canonical

    # ------------------------ canonical loader ---------------------------
    def load_plugins(self, canonical_items: Iterable[Dict[str, Any]]) -> Tuple[Dict[str, List[type]], List[type], List[Dict[str, Any]]]:
        """Load all plugins from canonical items.

        Supports spec forms:
            - Dotted class: ``pkg.module.Class``
            - Local path (string/object): single class, module-only, entries list
            - Git (string/object): single class, module-only, entries list
            - Module-only discovery reads ``agent_plugin.json`` when present (preferred) or auto-discovers
              provider/tool/extension/application classes defined in the package and submodules.

        Args:
            canonical_items: iterable of canonical items ``{"spec": ..., "kind": optional}``

        Returns:
            (core_kinds, app_classes, errors)
            - core_kinds: mapping of kind -> list of classes
            - app_classes: list of application plugin classes
            - errors: list of error dicts with ``type/detail/path``

        See also: docs/plugins/development.md, docs/plugins/application-config.md
        """
        core_kinds: Dict[str, List[type]] = {"providers": [], "features": [], "tools": [], "extensions": []}
        app_classes: List[type] = []
        errors: List[Dict[str, Any]] = []

        def _auto_kind(cls: type) -> str:
            # Try in the same order used by core's deduction logic
            for k in ("providers", "tools", "extensions", "application", "features"):
                if validate_plugin_for_kind(cls, k) is None:
                    return k
            return "features"

        def _import_dotted(entry: str) -> Tuple[Optional[type], Optional[Dict[str, Any]]]:
            module_path, sep, attr = entry.rpartition(".")
            if not sep:
                return None, {"type": "plugin_path_invalid", "detail": "Invalid entry: expected 'module.Class'", "path": entry}
            try:
                module = importlib.import_module(module_path)
                cls = getattr(module, attr)
                return cls, None
            except Exception as exc:
                return None, {"type": "plugin_import_error", "detail": str(exc), "path": entry}

        def _discover_module(module_name: str) -> List[type]:
            """Import a package/module and discover plugin classes.

            Rules:
              - If a package, recursively walk submodules.
              - Only classes defined in the scanned module are considered
                (skip re-exports and imported bases).
              - Only classes that match a plugin protocol are returned
                (providers/tools/extensions/application).
            """
            out: List[type] = []
            try:
                root_mod = importlib.import_module(module_name)
            except Exception:
                return out
            modules_to_scan = [root_mod]
            # If package, walk submodules
            try:
                is_pkg = hasattr(root_mod, "__path__")
            except Exception:
                is_pkg = False
            if is_pkg:  # type: ignore[truthy-function]
                prefix = module_name + "."
                for _finder, name, _ispkg in pkgutil.walk_packages(root_mod.__path__, prefix):  # type: ignore[arg-type]
                    try:
                        subm = importlib.import_module(name)
                        modules_to_scan.append(subm)
                    except Exception:
                        continue
            for m in modules_to_scan:
                for _, obj in inspect.getmembers(m, inspect.isclass):
                    # Only keep classes defined in this module (avoid imported bases)
                    if getattr(obj, "__module__", None) != m.__name__:
                        continue
                    # Only keep classes that clearly look like plugin implementations
                    k = None
                    for candidate in ("providers", "tools", "extensions", "application"):
                        if validate_plugin_for_kind(obj, candidate) is None:
                            k = candidate
                            break
                    if k is not None:
                        out.append(obj)
            # Deduplicate while preserving order
            seen = set()
            deduped: List[type] = []
            for cls in out:
                if cls in seen:
                    continue
                seen.add(cls)
                deduped.append(cls)
            return deduped

        for item in list(canonical_items or []):
            if not isinstance(item, dict) or "spec" not in item:
                errors.append({"type": "plugin_path_invalid", "detail": "Canonical item must be a dict with 'spec'", "path": item})
                continue
            spec = item.get("spec")
            kind = item.get("kind") if isinstance(item.get("kind"), str) else None
            # Multi-entry support via dict {path|git, entries: [...]}
            if isinstance(spec, dict) and isinstance(spec.get("entries"), list):
                base_spec = dict(spec)
                entries = [e for e in spec.get("entries") if isinstance(e, str)]
                loader = self._find_loader(spec)
                if loader is None:
                    errors.append({"type": "plugin_path_invalid", "detail": "No loader supports base spec for entries", "path": base_spec})
                    continue
                # Prepare once
                prepare_fn = getattr(loader, "prepare", None)
                if callable(prepare_fn):
                    _prep_path, prep_err = prepare_fn(spec, cache_dir=self.cache_dir, policy=self.policy)
                    if prep_err:
                        errors.append(prep_err)
                        continue
                # Import each entry class
                for entry in entries:
                    cls, err = _import_dotted(entry)
                    if err is not None or cls is None:
                        errors.append(err or {"type": "plugin_import_error", "detail": "unknown", "path": entry})
                        continue
                    assigned_kind = kind or _auto_kind(cls)
                    if assigned_kind == "application":
                        app_classes.append(cls)
                    elif assigned_kind in core_kinds:
                        core_kinds[assigned_kind].append(cls)
                    else:
                        core_kinds["features"].append(cls)
                continue

            # Module-only entry: strings (path/git) or dict with module/entry
            module_name: Optional[str] = None
            base_spec: Optional[Dict[str, Any]] = None
            if isinstance(spec, str) and "::" in spec and (spec.startswith("path:") or spec.startswith("git+")):
                left, _, entry = spec.partition("::")
                last_seg = entry.rsplit(".", 1)[-1] if isinstance(entry, str) else ""
                # Heuristic: treat CamelCase suffixes as single-class specs.
                # Module-only string specs typically end in a module/package name.
                if not (isinstance(last_seg, str) and last_seg[:1].isupper()):
                    # Build a base spec and prepare before import attempt
                    if spec.startswith("path:"):
                        base_spec = {"path": left.split(":", 1)[1], "entry": entry}
                    else:
                        base_spec = {"git": left[len("git+") :].split("#")[0], "entry": entry}
                    loader = self._find_loader(base_spec)
                    if loader is not None:
                        prepare_fn = getattr(loader, "prepare", None)
                        if callable(prepare_fn):
                            _p, prep_err = prepare_fn(base_spec, cache_dir=self.cache_dir, policy=self.policy)
                            if prep_err is None:
                                try:
                                    importlib.import_module(entry)
                                    module_name = entry
                                except Exception:
                                    module_name = None
            elif isinstance(spec, dict) and isinstance(spec.get("entry"), str):
                entry_val = str(spec.get("entry"))
                loader = self._find_loader(spec)
                if loader is not None:
                    prepare_fn = getattr(loader, "prepare", None)
                    if callable(prepare_fn):
                        _p, prep_err = prepare_fn(spec, cache_dir=self.cache_dir, policy=self.policy)
                        if prep_err is None:
                            try:
                                importlib.import_module(entry_val)
                                module_name = entry_val
                                base_spec = spec
                            except Exception:
                                module_name = None

            if module_name and base_spec:
                loader = self._find_loader(base_spec)
                if loader is None:
                    errors.append({"type": "plugin_path_invalid", "detail": "No loader supports module-only spec", "path": base_spec})
                    continue
                prepare_fn = getattr(loader, "prepare", None)
                install_dir: Optional[Path] = None
                if callable(prepare_fn):
                    install_dir, prep_err = prepare_fn(base_spec, cache_dir=self.cache_dir, policy=self.policy)
                    if prep_err:
                        errors.append(prep_err)
                        continue
                # Descriptor support (single descriptor file at install root)
                entries_from_descriptor: List[str] = []
                kinds_map: Dict[str, str] = {}
                if install_dir is not None:
                    desc = install_dir / "agent_plugin.json"
                    if desc.exists():
                        try:
                            desc_data = json.loads(desc.read_text(encoding="utf-8"))
                            entries_from_descriptor = [e for e in desc_data.get("entries", []) if isinstance(e, str)]
                            kinds_map = desc_data.get("kinds", {}) if isinstance(desc_data.get("kinds"), dict) else {}
                        except Exception:
                            entries_from_descriptor = []
                            kinds_map = {}

                classes: List[type] = []
                if entries_from_descriptor:
                    targets = entries_from_descriptor
                    for entry in targets:
                        cls, err = _import_dotted(entry)
                        if err is not None or cls is None:
                            errors.append(err or {"type": "plugin_import_error", "detail": "unknown", "path": entry})
                            continue
                        classes.append(cls)
                        assigned_kind = kinds_map.get(entry) or kind or _auto_kind(cls)
                        if assigned_kind == "application":
                            app_classes.append(cls)
                        elif assigned_kind in core_kinds:
                            core_kinds[assigned_kind].append(cls)
                        else:
                            core_kinds["features"].append(cls)
                else:
                    # Auto-discover classes from module (providers/tools/extensions/application only)
                    discovered = _discover_module(module_name)
                    if not discovered:
                        # If nothing discovered, fall back to default single-class path handling below
                        pass
                    else:
                        for cls in discovered:
                            assigned_kind = kind or _auto_kind(cls)
                            if assigned_kind == "application":
                                app_classes.append(cls)
                            elif assigned_kind in core_kinds:
                                core_kinds[assigned_kind].append(cls)
                            else:
                                # Skip non-plugin classes rather than forcing 'features'
                                continue
                        continue
                continue

            # Default single-class path
            result = self.load_one(spec, kind=kind)
            if result.error is not None or result.cls is None:
                err = dict(result.error or {})
                if kind:
                    err.setdefault("kind", kind)
                err.setdefault("path", spec)
                errors.append(err)
                continue
            cls = result.cls
            assigned_kind = kind or _auto_kind(cls)
            if assigned_kind == "application":
                app_classes.append(cls)
            elif assigned_kind in core_kinds:
                core_kinds[assigned_kind].append(cls)
            else:
                core_kinds["features"].append(cls)

        return core_kinds, app_classes, errors

    # ------------------------------ lifecycle ----------------------------
    def prefetch_all(
        self,
        plugin_config: Mapping[str, Any] | None,
        application_plugins: Iterable[Any] | None = None,
    ) -> List[Dict[str, Any]]:
        """Eagerly load all plugins according to config.

        In this stage (no git installer), this effectively validates imports.
        """

        errors: List[Dict[str, Any]] = []
        canonical = []
        if plugin_config:
            canonical.extend(self.normalize_plugins(plugin_config))
        if application_plugins:
            for raw in application_plugins:
                canonical.append({"spec": raw, "kind": "application"})
        _core, _apps, errs = self.load_plugins(canonical)
        errors.extend(errs)
        return errors

    # Stubs for future cache management (implemented with GitInstallerSource)
    def list_cached(self) -> List[PluginMetadata]:
        return []

    def purge(self, plugin_id_or_path: str) -> None:  # pragma: no cover - stage 3 will implement
        return


__all__ = ["LocalPathSource", "PluginManager"]


class GitInstallerSource:
    """Install plugins from a git repo into a per-plugin cache dir and import.

    Supported specs:
      - String (single class): ``"git+<url-or-local>[#<ref>]::pkg.module.Class"``
      - Dict (single class): ``{"git": "<url-or-local>", "ref": "tag|commit", "entry": "pkg.module.Class"}``
      - Dict (entries list): ``{"git": "<url-or-local>", "entries": ["pkg.module.ClassA", ...]}``

    Policy:
      - ``allow_remote`` (default False) — remote URLs require explicit opt-in
      - ``allowed_git_hosts`` — optional allowlist for remote hosts
      - ``pip_args`` — extra args for pip install
      - sys.path precedence is core-first (append)

    Security:
      - Git installs execute arbitrary code via pip install; always prefer pinned refs.

    See also: docs/plugins/application-config.md
    """

    def __init__(self, *, installer: InstallStrategy | None = None) -> None:
        self._installer = installer or PipTargetInstallStrategy()

    def supports(self, raw_spec: Any) -> bool:  # type: ignore[override]
        if isinstance(raw_spec, str):
            s = raw_spec.strip()
            return s.startswith("git+") and "::" in s
        if isinstance(raw_spec, dict):
            has_git = isinstance(raw_spec.get("git"), str)
            has_entry = isinstance(raw_spec.get("entry"), str)
            has_entries = isinstance(raw_spec.get("entries"), list)
            return has_git and (has_entry or has_entries)
        return False

    def _parse_string(self, spec: str) -> Tuple[str, Optional[str], str]:
        left, _, entry = spec.partition("::")
        url_ref = left[len("git+") :]
        ref: Optional[str] = None
        if "#" in url_ref:
            url, ref = url_ref.split("#", 1)
            if ref == "":
                ref = None
        else:
            url = url_ref
        return url, ref, entry

    def _safe_id(self, url: str, explicit_id: Optional[str]) -> str:
        if explicit_id:
            return explicit_id
        # Derive from last path component; strip .git
        base = url.rstrip("/").split("/")[-1]
        if base.endswith(".git"):
            base = base[:-4]
        return base or "plugin"

    def _git(self, *args: str, cwd: Optional[Path] = None) -> None:
        subprocess.check_call(["git", *args], cwd=str(cwd) if cwd else None)

    def _git_output(self, *args: str, cwd: Optional[Path] = None) -> str:
        return subprocess.check_output(["git", *args], cwd=str(cwd) if cwd else None).decode().strip()

    # Installation is delegated to InstallStrategy.

    def prepare(self, raw_spec: Any, *, cache_dir: Path, policy: Mapping[str, Any]) -> Tuple[Optional[Path], Optional[Dict[str, Any]]]:
        """Clone/install the repo into cache (if not present) and make it importable (sys.path append)."""
        logger = get_logger("PluginManager")
        allow_remote = bool(policy.get("allow_remote", False))
        allowed_hosts = policy.get("allowed_git_hosts") or []
        if isinstance(raw_spec, str):
            url, ref, entry = self._parse_string(raw_spec)
        elif isinstance(raw_spec, dict):
            url = str(raw_spec.get("git"))
            ref = raw_spec.get("ref")
            entry = str(raw_spec.get("entry", ""))
        else:
            return None, {"type": "plugin_path_invalid", "detail": "GitInstallerSource requires string 'git+...::...' or dict with 'git'", "path": raw_spec}
        base_dir = policy.get("base_dir")
        if not (url.startswith("http://") or url.startswith("https://") or url.startswith("ssh://") or "@" in url):
            try:
                url_path = Path(url)
                if not url_path.is_absolute() and isinstance(base_dir, str) and base_dir:
                    url = str((Path(base_dir) / url_path).resolve())
            except Exception:
                pass

        is_remote = url.startswith("http://") or url.startswith("https://") or url.startswith("ssh://") or "@" in url
        if is_remote and not allow_remote:
            return None, {"type": "plugin_install_error", "detail": "Remote git URLs are disabled by policy", "path": url}
        if is_remote and allow_remote and allowed_hosts:
            host = None
            if url.startswith("http://") or url.startswith("https://") or url.startswith("ssh://"):
                host = urlsplit(url).hostname
            elif "@" in url and ":" in url:
                # git@host:org/repo
                host = url.split("@", 1)[1].split(":", 1)[0]
            if host and host not in allowed_hosts:
                return None, {"type": "plugin_install_error", "detail": f"Git host '{host}' not allowed by policy", "path": url}
        if is_remote and allow_remote and not (raw_spec.get("ref") if isinstance(raw_spec, dict) else None):
            logger.warning("plugin_remote_unpinned", url=url)
        cache_dir.mkdir(parents=True, exist_ok=True)
        src_root = cache_dir / "src"
        src_root.mkdir(parents=True, exist_ok=True)
        tmp_clone = Path(tempfile.mkdtemp(prefix="plugin_clone_", dir=str(src_root)))
        try:
            try:
                self._git("clone", url, str(tmp_clone))
            except Exception as exc:
                return None, {"type": "plugin_install_error", "detail": f"git clone failed: {exc}", "path": url}
            if ref:
                try:
                    self._git("-C", str(tmp_clone), "checkout", str(ref))
                except Exception as exc:
                    return None, {"type": "plugin_install_error", "detail": f"git checkout {ref} failed: {exc}", "path": url}
            try:
                commit = self._git_output("-C", str(tmp_clone), "rev-parse", "HEAD")
            except Exception:
                commit = "unknown"
            safe_id = self._safe_id(url, raw_spec.get("id") if isinstance(raw_spec, dict) else None)  # type: ignore[arg-type]
            subdir = raw_spec.get("subdirectory") if isinstance(raw_spec, dict) else None
            if not (isinstance(subdir, str) and subdir.strip()):
                try:
                    desc_path = tmp_clone / "agent_plugin.json"
                    if desc_path.is_file():
                        desc = json.loads(desc_path.read_text(encoding="utf-8"))
                        desc_subdir = desc.get("subdirectory")
                        if isinstance(desc_subdir, str) and desc_subdir.strip():
                            subdir = desc_subdir
                except Exception:
                    pass
            src_path = tmp_clone / subdir if isinstance(subdir, str) and subdir.strip() else tmp_clone

            try:
                install_dir = self._installer.ensure_installed(
                    InstallRequest(
                        cache_dir=cache_dir,
                        safe_id=safe_id,
                        revision=commit,
                        project_dir=src_path,
                        policy=policy,
                        metadata={
                            "git": url,
                            "ref": ref,
                            "commit": commit,
                            "entry": entry,
                        },
                    )
                )
                return install_dir, None
            except PluginInstallError as exc:
                return None, {"type": "plugin_install_error", "detail": exc.detail, "path": url}
        finally:
            try:
                shutil.rmtree(tmp_clone, ignore_errors=True)
            except Exception:
                pass

    def load(self, raw_spec: Any, *, cache_dir: Path, policy: Mapping[str, Any]) -> PluginLoadResult:  # type: ignore[override]
        if isinstance(raw_spec, str):
            url, ref, entry = self._parse_string(raw_spec)
        elif isinstance(raw_spec, dict):
            url = str(raw_spec.get("git"))
            ref = raw_spec.get("ref")
            entry_val = raw_spec.get("entry")
            if not isinstance(entry_val, str) or not entry_val:
                return PluginLoadResult(cls=None, metadata=None, error={
                    "type": "plugin_path_invalid",
                    "detail": "GitInstallerSource requires dict specs to include string 'entry'",
                    "path": raw_spec,
                })
            entry = entry_val
        else:
            return PluginLoadResult(cls=None, metadata=None, error={
                "type": "plugin_path_invalid",
                "detail": "GitInstallerSource requires string 'git+...::module.Class' or dict with 'git' and 'entry'",
                "path": raw_spec,
            })

        install_dir, prep_err = self.prepare(raw_spec, cache_dir=cache_dir, policy=policy)
        if prep_err is not None or install_dir is None:
            return PluginLoadResult(cls=None, metadata=None, error=prep_err or {
                "type": "plugin_install_error",
                "detail": "install failed",
                "path": url,
            })

        module_path, sep, attr = entry.rpartition(".")
        if not sep:
            return PluginLoadResult(cls=None, metadata=None, error={
                "type": "plugin_path_invalid",
                "detail": "Invalid entry: expected 'module.Class'",
                "path": entry,
            })
        try:
            module = importlib.import_module(module_path)
            cls = getattr(module, attr)
        except Exception as exc:
            return PluginLoadResult(cls=None, metadata=None, error={
                "type": "plugin_import_error",
                "detail": str(exc),
                "path": entry,
            })

        commit: Optional[str] = None
        origin_url = url
        meta_ref = ref
        try:
            meta_path = install_dir / "plugin_metadata.json"
            if meta_path.exists():
                meta_data = json.loads(meta_path.read_text(encoding="utf-8"))
                if isinstance(meta_data, dict):
                    origin_val = meta_data.get("git")
                    commit_val = meta_data.get("commit")
                    ref_val = meta_data.get("ref")
                    if isinstance(origin_val, str) and origin_val:
                        origin_url = origin_val
                    if isinstance(commit_val, str) and commit_val:
                        commit = commit_val
                    if isinstance(ref_val, str) and ref_val:
                        meta_ref = ref_val
        except Exception:
            pass

        metadata = PluginMetadata(
            id=get_plugin_id(cls),
            kind=None,
            origin=origin_url,
            entry=entry,
            raw_spec=raw_spec,
            ref=meta_ref if isinstance(meta_ref, str) and meta_ref else None,
            commit=commit,
            install_dir=install_dir,
        )
        return PluginLoadResult(cls=cls, metadata=metadata, error=None)

