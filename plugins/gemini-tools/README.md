# Gemini Tools

Compatibility-oriented Gemini-style filesystem tools for the AI Agent Platform.

Current scope in this subtask:
- `read_file`
- `write_file`
- `replace`

The package aims to match Gemini CLI model-facing schemas and important output
strings closely, while reusing shared Python filesystem helpers underneath.
Structured media payloads are preserved in tool results, but the current tool
message pipeline is still text-first. CLI confirmation UX, IDE diff handoff,
and other host-managed approval flows are intentionally out of scope here.