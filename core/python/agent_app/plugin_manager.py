from __future__ import annotations

"""Application-level plugin manager and local-path loader.

This module composes core loader interfaces with application-provided policy
and parameters (cache_dir, precedence). It deliberately avoids any network or
package installation logic in this stage; a GitInstallerSource will be added in
the next stage.
"""

from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple
import importlib
import os
import sys
import json
import shutil
import subprocess
import tempfile
from datetime import datetime
import pkgutil
import inspect

from agent_core.plugin.loader import (
    DottedPathSource,
    PluginLoadResult,
    PluginMetadata,
    PluginSource,
    get_plugin_id,
    validate_plugin_for_kind,
)


class LocalPathSource:
    """Load plugin classes from a local directory in development.

    Supported specs:
      - String: "path:/abs/or/rel::module.Class"
      - Dict: {"path": "/abs/or/rel", "entry": "module.Class"}
    """

    def supports(self, raw_spec: Any) -> bool:  # type: ignore[override]
        if isinstance(raw_spec, str):
            return raw_spec.strip().startswith("path:") and "::" in raw_spec
        if isinstance(raw_spec, dict):
            has_path = isinstance(raw_spec.get("path"), str)
            has_entry = isinstance(raw_spec.get("entry"), str)
            has_entries = isinstance(raw_spec.get("entries"), list)
            return has_path and (has_entry or has_entries)
        return False

    def prepare(self, raw_spec: Any, *, cache_dir: Path, policy: Mapping[str, Any]) -> Tuple[Optional[Path], Optional[Dict[str, Any]]]:
        """Make the local path importable (append to sys.path)."""
        if isinstance(raw_spec, str):
            left, _, _entry = raw_spec.partition("::")
            path = left.split(":", 1)[1]
        elif isinstance(raw_spec, dict):
            path = str(raw_spec.get("path"))
        else:
            return None, {"type": "plugin_path_invalid", "detail": "LocalPathSource requires string 'path:...::...' or dict with 'path'", "path": raw_spec}
        base = Path(os.path.expanduser(path)).resolve()
        if not base.exists():
            return None, {"type": "plugin_path_invalid", "detail": f"Local path {str(base)!r} does not exist", "path": path}
        s = str(base)
        if s not in sys.path:
            sys.path.append(s)
        return base, None

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

        base = Path(os.path.expanduser(path)).resolve()
        if not base.exists():
            return PluginLoadResult(cls=None, metadata=None, error={
                "type": "plugin_path_invalid",
                "detail": f"Local path {str(base)!r} does not exist",
                "path": path,
            })

        # Core-first precedence: append to end of sys.path, do not insert at front.
        s = str(base)
        if s not in sys.path:
            sys.path.append(s)

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
            origin=str(base),
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
        self.loaders: List[PluginSource] = loaders or [DottedPathSource(), LocalPathSource(), GitInstallerSource()]

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
        """Rewrite raw config into canonical list items: [{"spec": ..., "kind": kind_or_none}, ...].

        Accepts mapping form with keys for kinds, flat list, or canonical items. Plain strings/objects
        inside a list are wrapped as short canonical entries with kind=None.
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
            """Import a module or package and discover plugin classes.

            - If it's a package, recursively walk submodules.
            - Collect classes defined in each module.
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

            # Module-only entry: e.g. "path:...::dev_plugins" or dict with entry module
            module_name: Optional[str] = None
            if isinstance(spec, str) and spec.startswith("path:") and "::" in spec:
                _left, _, entry = spec.partition("::")
                if entry and "." not in entry:
                    module_name = entry
                    base_spec = {"path": spec.split(":", 1)[1], "entry": entry}
                else:
                    module_name = None
            elif isinstance(spec, str) and spec.startswith("git+") and "::" in spec:
                _left, _, entry = spec.partition("::")
                if entry and "." not in entry:
                    module_name = entry
                    base_spec = {"git": spec[len("git+") :].split("#")[0], "entry": entry}
                else:
                    module_name = None
            elif isinstance(spec, dict) and isinstance(spec.get("entry"), str):
                entry_val = str(spec.get("entry"))
                # Try to import entry as a module; if it succeeds, treat as module-only
                try:
                    importlib.import_module(entry_val)
                    module_name = entry_val
                    base_spec = spec
                except Exception:
                    module_name = None
            else:
                module_name = None

            if module_name:
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
                # Descriptor support
                entries_from_descriptor: List[str] = []
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
                    else:
                        kinds_map = {}
                else:
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
                    # Auto-discover classes from module
                    for cls in _discover_module(module_name):
                        assigned_kind = kind or _auto_kind(cls)
                        if assigned_kind == "application":
                            app_classes.append(cls)
                        elif assigned_kind in core_kinds:
                            core_kinds[assigned_kind].append(cls)
                        else:
                            core_kinds["features"].append(cls)
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
      - String: "git+<url>[#<ref>]::module.Class"
      - Dict: {"git": url, "ref": opt, "subdirectory": opt, "entry": "module.Class", "id": opt}

    Policy respected:
      - allow_remote: bool (default True) — if False, only local paths allowed
      - pip_args: List[str] (optional) — extra pip args appended to install command
      - sys_path_precedence: "core_first" — honored by appending install_dir to sys.path
    """

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

    def _pip_install(self, target: Path, src: Path, extra_args: List[str]) -> None:
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "--target", str(target), str(src), *extra_args]
        subprocess.check_call(cmd)

    def prepare(self, raw_spec: Any, *, cache_dir: Path, policy: Mapping[str, Any]) -> Tuple[Optional[Path], Optional[Dict[str, Any]]]:
        """Clone/install the repo into cache (if not present) and make it importable (sys.path append)."""
        pip_args: List[str] = list(policy.get("pip_args") or [])
        allow_remote = bool(policy.get("allow_remote", True))
        if isinstance(raw_spec, str):
            url, ref, entry = self._parse_string(raw_spec)
        elif isinstance(raw_spec, dict):
            url = str(raw_spec.get("git"))
            ref = raw_spec.get("ref")
            entry = str(raw_spec.get("entry", ""))
        else:
            return None, {"type": "plugin_path_invalid", "detail": "GitInstallerSource requires string 'git+...::...' or dict with 'git'", "path": raw_spec}
        is_remote = url.startswith("http://") or url.startswith("https://") or url.startswith("ssh://") or "@" in url
        if is_remote and not allow_remote:
            return None, {"type": "plugin_install_error", "detail": "Remote git URLs are disabled by policy", "path": url}
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
            final_dir = cache_dir / f"{safe_id}@{commit}"
            if final_dir.exists():
                install_dir = final_dir
            else:
                temp_dir = cache_dir / f".{safe_id}@{commit}.tmp"
                if temp_dir.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)
                temp_dir.mkdir(parents=True, exist_ok=True)
                try:
                    subdir = raw_spec.get("subdirectory") if isinstance(raw_spec, dict) else None
                    src_path = tmp_clone / subdir if subdir else tmp_clone
                    self._pip_install(temp_dir, src_path, pip_args)
                    meta = {
                        "git": url,
                        "ref": ref,
                        "commit": commit,
                        "installed_at": datetime.utcnow().isoformat() + "Z",
                        "id": safe_id,
                    }
                    (temp_dir / "plugin_metadata.json").write_text(json.dumps(meta), encoding="utf-8")
                    temp_dir.replace(final_dir)
                    install_dir = final_dir
                except Exception as exc:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return None, {"type": "plugin_install_error", "detail": f"pip install failed: {exc}", "path": url}
            sdir = str(install_dir)
            if sdir not in sys.path:
                sys.path.append(sdir)
            return install_dir, None
        finally:
            try:
                shutil.rmtree(tmp_clone, ignore_errors=True)
            except Exception:
                pass

    def load(self, raw_spec: Any, *, cache_dir: Path, policy: Mapping[str, Any]) -> PluginLoadResult:  # type: ignore[override]
        pip_args: List[str] = list(policy.get("pip_args") or [])
        allow_remote = bool(policy.get("allow_remote", True))

        if isinstance(raw_spec, str):
            url, ref, entry = self._parse_string(raw_spec)
        elif isinstance(raw_spec, dict):
            url = str(raw_spec.get("git"))
            ref = raw_spec.get("ref")
            entry = str(raw_spec.get("entry"))
        else:
            return PluginLoadResult(cls=None, metadata=None, error={
                "type": "plugin_path_invalid",
                "detail": "GitInstallerSource requires string 'git+...::module.Class' or dict with 'git' and 'entry'",
                "path": raw_spec,
            })

        # Simple local/remote detection (http/ssh considered remote)
        is_remote = url.startswith("http://") or url.startswith("https://") or url.startswith("ssh://") or "@" in url
        if is_remote and not allow_remote:
            return PluginLoadResult(cls=None, metadata=None, error={
                "type": "plugin_install_error",
                "detail": "Remote git URLs are disabled by policy",
                "path": url,
            })

        cache_dir.mkdir(parents=True, exist_ok=True)
        src_root = cache_dir / "src"
        src_root.mkdir(parents=True, exist_ok=True)

        tmp_clone = Path(tempfile.mkdtemp(prefix="plugin_clone_", dir=str(src_root)))
        install_dir: Optional[Path] = None
        try:
            # Clone and checkout
            try:
                self._git("clone", url, str(tmp_clone))
            except Exception as exc:
                return PluginLoadResult(cls=None, metadata=None, error={
                    "type": "plugin_install_error",
                    "detail": f"git clone failed: {exc}",
                    "path": url,
                })
            if ref:
                try:
                    self._git("-C", str(tmp_clone), "checkout", str(ref))
                except Exception as exc:
                    return PluginLoadResult(cls=None, metadata=None, error={
                        "type": "plugin_install_error",
                        "detail": f"git checkout {ref} failed: {exc}",
                        "path": url,
                    })
            try:
                commit = self._git_output("-C", str(tmp_clone), "rev-parse", "HEAD")
            except Exception:
                commit = "unknown"

            safe_id = self._safe_id(url, raw_spec.get("id") if isinstance(raw_spec, dict) else None)  # type: ignore[arg-type]
            final_dir = cache_dir / f"{safe_id}@{commit}"
            if final_dir.exists():
                install_dir = final_dir
            else:
                temp_dir = cache_dir / f".{safe_id}@{commit}.tmp"
                if temp_dir.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)
                temp_dir.mkdir(parents=True, exist_ok=True)
                try:
                    subdir = raw_spec.get("subdirectory") if isinstance(raw_spec, dict) else None
                    src_path = tmp_clone / subdir if subdir else tmp_clone
                    self._pip_install(temp_dir, src_path, pip_args)
                    # Write metadata
                    meta = {
                        "git": url,
                        "ref": ref,
                        "commit": commit,
                        "entry": entry,
                        "installed_at": datetime.utcnow().isoformat() + "Z",
                        "id": safe_id,
                    }
                    (temp_dir / "plugin_metadata.json").write_text(json.dumps(meta), encoding="utf-8")
                    # Atomic move
                    temp_dir.replace(final_dir)
                    install_dir = final_dir
                except Exception as exc:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return PluginLoadResult(cls=None, metadata=None, error={
                        "type": "plugin_install_error",
                        "detail": f"pip install failed: {exc}",
                        "path": url,
                    })

            # Core-first: append install_dir to sys.path
            sdir = str(install_dir)
            if sdir not in sys.path:
                sys.path.append(sdir)

            # Import entry
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

            metadata = PluginMetadata(
                id=get_plugin_id(cls),
                kind=None,
                origin=url,
                entry=entry,
                raw_spec=raw_spec,
                ref=ref,
                commit=commit,
                install_dir=install_dir,
            )
            return PluginLoadResult(cls=cls, metadata=metadata, error=None)
        finally:
            try:
                shutil.rmtree(tmp_clone, ignore_errors=True)
            except Exception:
                pass

