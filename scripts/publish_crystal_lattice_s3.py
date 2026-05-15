#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
import sys
import tempfile

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[1]
APP_PYPROJECT = ROOT / "application" / "python" / "pyproject.toml"
DEFAULT_BUCKET = "crystal-lattice-downloads-874087778966"
DEFAULT_PREFIX = "crystal-lattice-cli"
DEFAULT_REGION = "us-east-1"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Publish Crystal Lattice release assets to the public S3 download bucket."
    )
    parser.add_argument("--bucket", default=DEFAULT_BUCKET)
    parser.add_argument("--prefix", default=DEFAULT_PREFIX)
    parser.add_argument("--region", default=DEFAULT_REGION)
    parser.add_argument(
        "--assets-dir",
        type=Path,
        default=ROOT / "dist" / "crystal-lattice",
        help="directory containing release archives",
    )
    parser.add_argument("--version", default=None, help="version without tag prefix")
    args = parser.parse_args()

    version = args.version or read_project_version()
    tag = f"crystal-lattice-cli-v{version}"
    assets_dir = args.assets_dir.expanduser().resolve()
    assets = expected_assets(assets_dir, version)

    s3_base = f"s3://{args.bucket}/{args.prefix}"
    upload(
        ROOT / "scripts" / "install.sh", f"{s3_base}/install.sh", "text/x-shellscript"
    )
    for asset in assets:
        content_type = (
            "application/zip" if asset.suffix == ".zip" else "application/gzip"
        )
        upload(asset, f"{s3_base}/{asset.name}", content_type)

    with tempfile.TemporaryDirectory(prefix="crystal-lattice-s3-publish-") as temp_dir:
        latest = Path(temp_dir) / "latest.txt"
        latest.write_text(tag + "\n", encoding="utf-8")
        upload(latest, f"{s3_base}/latest.txt", "text/plain")

    public_base_url = (
        f"https://{args.bucket}.s3.{args.region}.amazonaws.com/{args.prefix}"
    )
    print(f"Published {tag} to {public_base_url}")


def read_project_version() -> str:
    metadata = tomllib.loads(APP_PYPROJECT.read_text(encoding="utf-8"))
    version = metadata["project"]["version"]
    if not isinstance(version, str) or not version:
        raise RuntimeError(f"Could not read project.version from {APP_PYPROJECT}")
    return version


def expected_assets(assets_dir: Path, version: str) -> list[Path]:
    names = [
        f"crystal-lattice-cli-v{version}-darwin-amd64.tar.gz",
        f"crystal-lattice-cli-v{version}-darwin-arm64.tar.gz",
        f"crystal-lattice-cli-v{version}-linux-amd64.tar.gz",
        f"crystal-lattice-cli-v{version}-windows-amd64.zip",
    ]
    assets = [assets_dir / name for name in names]
    missing = [path for path in assets if not path.is_file()]
    if missing:
        missing_list = "\n".join(str(path) for path in missing)
        raise RuntimeError(f"Missing release assets:\n{missing_list}")
    return assets


def upload(source: Path, destination: str, content_type: str) -> None:
    run(
        [
            "aws",
            "s3",
            "cp",
            str(source),
            destination,
            "--content-type",
            content_type,
        ]
    )


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=str(ROOT), check=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
