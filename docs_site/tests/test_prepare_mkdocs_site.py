from __future__ import annotations

from pathlib import Path, PurePosixPath

import pytest

import prepare_mkdocs_site as prepare


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def package_toml(
    package_id: str,
    source: str,
    *,
    title: str | None = None,
    group: str = "Test packages",
    summary: str | None = None,
    destination: str | None = None,
    include_readme: bool = True,
    include_docs: bool = True,
    publish_development: bool = True,
) -> str:
    return "\n".join(
        [
            "[[package]]",
            f'id = "{package_id}"',
            f'title = "{title or package_id.title()}"',
            f'group = "{group}"',
            f'summary = "{summary or f"Documentation for {package_id}."}"',
            f'source = "{source}"',
            f'destination = "{destination or f"packages/{package_id}"}"',
            f"include_readme = {str(include_readme).lower()}",
            f"include_docs = {str(include_docs).lower()}",
            f"publish_development = {str(publish_development).lower()}",
            "",
        ]
    )


def create_repository(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    write(root / "docs/index.md", "# Root Docs\n")
    write(root / "docs/overlay.txt", "root\n")
    write(root / "docs_site/source/overlay.txt", "site overlay\n")
    write(root / "docs_site/source/assets/icon.svg", "<svg />\n")
    write(root / "plugins/docs/index.md", "# Plugin Development\n")
    write(root / "plugins/docs/AGENTS.md", "# Private agent guidance\n")
    write(
        root / "plugins/example-plugin/README.md",
        "\n".join(
            [
                "# Example Plugin",
                "",
                "[Default config]"
                "(application/python/agent_terminal_app/default_config/config.json)",
                "",
            ]
        ),
    )
    write(
        root / "plugins/example-plugin/docs/guide.md",
        "# Example Plugin Guide\n\n[Plugin README](../README.md)\n",
    )
    write(
        root / "plugins/example-plugin/docs/development/AGENTS.md",
        "# Private plugin guidance\n",
    )
    write(
        root
        / "application/python/agent_terminal_app/default_config/config.json",
        '{"agents": {}}\n',
    )

    write(
        root / "packages/alpha/README.md",
        "\n".join(
            [
                "# Alpha README",
                "",
                '[Guide](docs/guide.md#part "Guide title")',
                "[Root docs](../../docs/index.md)",
                "[Source code](src/code.py)",
                "![Diagram](docs/image.png)",
                "",
            ]
        ),
    )
    write(root / "packages/alpha/src/code.py", "VALUE = 1\n")
    write(root / "packages/alpha/docs/guide.md", "# Guide\n\n## Part\n")
    write(root / "packages/alpha/docs/image.png", "not-a-real-png")
    write(
        root / "packages/alpha/docs/development/index.md",
        "# Alpha Development\n",
    )
    write(
        root / "packages/alpha/docs/nested/AGENTS.md",
        "# Private nested guidance\n",
    )

    write(root / "packages/beta/README.md", "# Beta README fallback\n")
    write(root / "packages/beta/docs/index.md", "# Beta Docs Index\n")
    write(root / "packages/beta/docs/guide.md", "# Beta Guide\n")
    write(root / "packages/beta/docs/development/index.md", "# Beta Development\n")

    registry = "\n".join(
        [
            "version = 1",
            "",
            package_toml("alpha", "packages/alpha", title="Alpha Package"),
            package_toml("beta", "packages/beta", title="Beta Package"),
        ]
    )
    write(root / "docs_site/packages.toml", registry)
    return root


def registry_path(root: Path) -> Path:
    return root / "docs_site/packages.toml"


def test_production_registry_contains_approved_package_metadata() -> None:
    """DOCPUB-001: the repository registry carries explicit publication policy."""
    paths = prepare.SitePaths.from_repo_root(prepare.REPO_ROOT)

    entries = prepare.load_package_registry(paths)

    assert [entry.id for entry in entries] == [
        "core-python",
        "application-python",
        "frontend-sdk",
        "frontend-sdk-react",
        "frontend-rn-components",
        "react-native-mac-text-view",
        "crystal-lattice-control-mobile",
        "crystal-lattice-control-desktop",
        "tool-host-node",
        "bridge-elixir",
        "cloud-orchestrator",
    ]
    assert all(entry.title for entry in entries)
    assert all(entry.group and entry.summary for entry in entries)
    assert all(
        entry.destination == PurePosixPath("packages") / entry.id
        for entry in entries
    )


def test_package_assembly_and_existing_generators(tmp_path: Path) -> None:
    """DOCPUB-002/003 and DOCVAL-001: assemble canonical public package docs."""
    root = create_repository(tmp_path)

    prepare.prepare_docs_site(root)

    prepared = root / "docs_site/prepared"
    alpha_index = (prepared / "packages/alpha/index.md").read_text(encoding="utf-8")
    assert "# Alpha README" in alpha_index
    assert '[Guide](guide.md#part "Guide title")' in alpha_index
    assert "[Root docs](../../index.md)" in alpha_index
    assert (
        "[Source code]"
        "(https://github.com/dynamicprogrammingsolutions/crystal-lattice/blob/main/"
        "packages/alpha/src/code.py)"
    ) in alpha_index
    assert "![Diagram](image.png)" in alpha_index
    assert (prepared / "packages/alpha/image.png").read_text() == "not-a-real-png"
    assert (prepared / "packages/alpha/development/index.md").is_file()
    assert not (prepared / "packages/alpha/nested/AGENTS.md").exists()

    beta_index = (prepared / "packages/beta/index.md").read_text(encoding="utf-8")
    assert "# Beta Docs Index" in beta_index
    assert "Beta README fallback" not in beta_index

    catalog = (prepared / "packages/index.md").read_text(encoding="utf-8")
    assert "## Test packages" in catalog
    assert catalog.index("[Alpha Package](alpha/index.md)") < catalog.index(
        "[Beta Package](beta/index.md)"
    )
    assert "Documentation for alpha." in catalog

    assert (prepared / "index.md").is_file()
    assert (prepared / "overlay.txt").read_text() == "site overlay\n"
    assert (prepared / "plugin-development/index.md").is_file()
    assert not (prepared / "plugin-development/AGENTS.md").exists()
    plugin_page = (
        prepared / "built-in-plugins/example-plugin/index.md"
    ).read_text(encoding="utf-8")
    assert "[Default config](../../reference/default-config.md)" in plugin_page
    assert "[browse guides and development docs](docs/index.md)" in plugin_page
    plugin_docs_index = (
        prepared / "built-in-plugins/example-plugin/docs/index.md"
    ).read_text(encoding="utf-8")
    assert "[Example Plugin Guide](guide.md)" in plugin_docs_index
    plugin_guide = (
        prepared / "built-in-plugins/example-plugin/docs/guide.md"
    ).read_text(encoding="utf-8")
    assert "[Plugin README](../index.md)" in plugin_guide
    assert not (
        prepared
        / "built-in-plugins/example-plugin/docs/development/AGENTS.md"
    ).exists()
    assert (prepared / "reference/default-config.md").is_file()


def test_plugin_authored_docs_index_takes_precedence(tmp_path: Path) -> None:
    root = create_repository(tmp_path)
    write(
        root / "plugins/example-plugin/docs/index.md",
        "# Authored Plugin Documentation\n\n[Guide](guide.md)\n",
    )

    prepare.prepare_docs_site(root)

    index = (
        root / "docs_site/prepared/built-in-plugins/example-plugin/docs/index.md"
    ).read_text(encoding="utf-8")
    assert "# Authored Plugin Documentation" in index
    assert "Generated from `plugins/example-plugin/docs/`." not in index


def test_development_docs_can_be_excluded(tmp_path: Path) -> None:
    root = create_repository(tmp_path)
    write(
        registry_path(root),
        "\n".join(
            [
                "version = 1",
                "",
                package_toml(
                    "beta",
                    "packages/beta",
                    title="Beta Package",
                    publish_development=False,
                ),
            ]
        ),
    )

    prepare.prepare_docs_site(root)

    destination = root / "docs_site/prepared/packages/beta"
    assert (destination / "index.md").is_file()
    assert (destination / "guide.md").is_file()
    assert not (destination / "development").exists()


@pytest.mark.parametrize(
    ("registry", "message"),
    [
        (
            "\n".join(
                [
                    "version = 1",
                    package_toml("alpha", "packages/alpha"),
                    package_toml(
                        "alpha",
                        "packages/beta",
                        destination="packages/alpha",
                    ),
                ]
            ),
            "duplicate package id",
        ),
        (
            "\n".join(
                [
                    "version = 1",
                    package_toml("alpha", "packages/alpha"),
                    package_toml(
                        "beta",
                        "packages/beta",
                        destination="packages/alpha",
                    ),
                ]
            ),
            "duplicate package destination",
        ),
        (
            "\n".join(
                [
                    "version = 1",
                    package_toml("alpha", "packages/alpha"),
                    package_toml("beta", "packages/alpha"),
                ]
            ),
            "duplicate package source",
        ),
        (
            "\n".join(
                [
                    "version = 1",
                    package_toml("Bad_ID", "packages/alpha"),
                ]
            ),
            "lowercase URL-safe kebab-case",
        ),
        (
            "\n".join(
                [
                    "version = 1",
                    package_toml("alpha", "../outside"),
                ]
            ),
            "without traversal",
        ),
        (
            "\n".join(
                [
                    "version = 1",
                    package_toml(
                        "alpha",
                        "packages/alpha",
                        include_docs=False,
                        publish_development=True,
                    ),
                ]
            ),
            "publish_development cannot be true",
        ),
        (
            "\n".join(
                [
                    "version = 1",
                    package_toml("alpha", "packages/alpha"),
                    'unexpected = "value"',
                ]
            ),
            "unknown key",
        ),
        (
            "\n".join(
                [
                    "version = 1",
                    "[[package]]",
                    'id = "alpha"',
                    'group = "Test packages"',
                    'summary = "Alpha docs."',
                    'source = "packages/alpha"',
                    'destination = "packages/alpha"',
                    "include_readme = true",
                    "include_docs = true",
                    "publish_development = true",
                ]
            ),
            "missing required key",
        ),
    ],
)
def test_invalid_registry_is_actionable_and_non_destructive(
    tmp_path: Path,
    registry: str,
    message: str,
) -> None:
    root = create_repository(tmp_path)
    prepared = root / "docs_site/prepared"
    write(prepared / "sentinel.txt", "old output\n")
    write(registry_path(root), registry)

    with pytest.raises(prepare.PreparationError, match=message):
        prepare.prepare_docs_site(root)

    assert (prepared / "sentinel.txt").read_text() == "old output\n"


def test_missing_and_non_public_sources_are_rejected(tmp_path: Path) -> None:
    root = create_repository(tmp_path)
    write(
        registry_path(root),
        "\n".join(
            [
                "version = 1",
                package_toml("missing", "packages/missing"),
            ]
        ),
    )
    with pytest.raises(prepare.PreparationError, match="does not exist"):
        prepare.create_preparation_plan(prepare.SitePaths.from_repo_root(root))

    write(root / "maintainer/README.md", "# Private\n")
    write(
        registry_path(root),
        "\n".join(
            [
                "version = 1",
                package_toml(
                    "private",
                    "maintainer",
                    include_docs=False,
                    publish_development=False,
                ),
            ]
        ),
    )
    with pytest.raises(prepare.PreparationError, match="non-public source root"):
        prepare.create_preparation_plan(prepare.SitePaths.from_repo_root(root))


def test_fixed_output_collision_is_rejected(tmp_path: Path) -> None:
    root = create_repository(tmp_path)
    write(root / "docs/packages/alpha/index.md", "# Existing output\n")

    with pytest.raises(
        prepare.PreparationError,
        match="collides with an existing prepared path",
    ):
        prepare.create_preparation_plan(prepare.SitePaths.from_repo_root(root))


def test_assembly_failure_keeps_previous_prepared_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = create_repository(tmp_path)
    prepared = root / "docs_site/prepared"
    write(prepared / "sentinel.txt", "old output\n")

    def fail_generation(paths: prepare.SitePaths, output_root: Path) -> None:
        raise RuntimeError("simulated generation failure")

    monkeypatch.setattr(
        prepare,
        "generate_default_config_reference",
        fail_generation,
    )

    with pytest.raises(RuntimeError, match="simulated generation failure"):
        prepare.prepare_docs_site(root)

    assert (prepared / "sentinel.txt").read_text() == "old output\n"
    assert not list((root / "docs_site").glob(".prepared-staging-*"))