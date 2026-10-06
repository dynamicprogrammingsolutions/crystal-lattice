#!/usr/bin/env python3
"""Prepare and build the MkDocs site."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import prepare_mkdocs_site


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_SITE_DIR = REPO_ROOT / "docs_site"

def main() -> int:
    prepare_mkdocs_site.main()
    result = subprocess.run(
        ["mkdocs", "build"],
        cwd=DOCS_SITE_DIR,
        check=False,
    )
    if result.returncode != 0:
        return result.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())