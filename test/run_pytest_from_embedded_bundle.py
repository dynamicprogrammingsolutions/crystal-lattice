from __future__ import annotations

import argparse
import importlib
import os
import sys
from pathlib import Path


def parse_args() -> tuple[Path, str, list[str]]:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    pytest_args = list(args.pytest_args)
    if pytest_args and pytest_args[0] == "--":
        pytest_args.pop(0)
    return Path(args.archive).resolve(), str(args.module), pytest_args


def main() -> int:
    archive, module_name, pytest_args = parse_args()
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

    module = importlib.import_module(module_name)
    module_file = str(getattr(module, "__file__", ""))
    if not module_file.startswith(f"{archive_text}/"):
        raise SystemExit(
            f"{module_name} did not import from embedded archive: {module_file}"
        )
    print(f"embedded-bundle-import:{module_name}:{module_file}")

    import pytest

    return int(pytest.main(pytest_args))


if __name__ == "__main__":
    raise SystemExit(main())