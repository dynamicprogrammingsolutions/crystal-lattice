import os
import shlex
import stat
import subprocess
import tarfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
INSTALL_SCRIPT = ROOT / "application" / "python" / "scripts" / "install.sh"


def _write_executable(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _write_fake_commands(tmp_path: Path, archive: Path, requested_url: Path) -> Path:
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    archive_arg = shlex.quote(str(archive))
    requested_url_arg = shlex.quote(str(requested_url))
    _write_executable(
        fake_bin / "uname",
        """#!/usr/bin/env sh
case "$1" in
  -s) printf '%s\\n' "$FAKE_UNAME_S" ;;
  -m) printf '%s\\n' "$FAKE_UNAME_M" ;;
  *) exit 1 ;;
esac
""",
    )
    _write_executable(
        fake_bin / "curl",
        f"""#!/usr/bin/env sh
if [ "$1" = "-fsSL" ]; then
  case "$2" in
    */latest.txt) printf '%s\\n' 'crystal-lattice-cli-v9.8.7' ;;
    *) exit 1 ;;
  esac
elif [ "$1" = "-fL" ]; then
  printf '%s\\n' "$2" > {requested_url_arg}
  [ "$3" = "-o" ] || exit 1
  cp {archive_arg} "$4"
else
  exit 1
fi
""",
    )
    return fake_bin


def _launcher_text(plugin_path: str = "/tmp/plugins") -> str:
    return f"""#!/usr/bin/env sh
case "$1" in
  --help) exit 0 ;;
  --runtime-layout-json)
    printf '%s\\n' '{{"layout": "python-runtime", "bundle_paths": {{"builtin_plugins": "{plugin_path}"}}}}'
    ;;
  *) exit 0 ;;
esac
"""


def _make_posix_archive(tmp_path: Path, stem: str) -> Path:
    bundle = tmp_path / "bundle-src" / stem
    _write_executable(bundle / "bin" / "crystal-lattice", _launcher_text())
    archive = tmp_path / f"{stem}.tar.gz"
    with tarfile.open(archive, "w:gz") as tf:
        tf.add(bundle, arcname=stem)
    return archive


def _make_windows_archive(tmp_path: Path, stem: str) -> Path:
    bundle = tmp_path / "bundle-src" / stem
    _write_executable(
        bundle / "Scripts" / "crystal-lattice.cmd",
        _launcher_text("C:\\\\crystal-lattice\\\\plugins"),
    )
    archive = tmp_path / f"{stem}.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        launcher = bundle / "Scripts" / "crystal-lattice.cmd"
        info = zipfile.ZipInfo(f"{stem}/Scripts/crystal-lattice.cmd")
        info.external_attr = 0o755 << 16
        zf.writestr(info, launcher.read_bytes())
    return archive


def _run_installer(
    tmp_path: Path,
    *,
    archive: Path,
    uname_s: str,
    uname_m: str,
    explicit_bin_dir: bool = True,
    local_archive: bool = False,
) -> tuple[subprocess.CompletedProcess[str], Path, Path, Path]:
    requested_url = tmp_path / "requested-url.txt"
    fake_bin = _write_fake_commands(tmp_path, archive, requested_url)
    install_root = tmp_path / "install-root"
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    bin_dir = tmp_path / "bin" if explicit_bin_dir else home_dir / ".local" / "bin"
    bin_dir.mkdir(parents=True)
    inherited_path = os.pathsep.join(
        entry
        for entry in os.environ["PATH"].split(os.pathsep)
        if not any(
            (Path(entry) / name).exists()
            for name in (
                "crystal-lattice",
                "crystal-lattice.cmd",
                "crystal-lattice.exe",
            )
        )
    )
    env = {
        **os.environ,
        "PATH": os.pathsep.join([str(bin_dir), str(fake_bin), inherited_path]),
        "HOME": str(home_dir),
        "USERPROFILE": str(home_dir),
        "FAKE_UNAME_S": uname_s,
        "FAKE_UNAME_M": uname_m,
        "INSTALL_ROOT": str(install_root),
        "CRYSTAL_LATTICE_DOWNLOAD_BASE_URL": "https://example.test/crystal-lattice-cli",
    }
    if explicit_bin_dir:
        env["BIN_DIR"] = str(bin_dir)
    else:
        env.pop("BIN_DIR", None)
    if local_archive:
        env["CRYSTAL_LATTICE_PYTHON_RUNTIME_ARCHIVE"] = str(archive)
    else:
        env.pop("CRYSTAL_LATTICE_PYTHON_RUNTIME_ARCHIVE", None)
    env.pop("VIRTUAL_ENV", None)
    result = subprocess.run(
        ["bash", str(INSTALL_SCRIPT)],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    return result, requested_url, install_root, bin_dir


def test_install_script_installs_linux_tarball_to_isolated_paths(
    tmp_path: Path,
) -> None:
    stem = "crystal-lattice-python-runtime-v9.8.7-linux-amd64"
    archive = _make_posix_archive(tmp_path, stem)

    result, requested_url, install_root, bin_dir = _run_installer(
        tmp_path,
        archive=archive,
        uname_s="Linux",
        uname_m="x86_64",
    )

    assert result.returncode == 0, result.stderr
    assert requested_url.read_text(encoding="utf-8").strip().endswith(f"/{stem}.tar.gz")
    assert (install_root / stem / "bin" / "crystal-lattice").is_file()
    assert (
        "[1/5] Checking installer prerequisites and command location" in result.stdout
    )
    assert "[5/5] Verifying the installed command" in result.stdout
    shim = bin_dir / "crystal-lattice"
    assert shim.is_file()
    assert f'exec "{install_root / stem}/bin/crystal-lattice" "$@"' in shim.read_text(
        encoding="utf-8"
    )


def test_install_script_installs_linux_arm64_tarball(tmp_path: Path) -> None:
    stem = "crystal-lattice-python-runtime-v9.8.7-linux-arm64"
    archive = _make_posix_archive(tmp_path, stem)

    result, requested_url, install_root, bin_dir = _run_installer(
        tmp_path,
        archive=archive,
        uname_s="Linux",
        uname_m="aarch64",
    )

    assert result.returncode == 0, result.stderr
    assert requested_url.read_text(encoding="utf-8").strip().endswith(f"/{stem}.tar.gz")
    assert (install_root / stem / "bin" / "crystal-lattice").is_file()
    assert (bin_dir / "crystal-lattice").is_file()


def test_install_script_installs_windows_zip_from_git_bash(tmp_path: Path) -> None:
    stem = "crystal-lattice-python-runtime-v9.8.7-windows-amd64"
    archive = _make_windows_archive(tmp_path, stem)

    result, requested_url, install_root, bin_dir = _run_installer(
        tmp_path,
        archive=archive,
        uname_s="MINGW64_NT-10.0",
        uname_m="x86_64",
    )

    assert result.returncode == 0, result.stderr
    assert requested_url.read_text(encoding="utf-8").strip().endswith(f"/{stem}.zip")
    assert (install_root / stem / "Scripts" / "crystal-lattice.cmd").is_file()
    shim = bin_dir / "crystal-lattice"
    assert shim.is_file()
    assert (
        f'exec "{install_root / stem}/Scripts/crystal-lattice.cmd" "$@"'
        in shim.read_text(encoding="utf-8")
    )
    windows_shim = bin_dir / "crystal-lattice.cmd"
    assert windows_shim.is_file()
    assert "call " in windows_shim.read_text(encoding="utf-8")


def test_install_script_installs_windows_arm64_zip_from_git_bash(
    tmp_path: Path,
) -> None:
    stem = "crystal-lattice-python-runtime-v9.8.7-windows-arm64"
    archive = _make_windows_archive(tmp_path, stem)

    result, requested_url, install_root, bin_dir = _run_installer(
        tmp_path,
        archive=archive,
        uname_s="MINGW64_NT-10.0",
        uname_m="aarch64",
    )

    assert result.returncode == 0, result.stderr
    assert requested_url.read_text(encoding="utf-8").strip().endswith(f"/{stem}.zip")
    assert (install_root / stem / "Scripts" / "crystal-lattice.cmd").is_file()
    assert (bin_dir / "crystal-lattice").is_file()
    assert (bin_dir / "crystal-lattice.cmd").is_file()


def test_install_script_selects_existing_user_bin_from_path(tmp_path: Path) -> None:
    stem = "crystal-lattice-python-runtime-v9.8.7-linux-amd64"
    archive = _make_posix_archive(tmp_path, stem)

    result, _requested_url, install_root, bin_dir = _run_installer(
        tmp_path,
        archive=archive,
        uname_s="Linux",
        uname_m="x86_64",
        explicit_bin_dir=False,
    )

    assert result.returncode == 0, result.stderr
    assert (install_root / stem).is_dir()
    assert (bin_dir / "crystal-lattice").is_file()
    assert "Add this directory to PATH" not in result.stdout


def test_install_script_accepts_local_runtime_archive(tmp_path: Path) -> None:
    stem = "crystal-lattice-python-runtime-v9.8.7-linux-amd64"
    archive = _make_posix_archive(tmp_path, stem)

    result, requested_url, install_root, bin_dir = _run_installer(
        tmp_path,
        archive=archive,
        uname_s="Linux",
        uname_m="x86_64",
        local_archive=True,
    )

    assert result.returncode == 0, result.stderr
    assert not requested_url.exists()
    assert (install_root / stem).is_dir()
    assert (bin_dir / "crystal-lattice").is_file()
    assert f"from {archive}" in result.stdout


def test_install_script_skips_incompatible_existing_command_directory(
    tmp_path: Path,
) -> None:
    stem = "crystal-lattice-python-runtime-v9.8.7-linux-amd64"
    archive = _make_posix_archive(tmp_path, stem)
    requested_url = tmp_path / "requested-url.txt"
    fake_bin = _write_fake_commands(tmp_path, archive, requested_url)
    conflict_bin = tmp_path / "conflict-bin"
    _write_executable(
        conflict_bin / "crystal-lattice",
        """#!/usr/bin/env sh
if [ "$1" = "--runtime-layout-json" ]; then
  printf '%s\n' '{"layout": "source"}'
fi
""",
    )
    home_dir = tmp_path / "home"
    preferred_bin = home_dir / ".local" / "bin"
    preferred_bin.mkdir(parents=True)
    install_root = tmp_path / "install-root"
    env = {
        **os.environ,
        "PATH": os.pathsep.join(
            [str(conflict_bin), str(preferred_bin), str(fake_bin), os.environ["PATH"]]
        ),
        "HOME": str(home_dir),
        "USERPROFILE": str(home_dir),
        "FAKE_UNAME_S": "Linux",
        "FAKE_UNAME_M": "x86_64",
        "INSTALL_ROOT": str(install_root),
        "CRYSTAL_LATTICE_DOWNLOAD_BASE_URL": "https://example.test/crystal-lattice-cli",
    }
    env.pop("BIN_DIR", None)
    env.pop("VIRTUAL_ENV", None)

    result = subprocess.run(
        ["bash", str(INSTALL_SCRIPT)],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert '"layout": "source"' in (conflict_bin / "crystal-lattice").read_text(
        encoding="utf-8"
    )
    assert (preferred_bin / "crystal-lattice").is_file()


def test_install_script_reuses_existing_runtime_command_directory(
    tmp_path: Path,
) -> None:
    stem = "crystal-lattice-python-runtime-v9.8.7-linux-amd64"
    archive = _make_posix_archive(tmp_path, stem)
    requested_url = tmp_path / "requested-url.txt"
    fake_bin = _write_fake_commands(tmp_path, archive, requested_url)
    existing_bin = tmp_path / "existing-bin"
    _write_executable(
        existing_bin / "crystal-lattice",
        """#!/usr/bin/env sh
if [ "$1" = "--runtime-layout-json" ]; then
  printf '%s\n' '{"layout": "python-runtime"}'
fi
""",
    )
    home_dir = tmp_path / "home"
    preferred_bin = home_dir / ".local" / "bin"
    preferred_bin.mkdir(parents=True)
    install_root = tmp_path / "install-root"
    env = {
        **os.environ,
        "PATH": os.pathsep.join(
            [str(existing_bin), str(preferred_bin), str(fake_bin), os.environ["PATH"]]
        ),
        "HOME": str(home_dir),
        "USERPROFILE": str(home_dir),
        "FAKE_UNAME_S": "Linux",
        "FAKE_UNAME_M": "x86_64",
        "INSTALL_ROOT": str(install_root),
        "CRYSTAL_LATTICE_DOWNLOAD_BASE_URL": "https://example.test/crystal-lattice-cli",
    }
    env.pop("BIN_DIR", None)
    env.pop("VIRTUAL_ENV", None)

    result = subprocess.run(
        ["bash", str(INSTALL_SCRIPT)],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert f"Installed command: {existing_bin}/crystal-lattice" in result.stdout
    assert f'exec "{install_root / stem}/bin/crystal-lattice" "$@"' in (
        existing_bin / "crystal-lattice"
    ).read_text(encoding="utf-8")
    assert not (preferred_bin / "crystal-lattice").exists()


def test_install_script_fails_when_path_has_no_suitable_directory(
    tmp_path: Path,
) -> None:
    stem = "crystal-lattice-python-runtime-v9.8.7-linux-amd64"
    archive = _make_posix_archive(tmp_path, stem)
    requested_url = tmp_path / "requested-url.txt"
    fake_bin = _write_fake_commands(tmp_path, archive, requested_url)
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    install_root = tmp_path / "install-root"
    env = {
        **os.environ,
        "PATH": os.pathsep.join([str(fake_bin), "/usr/bin", "/bin"]),
        "HOME": str(home_dir),
        "USERPROFILE": str(home_dir),
        "VIRTUAL_ENV": str(tmp_path),
        "FAKE_UNAME_S": "Linux",
        "FAKE_UNAME_M": "x86_64",
        "INSTALL_ROOT": str(install_root),
        "CRYSTAL_LATTICE_DOWNLOAD_BASE_URL": "https://example.test/crystal-lattice-cli",
    }
    env.pop("BIN_DIR", None)

    result = subprocess.run(
        ["bash", str(INSTALL_SCRIPT)],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "could not find an existing writable command directory on PATH" in (
        result.stderr
    )
    assert not install_root.exists()


def test_install_script_rejects_unsupported_windows_architecture(
    tmp_path: Path,
) -> None:
    stem = "crystal-lattice-python-runtime-v9.8.7-windows-amd64"
    archive = _make_windows_archive(tmp_path, stem)

    result, _requested_url, _install_root, _bin_dir = _run_installer(
        tmp_path,
        archive=archive,
        uname_s="MINGW64_NT-10.0",
        uname_m="riscv64",
    )

    assert result.returncode != 0
    assert "unsupported Windows architecture for Git Bash installer" in result.stderr
