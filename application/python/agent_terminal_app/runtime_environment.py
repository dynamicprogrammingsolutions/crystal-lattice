from __future__ import annotations

import os
from pathlib import Path


def collect_additional_dotenv_values(
    config_path: Path,
    *,
    working_directory: Path | None = None,
) -> dict[str, str]:
    """Collect config-related dotenv values without mutating ``os.environ``."""

    try:
        from dotenv import dotenv_values, find_dotenv  # type: ignore[import-not-found]
    except Exception:
        return {}

    collected: dict[str, str] = {}
    working_root = (working_directory or Path.cwd()).expanduser().resolve()

    def collect_file(path: Path) -> None:
        try:
            values = dotenv_values(str(path))
        except Exception:
            return
        for key, value in values.items():
            if not isinstance(key, str) or not key:
                continue
            if not isinstance(value, str):
                continue
            if key in os.environ or key in collected:
                continue
            collected[key] = value

    try:
        config_dir = config_path.expanduser().resolve().parent
    except Exception:
        config_dir = config_path.parent
    config_env = config_dir / ".env"
    if config_env.is_file():
        collect_file(config_env)

    local_env = working_root / ".crystal" / ".env"
    if local_env.is_file():
        collect_file(local_env)

    user_env = Path.home() / ".crystal" / ".env"
    if user_env.is_file():
        collect_file(user_env)

    try:
        if working_directory is None:
            standard_env = find_dotenv(filename=".env", usecwd=True)
        else:
            candidate = working_root
            standard_env = ""
            while True:
                env_path = candidate / ".env"
                if env_path.is_file():
                    standard_env = str(env_path)
                    break
                if candidate.parent == candidate:
                    break
                candidate = candidate.parent
    except Exception:
        standard_env = ""
    if standard_env:
        collect_file(Path(standard_env))

    return collected


__all__ = ["collect_additional_dotenv_values"]
