from __future__ import annotations

from pathlib import Path

from embedded_workspace_settings import EmbeddedWorkspaceSettingsFeature


def test_feature_lists_workspace_root_and_existing_descendants(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    selected = workspace / "projects" / "alpha"
    selected.mkdir(parents=True)
    (workspace / "projects" / "beta").mkdir()
    (workspace / ".hidden").mkdir()

    elements = EmbeddedWorkspaceSettingsFeature().get_ui_elements(
        {
            "workspace_root": str(workspace),
            "allowed_paths": [str(workspace)],
            "working_directory": str(selected),
        }
    )

    assert len(elements) == 1
    element = elements[0]
    assert element["type"] == "directory"
    assert element["key"] == "working_directory"
    assert element["options"] == [
        {"value": str(workspace.resolve()), "label": "Workspace root"},
        {
            "value": str((workspace / "projects").resolve()),
            "label": "projects",
        },
        {
            "value": str(selected.resolve()),
            "label": "projects/alpha",
        },
        {
            "value": str((workspace / "projects" / "beta").resolve()),
            "label": "projects/beta",
        },
    ]


def test_feature_omits_symlinks_and_paths_outside_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()
    (workspace / "outside-link").symlink_to(outside, target_is_directory=True)

    element = EmbeddedWorkspaceSettingsFeature().get_ui_elements(
        {
            "workspace_root": str(workspace),
            "working_directory": str(outside),
        }
    )[0]

    assert element["options"] == [
        {"value": str(workspace.resolve()), "label": "Workspace root"}
    ]


def test_feature_requires_a_fixed_workspace_boundary(tmp_path: Path) -> None:
    assert (
        EmbeddedWorkspaceSettingsFeature().get_ui_elements(
            {"working_directory": str(tmp_path)}
        )
        == []
    )