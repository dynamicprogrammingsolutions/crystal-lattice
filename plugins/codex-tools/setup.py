from __future__ import annotations

from pathlib import Path

from setuptools import setup


def _shared_dependency() -> str:
    sibling = (Path(__file__).resolve().parents[1] / "tool-compat-shared").resolve()
    return f"tool-compat-shared @ file://{sibling}"


def _mcp_shared_dependency() -> str:
    sibling = (Path(__file__).resolve().parents[1] / "mcp-shared").resolve()
    return f"mcp-shared @ file://{sibling}"


def _skill_shared_dependency() -> str:
    sibling = (Path(__file__).resolve().parents[1] / "skill-shared").resolve()
    return f"skill-shared @ file://{sibling}"


setup(
    install_requires=[
        _shared_dependency(),
        _mcp_shared_dependency(),
        _skill_shared_dependency(),
    ]
)