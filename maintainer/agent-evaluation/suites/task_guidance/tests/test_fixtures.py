from __future__ import annotations

import subprocess
import time

from maintainer.guidance import compile_guidance

from ..configuration import selected_bundle
from ..fixtures import (
    GUIDANCE_TARGET_ROOT,
    REPOSITORY_ROOT,
    _commit_fixture,
    fixture_files,
    fixture_sha256,
)
from ..scenarios import SCENARIOS


def _git_head(workspace) -> str:
    result = subprocess.run(
        ["git", "-C", str(workspace), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return result.stdout.strip()


def test_every_scenario_has_a_nontrivial_fixed_fixture() -> None:
    for scenario in SCENARIOS:
        files = fixture_files(scenario.fixture_id)
        assert "README.md" in files
        assert len(files) >= 6
        assert len(fixture_sha256(scenario.fixture_id)) == 64


def test_project_guidance_targets_compile_current_portable_sections() -> None:
    for family in {scenario.project_family for scenario in SCENARIOS}:
        result = compile_guidance(
            bundle=selected_bundle(),
            target=GUIDANCE_TARGET_ROOT / family,
            repository_root=REPOSITORY_ROOT,
        )
        agents = result.outputs["AGENTS.md"].decode("utf-8")
        assert "## Project context" in agents
        assert "## Testing" in agents


def test_fixture_claims_have_corresponding_project_infrastructure() -> None:
    fastapi = fixture_files("tg02-fastapi-pagination")
    assert "metadata.create_all(engine)" in fastapi["src/app/db.py"]
    assert "lifespan=lifespan" in fastapi["src/app/main.py"]
    assert "@router.post" in fastapi["src/app/api/notes.py"]
    assert "@pytest.fixture" in fastapi["src/tests/conftest.py"]

    flask_vue = fixture_files("tg03-flask-vue-refresh")
    assert "<template>" in flask_vue["client/src/components/Books.vue"]
    assert '"test": "vitest run"' in flask_vue["client/package.json"]
    assert "@pytest.fixture" in flask_vue["tests/conftest.py"]
    assert 'methods=["PUT", "DELETE"]' in flask_vue["server/app.py"]

    multi_consumer = fixture_files("tg05-fastapi-multi-consumer")
    assert "[project.scripts]" in multi_consumer["apps/notes_cli/pyproject.toml"]
    assert (
        "from_environment"
        in multi_consumer["packages/notes_client/notes_client/client.py"]
    )
    assert "def client" in multi_consumer["packages/notes_client/tests/conftest.py"]

    eleventy = fixture_files("tg06-eleventy-author-migration")
    assert 'addFilter("head"' in eleventy["eleventy.config.js"]
    assert "content/posts/posts.json" not in eleventy["eleventy.config.js"]
    assert "layout" in eleventy["content/posts/posts.json"]
    assert "permalink: /feed/feed.xml" in eleventy["content/feed.xml.njk"]

    archive = fixture_files("tg01-eleventy-archive")
    assert "_includes/layouts/post.njk" in archive
    assert "layout" in archive["content/posts/posts.json"]


def test_fixture_commit_is_deterministic(tmp_path) -> None:
    """The prepared-workspace revision must not depend on the wall clock.

    The fixture commit's SHA is the workspace revision, which enters the
    workspace fingerprint and through it the execution cache key. A
    timestamp-dependent commit makes every invocation prepare a
    "different" workspace, so unchanged requests never replay across
    invocations.
    """

    revisions = []
    for index in range(2):
        workspace = tmp_path / f"case-{index}" / "workspace"
        workspace.mkdir(parents=True)
        subprocess.run(
            ["git", "-C", str(workspace), "init"],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        (workspace / "AGENTS.md").write_text(
            "# Evaluation workspace\n", encoding="utf-8"
        )
        _commit_fixture(workspace)
        revisions.append(_git_head(workspace))
        time.sleep(1.1)

    assert revisions[0] == revisions[1], (
        "fixture commit SHA depends on the commit timestamp; unchanged"
        " workspaces would get different revisions and never replay from"
        " the execution cache"
    )
