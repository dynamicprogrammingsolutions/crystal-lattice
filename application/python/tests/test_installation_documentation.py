from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SHELL_COMMAND = (
    "curl -fsSL "
    "https://download.crystallattice.dev/crystal-lattice-cli/install.sh "
    "| bash"
)
POWERSHELL_COMMAND = (
    "irm "
    "https://download.crystallattice.dev/crystal-lattice-cli/install.ps1 "
    "| iex"
)
TARGETS = (
    "darwin-amd64",
    "darwin-arm64",
    "linux-amd64",
    "linux-arm64",
    "windows-amd64",
    "windows-arm64",
)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_installation_overview_routes_to_each_supported_method() -> None:
    overview = read("application/python/docs/installation.md")

    for target in (
        "installation-macos-linux.md",
        "installation-windows.md",
        "installation-manual.md",
    ):
        assert target in overview
    assert "crystal-lattice --help" in overview
    assert "crystal-lattice --console" in overview
    assert "do not need a system Python installation or provider credentials" in (
        overview
    )
    assert ".env" in overview


def test_platform_guides_use_the_public_installer_commands_and_paths() -> None:
    macos_linux = read("application/python/docs/installation-macos-linux.md")
    windows = read("application/python/docs/installation-windows.md")

    assert SHELL_COMMAND in macos_linux
    assert "~/.local/opt/crystal-lattice-cli/" in macos_linux
    assert 'BIN_DIR="$HOME/.local/bin"' in macos_linux
    for target in TARGETS[:4]:
        assert target in macos_linux

    assert POWERSHELL_COMMAND in windows
    assert "%USERPROFILE%\\.local\\opt\\crystal-lattice-cli" in windows
    assert "%LOCALAPPDATA%\\Programs\\Crystal Lattice\\bin" in windows
    assert "Get-Command crystal-lattice" in windows
    assert "where crystal-lattice" in windows
    assert "administrator rights" in windows
    assert "Windows x64 or ARM64" in windows


def test_manual_guide_maps_every_archive_and_real_launcher() -> None:
    manual = read("application/python/docs/installation-manual.md")

    for target in TARGETS:
        assert target in manual
    assert "bin/crystal-lattice" in manual
    assert "Scripts\\crystal-lattice.cmd" in manual
    assert "archive filename without `.tar.gz` or `.zip`" in manual
    assert "checksum" not in manual.lower()
    assert "latest GitHub Release" in manual


def test_package_entry_points_route_to_focused_installation_guides() -> None:
    root_readme = read("README.md")
    app_readme = read("application/python/README.md")
    docs_index = read("application/python/docs/index.md")
    quickstart = read("application/python/docs/quickstart.md")

    assert SHELL_COMMAND in root_readme
    assert POWERSHELL_COMMAND in root_readme
    assert "application/python/docs/installation.md" in root_readme

    for path in (
        "docs/installation.md",
        "docs/installation-macos-linux.md",
        "docs/installation-windows.md",
        "docs/installation-manual.md",
    ):
        assert path in app_readme
    assert "PowerShell installation is not implemented" not in app_readme

    for page in (
        "installation.md",
        "installation-macos-linux.md",
        "installation-windows.md",
        "installation-manual.md",
    ):
        assert page in docs_index
    for page in (
        "installation-macos-linux.md",
        "installation-windows.md",
        "installation-manual.md",
    ):
        assert page in quickstart


def test_docs_site_navigation_and_llm_index_publish_installation_pages() -> None:
    mkdocs = read("docs_site/mkdocs.yml")

    for page in (
        "packages/application-python/installation.md",
        "packages/application-python/installation-macos-linux.md",
        "packages/application-python/installation-windows.md",
        "packages/application-python/installation-manual.md",
    ):
        assert page in mkdocs
