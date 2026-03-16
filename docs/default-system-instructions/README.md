# Default System Instructions

This directory collects human-oriented reconstruction material for multiple agent families.

The goal is to make it easy to:

1. copy and paste sections into a final system message
2. understand which parts are static and which depend on runtime state
3. see concrete examples of dynamic-element substitution
4. hand off further research or implementation work without rediscovering source material

## Vendor layout

The Gemini, Qwen, and Grok directories follow the same general shape:

- `template.md`: top-level raw text containing section placeholders
- section files: raw text for individual sections, sometimes with smaller placeholders inside
- `dynamic-elements.md`: explanation of every dynamic element with examples
- `compiled.md`: a worked example with placeholders substituted
- `agent-notes.md`: extra research and implementation notes with repo-relative source references

`codex/` remains an extracted archive of model instruction files rather than a newly reconstructed template set.