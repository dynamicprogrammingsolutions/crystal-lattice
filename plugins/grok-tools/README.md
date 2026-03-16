# Grok Tools

Compatibility-oriented Grok-style filesystem tools for the AI Agent Platform.

Current scope in this subtask:
- `view_file`
- `create_file`
- `str_replace_editor`

This package keeps the Grok-facing schema and combined file-view / directory-list
surface while using shared Python helpers for filesystem access. Host-level
approval UX and the surrounding agent prompting strategy remain outside the
scope of these pure tool plugins.