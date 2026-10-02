from __future__ import annotations

from pathlib import Path

from embedded_workspace_settings import (
    EmbeddedWorkspaceAppPlugin,
    EmbeddedWorkspaceSettingsFeature,
)


def test_application_plugin_lists_workspace_sources_and_settings_actions(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    selected = workspace / "projects" / "alpha"
    selected.mkdir(parents=True)
    private = workspace / ".sessions" / "session-1" / "private-one"
    private.mkdir(parents=True)

    elements = EmbeddedWorkspaceAppPlugin().get_ui_elements(
        {},
        {
            "workspace_root": str(workspace),
            "working_directory": str(selected),
            "workspace_grants": (
                '{"grant-1":{"path":"/tmp/files","display_name":"Files project",'
                '"available":true}}'
            ),
        },
        {
            "ui_context": "session",
            "session": {
                "session_id": "session-1",
                "metadata": {"overrides": {"working_directory": str(selected)}},
            },
        }
    )

    assert len(elements) == 4
    element = elements[0]
    assert element["type"] == "workspace"
    assert element["key"] == "workspace_id"
    assert element["default"] == "shared:projects/alpha"
    assert {option["value"] for option in element["options"]} == {
        "shared:root",
        "shared:projects",
        "shared:projects/alpha",
        "private:session-1:private-one",
        "external:grant-1",
    }
    assert all(
        action["rich_ui"]["placements"] == ["session_settings"]
        for action in elements[1:]
    )


def test_feature_defines_workspace_selection_without_owning_ui() -> None:
    feature = EmbeddedWorkspaceSettingsFeature()
    assert feature.get_config_schema()["workspace_id"]["type"] == "string"
    assert feature.get_ui_elements({}) == []