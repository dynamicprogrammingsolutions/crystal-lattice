from __future__ import annotations

import subprocess
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_cloud_orchestrator_source_bundle_includes_runtime_build_helper(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "source.tar.gz"

    subprocess.run(
        [
            "bash",
            "-lc",
            (
                "source cloud-orchestrator/deploy/lib/source_bundle.sh && "
                f"create_cloud_orchestrator_source_bundle {bundle!s} {ROOT!s}"
            ),
        ],
        cwd=ROOT,
        check=True,
    )

    with tarfile.open(bundle, "r:gz") as archive:
        names = set(archive.getnames())

    assert "scripts/build_cloud_runtime_plugin_bundle.py" in names
    assert "cloud-orchestrator/runtime/python/Dockerfile" in names