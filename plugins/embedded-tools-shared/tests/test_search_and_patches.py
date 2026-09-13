from __future__ import annotations

from pathlib import Path

import pytest

from embedded_tools_shared import (
    PatchError,
    WorkspacePathError,
    apply_workspace_patch,
    enumerate_workspace_paths,
    resolve_workspace_root,
    search_workspace_text,
)


def _workspace(tmp_path: Path) -> Path:
    root = resolve_workspace_root({"working_directory": str(tmp_path / "workspace")})
    (root / "docs/nested").mkdir(parents=True)
    (root / "src").mkdir()
    (root / "docs/alpha.md").write_text(
        "# Alpha\nmarker first\ncontext after\n",
        encoding="utf-8",
    )
    (root / "docs/nested/beta.md").write_text(
        "# Beta\nmarker second\n",
        encoding="utf-8",
    )
    (root / "src/sample.py").write_text(
        'VALUE = "marker source"\n',
        encoding="utf-8",
    )
    (root / ".hidden.txt").write_text("marker hidden\n", encoding="utf-8")
    return root


def test_enumeration_filters_kind_glob_hidden_and_depth(tmp_path: Path) -> None:
    root = _workspace(tmp_path)

    markdown = enumerate_workspace_paths(
        root,
        start_path="docs",
        path_globs=["**/*.md"],
    )
    assert [entry.path for entry in markdown.paths] == [
        "docs/alpha.md",
        "docs/nested/beta.md",
    ]

    shallow = enumerate_workspace_paths(
        root,
        start_path="docs",
        kind="any",
        max_depth=1,
    )
    assert [entry.path for entry in shallow.paths] == [
        "docs/alpha.md",
        "docs/nested",
    ]

    visible = enumerate_workspace_paths(root, include_hidden=False)
    assert ".hidden.txt" not in [entry.path for entry in visible.paths]
    all_paths = enumerate_workspace_paths(root, include_hidden=True)
    assert ".hidden.txt" in [entry.path for entry in all_paths.paths]


def test_enumeration_rejects_symlink_escape(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "outside-link").symlink_to(outside, target_is_directory=True)

    with pytest.raises(WorkspacePathError, match="escapes"):
        enumerate_workspace_paths(root, kind="any")


def test_search_returns_matches_counts_context_and_bounds(tmp_path: Path) -> None:
    root = _workspace(tmp_path)

    result = search_workspace_text(
        root,
        "MARKER",
        case_sensitive=False,
        path_globs=["**/*.md"],
        context_before=1,
        context_after=1,
        max_results=10,
    )
    assert [match.path for match in result.matches] == [
        "docs/alpha.md",
        "docs/nested/beta.md",
    ]
    assert result.matches[0].line_number == 2
    assert result.matches[0].before == ((1, "# Alpha"),)
    assert result.matches[0].after == ((3, "context after"),)
    assert result.counts == (
        ("docs/alpha.md", 1),
        ("docs/nested/beta.md", 1),
    )
    assert not result.truncated

    limited = search_workspace_text(root, "marker", max_results=1)
    assert len(limited.matches) == 1
    assert limited.truncated


def test_patch_add_update_move_and_delete(tmp_path: Path) -> None:
    root = resolve_workspace_root({"working_directory": str(tmp_path)})
    (root / "existing.txt").write_text("alpha\nbeta\n", encoding="utf-8")
    (root / "delete.txt").write_text("obsolete\n", encoding="utf-8")

    result = apply_workspace_patch(
        root,
        """*** Begin Patch
*** Add File: added.txt
+created
*** Update File: existing.txt
*** Move to: moved.txt
@@
 alpha
-beta
+gamma
*** Delete File: delete.txt
*** End Patch
""",
    )

    assert [(change.type, change.path, change.move_path) for change in result.changes] == [
        ("add", "added.txt", None),
        ("update", "existing.txt", "moved.txt"),
        ("delete", "delete.txt", None),
    ]
    assert (root / "added.txt").read_text(encoding="utf-8") == "created"
    assert not (root / "existing.txt").exists()
    assert (root / "moved.txt").read_text(encoding="utf-8") == "alpha\ngamma\n"
    assert not (root / "delete.txt").exists()


def test_patch_rejects_invalid_context_and_path_escape(tmp_path: Path) -> None:
    root = resolve_workspace_root({"working_directory": str(tmp_path / "workspace")})
    (root / "existing.txt").write_text("alpha\n", encoding="utf-8")

    with pytest.raises(PatchError, match="context not found"):
        apply_workspace_patch(
            root,
            """*** Begin Patch
*** Update File: existing.txt
@@
-missing
+replacement
*** End Patch
""",
        )

    with pytest.raises(WorkspacePathError, match="escapes"):
        apply_workspace_patch(
            root,
            """*** Begin Patch
*** Add File: ../outside.txt
+blocked
*** End Patch
""",
        )
    assert not (tmp_path / "outside.txt").exists()


def test_patch_rejects_duplicate_and_oversized_input(tmp_path: Path) -> None:
    root = resolve_workspace_root({"working_directory": str(tmp_path)})

    with pytest.raises(PatchError, match="Duplicate"):
        apply_workspace_patch(
            root,
            """*** Begin Patch
*** Add File: duplicate.txt
+one
*** Add File: duplicate.txt
+two
*** End Patch
""",
        )

    with pytest.raises(PatchError, match="too large"):
        apply_workspace_patch(
            root,
            "*** Begin Patch\n*** Add File: a.txt\n+value\n*** End Patch\n",
            max_bytes=10,
        )