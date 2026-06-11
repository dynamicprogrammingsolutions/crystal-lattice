from __future__ import annotations

import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent


def repo_root() -> Path:
    return REPO_ROOT


def repo_env_path() -> Path:
    return REPO_ROOT / ".env"


def load_repo_root_env() -> Path | None:
    """Load the repo-root .env without overwriting existing process env values."""

    env_path = repo_env_path()
    if not env_path.exists():
        return None

    for raw_line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = value.strip().strip('"').strip("'")

    return env_path


def get_repo_env(name: str, default: str = "") -> str:
    load_repo_root_env()
    value = os.environ.get(name)
    if isinstance(value, str) and value:
        return value
    return default