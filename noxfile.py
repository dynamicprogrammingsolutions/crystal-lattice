from __future__ import annotations

import os
from pathlib import Path

import nox  # type: ignore[import-not-found]


nox.options.sessions = ["build_bundle", "install_prod_local"]


def _build_runtime_package(session: nox.Session) -> None:
    session.install(
        "-e",
        "core/python",
        "-e",
        "application/python[binary]",
        "uv",
    )
    runtime = _resolve_runtime_python(session)
    session.run(
        "python",
        "scripts/build_crystal_lattice_python_runtime_package.py",
        "--python-runtime",
        str(runtime),
    )


def _resolve_runtime_python(session: nox.Session) -> Path:
    configured = os.environ.get("CRYSTAL_PYTHON_RUNTIME")
    if configured:
        runtime = Path(configured).expanduser().resolve()
        if not runtime.is_dir():
            session.error(f"CRYSTAL_PYTHON_RUNTIME is not a directory: {runtime}")
        return runtime

    install_dir = (Path(session.create_tmp()) / "uv-python").resolve()
    session.run(
        "uv",
        "python",
        "install",
        "--install-dir",
        str(install_dir),
        "--python-preference",
        "only-managed",
        "3.11",
    )
    candidates = sorted(
        path
        for path in install_dir.iterdir()
        if path.is_dir() and not path.is_symlink() and not path.name.startswith(".")
    )
    if len(candidates) != 1:
        found = ", ".join(path.name for path in candidates) or "<none>"
        session.error(
            f"Expected one uv-managed Python runtime under {install_dir}, found: "
            f"{found}"
        )
    return candidates[0]


@nox.session()
def build_bundle(session: nox.Session) -> None:
    """Build the current-platform production bundled-Python archive."""
    _build_runtime_package(session)


@nox.session(python=False)
def build_optimized_bundle(session: nox.Session) -> None:
    """Build the current-platform optimized PyInstaller archive."""
    session.run(
        "python",
        "-m",
        "pip",
        "install",
        "-e",
        "core/python",
        "-e",
        "application/python[binary]",
    )
    session.run("python", "scripts/build_crystal_lattice_binary.py")


@nox.session(python=False)
def install_prod_local(session: nox.Session) -> None:
    """Smoke-test and install the current-platform production package locally."""
    session.run("python", "scripts/install_crystal_lattice_archive.py")


@nox.session(python=False)
def install_dev_local(session: nox.Session) -> None:
    """Install an editable-source dev command named crystal-lattice-cli-dev."""
    session.run("python", "scripts/install_crystal_lattice_cli_dev.py")
