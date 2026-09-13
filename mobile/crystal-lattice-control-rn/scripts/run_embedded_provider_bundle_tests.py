from __future__ import annotations

import argparse
import subprocess
import sys
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


@dataclass(frozen=True)
class ProviderSuite:
    project: str
    module: str
    integration_marker: str

    @property
    def tests(self) -> Path:
        return REPO_ROOT / "plugins" / self.project / "tests"


SUITES = (
    ProviderSuite(
        "reference-openai-compatible-provider",
        "reference_openai_compatible_provider",
        "integration and not api and not slow_integration",
    ),
    ProviderSuite(
        "openai_responses",
        "openai_responses_plugins",
        "integration and not api and not slow_integration and not manual_integration",
    ),
    ProviderSuite(
        "openrouter",
        "openrouter_plugins",
        "integration and not api and not slow_integration",
    ),
    ProviderSuite(
        "anthropic-compatible",
        "anthropic_plugins",
        "integration and not api and not slow_integration",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=("default", "api", "manual"),
        nargs="?",
        default="default",
    )
    parser.add_argument("--provider", action="append", default=[])
    return parser.parse_args()


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def pytest_command(suite: ProviderSuite, marker: str) -> list[str]:
    return [
        sys.executable,
        str(BOOTSTRAP),
        "--archive",
        str(ARCHIVE),
        "--module",
        suite.module,
        "--",
        str(suite.tests),
        "-q",
        "-m",
        marker,
    ]


def main() -> int:
    args = parse_args()
    run(
        [
            sys.executable,
            str(MOBILE_ROOT / "scripts" / "prepare_ios_python_runtime.py"),
        ]
    )
    selected = [
        suite
        for suite in SUITES
        if not args.provider or suite.project in set(args.provider)
    ]
    if not selected:
        raise SystemExit("No embedded provider suites matched --provider")

    for suite in selected:
        if args.mode == "default":
            run(pytest_command(suite, "not integration"))
            run(pytest_command(suite, suite.integration_marker))
        elif args.mode == "api":
            run(
                pytest_command(
                    suite,
                    "integration and api and not slow_integration and not manual_integration",
                )
            )
        else:
            run(pytest_command(suite, "manual_integration"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())