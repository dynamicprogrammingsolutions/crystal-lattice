from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    import tomli as tomllib


def test_dev_extra_includes_application_test_dependencies() -> None:
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    metadata = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

    dev_dependencies = metadata["project"]["optional-dependencies"]["dev"]

    assert "fastapi" in dev_dependencies
    assert "httpx>=0.27.0" in dev_dependencies
