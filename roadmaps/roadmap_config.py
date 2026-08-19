"""Self-contained named roadmap and MCP configuration loading."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = Path(__file__).with_name("config.json")
ENV_REFERENCE_RE = re.compile(r"\$\{env:([A-Za-z_][A-Za-z0-9_]*)\}")


class RoadmapConfigError(ValueError):
    """Raised when roadmap or MCP configuration is invalid."""


@dataclass(frozen=True)
class MCPServerDefinition:
    command: str
    args: tuple[str, ...]
    env: dict[str, str]
    cwd: str | None
    startup_timeout_seconds: int | None
    tool_timeout_seconds: int | None


@dataclass(frozen=True)
class MCPSettings:
    server: str
    definition: MCPServerDefinition


@dataclass(frozen=True)
class RoadmapTarget:
    key: str
    csv_path: Path
    spreadsheet_id: str
    spreadsheet_title: str
    sheet: str


@dataclass(frozen=True)
class Registry:
    path: Path
    env_file: Path
    mcp: MCPSettings
    roadmaps: dict[str, RoadmapTarget]


def configured_registry_path(path: Path | None = None) -> Path:
    if path is not None:
        return path.expanduser().resolve()
    override = os.environ.get("ROADMAP_CONFIG")
    if override:
        return Path(override).expanduser().resolve()
    return DEFAULT_CONFIG.resolve()


def _load_dotenv(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise RoadmapConfigError(
            f"roadmap environment file is missing: {path}; "
            "copy roadmaps/.env.example to roadmaps/.env"
        )
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            raise RoadmapConfigError(
                f"{path}:{line_number}: expected NAME=value"
            )
        key, value = line.split("=", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            raise RoadmapConfigError(
                f"{path}:{line_number}: invalid environment variable name"
            )
        values[key] = value.strip().strip('"').strip("'")
    return values


def _resolved_environment(path: Path) -> dict[str, str]:
    values = _load_dotenv(path)
    values.update(os.environ)
    return values


def _resolve_env_references(value: str, environment: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        resolved = environment.get(name)
        if resolved is None or resolved == "":
            raise RoadmapConfigError(
                f"roadmap environment variable {name} is required"
            )
        return resolved

    return ENV_REFERENCE_RE.sub(replace, value)


def _required_string(
    value: Any,
    *,
    field: str,
    environment: dict[str, str],
) -> str:
    if not isinstance(value, str) or not value:
        raise RoadmapConfigError(f"{field} must be a non-empty string")
    resolved = _resolve_env_references(value, environment)
    if not resolved:
        raise RoadmapConfigError(f"{field} resolved to an empty string")
    return resolved


def _positive_int(value: Any) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    return None


def _load_mcp_definition(
    raw_mcp: dict[str, Any],
    *,
    environment: dict[str, str],
) -> MCPSettings:
    server = _required_string(
        raw_mcp.get("server"),
        field="mcp.server",
        environment=environment,
    )
    command = _required_string(
        raw_mcp.get("command"),
        field="mcp.command",
        environment=environment,
    )
    raw_args = raw_mcp.get("args", [])
    if not isinstance(raw_args, list):
        raise RoadmapConfigError("mcp.args must be an array")
    args = tuple(
        _required_string(
            str(value),
            field="mcp.args item",
            environment=environment,
        )
        for value in raw_args
    )
    raw_env = raw_mcp.get("env", {})
    if not isinstance(raw_env, dict):
        raise RoadmapConfigError("mcp.env must be an object")
    mcp_env: dict[str, str] = {}
    for key, value in raw_env.items():
        if not isinstance(key, str):
            raise RoadmapConfigError("mcp.env keys must be strings")
        mcp_env[key] = _required_string(
            value,
            field=f"mcp.env.{key}",
            environment=environment,
        )
    cwd_value = raw_mcp.get("cwd")
    cwd = (
        _required_string(
            cwd_value,
            field="mcp.cwd",
            environment=environment,
        )
        if cwd_value is not None
        else None
    )
    definition = MCPServerDefinition(
        command=command,
        args=args,
        env=mcp_env,
        cwd=cwd,
        startup_timeout_seconds=_positive_int(
            raw_mcp.get("startup_timeout_seconds")
        ),
        tool_timeout_seconds=_positive_int(
            raw_mcp.get("tool_timeout_seconds")
        ),
    )
    return MCPSettings(server=server, definition=definition)


def load_registry(path: Path | None = None) -> Registry:
    config_path = configured_registry_path(path)
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RoadmapConfigError(
            f"cannot read roadmap config {config_path}: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise RoadmapConfigError(
            f"invalid JSON in roadmap config {config_path}: {exc}"
        ) from exc

    if data.get("version") != 1:
        raise RoadmapConfigError("roadmap config version must be 1")

    env_file_value = os.environ.get(
        "ROADMAP_ENV",
        data.get("env_file", ".env"),
    )
    if not isinstance(env_file_value, str) or not env_file_value:
        raise RoadmapConfigError("env_file must be a non-empty string")
    env_file = Path(env_file_value).expanduser()
    if not env_file.is_absolute():
        env_file = config_path.parent / env_file
    env_file = env_file.resolve()
    environment = _resolved_environment(env_file)

    raw_mcp = data.get("mcp")
    if not isinstance(raw_mcp, dict):
        raise RoadmapConfigError("roadmap config mcp must be an object")
    mcp = _load_mcp_definition(raw_mcp, environment=environment)

    raw_roadmaps = data.get("roadmaps")
    if not isinstance(raw_roadmaps, dict) or not raw_roadmaps:
        raise RoadmapConfigError("roadmaps must be a non-empty object")

    targets: dict[str, RoadmapTarget] = {}
    for key, raw_target in raw_roadmaps.items():
        if not isinstance(key, str) or not key:
            raise RoadmapConfigError("roadmap keys must be non-empty strings")
        if not isinstance(raw_target, dict):
            raise RoadmapConfigError(f"roadmaps.{key} must be an object")
        csv_value = _required_string(
            raw_target.get("csv"),
            field=f"roadmaps.{key}.csv",
            environment=environment,
        )
        targets[key] = RoadmapTarget(
            key=key,
            csv_path=(config_path.parent / csv_value).resolve(),
            spreadsheet_id=_required_string(
                raw_target.get("spreadsheet_id"),
                field=f"roadmaps.{key}.spreadsheet_id",
                environment=environment,
            ),
            spreadsheet_title=_required_string(
                raw_target.get("spreadsheet_title"),
                field=f"roadmaps.{key}.spreadsheet_title",
                environment=environment,
            ),
            sheet=_required_string(
                raw_target.get("sheet"),
                field=f"roadmaps.{key}.sheet",
                environment=environment,
            ),
        )

    return Registry(
        path=config_path,
        env_file=env_file,
        mcp=mcp,
        roadmaps=targets,
    )


def resolve_csv_argument(value: str, registry: Registry) -> Path:
    target = registry.roadmaps.get(value)
    if target is not None:
        return target.csv_path
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    if path.suffix == ".csv" or path.exists():
        return path.resolve()
    available = ", ".join(sorted(registry.roadmaps))
    raise RoadmapConfigError(
        f"unknown roadmap key {value!r}; available keys: {available}"
    )


def resolve_target(key: str, registry: Registry) -> RoadmapTarget:
    try:
        return registry.roadmaps[key]
    except KeyError as exc:
        available = ", ".join(sorted(registry.roadmaps))
        raise RoadmapConfigError(
            f"unknown roadmap key {key!r}; available keys: {available}"
        ) from exc


def load_mcp_server(settings: MCPSettings) -> MCPServerDefinition:
    definition = settings.definition
    env = dict(definition.env)
    credentials_path = env.get("GOOGLE_APPLICATION_CREDENTIALS")
    if credentials_path:
        credential_file = Path(credentials_path).expanduser().resolve()
        if not credential_file.is_file():
            raise RoadmapConfigError(
                "configured Google application credentials file is missing"
            )
        env["GOOGLE_APPLICATION_CREDENTIALS"] = str(credential_file)
    return MCPServerDefinition(
        command=definition.command,
        args=definition.args,
        env=env,
        cwd=definition.cwd,
        startup_timeout_seconds=definition.startup_timeout_seconds,
        tool_timeout_seconds=definition.tool_timeout_seconds,
    )


def unpinned_npm_packages(definition: MCPServerDefinition) -> tuple[str, ...]:
    return tuple(arg for arg in definition.args if arg.endswith("@latest"))