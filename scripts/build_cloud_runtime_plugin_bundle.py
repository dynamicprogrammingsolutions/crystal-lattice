#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from build_plugin_packaging_support import copy_local_project_sources
from build_plugin_packaging_support import copytree_sanitized
from build_plugin_packaging_support import discover_builtin_plugin_resource_paths
from build_plugin_packaging_support import discover_selected_bundled_plugin_names
from build_plugin_packaging_support import is_python_project
from build_plugin_packaging_support import resolve_local_project_names
from build_plugin_packaging_support import stage_cloud_runtime_plugin_bundle
from build_plugin_packaging_support import stage_preinstalled_plugin_metadata
from build_plugin_packaging_support import stage_preinstalled_plugins


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Stage preinstalled plugin metadata/resources for the cloud runtime "
            "and write a local-project requirements file for wheel building."
        )
    )
    parser.add_argument("--plugins-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--local-project-prefix",
        default=None,
        help=(
            "Prefix used in local-projects.txt. Defaults to the resolved "
            "--plugins-root path."
        ),
    )
    args = parser.parse_args()

    stage_cloud_runtime_plugin_bundle(
        plugins_root=args.plugins_root,
        selected_config=args.config,
        output=args.output,
        local_project_prefix=args.local_project_prefix,
    )


if __name__ == "__main__":
    main()