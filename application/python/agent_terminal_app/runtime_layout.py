from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Mapping


_ENV_PLACEHOLDER_RE = re.compile(r"\$\{env:([^}]+)\}")
_APPLICATION_DOCS_URL = (
    "https://docs.crystallattice.dev/packages/application-python/"
    "headless-agent-runs/"
)


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

    @property
    def application_docs(self) -> Path | None:
        return self.optional_bundle_path("application_docs")

    @property
    def cloud_runtime_build_context(self) -> Path | None:
        return self.optional_bundle_path("cloud_runtime_build_context")

    @property
    def cloud_runtime_dockerfile(self) -> Path | None:
        return self.optional_bundle_path("cloud_runtime_dockerfile")

    @property
    def python_executable(self) -> Path | None:
        return self.optional_bundle_path("python_executable")

    @property
    def bundle_script(self) -> Path | None:
        return self.optional_bundle_path("bundle_script")

    @property
    def preinstalled_plugin_manifest(self) -> Path | None:
        return self.optional_bundle_path("preinstalled_plugin_manifest")

    def bundle_path(self, name: str) -> Path:
        return _resolve_bundle_path(self.manifest_dir, self.bundle_paths[name])

    def optional_bundle_path(self, name: str) -> Path | None:
        raw_path = self.bundle_paths.get(name)
        if not isinstance(raw_path, str) or not raw_path:
            return None
        return _resolve_bundle_path(self.manifest_dir, raw_path)

    def user_path(self, name: str) -> Path:
        return _resolve_user_path(self.user_paths[name])

    def env_overrides(self) -> dict[str, str]:
        values = {
            "BUILTIN_PLUGINS": str(self.builtin_plugins),
            "CRYSTAL_LATTICE_SYSTEM_MESSAGES": str(self.root_system_messages),
        }
        cloud_runtime_context = self.cloud_runtime_build_context
        if cloud_runtime_context is None and self.layout == "source":
            cloud_runtime_context = (
                self.manifest_path.parents[3]
                / "build"
                / f"cloud-runtime-source-context-{os.getpid()}"
            )
        if cloud_runtime_context is not None:
            values["CLOUD_RUNTIME_BUILD_CONTEXT"] = str(cloud_runtime_context)
        python_executable = self.python_executable
        if python_executable is not None:
            values["CRYSTAL_PLUGIN_PYTHON"] = str(python_executable)
        preinstalled_plugin_manifest = self.preinstalled_plugin_manifest
        if preinstalled_plugin_manifest is not None:
            values["CRYSTAL_PREINSTALLED_PLUGIN_MANIFEST"] = str(
                preinstalled_plugin_manifest
            )
        return values

    def application_env_overrides(
        self,
        *,
        config_path: str | Path,
        session_root: str | Path,
        env_overrides: Mapping[str, str] | None = None,
    ) -> dict[str, str]:
        """Return runtime-owned config and external-project access values."""

        config = Path(config_path).expanduser().resolve()
        sessions = Path(session_root).expanduser().resolve()
        values = self.env_overrides()
        if env_overrides is not None:
            values.update({key: str(value) for key, value in env_overrides.items()})

        python_executable: Path | None
        if self.layout == "bundled":
            python_executable = None
            cli_argv = [str(Path(sys.executable).resolve())]
        else:
            python_executable = self.python_executable or Path(sys.executable).resolve()
            cli_argv = [
                str(python_executable),
                "-m",
                "agent_terminal_app",
            ]

        cli_argv.extend(
            [
                "--config",
                str(config),
                "--sessions-dir",
                str(sessions),
            ]
        )
        values.update(
            {
                "CRYSTAL_LATTICE_CLI_ARGV_JSON": json.dumps(cli_argv),
                "CRYSTAL_LATTICE_CONFIG": str(config),
                "CRYSTAL_LATTICE_SESSIONS": str(sessions),
                "CRYSTAL_LATTICE_DOCS_URL": _APPLICATION_DOCS_URL,
            }
        )

        if python_executable is not None:
            values["CRYSTAL_LATTICE_PYTHON"] = str(python_executable)
            values["CRYSTAL_LATTICE_PYTHON_API_MODULE"] = "agent_terminal_app"

        application_docs = self.application_docs
        if application_docs is not None and application_docs.is_dir():
            values["CRYSTAL_LATTICE_DOCS"] = str(application_docs)

        return values

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
