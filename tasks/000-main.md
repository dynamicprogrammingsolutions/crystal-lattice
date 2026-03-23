# AI Agent Platform - Task Tree

Master index of all task directories and their completion status.

## Quick Stats

| Category | Count |
|----------|-------|
| All Done | 1 |
| Mostly Done | 8 |
| Partially Done | 9 |
| Not Done | 3 |
| **Total** | **21** |

---

## Task Tree

### 20260128 - Sandboxing Prerequisites ❌ NOT DONE
- [ ] **20260128-sandboxing-prereqs/000-main.md**
  - [ ] `010-standardize-workspace-path-semantics.md`
  - [ ] `020-expose-workspace-ui-elements.md`
  - [ ] `030-add-session-override-helper-apis.md`
  - [ ] `040-session-aware-app-plugin-ui-and-conditions.md`
  - [ ] `050-app-plugin-lifecycle-hooks-for-cleanup.md`

### 20260129 - Events (No Full Session) ✅ ALL DONE
- [x] **20260129-events-no-full-session/000-main.md** (9/9 complete)
  - [x] `005-sdk-reducer-prep-no-ux-change.md`
  - [x] `010-event-contract.md`
  - [x] `020-python-event-producers.md`
  - [x] `030-python-tests-and-docs.md`
  - [x] `040-sdk-event-types.md`
  - [x] `050-sdk-pure-reducer.md`
  - [x] `060-chatcontroller-integration.md`
  - [x] `070-mobile-remove-reloads.md`
  - [x] `080-mobile-auto-reload-on-dirty.md`
  - [x] `090-plugin-action-reload-control.md`

### 20260129 - Frontend SDK ⚠️ MOSTLY DONE (9/11)
- [x] **20260129-frontend-sdk/000-main.md**
  - [x] `010-phase-0-monorepo-layout.md`
  - [x] `020-phase-1-types-and-helpers.md`
  - [x] `030-phase-2-agentbackend-restbackend.md`
  - [x] `040-phase-3-bridge-transport.md`
  - [x] `050-phase-4-headless-controllers.md`
  - [x] `060-phase-4-4-chat-persistence-scroll-reconcile.md`
  - [x] `065-phase-4-5-event-contract-and-reducer.md`
  - [ ] `070-phase-5-desktop-frontend.md` ❌
  - [ ] `080-phase-6-vscode-extension.md` ❌

### 20260130 - OpenRouter Usage/Cost ❌ NOT DONE
- [ ] **20260130-openrouter-usage-round-cost-and-ui-schema/000-main.md**
  - [ ] `010-config-aware-ui-schema-and-conditions.md`
  - [ ] `020-openrouter-round-cost.md`
  - [ ] `030-openrouter-cumulative-and-deleted-history-cost.md`
  - [ ] `040-openrouter-token-breakdown-and-ui-toggles.md`
  - [ ] `050-tests-and-fixtures.md`

### 20260202 - Desktop macOS Frontend ⚠️ MOSTLY DONE (15/18)
- [x] **20260202-desktop-macos-frontend/000-main.md**
  - [x] `010-shared-components-package.md`
  - [x] `020-rn-macos-scaffold-and-version.md`
  - [x] `030-desktop-metro-and-ts-wiring.md`
  - [x] `040-shared-connection-model.md`
  - [x] `050-desktop-shell-layout.md`
  - [x] `060-desktop-connections-panel.md`
  - [x] `065-desktop-tab-strip-styles-and-view-menu.md`
  - [ ] `066-desktop-theming-semantic-colors.md` ❌
  - [x] `070-desktop-sessions-pane.md`
  - [x] `080-desktop-chat-tabs-and-chat-pane.md`
  - [x] `081-desktop-chat-header-and-session-actions.md`
  - [x] `082-desktop-session-settings-ui.md`
  - [x] `083-desktop-markdown-renderer.md`
  - [x] `084-desktop-rich-assistant-rendering.md`
  - [ ] `085-desktop-session-status-bar.md` ❌
  - [x] `086-desktop-plugin-actions-in-chat.md`
  - [x] `087-desktop-chat-state-persistence.md`
  - [ ] `089-session-metadata-single-source-of-truth.md` ❌
  - [ ] `090-smoke-tests-and-docs.md` ❌

### 20260213 - Session Plugins UI ⚠️ MOSTLY DONE (4/5)
- [x] **20260213-session-plugins-ui/000-main.md**
  - [x] `010-server-endpoints.md`
  - [x] `020-shared-frontend-sdk.md`
  - [x] `030-shared-ui-and-controller.md`
  - [ ] `040-mobile-integration.md` ❌
  - [x] `050-desktop-integration.md`

