# claude-tools

Claude Code-compatible tool plugin bundle for Crystal Lattice.

This package is being built from behavior-driven investigations of Claude Code's Anthropic API traffic. Raw logs live under `investigation/raw/` and are ignored; normalized fixtures and implementation notes live under `investigation/fixtures/` and `investigation/notes/`.

## Implemented Tools

- `Read`: Claude Code-compatible file reader with Anthropic-native schemas and tool-result payloads.

`Read` currently supports text files, images, PDF status/page rendering through Poppler, simple Jupyter notebooks, and observed Claude Code error formatting. OpenAI Chat Completions-compatible providers consume the Anthropic-native result through a narrow temporary bridge until first-class tool-result interop lands.
