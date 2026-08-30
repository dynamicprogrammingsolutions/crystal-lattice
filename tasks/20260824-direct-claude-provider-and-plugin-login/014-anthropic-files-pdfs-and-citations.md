# Anthropic Files, PDFs, And Document Citations

Add secure Anthropic Files API integration, PDF/document input, and document
citations on top of the baseline image attachment contract.

## Requirements checklist

### Functional requirements

- [ ] Users can upload, list, reference, download where supported, and delete
  provider files through plugin-owned actions.
- [ ] Session attachments can be sent as supported image or PDF/document
  references without embedding unnecessary data in session JSON.
- [ ] PDF visual and text content maps through provider-native document blocks.
- [ ] Document citations are normalized into stable metadata and display
  contracts.
- [ ] Provider-file ownership and cleanup behavior are explicit across
  sessions, logout, and application restart.

### Non-functional requirements

- [ ] Workspace-scoped provider files cannot be exposed through an unrelated
  connection or session.
- [ ] Credentials, file contents, and signed/provider URLs are not written to
  ordinary logs.
- [ ] Local session assets remain distinct from remote provider file IDs.
- [ ] Compatible endpoints without Files/PDF support retain baseline image
  attachment behavior.

Parent Task:
`tasks/20260824-direct-claude-provider-and-plugin-login/000-main.md`

Depends On:

- `tasks/20260824-direct-claude-provider-and-plugin-login/010-direct-claude-provider-runtime.md`

Specification:

- `plugins/anthropic-compatible/docs/development/specifications/anthropic-provider/index.md`

## Execution plan

Status: Draft

Define a Files/PDF specification refinement before implementation. Reuse the
application-owned session asset store for local uploads while maintaining an
explicit mapping to remote Anthropic file IDs and their broader workspace
ownership.

### Implementation decisions and open questions

- Decision: local asset IDs and remote provider file IDs are separate.
- Decision: PDF/document support is not part of 010.
- Open: define remote-file cleanup defaults and cross-session reuse policy.

### Documentation

- Document upload/reference/delete behavior, ownership, supported formats,
  limits, citations, compatible-endpoint degradation, and privacy.

### Task checklist

- [ ] Define the Files/PDF specification refinement.
- [ ] Implement provider-file actions and persistence mapping.
- [ ] Implement PDF/document request conversion.
- [ ] Implement document citation normalization.
- [ ] Add authorization, cleanup, and redaction tests.
- [ ] Add hosted PDF/citation tests.
- [ ] Document delivered behavior.

### Requirement verification

- A stored PDF can be referenced in a request and produce citation-aware
  output.
- Logout/deletion behavior follows the documented remote-file policy.
- Unrelated sessions cannot access remote files without explicit authorization.

### Additional implementation verification

- Large files never enter session JSON or ordinary diagnostics.
- Remote-file errors retain safe provider request identifiers.