import os
from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    CONFIG = {}


def _tool_usage_path(filename: str) -> Path:
    builtin_plugins = os.environ.get("BUILTIN_PLUGINS", "")
    return (
        Path(builtin_plugins) / "claude-tools" / "system_messages" / "claude" / filename
    )


_config = globals().get("CONFIG", {})
if not isinstance(_config, dict):
    _config = {}
_cwd_persistence = bool(_config.get("bash_cwd_persistence", True))
_filename = (
    "tool-usage-permissive-cd.md"
    if _cwd_persistence
    else "tool-usage-permissive-cd-no-persistence.md"
)
try:
    SYSTEM_MESSAGE_VALUE = _tool_usage_path(_filename).read_text(encoding="utf-8")
except Exception:
    SYSTEM_MESSAGE_VALUE = ""
