# Extractable subcomponents (candidates + boundaries)

This document lists *candidate subcomponents* to extract from existing mixed-responsibility mobile components.

These are suggestions/hints (not final decisions). The goal is to reuse meaningful UI behavior across mobile + desktop while allowing platform-specific rendering, especially for macOS.

## Guiding principles

- Prefer extracting components that:
  - have reusable interaction logic (expand/collapse, action menus, pinning, tab state)
  - can be customized via render props / slots
  - do not lock the desktop app into mobile libraries (markdown renderer, icon library, modal-only UX)

- Avoid extracting components that:
  - directly call `AgentBackend`
  - require a single shared layout
  - force markdown/syntax-highlighting implementation choices

## Current status (already extracted vs scheduled)

This doc originally listed *candidates*. As of Phase 5 work, some items are now implemented and others are explicitly scheduled in `081–088`.

### Already extracted (implemented)

- Shared actions menu model + UI primitives
  - `packages/frontend-rn-components/src/actions/useActionsMenuModel.ts:1`
  - `packages/frontend-rn-components/src/actions/ActionsMenuBar.tsx:1`
  - `packages/frontend-rn-components/src/actions/MenuSurfaces.tsx:1`
- Shared session actions wrapper
  - `packages/frontend-rn-components/src/actions/SessionActionsBar.tsx:1`
- Shared application action dialog
  - `packages/frontend-rn-components/src/ApplicationActionDialog.tsx:1`
- Shared pinned-actions persistence hooks
  - `packages/frontend-sdk-react/src/usePersistentPinnedActions.ts:1`
  - `packages/frontend-sdk-react/src/usePersistentStringArray.ts:1`

### Scheduled extractions / decisions (planned)

- Session settings UI: extract a shared form body and migrate mobile to use it
  - Planned in: `tasks/20260202-desktop-macos-frontend/082-desktop-session-settings-ui.md`
- Message actions: extract action definitions + a shared `MessageActionsBar`
  - Planned in: `tasks/20260202-desktop-macos-frontend/085-desktop-message-actions-and-sharing.md`
- Markdown renderer: intentionally **not shared** (desktop-only implementation is allowed)
  - Planned in: `tasks/20260202-desktop-macos-frontend/083-desktop-markdown-renderer.md`

## From `MessageBubble.tsx`

Source: `mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx:1`

Practical note:

- It may be worthwhile to share the entire `MessageBubble` component (or the per-role bubble components) between mobile + desktop, treating it as a “mostly visual” building block.
- If we do this, keep the message list layout and controller wiring platform-specific.

### A) Collapsible content block (expand/collapse)

Used for tool output, reasoning, and tool-call details.

Candidate API:

- `ExpandableSection`
  - props:
    - `title?: string`
    - `expanded: boolean` / `onExpandedChange`
    - `collapsedPreview?: ReactNode` (e.g. single-line content)
    - `children` as expanded body
    - optional `maxHeight` and `scrollable`

Desktop-specific rendering hint:

- On macOS, hover affordances and focus ring can be applied at this level.

### B) Tool output preview row

There is already logic to compute a single-line preview and toggle expansion.

Candidate split:

- `ToolOutputPreview`
  - input: full tool output text + optional tool name
  - output: header row + collapsed preview + expand toggle

Keep the actual expanded renderer customizable.

### C) Tool calls list preview vs expanded list

There is logic for:

- collapsed summary: “N tool calls: …names…”
- expanded list with per-call preview text

Extract:

- `ToolCallsDisclosure`
  - takes `toolCalls` metadata + optional preview strings
  - renders collapsed summary and expanded list via render props

### D) Message footer renderer (UI schema driven)

MessageBubble computes footer parts using UI schema elements and `extractByPath/renderTemplate`.

Potential extraction:

- `MessageFooterParts`
  - input: `message`, `footerElements`
  - output: `string[]`
- `MessageFooterRow`
  - renders those parts with a provided `renderPart` or simple join

This would help both mobile and desktop render consistent metadata without sharing message layout.

### E) Message actions integration wrapper

MessageBubble repeatedly wires `MessageActionsBar` with role-based pin state.

Extract:

