from __future__ import annotations

from pathlib import Path

import pytest

tomllib = pytest.importorskip("tomllib")


def test_terminal_app_distribution_and_console_script_metadata() -> None:
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    metadata = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

    assert metadata["project"]["name"] == "crystal-lattice-cli"
    assert (
        metadata["project"]["scripts"]["crystal-lattice"]
        == "agent_terminal_app.__main__:main"
    )
    assert "pyinstaller>=6.0" in metadata["project"]["optional-dependencies"]["binary"]
    assert (
        "runtime_layout.json"
        in metadata["tool"]["setuptools"]["package-data"]["agent_terminal_app"]
    )
