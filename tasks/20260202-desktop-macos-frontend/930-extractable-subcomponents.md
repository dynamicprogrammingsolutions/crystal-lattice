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

Both components re-implement:

- merge base action defs + plugin action defs
- map by key
- filter by allowed/available
- pin/unpin

Extract a shared hook:

- `useActionsMenuModel({ baseActions, extraActions, pinned, availableActions })`
  - returns:
    - `actionsByKey`
    - `visiblePinned`
    - `visibleOverflow`
    - `togglePinned(key)`

Then each platform supplies:

- `ActionsMenuView` (modal on mobile, dropdown on desktop)

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

Extract:

- `ActionForm` (no modal)
  - controlled by:
    - `dialog` schema
    - `prefillContext`
    - `onSubmit(values)`
    - `onCancel()`

Platform note:

- Desktop can host this form in a dropdown/inspector; mobile can host it in a modal.

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

Recommended extraction split:

- `useSessionSettingsModel(backend, sessionId)`
  - returns:
    - `loading`, `error`
    - `fields: SettingField[]`
    - `setValue(key, value)`
    - `revert(key)`
    - `refresh()`

Then desktop can adopt native-ish widgets where possible.

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
