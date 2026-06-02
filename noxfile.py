from __future__ import annotations

import nox


def _build_runtime_package(session: nox.Session) -> None:
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
    session.run("python", "scripts/build_crystal_lattice_python_runtime_package.py")


@nox.session(python=False)
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
