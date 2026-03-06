# Design Desktop Rendering and Interaction Model for Interceptor Prompts

Short description: Design desktop UX for arbitrary interceptor prompt forms/buttons, including pending prompt visibility and resume-aware interaction semantics.

Parent Task: tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/000-main.md
Depends On: tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/010-design-toolplugin-interceptor-contract-and-prompt-schema.md

## Scope

- Define desktop UI model for rendering plugin-defined prompt forms and button sets.
- Define prompt presentation across inline chat, modal dialog, or popover patterns.
- Define response flow and lifecycle feedback in multi-window desktop environments.
- Define behavior when prompt state changes from another client/session view.
- Define rendering semantics for `interception_current.pending_prompt` and `interception_phases` event entries.

## Out Of Scope

- Core/application backend implementation.
- Mobile UX design.

## Proposed Steps

1. Review current desktop action-dialog and window management paths.
2. Evaluate suitable presentation modes (inline, modal window, popover) for prompt complexity.
3. Define mapping from generic prompt schema to desktop input controls.
4. Define keyboard accessibility and default action behavior where any button submits and exactly one button is the Enter-default.
5. Define pending/resolved prompt indicators and suspended-request affordances using current snapshot + event history.
6. Define synchronization behavior for cross-tab/cross-window prompt updates.
7. Produce desktop design spec and implementation notes.

## Deliverables

- Desktop prompt rendering specification.
- Interaction rules for modal/popover/inline presentations.
- State synchronization, metadata-contract, and accessibility guidelines.

## Success Criteria

1. Desktop design supports arbitrary prompt forms/buttons without policy-specific hardcoding.
2. Prompt lifecycle state is visible and understandable across desktop surfaces.
3. Design correctly reflects event-based prompt history and current pending prompt semantics.
4. Design is compatible with existing desktop window/dialog architecture.

## Context References

- `desktop/crystal-lattice-control-desktop-rn/src/windows/ApplicationActionDialogWindow.tsx#L66`
- `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`
- `desktop/crystal-lattice-control-desktop-rn/src/panels/SessionsPanel.tsx`
- `desktop/crystal-lattice-control-desktop-rn/src/windows/desktopWindowManager.ts#L82`
- `packages/frontend-rn-components/src/ApplicationActionDialog.tsx#L51`
