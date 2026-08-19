"""Self-contained named roadmap and Google Sheets configuration loading."""

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
    """Raised when roadmap or Google Sheets configuration is invalid."""


@dataclass(frozen=True)
class GoogleSheetsSettings:
    credentials_file: Path
    timeout_seconds: int


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
    google_sheets: GoogleSheetsSettings
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


def _positive_int(value: Any, *, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    raise RoadmapConfigError("timeout_seconds must be a positive integer")


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

    raw_sheets = data.get("google_sheets")
    if not isinstance(raw_sheets, dict):
        raise RoadmapConfigError("google_sheets must be an object")
    credentials_value = _required_string(
        raw_sheets.get("credentials_file"),
        field="google_sheets.credentials_file",
        environment=environment,
    )
    credentials_file = Path(credentials_value).expanduser().resolve()
    if not credentials_file.is_file():
        raise RoadmapConfigError(
            "configured Google application credentials file is missing"
        )
    google_sheets = GoogleSheetsSettings(
        credentials_file=credentials_file,
        timeout_seconds=_positive_int(
            raw_sheets.get("timeout_seconds"),
            default=30,
        ),
    )

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
        google_sheets=google_sheets,
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