# Anthropic Image Attachments

Implement image attachment actions, UI, Anthropic-native image blocks, and
compatible-endpoint verification outside the core provider runtime.

## Requirements checklist

### Functional requirements

- [ ] `AnthropicAttachmentsExtension` owns image attachment configuration, UI,
  session asset actions, request shaping, and public metadata.
- [ ] Stored session images can be sent as supported Anthropic-native image
  blocks without embedding unnecessary binary data in session JSON.
- [ ] Multimodal tool results preserve image and display metadata through the
  Anthropic tool-result contract.
- [ ] Official Anthropic and local Ollama profiles expose only their supported
  image source types.
- [ ] Image attachments survive persistence/reload and a later provider
  request.

### Non-functional requirements

- [ ] Local asset IDs remain distinct from provider-native content blocks and
  future remote Files API IDs.
- [ ] Image bytes, data URLs, and local paths do not enter ordinary logs.
- [ ] The extension reuses application-owned session asset actions rather than
  introducing provider-owned file persistence.
- [ ] PDF/document support remains in subtask 014.

Parent Task:
`tasks/20260824-direct-claude-provider-and-plugin-login/000-main.md`

Depends On:

- `tasks/20260824-direct-claude-provider-and-plugin-login/010-direct-claude-provider-runtime.md`

Specification:

- `plugins/anthropic-compatible/docs/development/specifications/anthropic-provider/index.md`

Primary requirement ID:

- `ANTH-010`

## Supporting facts

- The reference OpenAI-compatible provider already demonstrates a provider
  attachment extension backed by session asset actions.
- Ollama's Anthropic-compatible endpoint supports base64 image input but not
  every official Anthropic image source type.
- Remote Anthropic Files API and PDF ownership have broader security and
  lifecycle concerns tracked by subtask 014.

## Execution plan

Status: Draft

Reuse the existing session-asset action contract and implement only the
Anthropic-specific image policy and native conversion. Keep ordinary provider
messages independent from the extension and capability-gate image UI and
request fields by profile.

### Implementation decisions and open questions

- Decision: image attachments are not part of 010.
- Decision: base64/session-owned images are the first compatible contract.
- Decision: multimodal tool results are verified here.
- Open: decide whether official URL image sources should ship in the first
  attachment implementation or a later refinement.

### Documentation

- Document image storage, supported formats/sources, profile limitations,
  tool-result images, security, and cleanup.
- Update the package specification and requirement evidence during delivery.

### Task checklist

- [ ] Define the extension config, UI, tags, and source policy.
- [ ] Implement store/delete/download session asset actions.
- [ ] Implement Anthropic-native image request conversion.
- [ ] Implement multimodal tool-result conversion.
- [ ] Add deterministic extension and application tests.
- [ ] Run enabled Ollama image verification.
- [ ] Run selective hosted Anthropic image verification.
- [ ] Document delivered behavior and update evidence.

### Requirement verification

- A stored image is usable in an official Anthropic request.
- A stored image is usable through the documented Ollama-compatible profile.
- Multimodal tool results survive a tool loop and session reload.

### Additional implementation verification

- Unsupported source types are hidden or rejected before transport.
- Binary data and secrets remain absent from logs and session JSON.