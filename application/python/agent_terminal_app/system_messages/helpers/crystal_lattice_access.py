import json
import os
from pathlib import Path


CONFIG = globals().get("CONFIG", {})

_CLI_VARIABLES = (
    "CRYSTAL_LATTICE_CLI_ARGV_JSON",
    "CRYSTAL_LATTICE_CLI_COMMAND",
    "CRYSTAL_LATTICE_CONFIG",
    "CRYSTAL_LATTICE_SESSIONS",
    "CRYSTAL_LATTICE_DOCS",
    "CRYSTAL_LATTICE_DOCS_URL",
)
_FULL_VARIABLES = (
    "CRYSTAL_LATTICE_PYTHON",
    "CRYSTAL_LATTICE_PYTHON_API_MODULE",
)


def access_value(name: str) -> str:
    if name not in {*_CLI_VARIABLES, *_FULL_VARIABLES}:
        return ""
    return os.environ.get(name, "")


def _cli_argv() -> list[str] | None:
    try:
        value = json.loads(os.environ.get("CRYSTAL_LATTICE_CLI_ARGV_JSON", ""))
    except Exception:
        return None
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        return None
    return value


def _missing_cli_values() -> list[str]:
    missing = [name for name in _CLI_VARIABLES if not os.environ.get(name)]
    argv = _cli_argv()
    if argv is None:
        missing.append("CRYSTAL_LATTICE_CLI_ARGV_JSON (invalid JSON argv)")
    elif not Path(argv[0]).is_file():
        missing.append("CRYSTAL_LATTICE_CLI_ARGV_JSON (executable missing)")
    path_checks = (
        ("CRYSTAL_LATTICE_CONFIG", Path.is_file),
        ("CRYSTAL_LATTICE_SESSIONS", Path.is_dir),
        ("CRYSTAL_LATTICE_DOCS", Path.is_dir),
    )
    for name, predicate in path_checks:
        value = os.environ.get(name)
        if value and not predicate(Path(value)):
            missing.append(f"{name} (path missing)")
    return sorted(set(missing))


def _missing_full_values() -> list[str]:
    missing = [name for name in _FULL_VARIABLES if not os.environ.get(name)]
    python = os.environ.get("CRYSTAL_LATTICE_PYTHON")
    if python and not Path(python).is_file():
        missing.append("CRYSTAL_LATTICE_PYTHON (executable missing)")
    if os.environ.get("CRYSTAL_LATTICE_PYTHON_API_MODULE") not in {
        None,
        "",
        "agent_terminal_app",
    }:
        missing.append("CRYSTAL_LATTICE_PYTHON_API_MODULE (unsupported)")
    return sorted(set(missing))


def _requested() -> bool:
    return bool(CONFIG.get("include_crystal_lattice_access", False))


def include_crystal_lattice_access() -> bool:
    return _requested() and not _missing_cli_values() and not _missing_full_values()


def include_crystal_lattice_cli_access() -> bool:
    return _requested() and not _missing_cli_values() and bool(_missing_full_values())


def get_ui_elements() -> list[dict]:
    cli_missing = _missing_cli_values()
    full_missing = _missing_full_values()
    if cli_missing:
        label = "Include Crystal Lattice Access Guidance (unavailable)"
        description = (
            "Unavailable because these runtime values are missing or invalid: "
            + ", ".join(cli_missing)
        )
        disabled = True
        default = False
    elif full_missing:
        label = "Include Crystal Lattice Access Guidance (CLI only)"
        description = (
            "CLI-only guidance is available. Python SDK guidance is unavailable "
            "because: " + ", ".join(full_missing)
        )
        disabled = False
        default = _requested()
    else:
        label = "Include Crystal Lattice Access Guidance"
        description = "CLI and Python SDK guidance are available."
        disabled = False
        default = _requested()
    return [
        {
            "ui_type": "config",
            "type": "checkbox",
            "key": "include_crystal_lattice_access",
            "label": label,
            "description": description,
            "disabled": disabled,
            "default": default,
        }
    ]
