# `js_repl`

Executes JavaScript in a persistent Node kernel, with support for top-level `await`.

## Handler behavior (implementation notes)

- Tool input is freeform JS source text.
- Codex rejects common malformed inputs (JSON wrappers, quoted strings, markdown fences) before execution.
- Output is returned as plain text (and may include runtime diagnostics).
