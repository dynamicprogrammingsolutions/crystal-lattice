# Subtask: Smoke tests + docs for desktop app

Add minimal documentation and perform smoke tests for the desktop RN macOS app.

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260202-desktop-macos-frontend/085-desktop-message-actions-and-sharing.md`

## Status

- [ ] Not started

## Work plan

### 1) Desktop README

- Create/update `desktop/crystal-lattice-control-desktop-rn/README.md` with:
  - prerequisites (Xcode)
  - install steps
  - run steps
  - how to point at a local python server

### 2) Smoke test checklist

- Manual connect
- Sessions list
- Open multiple sessions as tabs
- Send message in each tab
- Agent selector + settings are accessible (no blocking modals)
- Markdown rendering works for assistant messages (or is clearly off)
- Reasoning/tool call sections render reasonably
- Message actions (copy/modify) work

### 3) Record known limitations

- Manual connection only
- No discovery / bridge
- UI is minimal and will evolve
