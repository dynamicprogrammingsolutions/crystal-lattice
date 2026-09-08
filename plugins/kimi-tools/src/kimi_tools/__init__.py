import importlib

# Tool modules are exported lazily so that consumers of the light modules
# (for example the compaction feature) do not need the tool dependency tree
# (shared helper packages and their external dependencies).
_LAZY_TOOL_EXPORTS = {
    "KimiReadFileTool": "kimi_read_file_tool",
    "KimiWriteFileTool": "kimi_write_file_tool",
    "KimiStrReplaceFileTool": "kimi_str_replace_file_tool",
    "KimiGlobTool": "kimi_glob_tool",
    "KimiGrepTool": "kimi_grep_tool",
    "KimiShellTool": "kimi_shell_tool",
    "KimiFetchURLTool": "kimi_fetch_url_tool",
    "KimiReadMediaFileTool": "kimi_read_media_file_tool",
    "KimiWebSearchTool": "kimi_web_search_tool",
}


def __getattr__(name: str):
    module_name = _LAZY_TOOL_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(f".{module_name}", __name__)
    return getattr(module, name)


__all__ = [
    "KimiReadFileTool",
    "KimiReadMediaFileTool",
    "KimiWriteFileTool",
    "KimiStrReplaceFileTool",
    "KimiGlobTool",
    "KimiGrepTool",
    "KimiShellTool",
    "KimiFetchURLTool",
    "KimiWebSearchTool",
]
