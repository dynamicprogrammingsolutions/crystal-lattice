"""Unit tests for ApplyPatchTool plugin (Codex-style apply_patch)."""

from __future__ import annotations

from textwrap import dedent

from agent_core.plugin import ToolWrapper

from codex_tools.apply_patch_tool import ApplyPatchTool


def _build_wrapper(tmp_path):
    wrapper = ToolWrapper(ApplyPatchTool)
    state = wrapper.init(
        {
            "working_directory": str(tmp_path),
            "allowed_paths": [str(tmp_path)],
        }
    )
    return wrapper, state


def test_apply_patch_add_update_and_delete_other_file(tmp_path):
    wrapper, state = _build_wrapper(tmp_path)

    # Create initial files: one to update and one to delete
    target = tmp_path / "foo.txt"
    target.write_text("line1\nline2\nline3\n", encoding="utf-8")
    to_delete = tmp_path / "delete_me.txt"
    to_delete.write_text("delete me\n", encoding="utf-8")

    patch = dedent(
        """\
        *** Begin Patch
        *** Add File: new.txt
        +hello
        +world
        *** Update File: foo.txt
        @@
         line1
        -line2
        +line2-updated
         line3
        *** Delete File: delete_me.txt
        *** End Patch
        """
    )

    result = wrapper.execute_tool("apply_patch", {"patch_text": patch}, state)

    assert result["success"] is True
    changes = result.get("changes") or {}
    assert "new.txt" in changes
    assert changes["new.txt"]["type"] == "add"
    assert "foo.txt" in changes
    assert changes["foo.txt"]["type"] == "update"
    assert "delete_me.txt" in changes
    assert changes["delete_me.txt"]["type"] == "delete"

    new_file = tmp_path / "new.txt"
    assert new_file.exists()
    assert new_file.read_text(encoding="utf-8") == "hello\nworld"

    # foo.txt should have been updated
    assert target.read_text(encoding="utf-8") == "line1\nline2-updated\nline3\n"
    # delete_me.txt should have been deleted
    assert not to_delete.exists()


def test_apply_patch_rejects_paths_outside_allowed(tmp_path):
    # working_directory inside tmp_path, but allowed_paths only permit a subdir
    base_dir = tmp_path
    safe_dir = base_dir / "safe"
    safe_dir.mkdir(parents=True, exist_ok=True)

    wrapper = ToolWrapper(ApplyPatchTool)
    state = wrapper.init(
        {
            "working_directory": str(base_dir),
            "allowed_paths": [str(safe_dir)],
        }
    )

    # Attempt to write a file directly under base_dir (not under safe_dir)
    patch = dedent(
        """\
        *** Begin Patch
        *** Add File: evil.txt
        +oops
        *** End Patch
        """
    )

    result = wrapper.execute_tool("apply_patch", {"patch_text": patch}, state)

    assert result["success"] is False
    assert "Access denied" in str(result.get("error", ""))

    assert not (base_dir / "evil.txt").exists()


def test_apply_patch_rejects_absolute_path_outside_allowed(tmp_path):
    wrapper, state = _build_wrapper(tmp_path)

    # Construct an absolute path outside allowed_paths
    from pathlib import Path

    outside = Path("/") / "tmp" / "not-allowed.txt"

    patch = dedent(
        f"""\
        *** Begin Patch
        *** Add File: {outside}
        +data
        *** End Patch
        """
    )

    result = wrapper.execute_tool("apply_patch", {"patch_text": patch}, state)
    assert result["success"] is False
    assert "Access denied" in str(result.get("error", ""))


def test_apply_patch_invalid_format(tmp_path):
    wrapper, state = _build_wrapper(tmp_path)

    bad_patch = "not a real patch"
    result = wrapper.execute_tool("apply_patch", {"patch_text": bad_patch}, state)

    assert result["success"] is False
    assert "Patch failed" in str(result.get("error", "")) or "Invalid patch" in str(
        result.get("error", "")
    )


def test_apply_patch_respects_max_patch_bytes(tmp_path):
    wrapper, state = _build_wrapper(tmp_path)

    # Override max_patch_bytes via state config
    state["config"]["max_patch_bytes"] = 10

    patch = dedent(
        """\
        *** Begin Patch
        *** End Patch
        """
    )

    result = wrapper.execute_tool("apply_patch", {"patch_text": patch}, state)

    assert result["success"] is False
    assert "Patch too large" in str(result.get("error", ""))


def test_apply_patch_reports_changes_and_fuzz(tmp_path):
    wrapper, state = _build_wrapper(tmp_path)

    # A simple update where context appears and exercises the
    # context matching path with a minimal fuzz accounting check.
    target = tmp_path / "file.txt"
    target.write_text("alpha\nbeta\n", encoding="utf-8")

    patch = dedent(
        """\
        *** Begin Patch
        *** Update File: file.txt
        @@
         alpha
        -beta
        +beta-updated
        *** End Patch
        """
    )

    result = wrapper.execute_tool("apply_patch", {"patch_text": patch}, state)

    assert result["success"] is True
    assert "file.txt" in (result.get("changes") or {})
    # Fuzz may be zero or positive; we only assert it is an int
    assert isinstance(result.get("fuzz"), int)

    content = target.read_text(encoding="utf-8")
    assert content == "alpha\nbeta-updated\n" or content.endswith("beta-updated\n")
