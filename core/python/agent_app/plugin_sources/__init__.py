"""Plugin sources for the application plugin manager.

Plugin sources are responsible for resolving a single spec into one or more
plugin classes (including any installation, cloning, descriptor parsing, and
import work).

The application-level :class:`agent_app.plugin_manager.PluginManager` is kept
thin and only orchestrates across sources.
"""

from .types import PluginContext, PluginResolution, PluginSource
from .dotted import DottedClassSource
from .bash_tool import BashToolSource
from .node_tool import NodeToolSource
from .local_path import LocalPathRepoSource
from .git_repo import GitRepoSource

__all__ = [
    "BashToolSource",
    "DottedClassSource",
    "GitRepoSource",
    "LocalPathRepoSource",
    "NodeToolSource",
    "PluginContext",
    "PluginResolution",
    "PluginSource",
]
