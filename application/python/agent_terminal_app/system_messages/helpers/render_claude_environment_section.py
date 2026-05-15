from pathlib import Path
import platform as platform_module
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    CONFIG = {}
    cwd = ""
    shell = ""

    def is_git_repo(path: str | None = None) -> bool: ...


def _shell_name(raw_shell: str) -> str:
    try:
        name = Path(raw_shell).name.strip()
    except Exception:
        name = ""
    return name or str(raw_shell or "").strip() or "unknown"


_cwd = str(Path(cwd).resolve())
_model = CONFIG.get("model") if isinstance(CONFIG, dict) else None
_model_line = (
    f" - You are powered by the model {_model}."
    if isinstance(_model, str) and _model
    else ""
)
_platform = platform_module.system().lower() or "unknown"
_os_version = (
    f"{platform_module.system()} {platform_module.release()}".strip() or "unknown"
)

_lines = [
    "# Environment",
    "You have been invoked in the following environment:",
    f" - Primary working directory: {_cwd}",
    f" - Is a git repository: {'true' if is_git_repo() else 'false'}",
    f" - Platform: {_platform}",
    f" - Shell: {_shell_name(str(shell))}",
    f" - OS Version: {_os_version}",
]
if _model_line:
    _lines.append(_model_line)
_lines.extend(
    [
        " - The most recent Claude model family is Claude 4.X. Model IDs - Opus 4.7: 'claude-opus-4-7', Sonnet 4.6: 'claude-sonnet-4-6', Haiku 4.5: 'claude-haiku-4-5-20251001'. When building AI applications, default to the latest and most capable Claude models.",
        " - Claude Code is available as a CLI in the terminal, desktop app (Mac/Windows), web app (claude.ai/code), and IDE extensions (VS Code, JetBrains).",
        " - Fast mode for Claude Code uses Claude Opus 4.6 with faster output and can be toggled with /fast.",
    ]
)

SYSTEM_MESSAGE_VALUE = "\n".join(_lines)