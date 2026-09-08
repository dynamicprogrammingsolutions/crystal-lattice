# Copyright 2026 Dynamic Programming Solutions Kft.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Claude Code-compatible tool plugin bundle."""

import importlib

from .claude_compaction_feature import ClaudeCompactionFeature

# Tool modules are exported lazily so that consumers of the light modules
# (for example the compaction feature) do not need the tool dependency tree
# (shared helper packages and their external dependencies).
_LAZY_TOOL_EXPORTS = {
    "ClaudeBashTool": "claude_bash_tool",
    "ClaudeEditTool": "claude_edit_tool",
    "ClaudeGlobTool": "claude_glob_tool",
    "ClaudeGrepTool": "claude_grep_tool",
    "ClaudeMCPTool": "claude_mcp_tool",
    "ClaudeReadTool": "claude_read_tool",
    "ClaudeTaskStopTool": "claude_task_stop_tool",
    "ClaudeWebFetchTool": "claude_web_fetch_tool",
    "ClaudeWebSearchTool": "claude_web_search_tool",
    "ClaudeWriteTool": "claude_write_tool",
}


def __getattr__(name: str):
    module_name = _LAZY_TOOL_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(f".{module_name}", __name__)
    return getattr(module, name)


__all__ = [
    "ClaudeBashTool",
    "ClaudeCompactionFeature",
    "ClaudeReadTool",
    "ClaudeWriteTool",
    "ClaudeEditTool",
    "ClaudeGrepTool",
    "ClaudeGlobTool",
    "ClaudeMCPTool",
    "ClaudeTaskStopTool",
    "ClaudeWebFetchTool",
    "ClaudeWebSearchTool",
]
