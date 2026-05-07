from __future__ import annotations

from pathlib import Path

from setuptools import setup


def _app_dependency() -> str:
    sibling = (Path(__file__).resolve().parents[1] / "gemini-compaction-app").resolve()
    return f"gemini-compaction-app @ file://{sibling}"


setup(install_requires=[_app_dependency()])