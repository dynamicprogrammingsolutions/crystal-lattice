#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from build_crystal_lattice_binary import prepare_cloud_runtime_build_context


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare the plugin-owned Crystal Lattice cloud runtime Docker build context."
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="config file used to select preinstalled plugin runtime assets",
    )
    args = parser.parse_args()
    prepare_cloud_runtime_build_context(
        args.output.expanduser().resolve(),
        selected_config=args.config.expanduser().resolve() if args.config else None,
    )


if __name__ == "__main__":
    main()
