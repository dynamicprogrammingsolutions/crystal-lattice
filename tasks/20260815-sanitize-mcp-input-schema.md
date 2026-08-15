# Sanitize non-standard MCP tool input schemas

## Description

Some MCP servers (notably `mcp-gsheets@latest`) return tool `inputSchema` that is
not valid JSON Schema. The schemas use a TypeScript schema-library format
(Effect/Schema-style) with fields like `def`, `shape`, `element`, `entries`,
`options`, `innerType`, `type: "enum"`, `type: "optional"`, and `null`-valued
optional fields. When these schemas are forwarded to OpenRouter → Anthropic, the
API rejects them with `tools.N.custom.input_schema: JSON schema is invalid. It
must match JSON Schema draft 2020-12`, so the session fails on the first
request.

Sample session: `09ed27b2-7e6b-4b28-9b19-d32aa4cfb1b4` (agent
`claude-openrouter`, `mcp_server__mcp-gsheets__enabled: true`). The session only
contains the system message and the user "Hi"; no assistant response was ever
produced because the first request 400'd.

## Requirements checklist

- [x] MCP discovered tool `input_schema` is sanitized to valid JSON Schema
      (draft 2020-12) before being exposed to the rest of the platform.
- [x] Non-standard `type: "enum"` (with `entries`/`options`) is converted to
      `type: "string"` with an `enum` list.
- [x] Non-standard `type: "optional"` (with `innerType`) is unwrapped to the
      inner schema.
- [x] Non-standard `shape` is converted to `properties`; `element` is converted
      to `items`.
- [x] Non-standard wrapper fields (`def`, `entries`, `options`, `innerType`,
      `checks`, `isInt`, `isFinite`, `minValue`, `maxValue`) are removed.
- [x] `null`-valued optional fields (`format`, `minLength`, `maxLength`, etc.)
      are omitted.
- [x] Already-valid JSON Schema passes through unchanged (no regression).
- [x] Sanitization is covered by unit tests, including a regression test using
      the real `sheets_merge_cells` schema shape.

## Unresolved requirement questions and decisions

None. Scope is limited to input-schema sanitization at the MCP runtime
boundary; no provider or interop-layer changes are required.

## Supporting details

**Reproduction (performed during investigation):**
- Connected to `mcp-gsheets` via the platform's `MCPRuntimeManager`; 44 tools
  discovered, 5 with non-standard schemas (`sheets_format_cells`,
  `sheets_update_borders`, `sheets_merge_cells`, `sheets_unmerge_cells`,
  `sheets_add_conditional_formatting`).
- Ran the discovered schemas through `ClaudeMCPTool._prepare_tools` →
  `registry.convert_schemas` (Anthropic → OpenAI chat format). The conversion
  rewrites the wrapper (`name`/`description`/`input_schema` →
  `type:"function"`/`function.parameters`) but passes `parameters` through
  unchanged, so the non-standard fields survive.
- Sent a test request to OpenRouter with `anthropic/claude-haiku-4.5` and the
  converted tools. Got HTTP 400 from Amazon Bedrock, Google Vertex, and
  Anthropic: `tools.14.custom.input_schema: JSON schema is invalid. It must
  match JSON Schema draft 2020-12`.
- Sending only the first 5 (standard-schema) tools succeeded with HTTP 200.

