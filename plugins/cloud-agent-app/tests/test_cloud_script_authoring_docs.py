from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
GUIDE = ROOT / "plugins" / "cloud-agent-app" / "docs" / "cloud-script-authoring.md"
README = ROOT / "plugins" / "cloud-agent-app" / "README.md"


def test_cloud_script_authoring_guide_documents_container_profiles() -> None:
    text = GUIDE.read_text(encoding="utf-8")
    normalized = " ".join(text.split())

    for required in (
        "## Container Profiles",
        "container_profiles",
        "default_container_profile",
        "Dockerfile mode",
        "build_assets",
        "cache_mounts",
        "mounts",
        "node_modules",
        "Ollama",
        "The Dockerfile build has a hard project boundary",
        "Avoid volatile generated files",
        "secret",
    ):
        assert required in text
    assert (
        "The project workspace is mounted only when the runtime container starts"
        in normalized
    )


def test_cloud_script_authoring_guide_warns_against_implicit_project_context() -> None:
    text = " ".join(GUIDE.read_text(encoding="utf-8").lower().split())

    assert "cannot use project files implicitly" in text
    assert "declare them explicitly in `build_assets`" in text
    assert "normal project source as the runtime workspace mount" in text


def test_cloud_script_authoring_guide_allows_small_external_validation_smoke() -> None:
    text = " ".join(GUIDE.read_text(encoding="utf-8").lower().split())

    assert "fast, repeatable, and as deterministic as practical" in text
    assert "small smoke check" in text
    assert "transferred credential works" in text
    assert "do not assume the target project is itself an ai application" in text
    assert "provider-free" not in text


def test_cloud_agent_readme_points_authoring_agent_to_guide() -> None:
    text = README.read_text(encoding="utf-8")
    normalized = " ".join(text.split())

    assert "cloud-script-author" in text
    assert "docs/cloud-script-authoring.md" in text
    assert "Keep the guide in sync with this reference" in normalized