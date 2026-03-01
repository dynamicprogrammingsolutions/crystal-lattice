# `search_tool_bm25`

Discovers “Apps” MCP tools by searching over their metadata (BM25). Matching tools are then added to the tool list for subsequent turns.

## Handler behavior (implementation notes)

- This is only present when Apps mode/features are enabled.
- The description text in the real tool spec substitutes `{{app_names}}` with a comma-separated list of connector names.
