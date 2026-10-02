from __future__ import annotations

import json
from pathlib import Path

import pytest

from embedded_tools_shared import (
    WorkspacePathError,
    resolve_workspace_boundaries,
    resolve_workspace_root,
)


def test_workspace_descendant_is_created_inside_fixed_root(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    selected = workspace / "projects" / "alpha"

    root = resolve_workspace_root(
        {
            "workspace_root": str(workspace),
            "allowed_paths": [str(workspace)],
            "working_directory": str(selected),
        }
    )

    assert root == selected.resolve()
    assert root.is_dir()
    assert resolve_workspace_boundaries(
        {
            "workspace_root": str(workspace),
            "allowed_paths": [str(tmp_path / "ignored")],
        }
    ) == (workspace.resolve(),)


def test_workspace_rejects_sibling_and_traversal_selection(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    sibling = tmp_path / "sibling"
    sibling.mkdir()

    for selected in (sibling, workspace / ".." / "sibling"):
        with pytest.raises(WorkspacePathError, match="escapes"):
            resolve_workspace_root(
                {
                    "workspace_root": str(workspace),
                    "working_directory": str(selected),
                }
            )


def test_workspace_rejects_symlink_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()
    link = workspace / "linked"
    link.symlink_to(outside, target_is_directory=True)

    with pytest.raises(WorkspacePathError, match="escapes"):
        resolve_workspace_root(
            {
                "workspace_root": str(workspace),
                "working_directory": str(link),
            }
        )


def test_workspace_without_boundary_keeps_legacy_behavior(tmp_path: Path) -> None:
    selected = tmp_path / "legacy"

    assert resolve_workspace_root({"working_directory": str(selected)}) == (
        selected.resolve()
    )


def test_workspace_accepts_only_registered_external_grants(tmp_path: Path) -> None:
    internal = tmp_path / "internal"
    external = tmp_path / "external"
    unregistered = tmp_path / "unregistered"
    internal.mkdir()
    external.mkdir()
    unregistered.mkdir()
    config = {
        "workspace_root": str(internal),
        "working_directory": str(external),
        "workspace_grants": json.dumps(
            {
                "grant-1": {
                    "path": str(external),
                    "available": True,
                }
            }
        ),
    }

    assert resolve_workspace_root(config) == external.resolve()

    with pytest.raises(WorkspacePathError, match="escapes"):
        resolve_workspace_root(
            {
                **config,
                "working_directory": str(unregistered),
            }
        )