# Qwen Tools

Compatibility-oriented Qwen-style filesystem tools for the AI Agent Platform.

Current scope in this subtask:
- `read_file`
- `write_file`
- `edit`

This package keeps the Qwen-specific schema, absolute-path validation, and
truncation wording while reusing shared Python helpers for filesystem access.
CLI confirmation UX and IDE/approval integrations from Qwen Code are out of
scope for this tool-plugin implementation.