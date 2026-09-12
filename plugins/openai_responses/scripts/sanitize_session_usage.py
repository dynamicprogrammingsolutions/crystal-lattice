#!/usr/bin/env python
"""Remove unsupported persisted OpenAI Responses usage root fields."""

from __future__ import annotations

import sys
from contextlib import redirect_stdout
from pathlib import Path


_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
_REPO_ROOT = _PLUGIN_ROOT.parents[1]
_SRC_ROOT = _PLUGIN_ROOT / "src"
_CORE_ROOT = _REPO_ROOT / "core" / "python"
for source_root in (_CORE_ROOT, _SRC_ROOT):
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))

with redirect_stdout(sys.stderr):
    from openai_responses_plugins.openai_responses_usage_session_sanitizer import (
        main,
    )


if __name__ == "__main__":
    raise SystemExit(main())
