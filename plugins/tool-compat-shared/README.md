# Tool Compatibility Shared Helpers

Internal helper package for the vendor-style tool bundles.

This package is intentionally not a public plugin package and does not expose
`agent_plugin.json` entries. It exists only to share filesystem, decoding,
truncation, and formatting logic across `gemini-tools`, `qwen-tools`, and
`grok-tools`.