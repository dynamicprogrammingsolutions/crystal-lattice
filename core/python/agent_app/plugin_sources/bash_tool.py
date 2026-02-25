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

from agent_core.tool_hosts.bash_tool_plugin import BashToolPlugin
from agent_core.utils import get_logger

from .types import PluginContext, PluginResolution


logger = get_logger("BashToolSource")


class BashToolSource:
    """Resolve bash tool plugins executed by ``bash``.

    Supported specs:
      - {"bash_tool": {"file": "./tool.bash"}}
      - {"bash_tool": {"path": "./dir"}}  (requires agent_plugin.json with bash_tools)
      - {"bash_tool": {"git": "https://...", "ref": "optional", "subdirectory": "optional"}}

    String shortcuts:
      - "bash:/abs/or/rel" (file or directory)
      - "bash+git:<url-or-local>[#<ref>]"
    """

    def supports(self, spec: Any) -> bool:
        if isinstance(spec, str):
            s = spec.strip()
            return s.startswith("bash:") or s.startswith("bash+git:")
        if isinstance(spec, dict):
            return isinstance(spec.get("bash_tool"), dict)
        return False

    def resolve(self, spec: Any, ctx: PluginContext) -> PluginResolution:
        if not bool(ctx.policy.get("allow_bash_tools", False)):
            return PluginResolution(
                classes=[],
                errors=[
                    {
                        "type": "plugin_install_error",
                        "detail": "Bash tool plugins are disabled by policy (set plugin_policy.allow_bash_tools: true)",
                        "path": spec,
                    }
                ],
            )

        if shutil.which("bash") is None:
            return PluginResolution(
                classes=[],
                errors=[
                    {
                        "type": "plugin_install_error",
                        "detail": "bash executable not available",
                        "path": spec,
                    }
                ],
            )

        if isinstance(spec, str):
            parsed, err = self._parse_string_spec(spec)
            if err is not None or parsed is None:
                return PluginResolution(
                    classes=[],
                    errors=[
                        err
                        or {
                            "type": "plugin_path_invalid",
                            "detail": "Invalid bash tool spec",
                            "path": spec,
                        }
                    ],
                )
            bash_spec = parsed
        elif isinstance(spec, dict) and isinstance(spec.get("bash_tool"), dict):
            bash_spec = dict(spec.get("bash_tool") or {})
        else:
            return PluginResolution(
                classes=[],
                errors=[
                    {
                        "type": "plugin_path_invalid",
                        "detail": "bash_tool spec must be a dict or a supported string shortcut",
                        "path": spec,
                    }
                ],
            )

        if "file" in bash_spec:
            return self._resolve_file(bash_spec, ctx)
        if "path" in bash_spec:
            return self._resolve_local_path(bash_spec, ctx)
        if "git" in bash_spec:
            return self._resolve_git(bash_spec, ctx)

        return PluginResolution(
            classes=[],
            errors=[
                {
                    "type": "plugin_path_invalid",
                    "detail": "bash_tool must include one of: file, path, git",
                    "path": spec,
                }
            ],
        )

    def _parse_string_spec(
        self, spec: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        s = spec.strip()
        if s.startswith("bash+git:"):
            url_ref = s[len("bash+git:") :]
            if "#" in url_ref:
                url, ref = url_ref.split("#", 1)
            else:
                url, ref = url_ref, None
            url = url.strip()
            if not url:
                return None, {
                    "type": "plugin_path_invalid",
                    "detail": "bash+git spec must include a URL/path",
                    "path": spec,
                }
            out: Dict[str, Any] = {"git": url}
            if isinstance(ref, str) and ref.strip():
                out["ref"] = ref.strip()
            return out, None

        if s.startswith("bash:"):
            raw_path = s[len("bash:") :].strip()
            if not raw_path:
                return None, {
                    "type": "plugin_path_invalid",
                    "detail": "bash: spec must include a path",
                    "path": spec,
                }
            return {"path": raw_path}, None

        return None, {
            "type": "plugin_path_invalid",
            "detail": "Unsupported bash tool shortcut; expected bash:<path> or bash+git:<url>[#ref]",
            "path": spec,
        }

    # ------------------------------------------------------------------
    # Local path
    # ------------------------------------------------------------------

    def _resolve_local_path(
        self, bash_spec: Mapping[str, Any], ctx: PluginContext
    ) -> PluginResolution:
        raw_path = bash_spec.get("path")
        if not isinstance(raw_path, str) or not raw_path.strip():
            return PluginResolution(
                classes=[],
                errors=[
                    {
                        "type": "plugin_path_invalid",
                        "detail": "bash_tool.path must be a non-empty string",
                        "path": raw_path,
                    }
                ],
            )

        base = self._resolve_base_dir(raw_path, ctx.policy)
        if not base.exists():
            return PluginResolution(
                classes=[],
                errors=[
                    {
                        "type": "plugin_path_invalid",
                        "detail": f"Local path {str(base)!r} does not exist",
                        "path": raw_path,
                    }
                ],
            )

        if base.is_file():
            overrides = dict(bash_spec)
            overrides.pop("path", None)
            overrides.setdefault("file", raw_path)
            return self._resolve_file(overrides, ctx)

        subdir = bash_spec.get("subdirectory")
        project_dir = (
            (base / subdir).resolve() if isinstance(subdir, str) and subdir.strip() else base
        )
        if not project_dir.is_dir():
            return PluginResolution(
                classes=[],
                errors=[
                    {
                        "type": "plugin_path_invalid",
                        "detail": f"Project directory {str(project_dir)!r} does not exist",
                        "path": str(project_dir),
                    }
                ],
            )

        git_fp = self._fingerprint_git(base, project_dir)
        fp = git_fp or self._fingerprint_files(project_dir)
        revision = hashlib.sha256(fp.encode("utf-8", errors="ignore")).hexdigest()
        safe_id = base.name or "bash_tool"

        install_dir = ctx.cache_dir / "bash" / f"{safe_id}@{revision}"
        install_dir = self._ensure_cached_copy(install_dir, project_dir, expects_manifest=True)
        return self._classes_from_manifest(install_dir, ctx.policy)

    # ------------------------------------------------------------------
    # Git
    # ------------------------------------------------------------------

    def _resolve_git(self, bash_spec: Mapping[str, Any], ctx: PluginContext) -> PluginResolution:
        url = bash_spec.get("git")
        if not isinstance(url, str) or not url.strip():
            return PluginResolution(
                classes=[],
                errors=[
                    {
                        "type": "plugin_path_invalid",
                        "detail": "bash_tool.git must be a non-empty string",
                        "path": url,
                    }
                ],
            )

        url = self._resolve_local_git_path(url, ctx.policy)
        remote_err = self._enforce_remote_policy(url, ctx.policy)
        if remote_err is not None:
            return PluginResolution(classes=[], errors=[remote_err])

        ref = bash_spec.get("ref")
        ref_value = ref.strip() if isinstance(ref, str) and ref.strip() else None

        src_root = ctx.cache_dir / "src"
        src_root.mkdir(parents=True, exist_ok=True)
        tmp_clone = Path(tempfile.mkdtemp(prefix="bash_tool_clone_", dir=str(src_root)))

        try:
            try:
                subprocess.check_call(["git", "clone", url, str(tmp_clone)])
            except Exception as exc:
                return PluginResolution(
                    classes=[],
                    errors=[
                        {
                            "type": "plugin_install_error",
                            "detail": f"git clone failed: {exc}",
                            "path": url,
                        }
                    ],
                )

            if ref_value:
                try:
                    subprocess.check_call(["git", "-C", str(tmp_clone), "checkout", ref_value])
                except Exception as exc:
                    return PluginResolution(
                        classes=[],
                        errors=[
                            {
                                "type": "plugin_install_error",
                                "detail": f"git checkout {ref_value} failed: {exc}",
                                "path": url,
                            }
                        ],
                    )

            try:
                commit = (
                    subprocess.check_output(["git", "-C", str(tmp_clone), "rev-parse", "HEAD"])
                    .decode()
                    .strip()
                )
            except Exception:
                commit = "unknown"

            subdir = bash_spec.get("subdirectory")
            project_dir = (
                (tmp_clone / subdir).resolve()
                if isinstance(subdir, str) and subdir.strip()
                else tmp_clone
            )
            if not project_dir.is_dir():
                return PluginResolution(
                    classes=[],
                    errors=[
                        {
                            "type": "plugin_path_invalid",
                            "detail": f"Project directory {str(project_dir)!r} does not exist",
                            "path": str(project_dir),
                        }
                    ],
                )

            safe_id = self._safe_id(url)
            install_dir = ctx.cache_dir / "bash" / f"{safe_id}@{commit}"
            install_dir = self._ensure_cached_copy(install_dir, project_dir, expects_manifest=True)
            return self._classes_from_manifest(install_dir, ctx.policy)
        finally:
            try:
                shutil.rmtree(tmp_clone, ignore_errors=True)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Single file
    # ------------------------------------------------------------------

    def _resolve_file(self, bash_spec: Mapping[str, Any], ctx: PluginContext) -> PluginResolution:
        raw_file = bash_spec.get("file")
        if not isinstance(raw_file, str) or not raw_file.strip():
            return PluginResolution(
                classes=[],
                errors=[
                    {
                        "type": "plugin_path_invalid",
                        "detail": "bash_tool.file must be a non-empty string",
                        "path": raw_file,
                    }
                ],
            )

        path = self._resolve_base_dir(raw_file, ctx.policy)
        if not path.is_file():
            return PluginResolution(
                classes=[],
                errors=[
                    {
                        "type": "plugin_path_invalid",
                        "detail": f"Tool file {str(path)!r} does not exist",
                        "path": raw_file,
                    }
                ],
            )

        try:
            content = path.read_bytes()
        except Exception as exc:
            return PluginResolution(
                classes=[],
                errors=[
                    {
                        "type": "plugin_path_invalid",
                        "detail": f"Could not read tool file: {exc}",
                        "path": raw_file,
                    }
                ],
            )

        revision = hashlib.sha256(content).hexdigest()
        safe_id = Path(raw_file).stem or "bash_tool"

        install_dir = ctx.cache_dir / "bash" / f"{safe_id}@{revision}"
        install_dir.mkdir(parents=True, exist_ok=True)
        dst = install_dir / path.name
        if not dst.exists():
            shutil.copy2(path, dst)

        schema, err = self._read_tool_schema(dst, ctx.policy)
        if err is not None or schema is None:
            return PluginResolution(
                classes=[],
                errors=[
                    err
                    or {
                        "type": "plugin_descriptor_invalid",
                        "detail": "Invalid tool schema",
                        "path": str(dst),
                    }
                ],
            )

        cls, cls_err = self._make_proxy_class(install_dir, dst, schema, ctx.policy)
        if cls_err is not None or cls is None:
            return PluginResolution(
                classes=[],
                errors=[
                    cls_err
                    or {
                        "type": "plugin_install_error",
                        "detail": "Could not build bash tool proxy",
                        "path": str(dst),
                    }
                ],
            )

        return PluginResolution(classes=[cls], errors=[])

    # ------------------------------------------------------------------
    # Manifest + schema helpers
    # ------------------------------------------------------------------

    def _classes_from_manifest(
        self, install_dir: Path, policy: Mapping[str, Any]
    ) -> PluginResolution:
        manifest_path = install_dir / "agent_plugin.json"
        if not manifest_path.is_file():
            return PluginResolution(
                classes=[],
                errors=[
                    {
                        "type": "plugin_descriptor_missing",
                        "detail": "Missing agent_plugin.json",
                        "path": str(manifest_path),
                    }
                ],
            )

        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return PluginResolution(
                classes=[],
                errors=[
                    {
                        "type": "plugin_descriptor_invalid",
                        "detail": f"Could not parse agent_plugin.json: {exc}",
                        "path": str(manifest_path),
                    }
                ],
            )

        if not isinstance(raw, dict):
            return PluginResolution(
                classes=[],
                errors=[
                    {
                        "type": "plugin_descriptor_invalid",
                        "detail": "agent_plugin.json must be a JSON object",
                        "path": str(manifest_path),
                    }
                ],
            )

        tools_raw = raw.get("bash_tools")
        if not isinstance(tools_raw, list) or not tools_raw:
            return PluginResolution(
                classes=[],
                errors=[
                    {
                        "type": "plugin_descriptor_invalid",
                        "detail": "agent_plugin.json must include a non-empty 'bash_tools' list",
                        "path": str(manifest_path),
                    }
                ],
            )

        classes: List[type] = []
        errors: List[Dict[str, Any]] = []
        for item in tools_raw:
            if not isinstance(item, dict):
                continue
            file_rel = item.get("file")
            if not isinstance(file_rel, str) or not file_rel.strip():
                errors.append(
                    {
                        "type": "plugin_descriptor_invalid",
                        "detail": "bash_tools entry missing 'file'",
                        "path": str(manifest_path),
                    }
                )
                continue

            tool_path = (install_dir / file_rel).resolve()
            try:
                tool_path.relative_to(install_dir.resolve())
            except Exception:
                errors.append(
                    {
                        "type": "plugin_descriptor_invalid",
                        "detail": "bash_tools file must be within the plugin directory",
                        "path": str(tool_path),
                    }
                )
                continue

            if not tool_path.is_file():
                errors.append(
                    {
                        "type": "plugin_path_invalid",
                        "detail": f"Tool file {str(tool_path)!r} does not exist",
                        "path": str(tool_path),
                    }
                )
                continue

            schema, err = self._read_tool_schema(tool_path, policy)
            if err is not None or schema is None:
                errors.append(
                    err
                    or {
                        "type": "plugin_descriptor_invalid",
                        "detail": "Invalid tool schema",
                        "path": str(tool_path),
                    }
                )
                continue

            cls, cls_err = self._make_proxy_class(install_dir, tool_path, schema, policy)
            if cls_err is not None or cls is None:
                errors.append(
                    cls_err
                    or {
                        "type": "plugin_install_error",
                        "detail": "Could not build bash tool proxy",
                        "path": str(tool_path),
                    }
                )
                continue
            classes.append(cls)

        return PluginResolution(classes=classes, errors=errors)

    def _read_tool_schema(
        self, tool_path: Path, policy: Mapping[str, Any]
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        timeout = policy.get("bash_timeout_seconds")
        timeout_val = float(timeout) if isinstance(timeout, (int, float)) else 60.0

        cmd = ["bash", str(tool_path), "schema"]
        try:
            cp = subprocess.run(
                cmd,
                cwd=str(tool_path.parent),
                capture_output=True,
                text=True,
                timeout=timeout_val,
            )
        except subprocess.TimeoutExpired:
            return None, {
                "type": "plugin_descriptor_invalid",
                "detail": "Tool schema timed out",
                "path": str(tool_path),
            }
        except Exception as exc:
            return None, {
                "type": "plugin_descriptor_invalid",
                "detail": f"Could not invoke schema: {exc}",
                "path": str(tool_path),
            }

        if cp.returncode != 0:
            stderr = (cp.stderr or "").strip()
            detail = f"schema failed (exit code {cp.returncode})"
            if stderr:
                detail = f"{detail}: {stderr}"
            return None, {
                "type": "plugin_descriptor_invalid",
                "detail": detail,
                "path": str(tool_path),
            }

        try:
            raw = json.loads(cp.stdout)
        except Exception as exc:
            return None, {
                "type": "plugin_descriptor_invalid",
                "detail": f"schema did not return valid JSON: {exc}",
                "path": str(tool_path),
            }

        if not isinstance(raw, dict):
            return None, {
                "type": "plugin_descriptor_invalid",
                "detail": "schema must return a JSON object",
                "path": str(tool_path),
            }

        validated, err = self._validate_schema(raw, tool_path)
        if err is not None or validated is None:
            return None, err

        args_mode = validated.get("args_mode")
        if args_mode == "json" and shutil.which("jq") is None:
            return None, {
                "type": "plugin_install_error",
                "detail": "args_mode=json requires jq, but jq was not found",
                "path": str(tool_path),
            }

        return validated, None

    def _validate_schema(
        self, raw: Dict[str, Any], tool_path: Path
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        plugin_id = raw.get("id")
        if not isinstance(plugin_id, str) or not plugin_id.strip():
            return None, {
                "type": "plugin_descriptor_invalid",
                "detail": "schema.id must be a non-empty string",
                "path": str(tool_path),
            }

        version = raw.get("version")
        if not isinstance(version, str) or not version.strip():
            return None, {
                "type": "plugin_descriptor_invalid",
                "detail": "schema.version must be a non-empty string",
                "path": str(tool_path),
            }

        args_mode = raw.get("args_mode")
        if args_mode not in {"flags", "positional", "json"}:
            return None, {
                "type": "plugin_descriptor_invalid",
                "detail": "schema.args_mode must be one of: flags, positional, json",
                "path": str(tool_path),
            }

        tools = raw.get("tools")
        if not isinstance(tools, list) or not tools:
            return None, {
                "type": "plugin_descriptor_invalid",
                "detail": "schema.tools must be a non-empty list",
                "path": str(tool_path),
            }

        if len(tools) != 1:
            return None, {
                "type": "plugin_descriptor_invalid",
                "detail": "v1 requires exactly one tool schema per bash file",
                "path": str(tool_path),
            }

        schema0 = tools[0]
        if not isinstance(schema0, dict):
            return None, {
                "type": "plugin_descriptor_invalid",
                "detail": "tool schema entry must be an object",
                "path": str(tool_path),
            }

        fn = schema0.get("function")
        name = None
        if isinstance(fn, dict):
            name = fn.get("name")
        if not isinstance(name, str) or not name.strip():
            return None, {
                "type": "plugin_descriptor_invalid",
                "detail": "tool schema must include function.name",
                "path": str(tool_path),
            }

        if name.strip() != plugin_id.strip():
            return None, {
                "type": "plugin_descriptor_invalid",
                "detail": "v1 requires schema.id to match tools[0].function.name",
                "path": str(tool_path),
            }

        positional = raw.get("positional")
        pos_entries: List[Dict[str, Any]] = []
        if args_mode == "positional":
            if not isinstance(positional, list) or not positional:
                return None, {
                    "type": "plugin_descriptor_invalid",
                    "detail": "args_mode=positional requires a non-empty positional list",
                    "path": str(tool_path),
                }
            props = self._tool_schema_properties(schema0)
            for entry in positional:
                if not isinstance(entry, dict):
                    return None, {
                        "type": "plugin_descriptor_invalid",
                        "detail": "positional entries must be objects",
                        "path": str(tool_path),
                    }
                entry_name = entry.get("name")
                if not isinstance(entry_name, str) or not entry_name.strip():
                    return None, {
                        "type": "plugin_descriptor_invalid",
                        "detail": "positional entry missing name",
                        "path": str(tool_path),
                    }
                if props is not None and entry_name.strip() not in props:
                    return None, {
                        "type": "plugin_descriptor_invalid",
                        "detail": f"positional name {entry_name!r} not present in tool schema properties",
                        "path": str(tool_path),
                    }
                required_val = entry.get("required")
                if required_val is not None and not isinstance(required_val, bool):
                    return None, {
                        "type": "plugin_descriptor_invalid",
                        "detail": "positional.required must be a boolean when present",
                        "path": str(tool_path),
                    }
                default_val = entry.get("default") if "default" in entry else None
                if default_val is not None and not isinstance(default_val, (str, int, float, bool)):
                    return None, {
                        "type": "plugin_descriptor_invalid",
                        "detail": "positional.default must be a scalar when present",
                        "path": str(tool_path),
                    }
                pos_entries.append(dict(entry))

        return {
            "id": plugin_id.strip(),
            "version": version.strip(),
            "args_mode": args_mode,
            "tools": tools,
            "positional": pos_entries,
        }, None

    def _tool_schema_properties(self, schema0: Mapping[str, Any]) -> Optional[set[str]]:
        fn = schema0.get("function")
        if not isinstance(fn, dict):
            return None
        params = fn.get("parameters")
        if not isinstance(params, dict):
            return None
        props = params.get("properties")
        if not isinstance(props, dict):
            return None
        out: set[str] = set()
        for k in props.keys():
            if isinstance(k, str) and k.strip():
                out.add(k.strip())
        return out

    def _make_proxy_class(
        self,
        install_dir: Path,
        tool_path: Path,
        schema: Mapping[str, Any],
        policy: Mapping[str, Any],
    ) -> Tuple[Optional[type], Optional[Dict[str, Any]]]:
        plugin_id = str(schema.get("id") or "bash_tool")
        version = str(schema.get("version") or "unknown")

        args_mode = schema.get("args_mode")
        tools = schema.get("tools")
        positional = schema.get("positional")

        if args_mode not in {"flags", "positional", "json"}:
            return None, {
                "type": "plugin_descriptor_invalid",
                "detail": "Invalid args_mode",
                "path": str(tool_path),
            }
        if not isinstance(tools, list) or not tools:
            return None, {
                "type": "plugin_descriptor_invalid",
                "detail": "Missing tools list",
                "path": str(tool_path),
            }

        timeout = policy.get("bash_timeout_seconds")
        timeout_val = float(timeout) if isinstance(timeout, (int, float)) else 60.0
        err_timeout = policy.get("bash_error_timeout_seconds")
        err_timeout_val = float(err_timeout) if isinstance(err_timeout, (int, float)) else 5.0
        stream_stderr = bool(policy.get("bash_stream_stderr", False))

        attrs: Dict[str, Any] = {
            "name": plugin_id,
            "version": version,
            "bash_entry": str(tool_path.resolve()),
            "bash_schema": dict(schema),
            "bash_tools": tools,
            "bash_args_mode": str(args_mode),
            "bash_positional": positional if isinstance(positional, list) else [],
            "bash_timeout_seconds": timeout_val,
            "bash_error_timeout_seconds": err_timeout_val,
            "bash_stream_stderr": stream_stderr,
        }

        class_name = self._proxy_class_name(plugin_id)
        proxy_cls = type(class_name, (BashToolPlugin,), attrs)
        return proxy_cls, None

    def _proxy_class_name(self, plugin_id: str) -> str:
        cleaned = "".join(ch if ch.isalnum() else "_" for ch in plugin_id).strip("_")
        if not cleaned:
            cleaned = "Tool"
        if cleaned[0].isdigit():
            cleaned = f"Tool_{cleaned}"
        return f"BashTool_{cleaned}"

    # ------------------------------------------------------------------
    # Cache + fingerprint helpers
    # ------------------------------------------------------------------

    def _ensure_cached_copy(
        self, install_dir: Path, project_dir: Path, *, expects_manifest: bool
    ) -> Path:
        marker = install_dir / "agent_plugin.json" if expects_manifest else install_dir
        if install_dir.is_dir() and marker.exists():
            return install_dir

        install_dir.parent.mkdir(parents=True, exist_ok=True)
        if install_dir.exists():
            shutil.rmtree(install_dir, ignore_errors=True)
        shutil.copytree(
            project_dir,
            install_dir,
            ignore=shutil.ignore_patterns(".git", "__pycache__"),
        )
        logger.info("bash_tool_cached", source=str(project_dir), install_dir=str(install_dir))
        return install_dir

    def _resolve_base_dir(self, path: str, policy: Mapping[str, Any]) -> Path:
        base_dir = policy.get("base_dir")
        base_path = Path(os.path.expanduser(path))
        if not base_path.is_absolute() and isinstance(base_dir, str) and base_dir:
            base_path = Path(base_dir) / base_path
        return base_path.resolve()

    def _fingerprint_git(self, base: Path, project_dir: Path) -> Optional[str]:
        try:
            repo_root = (
                subprocess.check_output(
                    ["git", "-C", str(base), "rev-parse", "--show-toplevel"],
                    stderr=subprocess.DEVNULL,
                )
                .decode()
                .strip()
            )
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
                    [
                        "git",
                        "-C",
                        str(repo_root_path),
                        "rev-list",
                        "-1",
                        "HEAD",
                        "--",
                        scope,
                    ],
                    stderr=subprocess.DEVNULL,
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
                    [
                        "git",
                        "-C",
                        str(repo_root_path),
                        "status",
                        "--porcelain",
                        "--",
                        scope,
                    ],
                    stderr=subprocess.DEVNULL,
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
                "__pycache__",
                ".pytest_cache",
                ".mypy_cache",
                "build",
                "dist",
                ".venv",
                "venv",
            }

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
                hasher.update(
                    str(getattr(st, "st_mtime_ns", int(st.st_mtime * 1e9))).encode("utf-8")
                )
                hasher.update(str(st.st_size).encode("utf-8"))
        return hasher.hexdigest()

    def _safe_id(self, url: str) -> str:
        base = url.rstrip("/").split("/")[-1]
        if base.endswith(".git"):
            base = base[:-4]
        return base or "bash_tool"

    def _resolve_local_git_path(self, url: str, policy: Mapping[str, Any]) -> str:
        base_dir = policy.get("base_dir")
        is_remote = (
            url.startswith("http://")
            or url.startswith("https://")
            or url.startswith("ssh://")
            or "@" in url
        )
        if is_remote:
            return url
        try:
            url_path = Path(os.path.expanduser(url))
            if not url_path.is_absolute() and isinstance(base_dir, str) and base_dir:
                url_path = Path(base_dir) / url_path
            return str(url_path.resolve())
        except Exception:
            return url

    def _enforce_remote_policy(
        self, url: str, policy: Mapping[str, Any]
    ) -> Optional[Dict[str, Any]]:
        allow_remote = bool(policy.get("allow_remote", False))
        allowed_hosts = policy.get("allowed_git_hosts") or []
        is_remote = (
            url.startswith("http://")
            or url.startswith("https://")
            or url.startswith("ssh://")
            or "@" in url
        )
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


__all__ = ["BashToolSource"]
