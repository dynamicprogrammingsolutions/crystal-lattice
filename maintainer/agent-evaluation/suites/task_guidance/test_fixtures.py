from __future__ import annotations

from maintainer.guidance import compile_guidance

from .fixtures import (
    GUIDANCE_TARGET_ROOT,
    REPOSITORY_ROOT,
    fixture_files,
    fixture_sha256,
    selected_bundle,
)
from .scenarios import SCENARIOS


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
    assert "from_environment" in multi_consumer[
        "packages/notes_client/notes_client/client.py"
    ]
    assert "def client" in multi_consumer[
        "packages/notes_client/tests/conftest.py"
    ]

    eleventy = fixture_files("tg06-eleventy-author-migration")
    assert 'addFilter("head"' in eleventy["eleventy.config.js"]
    assert "content/posts/posts.json" not in eleventy["eleventy.config.js"]
    assert "layout" in eleventy["content/posts/posts.json"]
    assert "permalink: /feed/feed.xml" in eleventy["content/feed.xml.njk"]

    archive = fixture_files("tg01-eleventy-archive")
    assert "_includes/layouts/post.njk" in archive
    assert "layout" in archive["content/posts/posts.json"]