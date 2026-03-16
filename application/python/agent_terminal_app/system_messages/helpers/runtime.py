import subprocess
from pathlib import Path


cwd = str(Path.cwd().resolve())


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
