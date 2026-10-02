from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
INSTALL_SCRIPT = ROOT / "application" / "python" / "scripts" / "install.ps1"


def test_powershell_installer_is_native_and_supports_both_windows_architectures() -> (
    None
):
    script = INSTALL_SCRIPT.read_text(encoding="utf-8")

    assert '"windows-amd64"' in script
    assert '"windows-arm64"' in script
    assert "System.Net.WebClient" in script
    assert "System.IO.Compression.ZipFile" in script
    assert "Expand-Archive" not in script
    assert "Scripts\\crystal-lattice.cmd" in script
    assert "bash" not in script.lower()
    assert "python -m" not in script.lower()


def test_powershell_installer_supports_public_and_deterministic_inputs() -> None:
    script = INSTALL_SCRIPT.read_text(encoding="utf-8")

    for name in (
        "CRYSTAL_LATTICE_DOWNLOAD_BASE_URL",
        "CRYSTAL_LATTICE_PYTHON_RUNTIME_ARCHIVE",
        "DOWNLOAD_BASE_URL",
        "INSTALL_ROOT",
        "BIN_DIR",
        "COMMAND_NAME",
        "VERSION",
    ):
        assert f"$env:{name}" in script
    assert "latest.txt" in script
    assert "$DefaultDownloadBaseUrl" in script


def test_powershell_installer_uses_no_admin_user_path_fallback() -> None:
    script = INSTALL_SCRIPT.read_text(encoding="utf-8")

    assert 'Join-Path $localAppData "Programs\\Crystal Lattice\\bin"' in script
    assert '[Environment]::SetEnvironmentVariable("Path", $newUserPath, "User")' in (
        script
    )
    assert 'SetEnvironmentVariable("Path", $newUserPath, "Machine")' not in script
    assert "RunAs" not in script
    assert "PowerShell profile" not in script


def test_powershell_installer_reports_all_progress_phases() -> None:
    script = INSTALL_SCRIPT.read_text(encoding="utf-8")

    assert "$LogStepTotal = 5" in script
    assert (
        sum(
            line.strip().startswith("Write-InstallStep ")
            for line in script.splitlines()
        )
        == 5
    )
    for phase in (
        "Checking installer prerequisites and command location",
        "Resolving the target platform and release",
        "Acquiring the bundled-Python archive",
        "Installing the runtime and command",
        "Verifying the installed command",
    ):
        assert phase in script