**Schema flow through the code:**
1. `plugins/mcp-shared/src/mcp_shared/runtime.py:622`
   `_extract_discovered_tools()` reads `inputSchema` from the MCP server
   response as-is (only checks it's a dict).
2. `plugins/claude-tools/src/claude_tools/claude_mcp_tool.py:660`
   `_coerce_anthropic_input_schema()` only ensures top-level `type`/`properties`
   exist; no deep sanitization.
3. `plugins/openrouter/src/openrouter_plugins/openrouter_tools_extension.py:173`
   `registry.convert_schemas()` converts the wrapper format but passes
   `parameters` (the original `inputSchema`) through unchanged.
4. OpenRouter forwards to Anthropic → 400.

**Decision: fix at the MCP runtime boundary.** Sanitizing in
`_extract_discovered_tools` fixes the issue for every MCP server with
non-standard schemas, not just gsheets, and requires no changes to the tool
interop or provider layers. The `mcp-gsheets` upstream bug should also be
reported, but the platform-side sanitization is valuable as defense-in-depth.

**Non-standard → standard mapping (verified against real gsheets schemas):**

| Non-standard input | Standard JSON Schema output |
|---|---|
| `type: "enum"` + `options: [A,B]` or `entries: {A:A, B:B}` | `type: "string"` + `enum: [A, B]` |
| `type: "optional"` + `innerType: {…}` | unwrap to `innerType` |
| `shape: {…}` | `properties: {…}` (recursed) |
| `element: {…}` | `items: {…}` (recursed) |
| `def: {…}` | merge `def` content as base, then apply sibling overrides |
| `format: null`, `minLength: null`, etc. | omit null-valued optional fields |
| `checks`, `isInt`, `isFinite`, `minValue`, `maxValue`, `entries`, `options`, `innerType` | remove |

## Execution plan

Status: Approved

### Approach

Add a recursive `_sanitize_input_schema` helper in
`plugins/mcp-shared/src/mcp_shared/runtime.py` and call it from
`_extract_discovered_tools` when building each `MCPDiscoveredTool`. The helper
walks the schema dict and rewrites non-standard fields to standard JSON Schema
draft 2020-12, dropping unknown keys and null-valued optional fields. It
preserves standard JSON Schema keywords (`type`, `enum`, `description`,
`required`, `properties`, `items`, `additionalProperties`, `anyOf`, `oneOf`,
`allOf`, `format`, `minimum`, `maximum`, `minLength`, `maxLength`, `pattern`,
`const`, `exclusiveMinimum`, `exclusiveMaximum`, `minItems`, `maxItems`,
`uniqueItems`, `$ref`, `$defs`) and recurses into the container-like ones.

### Files to change

1. `plugins/mcp-shared/src/mcp_shared/runtime.py`
   - Add `_sanitize_input_schema(schema: Any) -> dict[str, Any]` helper.
   - Add a small set of module-level constants for the standard keyword allowlist
     and the set of keywords that hold sub-schemas (for recursion).
   - Call `_sanitize_input_schema(input_schema)` in `_extract_discovered_tools`
     before constructing each `MCPDiscoveredTool`.
2. `plugins/mcp-shared/tests/test_runtime.py`
   - Add unit tests for `_sanitize_input_schema` covering: enum→string+enum,
     optional→inner, shape→properties, element→items, null-valued optional
     fields omitted, non-standard keys dropped, already-valid schema unchanged.
   - Add a regression test for `_extract_discovered_tools` using a fake raw
     tool list whose `inputSchema` mirrors the real `sheets_merge_cells` shape,
     asserting the output `input_schema` is valid JSON Schema.

### Verification

- `pytest plugins/mcp-shared/tests -q` (default package-local run).
- Re-run the reproduction script (connect to `mcp-gsheets`, convert schemas,
  send to OpenRouter) to confirm the 400 is gone. This is a manual integration
  check, not an automated test, because it requires live credentials and
  network access.

### Implementation decisions and open questions

- **`def` handling:** when a node has both `def` and sibling fields (the
  gsheets pattern), merge `def` as the base and let non-standard sibling fields
  override, then run the rest of the sanitization. This keeps behavior stable
  when `def` and siblings agree (the common case) and prefers the expanded
  sibling form when they differ.
- **`minValue`/`maxValue`:** drop rather than convert to `minimum`/`maximum`.
  The gsheets `minValue`/`maxValue` are Effect-internal numeric constraints
  that may not be directly equivalent to JSON Schema `minimum`/`maximum`
  (e.g. they appear alongside `isInt`/`isFinite` metadata). Converting them
  risks introducing incorrect constraints; dropping them is safe because the
  tool description already conveys the intent to the model.
- **Recursion safety:** the helper uses an explicit `seen` set keyed by `id()`
  to guard against cyclic schemas (which would be malformed but cheap to
  defend against).
- **No interop/provider changes:** the conversion chain
  (Anthropic → OpenAI chat) already works; the only problem is the payload
  passing through unchanged. Fixing at the MCP boundary is sufficient.

### Documentation

No user-facing documentation changes are required. The MCP plugin docs already
state that `inputSchema` is exposed as-is; after this fix it is sanitized to
valid JSON Schema, which is what users already expect. If a maintainer later
adds a note about schema sanitization, it belongs in
`plugins/mcp-shared/docs/development/` (owner-appropriate location), not in
this task.

### Task checklist

- [x] Add `_sanitize_input_schema` helper in `runtime.py`
- [x] Wire it into `_extract_discovered_tools`
- [x] Add unit tests for the helper
- [x] Add regression test for `_extract_discovered_tools`
- [x] Run `pytest plugins/mcp-shared/tests -q`
- [x] Manual integration check against live `mcp-gsheets` + OpenRouter

### Requirement verification

- "MCP discovered tool `input_schema` is sanitized to valid JSON Schema":
  `test_extract_discovered_tools_sanitizes_non_standard_input_schema` asserts
  the output of `_extract_discovered_tools` for a non-standard input contains
  only standard JSON Schema keywords (via `_assert_no_non_standard_fields`).
- "Non-standard enum/optional/shape/element converted": dedicated unit tests
  per pattern (`test_sanitize_input_schema_converts_enum_with_entries_only`,
  `test_sanitize_input_schema_unwraps_optional_inner_type`,
  `test_sanitize_input_schema_maps_shape_to_properties_and_element_to_items`).
- "Already-valid JSON Schema passes through unchanged":
  `test_sanitize_input_schema_preserves_already_valid_json_schema` asserts
  deep equality.
- "Covered by unit tests including a regression test": the regression test
  uses the real `sheets_merge_cells` schema shape.
- "Live 400 is gone": manual integration check connected to `mcp-gsheets`,
  converted all 44 tool schemas through the full chain, and sent a request to
  OpenRouter with `anthropic/claude-haiku-4.5`; HTTP 200 with a normal
  assistant response. Before the fix, the same request returned HTTP 400 from
  Amazon Bedrock, Google Vertex, and Anthropic with
  `tools.14.custom.input_schema: JSON schema is invalid`.

## Implementation notes

- Added `_FakeTool` and `_FakeListToolsResult` helper classes in the test file
  because `_extract_discovered_tools` reads fields via `model_dump()` or
  `getattr` (matching the MCP SDK pydantic models), so plain dicts do not work.
- `black` reformatted both changed files; re-ran tests to confirm no regressions.

## Completion notes

**Outcome:** the gsheets MCP server schema error is fixed. The platform now
sanitizes non-standard MCP `inputSchema` to valid JSON Schema draft 2020-12 at
the MCP runtime boundary (`_extract_discovered_tools` in
`plugins/mcp-shared/src/mcp_shared/runtime.py`), before the schemas reach the
tool interop / provider layers.

**Files changed:**
- `plugins/mcp-shared/src/mcp_shared/runtime.py`: added
  `_sanitize_input_schema` + helpers (`_sanitize_schema_node`,
  `_sanitize_schema_map`, `_extract_enum_values`) and the
  `_STANDARD_SCHEMA_KEYWORDS` / `_SUBSCHEMA_*` constants; wired the sanitizer
  into `_extract_discovered_tools`.
- `plugins/mcp-shared/tests/test_runtime.py`: added 8 unit tests + 2 fake
  helper classes (`_FakeTool`, `_FakeListToolsResult`).

**Verification performed:**
- `pytest plugins/mcp-shared/tests -q`: 35 passed (34 existing + 8 new; one
  existing test was already counted in the 34).
- `pytest plugins/claude-tools/tests -q -m 'not integration'`: 114 passed,
  9 deselected (live-backend integration tests).
- `pytest plugins/claude-tools/tests/test_claude_mcp_tool.py -q`: 13 passed.
- `pytest plugins/codex-tools/tests/test_mcp_tool.py -q`: 7 passed.
- `pytest plugins/mcp-runtime-app/tests -q`: 21 passed.
- `ruff check` and `black` on both changed files: clean.
- Manual end-to-end check: connected to `mcp-gsheets` via `MCPRuntimeManager`,
  ran all 44 tools through `ClaudeMCPTool._prepare_tools` →
  `registry.convert_schemas` → OpenRouter `anthropic/claude-haiku-4.5`:
  HTTP 200 (was HTTP 400 before the fix).

**Plan deviations:** none.

**Unresolved / deferred:** the upstream `mcp-gsheets` package should be
reported to its maintainer (the MCP spec requires `inputSchema` to be a valid
JSON Schema object, and this server violates that contract). The
platform-side sanitization is valuable as defense-in-depth regardless.