from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    cwd = ""

    def git_root(path: str | None = None) -> str | None: ...


def _candidate_instruction_files() -> list[Path]:
    current = Path(cwd).resolve()
    repo_root_value = git_root()

    candidates: list[Path] = []
    for candidate in (
        current / "AGENTS.md",
        Path(repo_root_value) / "AGENTS.md" if repo_root_value else None,
    ):
        if candidate is None:
            continue
        if candidate.is_file() and candidate not in candidates:
            candidates.append(candidate)
    return candidates


def _load_text(paths: list[Path]) -> str:
    parts: list[str] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8").strip()
        except Exception:
            continue
        if text:
            parts.append(text)
    return "\n\n".join(parts)


instruction_files = _candidate_instruction_files()
loaded_context = _load_text(instruction_files)

if loaded_context:
    SYSTEM_MESSAGE_VALUE = (
        "# Contextual Instructions (AGENTS.md)\n"
        "The following content is loaded from local configuration files.\n\n"
        f"<loaded_context>\n{loaded_context}\n</loaded_context>"
    )
else:
    SYSTEM_MESSAGE_VALUE = ""
