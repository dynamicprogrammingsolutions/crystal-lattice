# Anthropic Server Web Search, Web Fetch, And Citations

Add opt-in Anthropic server-side web search and web fetch while preserving the
existing client-side Claude tools as explicit alternatives.

## Requirements checklist

### Functional requirements

- [ ] `AnthropicWebSearchExtension` can enable and configure the supported
  Anthropic server web-search tool.
- [ ] `AnthropicWebFetchExtension` can enable and configure the supported
  Anthropic server web-fetch tool.
- [ ] Search and fetch request controls include supported domain, location,
  usage-limit, result-size, and citation options.
- [ ] Streamed server-tool events, results, citations, and sources are mapped
  into stable core metadata and display contracts.
- [ ] Provider-native web-tool history remains reusable on later turns.
- [ ] Users can explicitly select Anthropic server web tools, existing
  `claude-tools` web tools, or neither.

### Non-functional requirements

- [ ] Enabling server web tools never silently removes, renames, or duplicates
  the existing `ClaudeWebSearchTool` or `ClaudeWebFetchTool`.
- [ ] URL, citation, source, and retrieved-content metadata are bounded and
  safe for persistence and display.
- [ ] Provider feature configuration, UI, enablement, and public metadata live
  in the extensions.
- [ ] Compatible endpoints that do not support server web tools omit the
  request fields and present no misleading UI.

Parent Task:
`tasks/20260824-direct-claude-provider-and-plugin-login/000-main.md`

Depends On:

- `tasks/20260824-direct-claude-provider-and-plugin-login/010-direct-claude-provider-runtime.md`

Specification:

- `plugins/anthropic-compatible/docs/development/specifications/anthropic-provider/index.md`

## Supporting facts

- The repository already has client-side Claude-compatible web search and web
  fetch tools backed by configurable local integrations.
- Anthropic server tools use provider-native content blocks and citation/source
  metadata rather than the ordinary client tool-result loop.
- Local Ollama does not provide these Anthropic server tools.

## Execution plan

Status: Draft

Extend the Anthropic package specification with a server-web-tools refinement
before implementation. Add separate search and fetch extensions sharing a
small provider-native server-tool mapper where appropriate. Keep tool
selection explicit so existing client tools remain stable.

### Implementation decisions and open questions

- Decision: search and fetch use separate extension classes but may share
  citation/source normalization helpers.
- Decision: server tools are opt-in.
- Open: select the exact config key that chooses server versus client web
  tooling without coupling the provider package to a specific tool bundle.

### Documentation

- Document server versus client web tools, supported request controls,
  citations, compatible-endpoint limitations, cost, and troubleshooting.
- Update the package specification and requirements before implementation.

### Task checklist

- [ ] Extend the package specification and requirements.
- [ ] Define explicit server/client web-tool selection.
- [ ] Implement web-search request and stream mapping.
- [ ] Implement web-fetch request and stream mapping.
- [ ] Add citation/source normalization and display metadata.
- [ ] Add deterministic extension and application tests.
- [ ] Run selective hosted search and fetch smokes.
- [ ] Document delivered behavior.

### Requirement verification

- Hosted search and fetch requests produce source-attributed assistant results.
- Existing client web tools remain independently selectable and unchanged.
- Compatible endpoints without server-tool support omit the features cleanly.

### Additional implementation verification

- Citation indices remain aligned after streaming and history reload.
- Retrieved content and source lists are bounded before session persistence.