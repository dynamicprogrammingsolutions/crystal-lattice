# Native macOS Table View POC for Message List

## Task Description

Implement a proof-of-concept native NSTableView-based virtualization component to replace ScrollView in the message list (ChatPane). This addresses scroll performance issues and variable-height row challenges that React Native's virtualization cannot solve on macOS.

## Background

Current solutions have failed:
- React Native's VirtualizedList/FlatList don't work properly on react-native-macos
- Manual windowing (like the SessionsPanel sliding window) requires complex scroll adjustment logic
- Variable-height message bubbles make estimated heights unreliable

## Goal

Create a minimal native module wrapping NSTableView that:
1. Renders only visible message bubbles (native virtualization)
2. Handles variable-height rows correctly
3. Integrates with existing ChatPane component
4. Proves the concept works before full implementation

## Non-Goals

- Full production-ready component
- Cross-platform support (macOS only for POC)
- Complex features (drag-drop, swipe actions, etc.)

## Subtasks

1. **010-research.md** - Research current message list implementation and NSTableView integration patterns
2. **020-native-module.md** - Create basic RCTViewManager subclass for NSTableView
3. **030-variable-height.md** - Implement dynamic row height measurement strategy
4. **040-integration.md** - Wire up to ChatPane with mock data for testing

## Files to Examine

- `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx` - Message list current implementation
- `desktop/crystal-lattice-control-desktop-rn/src/chat/DesktopMessageBubble.tsx` - Row rendering complexity
- `desktop/crystal-lattice-control-desktop-rn/macos/` - Existing native module structure

## Success Criteria

- POC renders 1000+ messages with smooth 60fps scrolling
- Variable-height bubbles display correctly without layout jumps
- Height measurement/caching works for message content
- Can be toggled on/off in ChatPane for A/B comparison