- `MessageActionsSlot`
  - input: `role`, `pinnedActions`, `onAction`, `onChangePinned`
  - internally merges base actions + plugin actions and renders `PinnedActionsBar`

This keeps “action bar wiring” consistent while leaving the message UI distinct.

## From `MessageActionsBar.tsx` and `SessionActionsBar.tsx`

Sources:

- `mobile/crystal-lattice-control-rn/src/components/MessageActionsBar.tsx:1`
- `mobile/crystal-lattice-control-rn/src/components/SessionActionsBar.tsx:1`

### A) Shared “actions menu model”

Status: implemented in `@crystal-lattice/frontend-rn-components`.

- `useActionsMenuModel` now lives at `packages/frontend-rn-components/src/actions/useActionsMenuModel.ts:1`.
- Desktop and mobile share the same menu content + surfaces via:
  - `packages/frontend-rn-components/src/actions/ActionsMenuContent.tsx:1`
  - `packages/frontend-rn-components/src/actions/ActionsMenuBar.tsx:1`
  - `packages/frontend-rn-components/src/actions/MenuSurfaces.tsx:1`

Remaining planned extraction:

- `MessageActionsBar` wrapper is still mobile-local and scheduled to move into the shared package.
  - See: `tasks/20260202-desktop-macos-frontend/085-desktop-message-actions-and-sharing.md`

### B) Menu surface abstraction

We want to keep options open for macOS-native menu/popover later.

Suggested boundary:

- shared: “menu content” (items, grouping, selection)
- platform: “menu surface” (modal, dropdown overlay, native NSMenu)

## From `ApplicationActionDialog.tsx`

Source: `mobile/crystal-lattice-control-rn/src/components/ApplicationActionDialog.tsx:1`

### A) Schema-driven form body

This file has reusable logic:

- field iteration
- required validation
- type parsing (`integer`, `number`, `boolean`, `multiline`)
- `prefill_from` resolution via `$session.*` and `$message.*`

Status: implemented and shared.

- Shared implementation: `packages/frontend-rn-components/src/ApplicationActionDialog.tsx:1`.
- Desktop hosts it using window/popover infrastructure; mobile hosts it as a modal.

## From `AgentSwitchModal.tsx`

Source: `mobile/crystal-lattice-control-rn/src/components/AgentSwitchModal.tsx:1`

### A) Agent selector as a reusable panel

Extract:

- `AgentSelector`
  - input: agents list + selected id + loading
  - output: a list with selection

Then:

- mobile uses modal container
- desktop uses dropdown/panel

## From `SessionSettingsModal.tsx`

Source: `mobile/crystal-lattice-control-rn/src/components/SessionSettingsModal.tsx:1`

### A) Settings model (preferred)

This file mixes:

- data loading (ui schema, overrides, base config)
- conversion into “fields”
- patch/revert logic
- and the actual UI widgets (Switch, TextInput, option selection)

Update: initial extraction was done as shared RN UI components, but the project moved to a better architecture:

- Rendering is app-owned (mobile + desktop each render their own UI).
- Shared code is logic-only and lives in `@crystal-lattice/frontend-sdk-react` (`sessionSettings/*`).
- Legacy shared RN UI components (`SessionSettingsCard` / `SessionSettingsSurface`) were removed.

See: `tasks/20260202-desktop-macos-frontend/082-desktop-session-settings-ui.md`

### B) Optional shared field renderer interface

If sharing a settings UI wrapper is still useful, keep it skinnable:

- `SessionSettingsPanel`
  - takes `fields` and render slots:
    - `renderBooleanField(field)`
    - `renderSelectField(field)`
    - `renderTextField(field)`

But avoid forcing a “native preferences window” design.

## From `SessionsScreen.tsx`

Source: `mobile/crystal-lattice-control-rn/src/SessionsScreen.tsx:1`

Candidate extraction:

- `SessionListItem` presentational component extracted from the session row renderer (aka `renderSessionItem`).
- Expected usage:
  - desktop: render items in a desktop-specific list container
  - mobile: render items in a `FlatList`

Keep this component dumb (no backend calls); it should accept:

- `session: SessionSummary`
- `onPress()`
- optional accessory slots (actions menu, badges)
