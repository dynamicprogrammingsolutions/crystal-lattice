"""Unit tests for :mod:`agent_terminal_app.project_profile`.

These tests cover project-name generation (including disambiguation),
port selection and persistence, bridge-server-id persistence, the
resolution order (CLI > local > user-level > default), file format,
and error handling for corrupt files.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from agent_terminal_app.project_profile import (
    ProjectProfileManager,
    _generate_unique_name,
)


# ---------------------------------------------------------------------------
# Name generation tests
# ---------------------------------------------------------------------------


def test_name_generation_no_collision(tmp_path: Path) -> None:
    project_dir = tmp_path / "iocharts"
    name = _generate_unique_name(project_dir, set())
    assert name == "iocharts"


def test_name_generation_one_parent_collision(tmp_path: Path) -> None:
    project_dir = tmp_path / "Kuhar_Balint" / "iocharts"
    name = _generate_unique_name(project_dir, {"iocharts"})
    assert name == "Kuhar_Balint-iocharts"


def test_name_generation_multiple_parents_collision(tmp_path: Path) -> None:
    project_dir = tmp_path / "dev" / "frontend" / "iocharts"
    name = _generate_unique_name(project_dir, {"iocharts", "frontend-iocharts"})
    assert name == "dev-frontend-iocharts"


def test_name_generation_root_numeric_suffix() -> None:
    """A project at the filesystem root gets a numeric suffix on collision."""
    name = _generate_unique_name(Path("/iocharts"), {"iocharts"})
    assert name == "iocharts-2"


def test_name_generation_root_numeric_suffix_increments() -> None:
    """The numeric suffix increments until a unique name is found."""
    name = _generate_unique_name(
        Path("/iocharts"), {"iocharts", "iocharts-2", "iocharts-3"}
    )
    assert name == "iocharts-4"


def test_name_generation_all_parents_exhausted(tmp_path: Path) -> None:
    """When all parent names are already taken, fall back to numeric suffix."""
    project_dir = tmp_path / "iocharts"
    existing: set[str] = {"iocharts"}
    candidate = "iocharts"
    parent = tmp_path
    while parent != parent.parent:
        candidate = f"{parent.name}-{candidate}"
        existing.add(candidate)
        parent = parent.parent
    name = _generate_unique_name(project_dir, existing)
    assert name == "iocharts-2"


# ---------------------------------------------------------------------------
# Port tests
# ---------------------------------------------------------------------------


def test_port_first_run_picks_and_persists(tmp_path: Path, monkeypatch) -> None:
    user_file = tmp_path / "projects.json"
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    monkeypatch.setattr(
        "agent_terminal_app.project_profile._find_free_port", lambda: 9999
    )

    manager = ProjectProfileManager(user_file=user_file, project_dir=project_dir)
    profile = manager.resolve()

    assert profile.port == 9999
    data = json.loads(user_file.read_text())
    assert data["projects"][str(project_dir.resolve())]["port"] == 9999


def test_port_second_run_reuses_persisted(tmp_path: Path, monkeypatch) -> None:
    user_file = tmp_path / "projects.json"
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()
    project_key = str(project_dir.resolve())

    user_file.write_text(
        json.dumps(
            {
                "projects": {
                    project_key: {
                        "name": "myproject",
                        "port": 8090,
                        "bridge_server_id": "test-id",
                    }
                }
            },
            indent=2,
        )
    )

    monkeypatch.setattr(
        "agent_terminal_app.project_profile._try_bind", lambda port: True
    )

    manager = ProjectProfileManager(user_file=user_file, project_dir=project_dir)
    profile = manager.resolve()

    assert profile.port == 8090
    # File should not have been rewritten (no changes to persist).
    data = json.loads(user_file.read_text())
    assert data["projects"][project_key]["port"] == 8090


def test_port_occupied_falls_back_and_updates(tmp_path: Path, monkeypatch) -> None:
    user_file = tmp_path / "projects.json"
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()
    project_key = str(project_dir.resolve())

    user_file.write_text(
        json.dumps(
            {
                "projects": {
                    project_key: {
                        "name": "myproject",
                        "port": 8090,
                        "bridge_server_id": "test-id",
                    }
                }
            },
            indent=2,
        )
    )

    monkeypatch.setattr(
        "agent_terminal_app.project_profile._try_bind", lambda port: False
    )
    monkeypatch.setattr(
        "agent_terminal_app.project_profile._find_free_port", lambda: 9090
    )

    manager = ProjectProfileManager(user_file=user_file, project_dir=project_dir)
    profile = manager.resolve()

    assert profile.port == 9090
    data = json.loads(user_file.read_text())
    assert data["projects"][project_key]["port"] == 9090


def test_port_local_override_occupied_no_persist(tmp_path: Path, monkeypatch) -> None:
    user_file = tmp_path / "projects.json"
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()
    local_override = project_dir / ".crystal" / "profile.json"
    local_override.parent.mkdir()
    local_override.write_text(json.dumps({"port": 7000}))

    monkeypatch.setattr(
        "agent_terminal_app.project_profile._try_bind", lambda port: False
    )
    monkeypatch.setattr(
        "agent_terminal_app.project_profile._find_free_port", lambda: 9090
    )

    manager = ProjectProfileManager(
        user_file=user_file,
        project_dir=project_dir,
        local_override_file=local_override,
    )
    profile = manager.resolve()

    assert profile.port == 9090

    # Local override file should be unchanged.
    assert json.loads(local_override.read_text())["port"] == 7000

    # User-level entry should not have the fallback port.
    data = json.loads(user_file.read_text())
    entry = data["projects"][str(project_dir.resolve())]
    assert entry.get("port") != 9090


# ---------------------------------------------------------------------------
# Bridge server-id tests
# ---------------------------------------------------------------------------


def test_bridge_server_id_generation_and_persistence(tmp_path: Path) -> None:
    user_file = tmp_path / "projects.json"
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    manager = ProjectProfileManager(user_file=user_file, project_dir=project_dir)
    profile = manager.resolve()

    # Should be a valid UUID.
    uuid.UUID(profile.bridge_server_id)

    data = json.loads(user_file.read_text())
    assert (
        data["projects"][str(project_dir.resolve())]["bridge_server_id"]
        == profile.bridge_server_id
    )


def test_bridge_server_id_reused_on_next_call(tmp_path: Path) -> None:
    user_file = tmp_path / "projects.json"
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    manager1 = ProjectProfileManager(user_file=user_file, project_dir=project_dir)
    profile1 = manager1.resolve()

    manager2 = ProjectProfileManager(user_file=user_file, project_dir=project_dir)
    profile2 = manager2.resolve()

    assert profile2.bridge_server_id == profile1.bridge_server_id


# ---------------------------------------------------------------------------
# Resolution order tests
# ---------------------------------------------------------------------------


def test_resolution_cli_wins(tmp_path: Path, monkeypatch) -> None:
    user_file = tmp_path / "projects.json"
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()
    local_override = project_dir / ".crystal" / "profile.json"
    local_override.parent.mkdir()
    project_key = str(project_dir.resolve())

    user_file.write_text(
        json.dumps(
            {
                "projects": {
                    project_key: {
                        "name": "user-level-name",
                        "port": 8090,
                        "bridge_server_id": "user-level-id",
                    }
                }
            },
            indent=2,
        )
    )
    local_override.write_text(
        json.dumps({"name": "local-name", "port": 9000, "bridge_server_id": "local-id"})
    )

    monkeypatch.setattr(
        "agent_terminal_app.project_profile._try_bind", lambda port: True
    )

    manager = ProjectProfileManager(
        user_file=user_file,
        project_dir=project_dir,
        local_override_file=local_override,
    )
    profile = manager.resolve(
        cli_name="cli-name",
        cli_port=7000,
        cli_bridge_server_id="cli-id",
    )

    assert profile.name == "cli-name"
    assert profile.port == 7000
    assert profile.bridge_server_id == "cli-id"

    # CLI values must not overwrite the user-level entry.
    data = json.loads(user_file.read_text())
    entry = data["projects"][project_key]
    assert entry["name"] == "user-level-name"
    assert entry["port"] == 8090
    assert entry["bridge_server_id"] == "user-level-id"


def test_resolution_local_over_user_level(tmp_path: Path, monkeypatch) -> None:
    user_file = tmp_path / "projects.json"
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()
    local_override = project_dir / ".crystal" / "profile.json"
    local_override.parent.mkdir()
    project_key = str(project_dir.resolve())

    user_file.write_text(
        json.dumps(
            {
                "projects": {
                    project_key: {
                        "name": "user-level-name",
                        "port": 8090,
                        "bridge_server_id": "user-level-id",
                    }
                }
            },
            indent=2,
        )
    )
    local_override.write_text(json.dumps({"name": "local-name", "port": 9000}))

    monkeypatch.setattr(
        "agent_terminal_app.project_profile._try_bind", lambda port: True
    )

    manager = ProjectProfileManager(
        user_file=user_file,
        project_dir=project_dir,
        local_override_file=local_override,
    )
    profile = manager.resolve()

    assert profile.name == "local-name"
    assert profile.port == 9000
    # bridge_server_id not in local override → falls through to user-level.
    assert profile.bridge_server_id == "user-level-id"

    # Nothing should have been persisted (all values came from existing sources).
    data = json.loads(user_file.read_text())
    entry = data["projects"][project_key]
    assert entry["name"] == "user-level-name"
    assert entry["port"] == 8090
    assert entry["bridge_server_id"] == "user-level-id"


def test_resolution_user_level_over_default(tmp_path: Path, monkeypatch) -> None:
    user_file = tmp_path / "projects.json"
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()
    project_key = str(project_dir.resolve())

    user_file.write_text(
        json.dumps(
            {
                "projects": {
                    project_key: {
                        "name": "stored-name",
                        "port": 8090,
                        "bridge_server_id": "stored-id",
                    }
                }
            },
            indent=2,
        )
    )

    monkeypatch.setattr(
        "agent_terminal_app.project_profile._try_bind", lambda port: True
    )

    manager = ProjectProfileManager(user_file=user_file, project_dir=project_dir)
    profile = manager.resolve()

    assert profile.name == "stored-name"
    assert profile.port == 8090
    assert profile.bridge_server_id == "stored-id"


def test_partial_local_override(tmp_path: Path, monkeypatch) -> None:
    user_file = tmp_path / "projects.json"
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()
    local_override = project_dir / ".crystal" / "profile.json"
    local_override.parent.mkdir()
    project_key = str(project_dir.resolve())

    user_file.write_text(
        json.dumps(
            {
                "projects": {
                    project_key: {
                        "name": "user-level-name",
                        "port": 8090,
                        "bridge_server_id": "user-level-id",
                    }
                }
            },
            indent=2,
        )
    )
    local_override.write_text(json.dumps({"port": 9000}))

    monkeypatch.setattr(
        "agent_terminal_app.project_profile._try_bind", lambda port: True
    )

    manager = ProjectProfileManager(
        user_file=user_file,
        project_dir=project_dir,
        local_override_file=local_override,
    )
    profile = manager.resolve()

    # Port from local override; name and bridge_server_id from user-level.
    assert profile.name == "user-level-name"
    assert profile.port == 9000
    assert profile.bridge_server_id == "user-level-id"


def test_default_local_override_file_used(tmp_path: Path, monkeypatch) -> None:
    """When local_override_file is not passed, defaults to <project>/.crystal/profile.json."""
    user_file = tmp_path / "projects.json"
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()
    local_override = project_dir / ".crystal" / "profile.json"
    local_override.parent.mkdir()
    local_override.write_text(json.dumps({"name": "from-local-default"}))

    monkeypatch.setattr(
        "agent_terminal_app.project_profile._find_free_port", lambda: 9999
    )

    manager = ProjectProfileManager(user_file=user_file, project_dir=project_dir)
    profile = manager.resolve()

    assert profile.name == "from-local-default"


# ---------------------------------------------------------------------------
# Persistence tests
# ---------------------------------------------------------------------------


def test_cli_values_not_persisted(tmp_path: Path, monkeypatch) -> None:
    """When all values come from CLI, nothing is written to the user file."""
    user_file = tmp_path / "projects.json"
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    monkeypatch.setattr(
        "agent_terminal_app.project_profile._find_free_port", lambda: 9999
    )

    manager = ProjectProfileManager(user_file=user_file, project_dir=project_dir)
    profile = manager.resolve(
        cli_name="cli-name",
        cli_port=7000,
        cli_bridge_server_id="cli-id",
    )

    assert profile.name == "cli-name"
    assert profile.port == 7000
    assert profile.bridge_server_id == "cli-id"
    assert not user_file.is_file()


def test_cli_name_not_persisted_but_defaults_are(tmp_path: Path, monkeypatch) -> None:
    """CLI-provided name is used but not persisted; other defaults are."""
    user_file = tmp_path / "projects.json"
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    monkeypatch.setattr(
        "agent_terminal_app.project_profile._find_free_port", lambda: 9999
    )

    manager = ProjectProfileManager(user_file=user_file, project_dir=project_dir)
    profile = manager.resolve(cli_name="cli-name")

    assert profile.name == "cli-name"

    data = json.loads(user_file.read_text())
    entry = data["projects"][str(project_dir.resolve())]
    assert "name" not in entry
    assert entry["port"] == 9999
    assert "bridge_server_id" in entry


# ---------------------------------------------------------------------------
# File format tests
# ---------------------------------------------------------------------------


def test_user_file_pretty_printed(tmp_path: Path, monkeypatch) -> None:
    user_file = tmp_path / "projects.json"
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    monkeypatch.setattr(
        "agent_terminal_app.project_profile._find_free_port", lambda: 9999
    )

    manager = ProjectProfileManager(user_file=user_file, project_dir=project_dir)
    manager.resolve()

    text = user_file.read_text()
    data = json.loads(text)
    # Pretty-printed (indent=2).
    assert "\n" in text
    # Keys sorted within each entry.
    entry = data["projects"][str(project_dir.resolve())]
    assert list(entry.keys()) == sorted(entry.keys())


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("content", ["{invalid", "", "[]", '"string"', "42"])
def test_corrupted_user_file_raises_clear_error(tmp_path: Path, content: str) -> None:
    user_file = tmp_path / "projects.json"
    user_file.write_text(content, encoding="utf-8")
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    manager = ProjectProfileManager(user_file=user_file, project_dir=project_dir)
    with pytest.raises(RuntimeError, match="profile file"):
        manager.resolve()


@pytest.mark.parametrize("content", ["{broken", "", "[]", "true"])
def test_corrupted_local_override_raises_clear_error(
    tmp_path: Path, content: str
) -> None:
    user_file = tmp_path / "projects.json"
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()
    local_override = project_dir / ".crystal" / "profile.json"
    local_override.parent.mkdir()
    local_override.write_text(content, encoding="utf-8")

    manager = ProjectProfileManager(
        user_file=user_file,
        project_dir=project_dir,
        local_override_file=local_override,
    )
    with pytest.raises(RuntimeError, match="profile override"):
        manager.resolve()


def test_missing_user_file_treated_as_empty(tmp_path: Path, monkeypatch) -> None:
    """When the user file does not exist, settings are auto-generated."""
    user_file = tmp_path / "projects.json"
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    monkeypatch.setattr(
        "agent_terminal_app.project_profile._find_free_port", lambda: 9999
    )

    manager = ProjectProfileManager(user_file=user_file, project_dir=project_dir)
    profile = manager.resolve()

    assert profile.name == "myproject"
    assert profile.port == 9999
    uuid.UUID(profile.bridge_server_id)


def test_missing_local_override_treated_as_empty(tmp_path: Path, monkeypatch) -> None:
    """When the local override file does not exist, user-level values are used."""
    user_file = tmp_path / "projects.json"
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()
    project_key = str(project_dir.resolve())

    user_file.write_text(
        json.dumps(
            {
                "projects": {
                    project_key: {
                        "name": "stored-name",
                        "port": 8090,
                        "bridge_server_id": "stored-id",
                    }
                }
            },
            indent=2,
        )
    )

    monkeypatch.setattr(
        "agent_terminal_app.project_profile._try_bind", lambda port: True
    )

    manager = ProjectProfileManager(user_file=user_file, project_dir=project_dir)
    profile = manager.resolve()

    assert profile.name == "stored-name"
    assert profile.port == 8090
    assert profile.bridge_server_id == "stored-id"


# ---------------------------------------------------------------------------
# Bridge URL tests
# ---------------------------------------------------------------------------


def test_bridge_url_none_when_no_source(tmp_path: Path, monkeypatch) -> None:
    """bridge_url is None when no source provides it."""
    user_file = tmp_path / "projects.json"
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    monkeypatch.setattr(
        "agent_terminal_app.project_profile._find_free_port", lambda: 9999
    )

    manager = ProjectProfileManager(user_file=user_file, project_dir=project_dir)
    profile = manager.resolve()

    assert profile.bridge_url is None


def test_bridge_url_from_cli(tmp_path: Path, monkeypatch) -> None:
    user_file = tmp_path / "projects.json"
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    monkeypatch.setattr(
        "agent_terminal_app.project_profile._find_free_port", lambda: 9999
    )

    manager = ProjectProfileManager(user_file=user_file, project_dir=project_dir)
    profile = manager.resolve(cli_bridge_url="wss://bridge.example/ws")

    assert profile.bridge_url == "wss://bridge.example/ws"


def test_bridge_url_from_local_override(tmp_path: Path, monkeypatch) -> None:
    user_file = tmp_path / "projects.json"
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()
    local_override = project_dir / ".crystal" / "profile.json"
    local_override.parent.mkdir()
    local_override.write_text(json.dumps({"bridge_url": "wss://local.example/ws"}))

    monkeypatch.setattr(
        "agent_terminal_app.project_profile._find_free_port", lambda: 9999
    )

    manager = ProjectProfileManager(
        user_file=user_file,
        project_dir=project_dir,
        local_override_file=local_override,
    )
    profile = manager.resolve()

    assert profile.bridge_url == "wss://local.example/ws"


def test_bridge_url_from_user_level(tmp_path: Path, monkeypatch) -> None:
    user_file = tmp_path / "projects.json"
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()
    project_key = str(project_dir.resolve())

    user_file.write_text(
        json.dumps(
            {
                "projects": {
                    project_key: {
                        "name": "myproject",
                        "port": 8090,
                        "bridge_server_id": "test-id",
                        "bridge_url": "wss://user.example/ws",
                    }
                }
            },
            indent=2,
        )
    )

    monkeypatch.setattr(
        "agent_terminal_app.project_profile._try_bind", lambda port: True
    )

    manager = ProjectProfileManager(user_file=user_file, project_dir=project_dir)
    profile = manager.resolve()

    assert profile.bridge_url == "wss://user.example/ws"


def test_bridge_url_cli_wins_over_local_and_user_level(
    tmp_path: Path, monkeypatch
) -> None:
    user_file = tmp_path / "projects.json"
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()
    local_override = project_dir / ".crystal" / "profile.json"
    local_override.parent.mkdir()
    project_key = str(project_dir.resolve())

    user_file.write_text(
        json.dumps(
            {
                "projects": {
                    project_key: {
                        "name": "myproject",
                        "port": 8090,
                        "bridge_server_id": "test-id",
                        "bridge_url": "wss://user.example/ws",
                    }
                }
            },
            indent=2,
        )
    )
    local_override.write_text(json.dumps({"bridge_url": "wss://local.example/ws"}))

    monkeypatch.setattr(
        "agent_terminal_app.project_profile._try_bind", lambda port: True
    )

    manager = ProjectProfileManager(
        user_file=user_file,
        project_dir=project_dir,
        local_override_file=local_override,
    )
    profile = manager.resolve(cli_bridge_url="wss://cli.example/ws")

    assert profile.bridge_url == "wss://cli.example/ws"


def test_bridge_url_not_persisted(tmp_path: Path, monkeypatch) -> None:
    """bridge_url from CLI is not written to the user-level file."""
    user_file = tmp_path / "projects.json"
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    monkeypatch.setattr(
        "agent_terminal_app.project_profile._find_free_port", lambda: 9999
    )

    manager = ProjectProfileManager(user_file=user_file, project_dir=project_dir)
    manager.resolve(cli_bridge_url="wss://bridge.example/ws")

    data = json.loads(user_file.read_text())
    entry = data["projects"][str(project_dir.resolve())]
    assert "bridge_url" not in entry