### 20260215 - Multipart Upload ⚠️ PARTIALLY DONE (8/11)
- [x] **20260215-multipart-upload/000-main.md**
  - [x] `010-core-message-multipartcontent.md`
  - [x] `020-server-append-multipartcontent.md`
  - [x] `030-frontend-sdk-types-and-payloads.md`
  - [x] `040-plugin-ui-schema-composer-attachments.md`
  - [x] `050-provider-mapping-multipartcontent.md`
  - [x] `060-mobile-composer-attachments.md`
  - [x] `070-desktop-composer-attachments.md`
  - [x] `075-desktop-composer-attachment-plus-and-metadata-window.md`
  - [ ] `080-docs-and-compat.md` ❌
  - [ ] `090-asset-prepare-upload-action.md` ❌
  - [x] `100-bridge-chunked-http-over-websocket.md`

### 20260217 - Bridge Dedup + Atomic Send ⚠️ MOSTLY DONE (3/5)
- [x] **20260217-bridge-dedup-and-atomic-send/000-main.md**
  - [x] `010-elixir-single-target-routing-and-takeover.md`
  - [x] `020-python-bridgeclient-takeover-and-local-guard.md`
  - [ ] `030-fastapi-send-singleflight-idempotency.md` ❌
  - [ ] `040-fastapi-atomic-append-send-endpoint.md` ❌
  - [x] `050-frontend-sdk-use-atomic-and-idempotency.md`

### 20260225 - Codex Tools Parity ❌ NOT DONE
- [ ] **20260225-codex-tools-parity/000-main.md**
  - [ ] `010-apply-patch-schema.md`
  - [ ] `020-bash-tool-round-1-schema.md`
  - [ ] `030-bash-tool-round-2-output-and-limits.md`
  - [ ] `040-bash-tool-round-3-sandboxing.md`
  - [ ] `050-update-plan-tool.md`
  - [ ] `060-view-image-tool.md`
  - [ ] `070-exec-command-and-write-stdin-tools.md`

### 20260301 - Tool Plugin Interceptor ❌ NOT DONE
- [ ] **20260301-tool-plugin-interceptor-and-prompt-lifecycle/000-main.md**
  - [ ] `010-design-toolplugin-interceptor-contract-and-prompt-schema.md`
  - [ ] `020-implement-toolplugin-interception-tool-loop-and-prompt-lifecycle-tests.md`
  - [ ] `030-design-mobile-rendering-for-interceptor-prompts.md`
  - [ ] `040-design-desktop-rendering-for-interceptor-prompts.md`
  - [ ] `050-build-reference-interceptor-tool-plugin-scenario.md`
  - [ ] `060-implement-tool-handler-and-formatter-upgrade-from-956.md`

### 20260303 - Provider Plugin Docs ⚠️ PARTIALLY DONE (4/7)
- [x] **20260303-provider-plugin-docs/000-main.md**
  - [x] `010-template-python-provider.md`
  - [x] `020-provider-plugins-doc.md`
  - [ ] `030-other-doc-updates.md` ❌
  - [x] `040-template-provider-tests.md`
  - [x] `050-provider-extensions-doc.md`
  - [ ] `060-openai-compatible-reference-implementation.md` ❌
  - [ ] `070-update-existing-provider-implementations.md` ❌

### 20260305 - Cross-Framework Desktop Prototype ❌ NOT DONE
- [ ] **20260305-cross-framework-desktop-prototype/000-main.md**
  - [ ] `010-electron-desktop.md`
  - [ ] `020-javafx-swing-desktop.md`
  - [ ] `030-qt-desktop.md`
  - [ ] `040-flutter-dart-desktop.md`
  - [ ] `050-vscode-extension-webview.md`
  - [ ] `060-jetbrains-ide-plugin.md`

### 20260306 - Session UI Reload ⚠️ PARTIALLY DONE (1/5)
- [x] **20260306-session-ui-reload/000-main.md**
  - [ ] `010-a1-sdk-local-invalidation.md` ❌
  - [ ] `020-a2-server-events-cross-client.md` ❌
  - [ ] `030-c-etag-versioning.md` ❌
  - [ ] `040-settings-ui-use-shared-schema-controller.md` ❌
  - [x] `050-session-settings-controller.md`

### 20260307 - Native History Preservation ⚠️ PARTIALLY DONE (1/2)
- [x] **20260307-native-history-preservation-and-single-provider/000-main.md**
  - [ ] `010-no-silent-native-history-stripping.md` ❌
  - [x] `020-application-single-provider-core-selection.md`

### 20260309 - OpenRouter Responses Provider ⚠️ MOSTLY DONE (4/6)
- [x] **20260309-openrouter-responses-provider/000-main.md**
  - [x] `010-tool-schema-and-call-adapters-and-accessors.md`
  - [x] `020-implement-openrouter-responses-provider.md`
  - [ ] `030-fix-gpt54-phase-reasoning-streaming.md` ❌
  - [x] `040-refactor-native-history-to-responses-items.md`
  - [x] `050-fix-native-indices-and-slicing-integration.md`
  - [ ] `060-dual-provider-coexistence-tags-and-agent-application-integration.md` ❌

