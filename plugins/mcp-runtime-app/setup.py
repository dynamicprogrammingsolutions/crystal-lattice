from __future__ import annotations

from pathlib import Path

from setuptools import setup


def _mcp_shared_dependency() -> str:
    sibling = (Path(__file__).resolve().parents[1] / "mcp-shared").resolve()
    return f"mcp-shared @ file://{sibling}"


setup(
    install_requires=[
        "httpx>=0.24.0",
        "mcp>=1.0.0",
        _mcp_shared_dependency(),
    ]
)
