from __future__ import annotations

from pathlib import Path

from setuptools import setup


def _shared_dependency() -> str:
    sibling = (Path(__file__).resolve().parents[1] / "tool-compat-shared").resolve()
    return f"tool-compat-shared @ file://{sibling}"


setup(install_requires=[_shared_dependency()])