### 20260310 - OpenAI Responses Provider ⚠️ PARTIALLY DONE (13/26)
- [x] **20260310-openai-responses-provider/000-main.md**
  - [x] `010-architecture-scope-and-boundaries.md`
  - [x] `020-scaffold-openai-responses-plugin-package.md`
  - [x] `030-provider-core-conversion-and-nonstreaming-sdk.md`
  - [x] `040-provider-streaming-event-normalization-and-finalization.md`
  - [ ] `041-system-message-rendering-and-developer-role-followup.md` ❌
  - [ ] `042-native-compaction-instruction-message-exclusion.md` ❌
  - [ ] `043-native-message-preparation-for-compaction.md` ❌
  - [ ] `044-visible-rebuild-from-compacted-native-output.md` ❌
  - [ ] `046-manual-range-selection-native-compaction.md` ❌
  - [ ] `047-auto-compaction-after-request-complete.md` ❌
  - [x] `050-tools-extension-responses-api.md`
  - [x] `060-reasoning-extension-responses-api.md`
  - [x] `061-openai-responses-native-conversion-and-reasoning-followup-regressions.md`
  - [x] `062-cross-provider-agent-switch-native-rebuild-regressions.md`
  - [x] `070-usage-extension-responses-api.md`
  - [x] `080-verbosity-extension-responses-api.md`
  - [x] `090-integration-native-retention-and-regression-tests.md`
  - [x] `095-native-compaction-provider-extension.md`
  - [x] `100-docs-readme-and-config-examples.md`
  - [ ] `110-replaced-by-provider-extension-session-actions-020.md` ❌
  - [ ] `120-model-discovery-provider-ui-and-doc-followup.md` ❌
  - [ ] `130-prompt-caching-session-key-extension.md` ❌
  - [ ] `140-openai-image-pdf-upload-and-upload-modes.md` ❌
  - [ ] `141-session-asset-storage-and-action-driven-attachments.md` ❌
  - [ ] `150-web-search-extension-and-citation-preservation.md` ❌
  - [ ] `160-openai-flex-processing-extension-and-provider-retries.md` ❌

### 20260312 - Provider Extension Session Actions ⚠️ MOSTLY DONE (2/3)
- [x] **20260312-provider-extension-session-actions/000-main.md**
  - [x] `010-core-capability-and-contract.md`
  - [x] `020-frontend-wiring-provider-extension-actions.md`
  - [ ] `030-docs-provider-extension-session-actions.md` ❌

### 20260312 - Provider Extension Session Settings ⚠️ PARTIALLY DONE (1/2)
- [x] **20260312-provider-extension-session-settings-lifecycle/000-main.md**
  - [x] `010-provider-extension-session-settings-lifecycle.md`
  - [ ] `020-provider-extension-session-settings-lifecycle-docs.md` ❌

### 20260315 - Gemini/Qwen/Grok/Kimi Tools ⚠️ PARTIALLY DONE (8/14)
- [x] **20260315-gemini-qwen-grok-tool-packages/000-main.md**
  - Phase 1: Core file tools
    - [x] `010-reader-tools.md`
    - [x] `020-edit-and-write-tools.md`
    - [x] `030-list-grep-glob-tools.md`
  - Phase 1.5: Application and config support
    - [x] `040-agent-and-provider-plugin-package-config.md`
    - [x] `050-vendor-friendly-system-messages.md`
    - [x] `060-simplified-system-message-configs-and-minimal-dynamics.md`
    - [x] `070-core-rebuild-after-native-initialize-changes.md`
    - [x] `080-portable-default-config-and-compiled-system-message-ui.md`
  - Phase 2: Kimi + cross-vendor tools
    - [x] `090-kimi-tools.md`
    - [ ] `095-kimi-system-message.md` ❌
    - [ ] `100-shell-tools.md` ❌
    - [ ] `110-web-fetch-tools.md` ❌
    - [ ] `120-web-search-tools.md` ❌
    - [ ] `130-todo-tools.md` ❌

### 20260322 - Reference OpenAI-Compatible Provider ⚠️ PARTIALLY DONE (2/3)
- [x] **20260322-reference-openai-compatible-provider-generalization/000-main.md**
  - [x] `010-ollama-safe-generalization.md`
  - [x] `020-fireworks-hosted-provider-verification.md`
  - [ ] `030-other-provider-integration-matrix.md` ❌

### 20260323 - Native macOS TableView POC ❌ NOT DONE
- [ ] **20260323-native-macos-tableview-poc/000-main.md**
  - [ ] `010-research.md`
  - [ ] `020-native-module.md`
  - [ ] `030-variable-height.md`
  - [ ] `040-integration.md`

---

## Standalone Task Files (No 000-main.md)

- `20260128-sandboxing-feature.md` — Sandboxing feature (no subtasks)
- `20260223-bash-tool-plugins.md` — Bash tool plugins
- `20260223-javascript-tool-plugins.md` — JavaScript tool plugins
- `20260223-plugin-repo-autodetect.md` — Plugin repo autodetect

---

*Last updated: 2026-03-23*
