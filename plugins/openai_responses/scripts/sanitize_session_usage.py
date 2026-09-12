#!/usr/bin/env python3
"""Remove persisted OpenAI Responses usage attribution from session JSON."""

from __future__ import annotations

import sys
from contextlib import redirect_stdout
from pathlib import Path


_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _PLUGIN_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

with redirect_stdout(sys.stderr):
    from openai_responses_plugins.openai_responses_usage_session_sanitizer import (
        main,
    )


if __name__ == "__main__":
    raise SystemExit(main())
