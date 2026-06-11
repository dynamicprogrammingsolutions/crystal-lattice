from __future__ import annotations

from pathlib import Path
import sys


def _add_plugin_src_paths() -> None:
    plugins_root = Path("/opt/ai-agent-platform/plugins")
    if not plugins_root.is_dir():
        return
    for child in sorted(plugins_root.iterdir()):
        src = child / "src"
        if src.is_dir():
            src_str = str(src)
            if src_str not in sys.path:
                sys.path.append(src_str)


_add_plugin_src_paths()