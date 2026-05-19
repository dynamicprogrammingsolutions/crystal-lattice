import os
import platform
import shutil
import subprocess
from pathlib import Path


CONFIG = globals().get("CONFIG", {})


def _resolve_path(raw_path: str, *, base: Path) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = base / path
    try:
        return path.resolve()
    except Exception:
        return path.absolute()


def _resolve_effective_cwd() -> Path:
    process_cwd = Path.cwd().resolve()
    raw_value = CONFIG.get("working_directory") if isinstance(CONFIG, dict) else None
    if isinstance(raw_value, str) and raw_value.strip():
        return _resolve_path(raw_value, base=process_cwd)
    return process_cwd


def _detect_shell() -> str:
    system = platform.system()
    if system == "Windows":
        return (
            shutil.which("powershell.exe")
            or shutil.which("pwsh.exe")
            or os.environ.get("COMSPEC")
            or "cmd.exe"
        )

    shell_path = os.environ.get("SHELL", "")
    if shell_path:
        return shell_path

    for candidate in ("/bin/bash", "/usr/bin/bash", "/usr/local/bin/bash", "/bin/sh"):
        if Path(candidate).exists():
            return candidate
    return "/bin/sh"


cwd = str(_resolve_effective_cwd())
shell = _detect_shell()


def git_root(path: str | None = None) -> str | None:
    target = Path(path or cwd)
    if not target.is_absolute():
        target = Path(cwd) / target

    try:
        target = target.resolve()
    except Exception:
        target = target.absolute()

    if target.is_file():
        target = target.parent

    try:
        proc = subprocess.run(
            ["git", "-C", str(target), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
            timeout=2,
        )
    except Exception:
        return None

    if proc.returncode != 0:
        return None

    value = (proc.stdout or "").strip()
    return value or None


def is_git_repo(path: str | None = None) -> bool:
    return git_root(path) is not None