#!/usr/bin/env python3
"""Run the full MkDocs site build pipeline."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import prepare_mkdocs_site
import refresh_reference_snapshots


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
    refresh_reference_snapshots.refresh_reference_snapshots()
    return 0


if __name__ == "__main__":
    sys.exit(main())