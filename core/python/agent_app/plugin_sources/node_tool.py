from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from urllib.parse import urlsplit

from agent_core.tool_hosts.node_tool_plugin import NodeToolPlugin
from agent_core.utils import get_logger

from .types import PluginContext, PluginResolution


logger = get_logger("NodeToolSource")


class NodeToolSource:
    """Resolve JavaScript/TypeScript tool plugins executed by Node.js.

    Supported specs:
      - {"node_tool": {"path": "./dir"}}
      - {"node_tool": {"git": "https://...", "ref": "optional"}}
      - {"node_tool": {"file": "./tool.js", "id": "my_tool"}}

    For directory-based specs, tool descriptors are read from
    ``package.json#agent.tools``.
    """

    def supports(self, spec: Any) -> bool:
        if isinstance(spec, str):
            s = spec.strip()
            return s.startswith("node:") or s.startswith("node+git:")
        if isinstance(spec, dict):
            return isinstance(spec.get("node_tool"), dict)
        return False

    def resolve(self, spec: Any, ctx: PluginContext) -> PluginResolution:
        if isinstance(spec, str):
            parsed, err = self._parse_string_spec(spec)
            if err is not None or parsed is None:
                return PluginResolution(classes=[], errors=[err or {
                    "type": "plugin_path_invalid",
                    "detail": "Invalid node tool spec",
                    "path": spec,
                }])
            node_spec = parsed
        elif isinstance(spec, dict) and isinstance(spec.get("node_tool"), dict):
            node_spec = dict(spec.get("node_tool") or {})
        else:
            return PluginResolution(
                classes=[],
                errors=[
                    {
                        "type": "plugin_path_invalid",
                        "detail": "node_tool spec must be a dict or a supported string shortcut",
                        "path": spec,
                    }
                ],
            )
        if "path" in node_spec:
            return self._resolve_local_path(node_spec, ctx)
        if "git" in node_spec:
            return self._resolve_git(node_spec, ctx)
        if "file" in node_spec:
            return self._resolve_file(node_spec, ctx)

        return PluginResolution(
            classes=[],
            errors=[
                {
                    "type": "plugin_path_invalid",
                    "detail": "node_tool must include one of: path, git, file",
                    "path": spec,
                }
            ],
        )

    def _parse_string_spec(
        self, spec: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        s = spec.strip()
        if s.startswith("node+git:"):
            url_ref = s[len("node+git:") :]
            if "#" in url_ref:
                url, ref = url_ref.split("#", 1)
            else:
                url, ref = url_ref, None
            url = url.strip()
            if not url:
                return None, {
                    "type": "plugin_path_invalid",
                    "detail": "node+git spec must include a URL/path",
                    "path": spec,
                }
            node_spec: Dict[str, Any] = {"git": url}
            if isinstance(ref, str) and ref.strip():
                node_spec["ref"] = ref.strip()
            return node_spec, None

        if s.startswith("node:"):
            raw_path = s[len("node:") :].strip()
            if not raw_path:
                return None, {
                    "type": "plugin_path_invalid",
                    "detail": "node: spec must include a path",
                    "path": spec,
                }
            # The loader decides file vs directory when resolving.
            return {"path": raw_path}, None

        return None, {
            "type": "plugin_path_invalid",
            "detail": "Unsupported node tool shortcut; expected node:<path> or node+git:<url>[#ref]",
            "path": spec,
        }

    # ---------------------------------------------------------------------
    # Local path
    # ---------------------------------------------------------------------

    def _resolve_local_path(self, node_spec: Mapping[str, Any], ctx: PluginContext) -> PluginResolution:
        raw_path = node_spec.get("path")
        if not isinstance(raw_path, str) or not raw_path.strip():
            return PluginResolution(classes=[], errors=[{
                "type": "plugin_path_invalid",
                "detail": "node_tool.path must be a non-empty string",
                "path": raw_path,
            }])

        base = self._resolve_base_dir(raw_path, ctx.policy)
        if not base.exists():
            return PluginResolution(classes=[], errors=[{
                "type": "plugin_path_invalid",
                "detail": f"Local path {str(base)!r} does not exist",
                "path": raw_path,
            }])

        if base.is_file():
            spec_overrides = dict(node_spec)
            spec_overrides.pop("path", None)
            spec_overrides.setdefault("file", raw_path)
            return self._resolve_file(spec_overrides, ctx)

        subdir = node_spec.get("subdirectory")
        project_dir = (base / subdir).resolve() if isinstance(subdir, str) and subdir.strip() else base
        if not project_dir.is_dir():
            return PluginResolution(classes=[], errors=[{
                "type": "plugin_path_invalid",
                "detail": f"Project directory {str(project_dir)!r} does not exist",
                "path": str(project_dir),
            }])

        git_fp = self._fingerprint_git(base, project_dir)
        fp = git_fp or self._fingerprint_files(project_dir)
        revision = hashlib.sha256(fp.encode("utf-8", errors="ignore")).hexdigest()
        safe_id = base.name or "node_tool"

        install_dir = self._ensure_cached_copy(
            ctx.cache_dir,
            safe_id=safe_id,
            revision=revision,
            project_dir=project_dir,
        )
        self._maybe_install_and_build(install_dir, ctx.policy)
        return self._classes_from_install(install_dir, node_spec, ctx.policy)

    # ---------------------------------------------------------------------
    # Git
    # ---------------------------------------------------------------------

    def _resolve_git(self, node_spec: Mapping[str, Any], ctx: PluginContext) -> PluginResolution:
        url = node_spec.get("git")
        if not isinstance(url, str) or not url.strip():
            return PluginResolution(classes=[], errors=[{
                "type": "plugin_path_invalid",
                "detail": "node_tool.git must be a non-empty string",
                "path": url,
            }])

        url = self._resolve_local_git_path(url, ctx.policy)
        remote_err = self._enforce_remote_policy(url, ctx.policy)
        if remote_err is not None:
            return PluginResolution(classes=[], errors=[remote_err])

        ref = node_spec.get("ref")
        ref_value = ref.strip() if isinstance(ref, str) and ref.strip() else None

        src_root = ctx.cache_dir / "src"
        src_root.mkdir(parents=True, exist_ok=True)
        tmp_clone = Path(tempfile.mkdtemp(prefix="node_tool_clone_", dir=str(src_root)))

        try:
            try:
                subprocess.check_call(["git", "clone", url, str(tmp_clone)])
            except Exception as exc:
                return PluginResolution(classes=[], errors=[{
                    "type": "plugin_install_error",
                    "detail": f"git clone failed: {exc}",
                    "path": url,
                }])

            if ref_value:
                try:
                    subprocess.check_call(["git", "-C", str(tmp_clone), "checkout", ref_value])
                except Exception as exc:
                    return PluginResolution(classes=[], errors=[{
                        "type": "plugin_install_error",
                        "detail": f"git checkout {ref_value} failed: {exc}",
                        "path": url,
                    }])

            try:
                commit = (
                    subprocess.check_output(["git", "-C", str(tmp_clone), "rev-parse", "HEAD"])
                    .decode()
                    .strip()
                )
            except Exception:
                commit = "unknown"

            subdir = node_spec.get("subdirectory")
            project_dir = (
                (tmp_clone / subdir).resolve()
                if isinstance(subdir, str) and subdir.strip()
                else tmp_clone
            )
            if not project_dir.is_dir():
                return PluginResolution(classes=[], errors=[{
                    "type": "plugin_path_invalid",
                    "detail": f"Project directory {str(project_dir)!r} does not exist",
                    "path": str(project_dir),
                }])

            safe_id = self._safe_id(url)
            install_dir = self._ensure_cached_copy(
                ctx.cache_dir,
                safe_id=safe_id,
                revision=commit,
                project_dir=project_dir,
            )
            self._maybe_install_and_build(install_dir, ctx.policy)
            return self._classes_from_install(install_dir, node_spec, ctx.policy)
        finally:
            try:
                shutil.rmtree(tmp_clone, ignore_errors=True)
            except Exception:
                pass

    # ---------------------------------------------------------------------
    # Single file
    # ---------------------------------------------------------------------

    def _resolve_file(self, node_spec: Mapping[str, Any], ctx: PluginContext) -> PluginResolution:
        raw_file = node_spec.get("file")
        if not isinstance(raw_file, str) or not raw_file.strip():
            return PluginResolution(classes=[], errors=[{
                "type": "plugin_path_invalid",
                "detail": "node_tool.file must be a non-empty string",
                "path": raw_file,
            }])

        path = self._resolve_base_dir(raw_file, ctx.policy)
        if not path.is_file():
            return PluginResolution(classes=[], errors=[{
                "type": "plugin_path_invalid",
                "detail": f"Tool file {str(path)!r} does not exist",
                "path": raw_file,
            }])

        try:
            content = path.read_bytes()
        except Exception as exc:
            return PluginResolution(classes=[], errors=[{
                "type": "plugin_path_invalid",
                "detail": f"Could not read tool file: {exc}",
                "path": raw_file,
            }])

        revision = hashlib.sha256(content).hexdigest()
        safe_id = Path(raw_file).stem or "node_tool"
        install_dir = ctx.cache_dir / "node" / f"{safe_id}@{revision}"
        install_dir.mkdir(parents=True, exist_ok=True)

        ext = path.suffix.lower()
        spec_overrides = dict(node_spec)
        spec_overrides.setdefault("id", safe_id)
        if ext == ".ts":
            src_dir = install_dir / "src"
            src_dir.mkdir(parents=True, exist_ok=True)

            tool_src = src_dir / path.name
            index_ts = src_dir / "index.ts"
            pkg_json = install_dir / "package.json"

            if not tool_src.exists():
                shutil.copy2(path, tool_src)
            if not index_ts.exists():
                index_ts.write_text(
                    f"export {{ default }} from './{path.stem}';\n",
                    encoding="utf-8",
                )
            if not pkg_json.exists():
                pkg_json.write_text(
                    json.dumps(
                        {
                            "name": safe_id,
                            "version": "0.0.0",
                            "type": "module",
                            "main": "dist/index.js",
                            "scripts": {
                                "build": "esbuild src/index.ts --bundle --platform=node --format=esm --outdir=dist"
                            },
                        }
                    ),
                    encoding="utf-8",
                )

            spec_overrides.setdefault("entry", "dist/index.js")
            self._maybe_install_and_build(install_dir, ctx.policy)
            return self._classes_from_install(install_dir, spec_overrides, ctx.policy)

        # Plain JS file: copy directly and run as an entry module.
        dst_file = install_dir / path.name
        if not dst_file.exists():
            shutil.copy2(path, dst_file)
            (install_dir / "package.json").write_text(
                json.dumps({"name": safe_id, "version": "0.0.0", "type": "module"}),
                encoding="utf-8",
            )

        spec_overrides = dict(spec_overrides)
        spec_overrides.setdefault("entry", dst_file.name)
        return self._classes_from_install(install_dir, spec_overrides, ctx.policy)

    # ---------------------------------------------------------------------
    # Install dir -> classes
    # ---------------------------------------------------------------------

    def _classes_from_install(
        self,
        install_dir: Path,
        node_spec: Mapping[str, Any],
        policy: Mapping[str, Any],
    ) -> PluginResolution:
        pkg_json, pkg_err = self._read_package_json(install_dir)
        entry_override = node_spec.get("entry")
        export_override = node_spec.get("export")
        id_override = node_spec.get("id")
        name_override = node_spec.get("name")
        version_override = node_spec.get("version")

        explicit = (
            isinstance(entry_override, str)
            and entry_override.strip()
            and (isinstance(id_override, str) and id_override.strip() or isinstance(name_override, str) and name_override.strip())
        )

        if explicit:
            plugin_id = str(id_override or name_override).strip()
            entry = str(entry_override).strip()
            export_name = str(export_override).strip() if isinstance(export_override, str) and export_override.strip() else None
            version = str(version_override).strip() if isinstance(version_override, str) and version_override.strip() else str((pkg_json or {}).get("version") or "unknown")
            cls, err = self._make_proxy_class(
                install_dir,
                plugin_id=plugin_id,
                version=version,
                entry=entry,
                export_name=export_name,
                policy=policy,
            )
            if err is not None or cls is None:
                return PluginResolution(classes=[], errors=[err or {
                    "type": "plugin_path_invalid",
                    "detail": "Invalid node_tool spec",
                    "path": str(install_dir),
                }])
            return PluginResolution(classes=[cls], errors=[])

        if pkg_err is not None:
            return PluginResolution(classes=[], errors=[pkg_err])
        assert pkg_json is not None

        tools = self._read_agent_tools(pkg_json)
        if not tools:
            return PluginResolution(classes=[], errors=[{
                "type": "plugin_descriptor_missing",
                "detail": "package.json missing agent.tools descriptor (or provide explicit {entry,id})",
                "path": str(install_dir / "package.json"),
            }])

        filter_id = id_override.strip() if isinstance(id_override, str) and id_override.strip() else None
        if filter_id is not None:
            tools = [t for t in tools if t.get("id") == filter_id]
            if not tools:
                return PluginResolution(classes=[], errors=[{
                    "type": "plugin_path_invalid",
                    "detail": f"No agent.tools entry matched id {filter_id!r}",
                    "path": str(install_dir),
                }])

        pkg_name = pkg_json.get("name") if isinstance(pkg_json.get("name"), str) else "node_tool"
        pkg_version = pkg_json.get("version") if isinstance(pkg_json.get("version"), str) else "unknown"

        classes: List[type] = []
        errors: List[Dict[str, Any]] = []
        for tool in tools:
            plugin_id = tool.get("id")
            entry = tool.get("entry")
            export_name = tool.get("export")
            if not isinstance(entry, str) or not entry.strip():
                errors.append({
                    "type": "plugin_descriptor_invalid",
                    "detail": "agent.tools entry missing 'entry'",
                    "path": str(install_dir / "package.json"),
                })
                continue

            if not isinstance(plugin_id, str) or not plugin_id.strip():
                plugin_id = str(name_override).strip() if isinstance(name_override, str) and name_override.strip() else pkg_name

            version = str(version_override).strip() if isinstance(version_override, str) and version_override.strip() else pkg_version
            cls, err = self._make_proxy_class(
                install_dir,
                plugin_id=plugin_id,
                version=version,
                entry=entry,
                export_name=export_name,
                policy=policy,
            )
            if err is not None or cls is None:
                errors.append(err or {
                    "type": "plugin_install_error",
                    "detail": "Could not build node tool proxy",
                    "path": str(install_dir),
                })
                continue
            classes.append(cls)

        return PluginResolution(classes=classes, errors=errors)

    def _make_proxy_class(
        self,
        install_dir: Path,
        *,
        plugin_id: str,
        version: str,
        entry: str,
        export_name: Optional[str],
        policy: Mapping[str, Any],
    ) -> Tuple[Optional[type], Optional[Dict[str, Any]]]:
        entry_path = (install_dir / entry).resolve()
        if not entry_path.is_file():
            return None, {
                "type": "plugin_path_invalid",
                "detail": f"node_tool entry {str(entry_path)!r} does not exist",
                "path": str(entry_path),
            }

        timeout = policy.get("node_timeout_seconds")
        timeout_val = float(timeout) if isinstance(timeout, (int, float)) else 60.0

        attrs: Dict[str, Any] = {
            "name": plugin_id,
            "version": version,
            "node_entry": str(entry_path),
            "node_workdir": str(install_dir),
            "node_export": export_name,
            "node_timeout_seconds": timeout_val,
        }

        class_name = self._proxy_class_name(plugin_id)
        proxy_cls = type(class_name, (NodeToolPlugin,), attrs)
        return proxy_cls, None

    def _proxy_class_name(self, plugin_id: str) -> str:
        cleaned = "".join(ch if ch.isalnum() else "_" for ch in plugin_id).strip("_")
        if not cleaned:
            cleaned = "Tool"
        # Ensure it is a valid identifier.
        if cleaned[0].isdigit():
            cleaned = f"Tool_{cleaned}"
        return f"NodeTool_{cleaned}"

    # ---------------------------------------------------------------------
    # Cache + build helpers
    # ---------------------------------------------------------------------

    def _ensure_cached_copy(
        self,
        cache_dir: Path,
        *,
        safe_id: str,
        revision: str,
        project_dir: Path,
    ) -> Path:
        target = cache_dir / "node" / f"{safe_id}@{revision}"
        if target.is_dir() and (target / "package.json").exists():
            return target

        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        shutil.copytree(
            project_dir,
            target,
            ignore=shutil.ignore_patterns(".git", "node_modules"),
        )
        logger.info("node_tool_cached", source=str(project_dir), install_dir=str(target))
        return target

    def _maybe_install_and_build(self, install_dir: Path, policy: Mapping[str, Any]) -> None:
        install_deps = bool(policy.get("node_install_deps", False))
        build = bool(policy.get("node_build", False))
        if not install_deps and not build:
            return

        pkg_json = install_dir / "package.json"
        if not pkg_json.is_file():
            return

        manager = policy.get("node_package_manager")
        pm = str(manager).strip() if isinstance(manager, str) and manager.strip() else "npm"
        allow_scripts = bool(policy.get("node_allow_install_scripts", False))
        env = dict(os.environ)
        if not allow_scripts:
            env.setdefault("npm_config_ignore_scripts", "true")

        lockfiles = {
            "npm": ("package-lock.json", "npm", ["npm", "ci"], ["npm", "install"]),
            "pnpm": ("pnpm-lock.yaml", "pnpm", ["pnpm", "install", "--frozen-lockfile"], ["pnpm", "install"]),
            "yarn": ("yarn.lock", "yarn", ["yarn", "install", "--frozen-lockfile"], ["yarn", "install"]),
        }
        lockfile, binary, locked_cmd, fallback_cmd = lockfiles.get(pm, lockfiles["npm"])
        has_lock = (install_dir / lockfile).is_file()

        if install_deps:
            cmd = locked_cmd if has_lock else fallback_cmd
            try:
                subprocess.check_call(cmd, cwd=str(install_dir), env=env)
            except Exception as exc:
                logger.error("node_tool_install_failed", err=str(exc), cwd=str(install_dir))

        if build:
            raw_cmd = policy.get("node_build_command")
            if isinstance(raw_cmd, str) and raw_cmd.strip():
                cmd = raw_cmd.strip().split()
            else:
                cmd = [binary, "run", "build"] if pm != "npm" else ["npm", "run", "build"]
            try:
                subprocess.check_call(cmd, cwd=str(install_dir), env=env)
            except Exception as exc:
                logger.error("node_tool_build_failed", err=str(exc), cwd=str(install_dir))

    # ---------------------------------------------------------------------
    # Descriptor parsing
    # ---------------------------------------------------------------------

    def _read_package_json(self, install_dir: Path) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        path = install_dir / "package.json"
        if not path.is_file():
            return None, {
                "type": "plugin_descriptor_missing",
                "detail": "package.json is required for directory-based node_tool plugins",
                "path": str(path),
            }
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            return None, {
                "type": "plugin_descriptor_invalid",
                "detail": f"Invalid package.json: {exc}",
                "path": str(path),
            }
        if not isinstance(raw, dict):
            return None, {
                "type": "plugin_descriptor_invalid",
                "detail": "package.json must be a JSON object",
                "path": str(path),
            }
        return raw, None

    def _read_agent_tools(self, pkg_json: Mapping[str, Any]) -> List[Dict[str, Any]]:
        agent = pkg_json.get("agent")
        if not isinstance(agent, dict):
            return []

        tools = agent.get("tools")
        if tools is None:
            return []

        out: List[Dict[str, Any]] = []
        if isinstance(tools, list):
            for item in tools:
                if isinstance(item, str) and item.strip():
                    out.append({"id": pkg_json.get("name"), "entry": item.strip()})
                elif isinstance(item, dict):
                    entry = item.get("entry")
                    if isinstance(entry, str) and entry.strip():
                        out.append(
                            {
                                "id": item.get("id"),
                                "entry": entry.strip(),
                                "export": item.get("export"),
                            }
                        )
        return out

    # ---------------------------------------------------------------------
    # Path + fingerprint helpers
    # ---------------------------------------------------------------------

    def _resolve_base_dir(self, path: str, policy: Mapping[str, Any]) -> Path:
        base_dir = policy.get("base_dir")
        base_path = Path(os.path.expanduser(path))
        if not base_path.is_absolute() and isinstance(base_dir, str) and base_dir:
            base_path = Path(base_dir) / base_path
        return base_path.resolve()

    def _fingerprint_git(self, base: Path, project_dir: Path) -> Optional[str]:
        try:
            repo_root = subprocess.check_output(
                ["git", "-C", str(base), "rev-parse", "--show-toplevel"]
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
            commit = (
                subprocess.check_output(
                    ["git", "-C", str(repo_root_path), "rev-list", "-1", "HEAD", "--", scope]
                )
                .decode()
                .strip()
            )
            if not commit:
                return None
        except Exception:
            return None

        try:
            status = (
                subprocess.check_output(
                    ["git", "-C", str(repo_root_path), "status", "--porcelain", "--", scope]
                )
                .decode()
                .strip()
            )
        except Exception:
            status = ""

        status_hash = hashlib.sha256(status.encode("utf-8", errors="ignore")).hexdigest()
        return f"git:{commit}:{status_hash}:{scope}"

    def _fingerprint_files(self, project_dir: Path) -> str:
        hasher = hashlib.sha256()

        def _ignore_dir(name: str) -> bool:
            return name in {
                ".git",
                "node_modules",
                ".cache",
                "dist",
                "build",
                ".pytest_cache",
                ".mypy_cache",
            }

        for root, dirs, files in os.walk(project_dir):
            dirs[:] = [d for d in dirs if not _ignore_dir(d)]
            rel_root = os.path.relpath(root, project_dir)
            for filename in sorted(files):
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

    def _safe_id(self, url: str) -> str:
        base = url.rstrip("/").split("/")[-1]
        if base.endswith(".git"):
            base = base[:-4]
        return base or "node_tool"

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


__all__ = ["NodeToolSource"]
