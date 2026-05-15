from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping


_ENV_PLACEHOLDER_RE = re.compile(r"\$\{env:([^}]+)\}")


@dataclass(frozen=True)
class RuntimeLayout:
    schema_version: int
    layout: str
    manifest_path: Path
    bundle_paths: Mapping[str, str]
    user_paths: Mapping[str, str]

    @property
    def manifest_dir(self) -> Path:
        return self.manifest_path.parent

    @property
    def builtin_plugins(self) -> Path:
        return self.bundle_path("builtin_plugins")

    @property
    def default_config_template(self) -> Path:
        return self.bundle_path("default_config_template")

    @property
    def config_examples(self) -> Path:
        return self.bundle_path("config_examples")

    @property
    def root_system_messages(self) -> Path:
        return self.bundle_path("root_system_messages")

    def bundle_path(self, name: str) -> Path:
        return _resolve_bundle_path(self.manifest_dir, self.bundle_paths[name])

    def user_path(self, name: str) -> Path:
        return _resolve_user_path(self.user_paths[name])

    def env_overrides(self) -> dict[str, str]:
        return {
            "BUILTIN_PLUGINS": str(self.builtin_plugins),
        }

    def to_resolved_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "layout": self.layout,
            "manifest_path": str(self.manifest_path),
            "bundle_paths": {
                key: str(self.bundle_path(key)) for key in sorted(self.bundle_paths)
            },
            "user_paths": {
                key: str(self.user_path(key)) for key in sorted(self.user_paths)
            },
            "env_overrides": self.env_overrides(),
        }


def load_runtime_layout(manifest_path: str | Path | None = None) -> RuntimeLayout:
    path = _resolve_manifest_path(manifest_path)
    data = json.loads(path.read_text(encoding="utf-8"))

    schema_version = data.get("schema_version")
    if schema_version != 1:
        raise RuntimeError(
            f"Unsupported runtime layout schema version: {schema_version!r}"
        )

    layout = data.get("layout")
    bundle_paths = data.get("bundle_paths")
    user_paths = data.get("user_paths")
    if not isinstance(layout, str) or not layout:
        raise RuntimeError("Runtime layout manifest must define a non-empty layout")
    if not isinstance(bundle_paths, dict):
        raise RuntimeError("Runtime layout manifest must define bundle_paths")
    if not isinstance(user_paths, dict):
        raise RuntimeError("Runtime layout manifest must define user_paths")

    required_bundle_paths = {
        "builtin_plugins",
        "default_config_template",
        "config_examples",
        "root_system_messages",
    }
    required_user_paths = {
        "local_config",
        "home_config",
        "default_config",
        "default_sessions_dir",
    }
    _require_string_paths(bundle_paths, required_bundle_paths, "bundle_paths")
    _require_string_paths(user_paths, required_user_paths, "user_paths")

    return RuntimeLayout(
        schema_version=schema_version,
        layout=layout,
        manifest_path=path,
        bundle_paths={key: str(value) for key, value in bundle_paths.items()},
        user_paths={key: str(value) for key, value in user_paths.items()},
    )


def _resolve_manifest_path(manifest_path: str | Path | None) -> Path:
    if manifest_path is not None:
        return Path(manifest_path).expanduser().resolve()

    override = os.environ.get("CRYSTAL_RUNTIME_LAYOUT")
    if override:
        return Path(override).expanduser().resolve()

    return (Path(__file__).resolve().parent / "runtime_layout.json").resolve()


def _require_string_paths(
    paths: Mapping[str, Any], required: set[str], section: str
) -> None:
    missing = sorted(required.difference(paths))
    if missing:
        raise RuntimeError(
            f"Runtime layout {section} missing required keys: {', '.join(missing)}"
        )
    invalid = sorted(
        key for key, value in paths.items() if not isinstance(value, str) or not value
    )
    if invalid:
        raise RuntimeError(
            f"Runtime layout {section} values must be non-empty strings: {', '.join(invalid)}"
        )


def _resolve_bundle_path(base_dir: Path, raw_path: str) -> Path:
    expanded = _expand_env_placeholders(raw_path)
    path = Path(expanded).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (base_dir / path).resolve()


def _resolve_user_path(raw_path: str) -> Path:
    expanded = _expand_env_placeholders(raw_path)
    path = Path(os.path.expandvars(expanded)).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (Path.cwd() / path).resolve()


def _expand_env_placeholders(raw_path: str) -> str:
    def replace(match: re.Match[str]) -> str:
        return os.environ.get(match.group(1), "")

    return _ENV_PLACEHOLDER_RE.sub(replace, raw_path)
