"""On-the-fly plugin provisioning for tests that require repo plugins.

Application and core test suites must not depend on plugin packages being
installed in the active environment. When a test genuinely needs a repo
plugin (for example, an application default-config test that drives a
provider plugin), it provisions the plugin on the fly with this helper:
the plugin and its dependencies are pip-installed into a throwaway
target directory that the test adds to ``sys.path``.

The plugin's own test suites do not use this helper; installing the plugin
package (``pip install -e "plugins/<name>[dev]"``) provisions their
environment because the plugin owns its dependencies.
"""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path


def module_importable(name: str) -> bool:
    """Return True when importing ``name`` succeeds in the current interpreter."""
    try:
        importlib.import_module(name)
    except ImportError:
        return False
    return True


def provision_plugin(plugin_dir: Path, target_dir: Path) -> None:
    """Pip-install ``plugin_dir`` with its dependencies into ``target_dir``.

    Uses ``pip install --target`` so the install is hermetic: it never
    mutates the active environment and resolves the plugin's declared
    dependencies (for example the ``openai`` SDK for ``openai_responses``)
    from the package index.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--quiet",
            "--no-input",
            "--target",
            str(target_dir),
            str(plugin_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"on-the-fly plugin install failed for {plugin_dir}:\n{result.stderr}"
        )
