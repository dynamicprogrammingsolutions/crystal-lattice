#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import tempfile


MOBILE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = (
    MOBILE_ROOT
    / "ios"
    / "CrystalLatticePythonRuntime"
    / "Resources"
    / "crystal_lattice_app.zip"
)

SMOKE_PROGRAM = r"""
import importlib
import json
from pathlib import Path
import sys

archive = str(Path(sys.argv[1]).resolve())
runtime_root = str(Path(sys.argv[2]).resolve())
sys.path[:] = [
    archive,
    *[
        entry
        for entry in sys.path
        if entry
        and "site-packages" not in entry
        and "dist-packages" not in entry
    ],
]

module_names = (
    "jsonpath",
    "agent_app",
    "chatgpt_auth_app",
    "crystal_lattice_mobile_runtime",
)
modules = {
    module_name: importlib.import_module(module_name)
    for module_name in module_names
}
archive_prefix = f"{archive}/"
for module_name, module in modules.items():
    module_file = str(getattr(module, "__file__", ""))
    if not module_file.startswith(archive_prefix):
        raise RuntimeError(
            f"{module_name} did not import from the embedded archive: {module_file}"
        )
    print(f"embedded-application-import:{module_name}:{module_file}")

runtime = modules["crystal_lattice_mobile_runtime"]
request = {
    "method": "POST",
    "path": "/actions",
    "body": {
        "plugin": "chatgpt_auth",
        "action_id": "check_status",
        "inputs": {},
    },
}
response = json.loads(runtime.execute_json(json.dumps(request), runtime_root))
if response.get("status") != 200:
    raise RuntimeError(f"Embedded application action failed: {response}")
data = response.get("data")
if not isinstance(data, dict) or data.get("status") != "ok":
    raise RuntimeError(f"Embedded application action returned invalid data: {response}")
result = data.get("result")
display = result.get("display") if isinstance(result, dict) else None
if not isinstance(display, dict) or not display.get("title"):
    raise RuntimeError(f"Embedded application action returned no display: {response}")
print(f"embedded-application-action:{display['title']}")
runtime.shutdown_runtime()
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    archive = args.archive.resolve()
    if not archive.is_file():
        raise SystemExit(
            f"Embedded application archive does not exist: {archive}. "
            "Build it before running the application bundle smoke."
        )

    with tempfile.TemporaryDirectory(
        prefix="crystal-embedded-application-smoke-"
    ) as temporary:
        subprocess.run(
            [
                sys.executable,
                "-S",
                "-c",
                SMOKE_PROGRAM,
                str(archive),
                str(Path(temporary) / "runtime"),
            ],
            cwd=temporary,
            check=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())