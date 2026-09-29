from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import os
import sys
from pathlib import Path


def parse_args() -> tuple[Path, str, list[str], list[str], list[str]]:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--runtime-module", action="append", default=[])
    parser.add_argument("--forbid-distribution", action="append", default=[])
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    pytest_args = list(args.pytest_args)
    if pytest_args and pytest_args[0] == "--":
        pytest_args.pop(0)
    return (
        Path(args.archive).resolve(),
        str(args.module),
        list(args.runtime_module),
        list(args.forbid_distribution),
        pytest_args,
    )


class BundleProvenancePlugin:
    def __init__(self, archive: Path, module_names: list[str]) -> None:
        self.archive_prefix = f"{archive}/"
        self.module_names = tuple(module_names)

    def assert_origins(self) -> None:
        for name, module in list(sys.modules.items()):
            if not any(
                name == root or name.startswith(f"{root}.")
                for root in self.module_names
            ):
                continue
            module_file = str(getattr(module, "__file__", ""))
            if module_file and not module_file.startswith(self.archive_prefix):
                raise AssertionError(
                    f"{name} did not import from the embedded archive: {module_file}"
                )

    def pytest_runtest_setup(self, item: object) -> None:
        _ = item
        self.assert_origins()

    def pytest_runtest_teardown(self, item: object, nextitem: object) -> None:
        _ = (item, nextitem)
        self.assert_origins()

    def pytest_sessionfinish(self, session: object, exitstatus: int) -> None:
        _ = (session, exitstatus)
        self.assert_origins()


def main() -> int:
    archive, module_name, runtime_modules, forbidden_distributions, pytest_args = (
        parse_args()
    )
    if not archive.is_file():
        raise SystemExit(f"Embedded application archive does not exist: {archive}")

    archive_text = str(archive)
    source_fragments = {
        str(
            (
                Path(__file__).resolve().parents[1]
                / "plugins"
                / project
                / "src"
            ).resolve()
        )
        for project in (
            "reference-openai-compatible-provider",
            "openai_responses",
            "openrouter",
            "anthropic-compatible",
        )
    }
    sys.path[:] = [
        entry
        for entry in sys.path
        if not entry or str(Path(entry).resolve()) not in source_fragments
    ]
    sys.path.insert(0, archive_text)
    os.environ["CRYSTAL_EMBEDDED_PROVIDER_BUNDLE"] = archive_text

    module_names = [module_name, *runtime_modules]
    for requested_module in module_names:
        module = importlib.import_module(requested_module)
        module_file = str(getattr(module, "__file__", ""))
        if not module_file.startswith(f"{archive_text}/"):
            raise SystemExit(
                f"{requested_module} did not import from embedded archive: {module_file}"
            )
        print(f"embedded-bundle-import:{requested_module}:{module_file}")

    for distribution_name in forbidden_distributions:
        try:
            installed = importlib.metadata.distribution(distribution_name)
        except importlib.metadata.PackageNotFoundError:
            continue
        raise SystemExit(
            f"Test overlay unexpectedly installed {distribution_name}: "
            f"{installed.locate_file('')}"
        )

    import pytest

    provenance = BundleProvenancePlugin(archive, module_names)
    provenance.assert_origins()
    return int(pytest.main(pytest_args, plugins=[provenance]))


if __name__ == "__main__":
    raise SystemExit(main())