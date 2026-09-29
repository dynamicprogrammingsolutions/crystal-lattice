from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import tempfile
import tomllib
import venv
import zipfile
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MOBILE_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = (
    MOBILE_ROOT
    / "ios"
    / "CrystalLatticePythonRuntime"
    / "Resources"
    / "crystal_lattice_app.zip"
)
BOOTSTRAP = REPO_ROOT / "test" / "run_pytest_from_embedded_bundle.py"
PROVIDED_DISTRIBUTIONS = frozenset({"agent-core"})
FORBIDDEN_ARCHIVE_PREFIXES = ("pytest/", "_pytest/", "dotenv/", "tests/")


@dataclass(frozen=True)
class ProviderSuite:
    project: str
    module: str
    distribution: str
    has_non_api: bool

    @property
    def root(self) -> Path:
        return REPO_ROOT / "plugins" / self.project

    @property
    def tests(self) -> Path:
        return self.root / "tests"

    def marked_test_files(self) -> list[Path]:
        selected: list[Path] = []
        for path in sorted(self.tests.glob("test_*.py")):
            source = path.read_text("utf-8")
            if "provider_integration" not in source:
                continue
            if "AgentApplication" in source:
                raise RuntimeError(
                    f"Provider bundle test imports AgentApplication: {path}"
                )
            selected.append(path)
        return selected


SUITES = (
    ProviderSuite(
        "openai_responses",
        "openai_responses_plugins",
        "openai_responses",
        False,
    ),
    ProviderSuite(
        "openrouter",
        "openrouter_plugins",
        "openrouter-plugins",
        True,
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=("default", "api"),
        nargs="?",
        default="default",
    )
    parser.add_argument("--provider", action="append", default=[])
    parser.add_argument("--archive", type=Path, default=ARCHIVE)
    return parser.parse_args()


def normalized_distribution_name(requirement: str) -> str:
    name = re.split(r"[<>=!~;\[ ]", requirement, maxsplit=1)[0]
    return name.strip().lower().replace("_", "-")


def dev_requirements(suite: ProviderSuite) -> list[str]:
    payload = tomllib.loads((suite.root / "pyproject.toml").read_text("utf-8"))
    configured = payload["project"]["optional-dependencies"]["dev"]
    return [
        requirement
        for requirement in configured
        if normalized_distribution_name(requirement) not in PROVIDED_DISTRIBUTIONS
    ]


def venv_python(environment_root: Path) -> Path:
    if os.name == "nt":
        return environment_root / "Scripts" / "python.exe"
    return environment_root / "bin" / "python"


def prepare_overlay(suite: ProviderSuite, environment_root: Path) -> Path:
    venv.EnvBuilder(with_pip=True, clear=True).create(environment_root)
    python = venv_python(environment_root)
    requirements = dev_requirements(suite)
    if requirements:
        subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                *requirements,
            ],
            cwd=REPO_ROOT,
            check=True,
        )
    return python


def archive_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def assert_archive_excludes_dev_content(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
    forbidden = [
        name
        for name in names
        if any(name.startswith(prefix) for prefix in FORBIDDEN_ARCHIVE_PREFIXES)
    ]
    if forbidden:
        raise RuntimeError(
            f"Prebuilt iOS provider archive contains dev/test content: {forbidden[:10]}"
        )


def pytest_marker(mode: str) -> str:
    if mode == "api":
        return (
            "provider_integration and integration and api "
            "and not slow_integration and not manual_integration"
        )
    return (
        "provider_integration and integration and not api "
        "and not slow_integration and not manual_integration"
    )


def run_suite(
    suite: ProviderSuite,
    *,
    archive: Path,
    mode: str,
    environment_root: Path,
) -> None:
    python = prepare_overlay(suite, environment_root)
    command = [
        str(python),
        str(BOOTSTRAP),
        "--archive",
        str(archive),
        "--module",
        suite.module,
        "--runtime-module",
        "agent_core",
        "--runtime-module",
        "requests",
        "--forbid-distribution",
        suite.distribution,
        "--",
        *(str(path) for path in suite.marked_test_files()),
        "-q",
        "--tb=short",
        "-m",
        pytest_marker(mode),
    ]
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def main() -> int:
    args = parse_args()
    archive = args.archive.resolve()
    if not archive.is_file():
        raise SystemExit(
            f"Prebuilt iOS provider archive does not exist: {archive}. "
            "Build it before running provider bundle tests."
        )

    requested = set(args.provider)
    selected = [
        suite
        for suite in SUITES
        if not requested or suite.project in requested
    ]
    if not selected:
        raise SystemExit("No embedded provider suites matched --provider")

    before = archive_digest(archive)
    assert_archive_excludes_dev_content(archive)
    print(f"embedded-provider-archive:{archive}")
    print(f"embedded-provider-archive-sha256:{before}")

    for suite in selected:
        if args.mode == "default" and not suite.has_non_api:
            continue
        with tempfile.TemporaryDirectory(
            prefix=f"crystal-{suite.project}-bundle-tests-"
        ) as temporary:
            run_suite(
                suite,
                archive=archive,
                mode=args.mode,
                environment_root=Path(temporary) / "venv",
            )

    after = archive_digest(archive)
    if after != before:
        raise SystemExit(
            f"Prebuilt iOS provider archive changed during tests: {before} -> {after}"
        )
    print(f"embedded-provider-archive-unchanged:{after}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())